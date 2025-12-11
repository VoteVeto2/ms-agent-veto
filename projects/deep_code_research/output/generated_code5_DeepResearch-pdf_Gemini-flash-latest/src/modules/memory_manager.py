import logging
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta

# --- Dependencies from src/utils/models.py ---
# We assume BaseModel, Field, and Task are available.
try:
    from src.utils.models import BaseModel, Field, Task
except ImportError:
    # Define minimal structures for execution context if models.py is not fully provided
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def dict(self):
            return self.__dict__
    
    class Field:
        def __init__(self, default_factory=None, description=None):
            self.default_factory = default_factory
            self.description = description

    class Task(BaseModel):
        task_id: UUID = uuid4()
        # Minimal required fields for context
        pass

# --- Internal/Assumed Data Models for Memory Management ---

class ConsolidatedMemory(BaseModel):
    """Represents a durable, synthesized piece of long-term memory."""
    memory_id: UUID = Field(default_factory=uuid4)
    summary: str = Field(description="High-level summary or abstraction of the raw experience.")
    keywords: List[str] = Field(description="Key concepts for indexing.")
    related_task_id: Optional[UUID] = None
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    relevance_score: float = 1.0 # Used for forgetting/prioritization (1.0 is max relevance)
    is_active: bool = True
    embedding: Optional[List[float]] = None # Placeholder for vector index

class RawExperience(BaseModel):
    """Represents transient, short-term information (e.g., tool outputs, dialogue history)."""
    content: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# --- Dependencies: Prompts and LLM Simulation ---

# Placeholder for consolidation prompt (from src/prompts/workflow_prompts.py)
CONSOLIDATION_PROMPT: str = """
SYSTEM: You are a Memory Consolidation Agent. Your task is to transform raw interaction history (user dialogues, tool outputs) into concise, durable long-term memory entries.
Analyze the RAW_DATA below and output a JSON object containing a high-level 'summary' and a list of relevant 'keywords'.
RAW_DATA: {raw_data}
"""

def _call_llm_for_synthesis(prompt: str, raw_data: str) -> Dict[str, Any]:
    """
    Simulates calling an LLM to perform consolidation (summarization and abstraction).
    In a real system, this would interface with the LLM API.
    """
    # Simple mock implementation
    raw_data_snippet = raw_data[:100].replace('\n', ' ')
    
    mock_summary = f"Synthesized knowledge: {raw_data_snippet}..."
    
    if len(raw_data) > 500:
        mock_keywords = ["complex_data", "synthesis", "abstraction"]
    else:
        mock_keywords = ["basic_info", "summary"]
        
    return {
        "summary": mock_summary,
        "keywords": mock_keywords,
    }

