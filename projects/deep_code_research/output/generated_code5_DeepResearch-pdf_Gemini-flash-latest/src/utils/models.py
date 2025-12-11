from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
import datetime
import uuid

# --- Enums ---

class ResearchState(str, Enum):
    """
    Defines the possible states for a Task, Subtask, or ResearchSession.
    """
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVIEWING = "reviewing"
    WAITING_FOR_INPUT = "waiting_for_input"

class Priority(str, Enum):
    """
    Defines the priority level for tasks.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# --- Utility Models ---

class UtilityBaseModel(BaseModel):
    """
    Base model providing common configuration for all utility models,
    enforcing strictness and configuration standards.
    """
    # Pydantic V2 configuration
    model_config = {
        "populate_by_name": True,
        "extra": "forbid",
        "use_enum_values": True,
        "strict": True,
    }

# Configuration for LLM calls
class ModelConfig(UtilityBaseModel):
    """
    Configuration parameters for interacting with a Language Model.
    """
    model_name: str = Field(..., description="The identifier of the language model to use (e.g., gpt-4, claude-3).")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature.")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum number of tokens to generate.")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter.")
    stop_sequences: Optional[List[str]] = Field(None, description="Sequences that stop generation.")
    
    context_window: Optional[int] = Field(None, gt=0, description="The maximum context window size of the model.")

# Structure for representing a tool or function call planned by an agent
class ToolCall(UtilityBaseModel):
    """
    Represents a planned call to an external tool or internal function.
    """
    tool_name: str = Field(..., description="The registered name of the tool (e.g., 'pubmed_search', 'code_sandbox').")
    arguments: Dict[str, Any] = Field(..., description="A dictionary of arguments required for the tool execution.")
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this specific tool call instance.")

# Structure for representing the result of a tool execution
class ToolResult(UtilityBaseModel):
    """
    Represents the output or result obtained from executing a ToolCall.
    """
    call_id: str = Field(..., description="The unique identifier corresponding to the ToolCall that generated this result.")
    success: bool = Field(..., description="True if the tool executed successfully, False otherwise.")
    output: Union[str, Dict[str, Any], List[Any]] = Field(..., description="The raw output data from the tool.")
    error_message: Optional[str] = Field(None, description="Error details if success is False.")
    
    source_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata about the source of the data (e.g., URL, timestamp).")

# Generic structure for reporting status or progress
class StatusReport(UtilityBaseModel):
    """
    A generic model for reporting the current status and progress of an operation.
    """
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now, description="Time the report was generated.")
    state: ResearchState = Field(..., description="The current state of the operation.")
    progress_percentage: float = Field(0.0, ge=0.0, le=100.0, description="Percentage completion.")
    message: str = Field("", description="A human-readable status message.")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional structured details.")

    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_timestamp(cls, v):
        """Ensures the timestamp is a datetime object, parsing strings if necessary."""
        if isinstance(v, str):
            try:
                # Handle ISO format strings
                return datetime.datetime.fromisoformat(v)
            except ValueError as e:
                # If parsing fails, raise a validation error
                raise ValueError(f"Invalid timestamp format: {v}. Must be ISO 8601 compatible.") from e
        return v