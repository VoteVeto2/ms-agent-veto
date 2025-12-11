import logging
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Set, Union, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from src.llm_client import LLMClient
from src.schemas import MemoryType

# Configure module logger
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------

class MemoryEntry(BaseModel):
    """
    Represents a consolidated memory unit within the agent's context.
    
    Attributes:
        id: Unique identifier for the memory.
        content: The consolidated textual representation of the memory.
        raw_source: The original raw data (e.g., observation, document snippet) before consolidation.
        memory_type: Classification of memory (Episodic vs Semantic).
        tags: Auxiliary metadata/keywords for signal-enhanced indexing.
        embedding: Vector representation for semantic search (optional).
        importance: A score (1-10) indicating the significance of this memory.
        created_at: Timestamp of creation.
        last_accessed: Timestamp of last retrieval/update.
        access_count: Number of times this memory has been retrieved.
    """
    id: UUID = Field(default_factory=uuid4)
    content: str
    raw_source: Optional[str] = None
    memory_type: MemoryType = Field(default=MemoryType.EPISODIC)
    tags: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None
    importance: int = Field(default=5, ge=1, le=10)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0

    def touch(self):
        """Update access statistics."""
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1

class ConsolidationOutput(BaseModel):
    """Structured output schema for the LLM consolidation step."""
    summary: str = Field(..., description="Concise summary of the information.")
    tags: List[str] = Field(..., description="List of relevant keywords, entities, or topics.")
    memory_type: MemoryType = Field(..., description="Type of memory: 'episodic' for events, 'semantic' for facts.")
    importance: int = Field(..., description="Rated importance from 1 (trivial) to 10 (critical).")

# -----------------------------------------------------------------------------
# Memory Manager
# -----------------------------------------------------------------------------