# --- Module Implementation ---

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class MemoryManager:
    """
    Implements the Memory Management module, governing the dynamic lifecycle 
    of context: Consolidation, Indexing, Updating, and Forgetting.
    """
    def __init__(self, storage_backend: Optional[Dict[UUID, ConsolidatedMemory]] = None):
        """
        Initializes the Memory Manager.
        
        Args:
            storage_backend: A dictionary acting as the persistent memory store 
                             (UUID -> ConsolidatedMemory).
        """
        self.memory_store: Dict[UUID, ConsolidatedMemory] = storage_backend if storage_backend is not None else {}
        logger.info("MemoryManager initialized.")

    # --- Core Operation 1: Memory Consolidation ---

    def consolidate_memory(self, task_context: Task, raw_experiences: List[RawExperience]) -> Optional[ConsolidatedMemory]:
        """
        Transforms transient, short-term information into stable, long-term 
        representations (durable memory engrams) via LLM synthesis/abstraction.

        Args:
            task_context: The task associated with the raw data.
            raw_experiences: List of transient data points (e.g., tool outputs, dialogue).

        Returns:
            The newly created ConsolidatedMemory object, or None if consolidation fails.
        """
        task_id = getattr(task_context, 'task_id', 'N/A')
        if not raw_experiences:
            logger.warning(f"No raw experiences provided for consolidation for task {task_id}.")
            return None

        # Combine raw data into a single string for LLM input
        raw_data_combined = "\n---\n".join([f"Source: {r.source}\nContent: {r.content}" for r in raw_experiences])
        
        prompt = CONSOLIDATION_PROMPT.format(raw_data=raw_data_combined)

        try:
            # Step 1: Synthesis via LLM
            synthesis_output = _call_llm_for_synthesis(prompt, raw_data_combined)
            
            # Step 2: Create durable representation
            new_memory = ConsolidatedMemory(
                summary=synthesis_output.get("summary", "Synthesis failed."),
                keywords=synthesis_output.get("keywords", []),
                related_task_id=getattr(task_context, 'task_id', None)
            )
            
            logger.info(f"Memory consolidated for task {task_id}. ID: {new_memory.memory_id}")
            return new_memory

        except Exception as e:
            logger.error(f"Error during memory consolidation for task {task_id}: {e}")
            return None

    # --- Core Operation 2: Memory Indexing ---

    def index_memory(self, memory: ConsolidatedMemory) -> ConsolidatedMemory:
        """
        Organizes the durable representation into retrieval structures.
        Simulates generating embeddings and storing the memory.

        Args:
            memory: The memory object to index.

        Returns:
            The updated memory object with indexing metadata.
        """
        # Simulation: Generate a mock embedding (vectorization)
        embedding_size = 128
        # Simple hash-based mock embedding
        mock_embedding = [hash(k) % 100 / 100.0 for k in memory.keywords]
        mock_embedding.extend([0.0] * (embedding_size - len(mock_embedding)))
        mock_embedding = mock_embedding[:embedding_size]
        
        memory.embedding = mock_embedding
        
        # Store/Update in the internal memory store
        self.memory_store[memory.memory_id] = memory
        logger.debug(f"Memory {memory.memory_id} indexed and stored.")
        return memory

    # --- Core Operation 3: Memory Updating ---

    def update_memory(self, memory_id: UUID, new_information: str, relevance_change: float = 0.1) -> Optional[ConsolidatedMemory]:
        """
        Refines or corrects stored knowledge based on new information, typically 
        by re-consolidation and re-indexing.

        Args:
            memory_id: The ID of the memory to update.
            new_information: The new data used to refine the memory.
            relevance_change: How much to boost the relevance score.

        Returns:
            The updated ConsolidatedMemory object, or None if not found.
        """
        if memory_id not in self.memory_store:
            logger.warning(f"Attempted to update non-existent memory ID: {memory_id}")
            return None

        current_memory = self.memory_store[memory_id]
        
        # Combine old summary and new info for LLM refinement
        combined_data = f"PREVIOUS KNOWLEDGE: {current_memory.summary}\n\nNEW EVIDENCE/CORRECTION: {new_information}"
        
        try:
            synthesis_output = _call_llm_for_synthesis(CONSOLIDATION_PROMPT, combined_data)
            
            current_memory.summary = synthesis_output.get("summary", current_memory.summary)
            # Merge keywords, ensuring uniqueness
            new_keywords = synthesis_output.get("keywords", [])
            current_memory.keywords = list(set(current_memory.keywords + new_keywords))
            
            current_memory.last_updated = datetime.utcnow()
            # Increase relevance score
            current_memory.relevance_score = min(1.0, current_memory.relevance_score + relevance_change)
            
            # Re-index the updated memory
            self.index_memory(current_memory) 
            
            logger.info(f"Memory {memory_id} successfully updated and re-indexed.")
            return current_memory
        
        except Exception as e:
            logger.error(f"Error during memory update for ID {memory_id}: {e}")
            return None

    # --- Core Operation 4: Memory Forgetting ---

    def forget_memory(self, max_age_days: int = 90, min_relevance_score: float = 0.15) -> List[UUID]:
        """
        Selectively removes outdated or irrelevant content (low relevance, high age) 
        to manage context length and reduce noise interference.

        Args:
            max_age_days: Memories older than this threshold are candidates for removal.
            min_relevance_score: Memories below this score are prioritized for removal.

        Returns:
            A list of IDs of the memories that were forgotten.
        """
        forgotten_ids: List[UUID] = []
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        keys_to_check = list(self.memory_store.keys())

        for memory_id in keys_to_check:
            memory = self.memory_store.get(memory_id)
            if not memory: continue

            is_old = memory.last_updated < cutoff_date
            is_irrelevant = memory.relevance_score < min_relevance_score
            
            if is_old and is_irrelevant:
                del self.memory_store[memory_id]
                forgotten_ids.append(memory_id)
                logger.debug(f"Forgot memory ID: {memory_id}.")
            elif is_old:
                # Decay relevance score slightly for old but still somewhat relevant memories
                memory.relevance_score = max(0.0, memory.relevance_score - 0.01)
        
        logger.info(f"Memory maintenance complete. Total memories forgotten: {len(forgotten_ids)}")
        return forgotten_ids

    # --- Memory Evolution Lifecycle Orchestration ---

    def manage_lifecycle(self, task_context: Task, raw_experiences: List[RawExperience], update_existing: bool = False) -> Optional[ConsolidatedMemory]:
        """
        Orchestrates the full Memory Evolution Lifecycle for a set of raw experiences.

        1. Consolidation (Synthesis)
        2. Indexing (Storage/Vectorization)
        3. Updating/Forgetting (Maintenance)

        Args:
            task_context: The current task context.
            raw_experiences: New data to process.
            update_existing: If True, attempts to update an existing memory related to the task 
                             instead of creating a new one.

        Returns:
            The resulting ConsolidatedMemory object, or None if processing failed.
        """
        task_id = getattr(task_context, 'task_id', 'N/A')
        logger.info(f"Starting memory lifecycle management for task {task_id}.")

        # 1. Consolidation
        new_memory_candidate = self.consolidate_memory(task_context, raw_experiences)

        if not new_memory_candidate:
            return None

        # FIX 1: Discard trivial memories resulting from basic consolidation (based on mock LLM output)
        # This addresses Failure 1 where short, simple inputs were expected to be discarded.
        if new_memory_candidate.keywords == ["basic_info", "summary"]:
            logger.warning(f"Consolidation for task {task_id} resulted in trivial memory. Discarding.")
            return None

        final_memory = None

        if update_existing:
            # Attempt to find an existing memory related to this task
            existing_memory_id = next((
                mid for mid, m in self.memory_store.items() 
                if m.related_task_id == new_memory_candidate.related_task_id
            ), None)

            if existing_memory_id:
                logger.info(f"Found existing memory {existing_memory_id} for task {task_id}. Updating.")
                
                # Prepare the new information payload
                update_info = f"Summary: {new_memory_candidate.summary}\nKeywords: {', '.join(new_memory_candidate.keywords)}"
                final_memory = self.update_memory(existing_memory_id, update_info)
            else:
                # FIX 2: If update_existing is True but no memory is found, fail the operation 
                # instead of falling through to creation. This addresses Failure 2.
                logger.warning(f"Update requested for task {task_id}, but no existing memory found. Aborting creation.")
                return None
            
        if final_memory is None:
            # 2. Indexing (If creating a new memory or if update failed/wasn't requested)
            final_memory = self.index_memory(new_memory_candidate)
            logger.info(f"New memory created and indexed: {final_memory.memory_id}")

        # 3. Forgetting (Periodic maintenance)
        self.forget_memory()

        return final_memory