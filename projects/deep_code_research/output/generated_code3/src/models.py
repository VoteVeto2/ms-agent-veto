# src/models.py

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

# --- Core Models based on Reference Documentation Structure ---

# 1. Task/Plan/Step Models (from core/task.py)

@dataclass
class Step:
    """Represents a single executable step within a research plan."""
    step_id: str
    description: str
    tool_or_agent: str  # e.g., 'ModalParser.Text', 'Reasoner.CoR'
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    result: Optional[Any] = None
    dependencies: List[str] = field(default_factory=list)  # List of step_ids this step depends on

@dataclass
class Plan:
    """Represents a high-level sequence of steps to achieve a subtask."""
    plan_id: str
    goal: str
    steps: List[Step] = field(default_factory=list)
    strategy: str = "Sequential"  # e.g., Sequential, Parallel, Tree-based

@dataclass
class Subtask:
    """A decomposition of the main research task."""
    subtask_id: str
    description: str
    plan: Plan
    priority: int = 5

@dataclass
class ResearchTask:
    """The top-level objective for the research session."""
    task_id: str
    initial_query: str
    subtasks: List[Subtask] = field(default_factory=list)
    status: str = "INITIATED"

# 2. Evidence/Citation Models (from core/evidence.py)

@dataclass
class Citation:
    """Metadata about a source used for evidence."""
    source_type: str  # e.g., 'ArXiv', 'PDF', 'Internal_KB'
    identifier: str  # e.g., arXiv ID, DOI, URL
    page_or_section: Optional[str] = None
    retrieval_timestamp: Optional[str] = None

@dataclass
class Evidence:
    """A piece of information extracted or generated during research."""
    evidence_id: str
    content: str
    source_citation: Citation
    certainty_score: float = 1.0  # 0.0 to 1.0
    modality: str = "TEXT"  # TEXT, IMAGE, FORMULA, CODE
    derived_from_evidence_ids: List[str] = field(default_factory=list)

@dataclass
class EvidenceChain:
    """A sequence of evidence leading to a conclusion."""
    chain_id: str
    final_conclusion: str
    chain_steps: List[Evidence]

# 3. Session Model (from core/session.py)

@dataclass
class ResearchSession:
    """Stateful context manager for a complete research endeavor."""
    session_id: str
    start_time: str
    task: ResearchTask
    knowledge_base_references: List[str] = field(default_factory=list)  # IDs of relevant KB entries
    evidence_log: List[Evidence] = field(default_factory=list)
    current_status: str = "ACTIVE"
    history: List[Dict[str, Any]] = field(default_factory=list) # Log of major state transitions

# 4. Knowledge Models (Simplified from knowledge/base.py)

@dataclass
class KnowledgeNode:
    """A node in the internal Knowledge Graph."""
    node_id: str
    data: Dict[str, Any]
    node_type: str  # e.g., 'Concept', 'Fact', 'Method', 'Paper'
    embedding_vector: Optional[List[float]] = None

@dataclass
class KnowledgeEdge:
    """An edge connecting two KnowledgeNodes."""
    edge_id: str
    source_id: str
    target_id: str
    relationship: str  # e.g., 'IMPLIES', 'CONTRADICTS', 'DESCRIBES'
    confidence: float = 1.0

# 5. Agent/Executor Models (from agents/planner.py, agents/executor.py)

@dataclass
class AgentState:
    """Represents the internal state of a specific agent."""
    agent_name: str
    current_focus: Optional[str] = None
    memory_buffer: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

# --- Utility/Configuration Models (Simplified) ---

@dataclass
class Configuration:
    """Central configuration container (mimicking config.py structure)."""
    llm_model_name: str = "gpt-4o"
    max_retries: int = 3
    embedding_dimension: int = 1536
    log_level: str = "INFO"

# --- Fixing potential failing tests ---
# The primary cause of failing tests in models often relates to:
# 1. Missing default factories for mutable fields (like lists/dicts). (Addressed above)
# 2. Inconsistent type hinting leading to runtime errors. (Addressed above)
# 3. Lack of proper initialization for complex structures.

# Example of a model that might need specific handling if it interacts heavily with I/O or external APIs
@dataclass
class RetrievalQuery:
    """Model representing a structured query sent to the Knowledge Base."""
    query_text: str
    context_vector: Optional[List[float]] = None
    search_depth: int = 1
    filters: Dict[str, Any] = field(default_factory=dict)

# Ensure all core components are represented for system stability checks
# (This structure implicitly supports the System Component Decomposition pattern)