class MemoryManager:
    """
    Manages the lifecycle of agent context: Consolidation, Indexing, Updating, and Forgetting.
    
    Implements:
    - Signal-enhanced Indexing: Uses tags and keywords.
    - Vector-based Indexing: Uses embeddings (if available) and numpy for similarity.
    - Lifecycle Management: Pruning old memories based on relevance and recency.
    """

    def __init__(
        self, 
        llm_client: LLMClient, 
        max_memory_size: int = 1000,
        embedding_dim: int = 1536
    ):
        """
        Initialize the Memory Manager.

        Args:
            llm_client: Instance of LLMClient for consolidation and query processing.
            max_memory_size: Maximum number of memory entries to retain.
            embedding_dim: Dimension of the vector embeddings.
        """
        self.llm = llm_client
        self.max_memory_size = max_memory_size
        self.embedding_dim = embedding_dim
        
        # Primary Storage
        self.memories: Dict[UUID, MemoryEntry] = {}
        
        # Indexes
        self.keyword_index: Dict[str, Set[UUID]] = {}
        # Note: In a production distributed system, use FAISS or a Vector DB.
        # Here we maintain a local cache for numpy operations.
        self._vector_cache: Dict[UUID, np.ndarray] = {}

    async def process_input(self, raw_content: str, source_metadata: Optional[Dict[str, Any]] = None) -> MemoryEntry:
        """
        Full pipeline: Consolidate raw input -> Index it -> Return the entry.
        """
        memory_entry = await self.consolidate(raw_content)
        if source_metadata:
            # Append metadata to raw_source or handle separately if schema permits
            memory_entry.raw_source = f"{memory_entry.raw_source} | Meta: {source_metadata}"
        
        await self.index(memory_entry)
        await self.prune()  # Check if we need to forget
        return memory_entry

    # -------------------------------------------------------------------------
    # 1. Consolidation
    # -------------------------------------------------------------------------
    
    async def consolidate(self, raw_content: str) -> MemoryEntry:
        """
        Transforms raw data into a durable format using the LLM.
        Extracts summary, tags, and importance.
        """
        logger.debug("Consolidating raw content...")
        
        system_prompt = (
            "You are the Memory Consolidation module of a Deep Research Agent. "
            "Your goal is to compress raw information into a concise, retrievable memory unit. "
            "Extract key facts, assign relevant tags for indexing, and rate importance."
        )
        
        user_prompt = f"Raw Content:\n{raw_content}\n\nAnalyze and consolidate this information."

        try:
            # Assuming LLMClient has a method for structured output
            # If the specific method name differs in implementation, this adapts to the pattern provided in llm_client.py
            result: ConsolidationOutput = await self.llm.get_structured_output(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_model=ConsolidationOutput
            )
            
            # Generate embedding (Placeholder: In real impl, call self.llm.get_embedding(result.summary))
            # For this implementation, we will initialize None and handle it in indexing if an embedding provider exists
            embedding = self._generate_embedding_mock(result.summary) 

            entry = MemoryEntry(
                content=result.summary,
                raw_source=raw_content[:500],  # Truncate raw source to save space
                memory_type=result.memory_type,
                tags=[tag.lower() for tag in result.tags],
                importance=result.importance,
                embedding=embedding
            )
            
            logger.info(f"Memory consolidated: {entry.id} (Type: {entry.memory_type})")
            return entry

        except Exception as e:
            logger.error(f"Failed to consolidate memory: {e}")
            # Fallback for failure
            return MemoryEntry(
                content=raw_content[:200],
                raw_source=raw_content,
                tags=["uncategorized"],
                importance=1
            )

    # -------------------------------------------------------------------------
    # 2. Indexing
    # -------------------------------------------------------------------------

    async def index(self, entry: MemoryEntry):
        """
        Adds the memory entry to storage and updates retrieval structures (Keyword Map & Vector Cache).
        """
        self.memories[entry.id] = entry
        
        # Update Keyword Index (Signal-enhanced)
        for tag in entry.tags:
            if tag not in self.keyword_index:
                self.keyword_index[tag] = set()
            self.keyword_index[tag].add(entry.id)
            
        # Update Vector Cache
        if entry.embedding:
            self._vector_cache[entry.id] = np.array(entry.embedding, dtype=np.float32)
            
        logger.debug(f"Indexed memory {entry.id} with tags: {entry.tags}")

    # -------------------------------------------------------------------------
    # 3. Retrieval
    # -------------------------------------------------------------------------

    async def retrieve(self, query: str, limit: int = 5, threshold: float = 0.5) -> List[MemoryEntry]:
        """
        Retrieves relevant memories using a hybrid approach:
        1. Keyword matching (Signal-enhanced).
        2. Semantic similarity (Vector-based, if embeddings exist).
        3. Recency and Importance weighting.
        """
        if not self.memories:
            return []

        # 1. Parse Query for Keywords (Simple split or LLM extraction could be used)
        query_terms = set(query.lower().split())
        
        # 2. Generate Query Embedding (Mocked here, would match consolidation embedding logic)
        query_embedding = self._generate_embedding_mock(query)
        
        scored_memories = []

        for uid, entry in self.memories.items():
            score = 0.0
            
            # A. Keyword Overlap Score (Jaccard-ish)
            entry_tags = set(entry.tags)
            overlap = len(query_terms.intersection(entry_tags))
            if overlap > 0:
                score += overlap * 0.3  # Weight for keyword match
            
            # B. Vector Similarity (Cosine)
            if query_embedding is not None and uid in self._vector_cache:
                vec_score = self._cosine_similarity(query_embedding, self._vector_cache[uid])
                score += vec_score * 0.5  # Weight for semantic match
            
            # C. Importance & Recency Boost
            # Normalize importance (1-10) to (0.1-1.0)
            score += (entry.importance / 20.0) 
            
            # Recency decay (simple linear decay over 24 hours)
            age_hours = (datetime.now(timezone.utc) - entry.last_accessed).total_seconds() / 3600
            recency_factor = max(0, 1.0 - (age_hours / 24.0)) * 0.1
            score += recency_factor

            if score > threshold:
                scored_memories.append((score, entry))

        # Sort by score descending
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        # Update access stats for retrieved items
        results = [m for _, m in scored_memories[:limit]]
        for m in results:
            m.touch()
            
        return results

    # -------------------------------------------------------------------------
    # 4. Updating
    # -------------------------------------------------------------------------

    async def update(self, memory_id: UUID, new_content: str):
        """
        Updates an existing memory entry with new information.
        Re-consolidates to ensure tags and embeddings are current.
        """
        if memory_id not in self.memories:
            logger.warning(f"Attempted to update non-existent memory {memory_id}")
            return

        # Create a temporary combined content to re-consolidate
        old_entry = self.memories[memory_id]
        combined_input = f"Old Memory: {old_entry.content}\nNew Update: {new_content}"
        
        # Re-consolidate
        updated_entry = await self.consolidate(combined_input)
        
        # Preserve ID and creation time, update the rest
        updated_entry.id = memory_id
        updated_entry.created_at = old_entry.created_at
        updated_entry.access_count = old_entry.access_count + 1
        
        # Re-index
        await self.index(updated_entry)
        logger.info(f"Updated memory {memory_id}")

    # -------------------------------------------------------------------------
    # 5. Forgetting (Pruning)
    # -------------------------------------------------------------------------

    async def prune(self):
        """
        Implements the 'Forgetting' lifecycle.
        Removes memories if storage exceeds capacity, prioritizing low importance and old access.
        """
        if len(self.memories) <= self.max_memory_size:
            return

        logger.info("Memory capacity exceeded. Pruning...")
        
        # Scoring formula for retention: Importance * Recency
        # We want to remove items with the LOWEST score.
        candidates = []
        now = datetime.now(timezone.utc)
        
        for uid, entry in self.memories.items():
            age_hours = (now - entry.last_accessed).total_seconds() / 3600
            # Avoid division by zero
            recency_score = 1.0 / (age_hours + 1.0)
            retention_score = entry.importance * recency_score
            candidates.append((retention_score, uid))
            
        # Sort ascending (lowest score first)
        candidates.sort(key=lambda x: x[0])
        
        # Remove excess
        num_to_remove = len(self.memories) - self.max_memory_size
        to_remove = candidates[:num_to_remove]
        
        for _, uid in to_remove:
            self._delete(uid)
            
        logger.info(f"Pruned {len(to_remove)} memories.")

    def _delete(self, uid: UUID):
        """Internal deletion logic."""
        if uid in self.memories:
            entry = self.memories.pop(uid)
            # Cleanup keyword index
            for tag in entry.tags:
                if tag in self.keyword_index:
                    self.keyword_index[tag].discard(uid)
                    if not self.keyword_index[tag]:
                        del self.keyword_index[tag]
            # Cleanup vector cache
            if uid in self._vector_cache:
                del self._vector_cache[uid]

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _generate_embedding_mock(self, text: str) -> List[float]:
        """
        Placeholder for embedding generation. 
        In production, this would call self.llm.client.embeddings.create(...)
        """
        # Return a random normalized vector for demonstration of numpy logic
        # or None if we want to rely purely on keywords.
        # Here we return a random vector to satisfy type hints and logic flow.
        vec = np.random.rand(self.embedding_dim).astype(np.float32)
        norm = np.linalg.norm(vec)
        return (vec / norm).tolist() if norm > 0 else vec.tolist()

    def _cosine_similarity(self, vec_a: List[float], vec_b: np.ndarray) -> float:
        """Calculates cosine similarity between two vectors."""
        a = np.array(vec_a, dtype=np.float32)
        b = vec_b
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot_product / (norm_a * norm_b))