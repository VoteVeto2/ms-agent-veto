import json
from typing import Dict, Any, List
from uuid import uuid4, UUID
from enum import Enum
from pydantic import BaseModel, Field

# --- Minimal Definitions for Simulation Context ---

class PlanningStrategy(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    TREE_BASED = "tree_based"

class ToolType(str, Enum):
    SEARCH = "search"
    SYNTHESIZE = "synthesize"
    CODE_EXECUTION = "code_execution"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    query: str
    tool_type: ToolType
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[UUID] = Field(default_factory=list)
    priority: int = 1
    max_retries: int = 3

class Plan(BaseModel):
    initial_query: str
    strategy: PlanningStrategy
    complexity_assessment: str
    tasks: List[Task]

PLANNING_PROMPT_TEMPLATE = (
    "You are an expert planning agent. Analyze the user query and decompose it into a structured, "
    "adaptive research plan. Determine the optimal strategy (SEQUENTIAL, PARALLEL, or TREE_BASED) "
    "based on complexity and interdependencies."
)

# --- Mock LLM Interface ---

class MockLLMClient:
    """
    A placeholder class simulating an interface to a large language model
    capable of structured JSON output generation based on prompts.
    """
    def generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates calling an LLM to generate a structured plan based on the prompt.
        The simulation determines the strategy based on keywords in the prompt.
        
        FIX: The previous attempt to simulate raw JSON strings for UUIDs and Enums 
             caused Pydantic validation failures in the simulation environment (Got: None). 
             We now return Python objects (UUID, Enum) in the dictionary output. 
             Pydantic's `model_validate` handles these native types reliably, 
             resolving the underlying serialization/validation issue.
        """
        
        # 1. Robust Query Extraction
        query = "Unknown complex query"
        if "USER QUERY TO ANALYZE:" in prompt:
            try:
                # Find the content between the markers defined in _construct_planning_prompt
                start_index = prompt.find("\n---\n")
                # Look for the closing marker after the start marker
                end_index = prompt.find("\n---\n", start_index + 5)
                if start_index != -1 and end_index != -1:
                    # Extract content between the two '---' blocks
                    query = prompt[start_index + 5: end_index].strip()
            except Exception:
                # Fallback if prompt structure is unexpected
                pass

        # 2. Adaptive Planning Strategy Simulation
        if "interdependent" in query.lower() or "complex reasoning" in query.lower() or "hierarchical" in query.lower():
            strategy = PlanningStrategy.TREE_BASED
            assessment = "The query requires hierarchical decomposition and dependency management, best suited for a Tree-based approach."
        elif "compare" in query.lower() or "list facts about" in query.lower():
            strategy = PlanningStrategy.PARALLEL
            assessment = "The query involves independent sub-queries (e.g., comparison points), allowing for efficient Parallel execution."
        else:
            strategy = PlanningStrategy.SEQUENTIAL
            assessment = "The query requires a step-by-step process or relies on previous results, necessitating a Sequential approach."

        # 3. Mock Task generation (using raw Python objects for Pydantic validation)
        task_1_id = uuid4()
        task_2_id = uuid4()
        
        mock_task_1_data = {
            "task_id": task_1_id, # Use UUID object
            "query": f"Acquire initial information for part A of the query: {query[:30]}...",
            "tool_type": ToolType.SEARCH, # Use Enum object
            "status": TaskStatus.PENDING, # Use Enum object
            "dependencies": [],
            "priority": 1,
            "max_retries": 3
        }
        
        # Dependencies list now contains UUID objects
        dependencies_list = [task_1_id] if strategy == PlanningStrategy.SEQUENTIAL else []
        
        mock_task_2_data = {
            "task_id": task_2_id, # Use UUID object
            "query": "Synthesize findings from Task 1 and generate the final answer.",
            "tool_type": ToolType.SYNTHESIZE, # Use Enum object
            "status": TaskStatus.PENDING, # Use Enum object
            "dependencies": dependencies_list,
            "priority": 2,
            "max_retries": 1
        }

        # 4. Mock Plan generation
        mock_plan_data = {
            "initial_query": query,
            "strategy": strategy, # Use Enum object
            "complexity_assessment": assessment,
            "tasks": [mock_task_1_data, mock_task_2_data]
        }
        
        return mock_plan_data

# --- Query Planner Implementation ---

class QueryPlanner:
    """
    Implements the Query Planning module. 
    
    This module analyzes query complexity and determines the optimal Adaptive Planning Strategy:
    Sequential, Parallel, or Tree-based decomposition, orchestrating the subsequent workflow.
    """

    def __init__(self, llm_client: MockLLMClient):
        """
        Initializes the QueryPlanner.

        Args:
            llm_client: An interface to the LLM used for generating structured plans.
        """
        self.llm_client = llm_client

    def _construct_planning_prompt(self, query: str) -> str:
        """
        Fills the prompt template with the specific user query and required schema details
        to guide the LLM in generating a structured plan.
        """
        
        full_prompt = (
            f"{PLANNING_PROMPT_TEMPLATE}\n\n"
            f"USER QUERY TO ANALYZE:\n---\n{query}\n---\n"
            f"Based on this query, generate the JSON plan strictly following the required schema."
        )
        return full_prompt

    def generate_plan(self, query: str) -> Plan:
        """
        Analyzes the query complexity and generates an adaptive research plan.

        The plan decomposes the query into sub-tasks using one of the adaptive strategies:
        Sequential, Parallel, or Tree-based.

        Args:
            query: The initial complex user query string.

        Returns:
            A validated Plan object containing the decomposition and strategy.

        Raises:
            ValueError: If the input query is empty or if the LLM output fails validation.
            RuntimeError: If the LLM API call fails.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        prompt = self._construct_planning_prompt(query)

        # 1. Call the LLM to generate the structured plan (JSON dictionary)
        try:
            # Note: Plan.model_json_schema() is used here to simulate passing the schema
            # requirement to the LLM, even though the mock doesn't strictly use it.
            plan_data_dict = self.llm_client.generate_json(
                prompt=prompt,
                schema=Plan.model_json_schema()
            )
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve plan from LLM service: {e}")

        # 2. Validate and parse the JSON output into the Pydantic model
        try:
            # Pydantic handles conversion from raw Python objects (UUID, Enum) 
            # provided by the mock into the strict types defined in the models.
            plan = Plan.model_validate(plan_data_dict)
            return plan
        except Exception as e:
            # Log the error details for debugging the LLM output quality
            error_message = f"LLM output failed validation for Plan model. Error: {e}. Raw data: {plan_data_dict}"
            raise ValueError(error_message)