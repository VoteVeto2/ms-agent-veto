from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, validator

# =============================================================================
# Enums & Constants
# =============================================================================

class PlanTopology(str, Enum):
    """
    Defines the structural topology of the research plan.
    
    - SEQUENTIAL: Tasks are executed one after another.
    - PARALLEL: Independent tasks are executed concurrently.
    - TREE: Hierarchical decomposition of tasks.
    - DAG: Directed Acyclic Graph allowing complex dependencies.
    """
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    TREE = "tree"
    DAG = "dag"


class TaskStatus(str, Enum):
    """Execution status of a task, subtask, or step."""
    PENDING = "pending"
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EvidenceType(str, Enum):
    """Supported modalities for evidence collection."""
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    FORMULA = "formula"
    CODE = "code"
    AUDIO = "audio"


# =============================================================================
# Evidence & Knowledge Models
# =============================================================================

class Source(BaseModel):
    """
    Represents an origin of information (e.g., a paper, website, or file).
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    url: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    publication_date: Optional[datetime] = None
    domain: Optional[str] = None
    reliability_score: float = Field(
        default=0.5, 
        ge=0.0, 
        le=1.0, 
        description="Trustworthiness of the source."
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    """
    A discrete unit of information collected during the research process.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    evidence_type: EvidenceType = EvidenceType.TEXT
    source_id: str
    confidence: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0, 
        description="Confidence in the relevance and accuracy of this evidence."
    )
    context: Optional[str] = Field(
        default=None, 
        description="Surrounding context or summary of where this evidence was found."
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    captured_at: datetime = Field(default_factory=datetime.utcnow)


class Citation(BaseModel):
    """
    Reference to specific evidence used to support a claim or answer.
    """
    evidence_id: str
    source_id: str
    text_span: Optional[str] = None
    start_index: Optional[int] = None
    end_index: Optional[int] = None


# =============================================================================
# Planning & Task Models
# =============================================================================

class Step(BaseModel):
    """
    An atomic unit of execution within a subtask (e.g., a single search query or API call).
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    action: str
    params: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    status: TaskStatus = TaskStatus.PENDING
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


class Subtask(BaseModel):
    """
    A decomposed part of the main research task, potentially containing multiple steps.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    dependencies: List[str] = Field(
        default_factory=list, 
        description="IDs of subtasks that must complete before this one starts."
    )
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    steps: List[Step] = Field(default_factory=list)
    result: Optional[str] = None
    evidences: List[Evidence] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def add_step(self, description: str, action: str, params: Dict[str, Any] = None) -> Step:
        step = Step(description=description, action=action, params=params or {})
        self.steps.append(step)
        return step


class Plan(BaseModel):
    """
    The strategic plan generated to answer the user's query.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    topology: PlanTopology = PlanTopology.SEQUENTIAL
    subtasks: List[Subtask] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def is_complete(self) -> bool:
        return all(t.status == TaskStatus.COMPLETED for t in self.subtasks)


# =============================================================================
# Memory Management Models
# =============================================================================

class MemoryEntry(BaseModel):
    """
    A unit of memory stored in the agent's context.
    Supports lifecycle management (consolidation, forgetting).
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    tags: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0
    access_count: int = 0
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def touch(self):
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


# =============================================================================
# Session & IO Models
# =============================================================================

class ResearchRequest(BaseModel):
    """
    Initial request payload from the user.
    """
    query: str
    depth: int = Field(default=3, ge=1, description="Depth of research recursion.")
    breadth: int = Field(default=3, ge=1, description="Breadth of search queries per step.")
    include_modalities: List[EvidenceType] = Field(default_factory=lambda: [EvidenceType.TEXT])
    max_budget: Optional[float] = None


class ResearchOutput(BaseModel):
    """
    The final answer and provenance generated by the system.
    """
    session_id: str
    answer: str
    summary: str
    citations: List[Citation] = Field(default_factory=list)
    sources: List[Source] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    provenance_chain: List[str] = Field(
        default_factory=list, 
        description="Trace of IDs (Plan -> Subtask -> Evidence) leading to the answer."
    )
    execution_time: float = 0.0
    cost: float = 0.0


class ResearchSession(BaseModel):
    """
    Stateful context for a running research job.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request: ResearchRequest
    plan: Optional[Plan] = None
    status: TaskStatus = TaskStatus.PENDING
    memory: List[MemoryEntry] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True