import logging
from enum import Enum
from typing import List, Optional, Set, Dict, Any

from pydantic import BaseModel, Field

from src.llm_client import LLMClient
# Importing TaskStatus to ensure alignment with system-wide schemas, 
# though the Planner primarily generates blueprints.
try:
    from src.schemas import TaskStatus
except ImportError:
    # Fallback if schemas are not fully defined in the environment yet
    TaskStatus = None

# Configure module logger
logger = logging.getLogger(__name__)

class PlanningStrategy(str, Enum):
    """
    Defines the topology for query decomposition.
    
    Attributes:
        PARALLEL: Decomposes the query into independent sub-tasks that can be executed simultaneously.
                  Best for broad information gathering where sub-tasks do not depend on each other.
        SEQUENTIAL: Decomposes the query into a strict linear chain of dependencies.
                    Best for tasks requiring iterative reasoning or step-by-step deduction.
        TREE: Decomposes the query into a hierarchical Directed Acyclic Graph (DAG).
              Balances efficiency (parallelism) and effectiveness (dependencies).
    """
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    TREE = "tree"

class SubTask(BaseModel):
    """
    Represents a single unit of work within the generated Research Plan.
    """
    id: str = Field(
        ..., 
        description="Unique identifier for the sub-task (e.g., '1', 'step_a', '1.1')."
    )
    description: str = Field(
        ..., 
        description="Detailed instruction or question for the research agent to execute."
    )
    dependencies: List[str] = Field(
        default_factory=list, 
        description="List of sub-task IDs that must be successfully completed before this task can start."
    )
    expected_output: str = Field(
        ..., 
        description="Description of the specific information or artifact expected from this task."
    )
    estimated_complexity: str = Field(
        "medium",
        description="Estimated complexity of the task (low, medium, high)."
    )

class ResearchPlan(BaseModel):
    """
    The structured output from the Query Planner, representing a decomposed strategy.
    """
    root_goal: str = Field(
        ..., 
        description="The original high-level research goal or query."
    )
    strategy: PlanningStrategy = Field(
        ..., 
        description="The planning topology applied to generate this plan."
    )
    reasoning: str = Field(
        ..., 
        description="Explanation of why this specific decomposition and dependency structure was chosen."
    )
    tasks: List[SubTask] = Field(
        ..., 
        description="The list of decomposed sub-tasks forming the execution graph."
    )

class QueryPlanner:
    """
    Implements the Query Planning module for the Deep Research system.
    
    This class is responsible for analyzing a user's complex query and decomposing it
    into a structured plan of executable sub-tasks using Parallel, Sequential, or 
    Tree-based strategies.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize the QueryPlanner.

        Args:
            llm_client: An instance of LLMClient for interacting with the language model.
        """
        self.llm_client = llm_client

    async def generate_plan(
        self, 
        query: str, 
        strategy: PlanningStrategy = PlanningStrategy.TREE,
        context: Optional[str] = None
    ) -> ResearchPlan:
        """
        Generates a ResearchPlan for the given query using the specified strategy.

        Args:
            query: The complex research query to decompose.
            strategy: The topological strategy for decomposition (Parallel, Sequential, Tree).
            context: Optional background context or memory to inform the planning process.

        Returns:
            ResearchPlan: A validated, structured plan containing sub-tasks and dependencies.

        Raises:
            Exception: If plan generation fails or validation errors occur.
        """
        logger.info(f"Generating research plan. Strategy: {strategy.value}, Query: {query[:50]}...")

        system_prompt = self._build_system_prompt(strategy)
        user_prompt = self._build_user_prompt(query, context)

        try:
            # Generate structured output using the LLM client
            plan = await self.llm_client.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=ResearchPlan
            )
            
            # Perform post-generation validation and cleanup
            self._validate_and_clean_plan(plan, strategy)
            
            logger.info(f"Plan generated successfully with {len(plan.tasks)} sub-tasks.")
            return plan

        except Exception as e:
            logger.error(f"Error generating research plan: {str(e)}")
            raise

    def _build_system_prompt(self, strategy: PlanningStrategy) -> str:
        """Constructs the system prompt based on the selected planning strategy."""
        
        base_prompt = (
            "You are an expert Research Planning Agent for a Deep Research system. "
            "Your goal is to decompose complex user queries into actionable, atomic sub-tasks.\n\n"
        )

        strategy_instructions = {
            PlanningStrategy.PARALLEL: (
                "STRATEGY: PARALLEL PLANNING\n"
                "- Decompose the query into multiple independent sub-questions.\n"
                "- Sub-tasks must NOT depend on each other (dependencies list must be empty).\n"
                "- Focus on breadth: covering different aspects of the query simultaneously.\n"
                "- Example: Comparing X and Y -> Task 1: Research X, Task 2: Research Y."
            ),
            PlanningStrategy.SEQUENTIAL: (
                "STRATEGY: SEQUENTIAL PLANNING\n"
                "- Decompose the query into a strict step-by-step process.\n"
                "- Each task should logically follow the previous one.\n"
                "- Use dependencies to enforce order (e.g., Task 'step_2' depends on 'step_1').\n"
                "- Focus on depth: using intermediate answers to inform subsequent steps."
            ),
            PlanningStrategy.TREE: (
                "STRATEGY: TREE-BASED PLANNING (DAG)\n"
                "- Decompose the query into a hierarchical or directed acyclic graph structure.\n"
                "- Identify high-level components and break them down if complex.\n"
                "- Combine parallel execution for independent parts and sequential execution for dependent parts.\n"
                "- Explicitly define dependencies where information from one task is strictly needed for another.\n"
                "- Balance efficiency (parallelism) with effectiveness (logical flow)."
            )
        }

        return base_prompt + strategy_instructions.get(strategy, "")

    def _build_user_prompt(self, query: str, context: Optional[str]) -> str:
        """Constructs the user prompt including query and optional context."""
        prompt = f"Research Query: {query}\n"
        
        if context:
            prompt += f"\nExisting Context/Memory:\n{context}\n"
        
        prompt += (
            "\nGenerate a ResearchPlan with a list of SubTasks. "
            "Ensure all task IDs are unique. "
            "Dependencies must refer to valid task IDs defined in the same plan."
        )
        return prompt

    def _validate_and_clean_plan(self, plan: ResearchPlan, strategy: PlanningStrategy) -> None:
        """
        Validates the generated plan against the strategy constraints and graph integrity.
        Modifies the plan in-place if minor corrections are needed.
        """
        task_ids = {t.id for t in plan.tasks}
        
        # 1. Validate Dependencies exist
        for task in plan.tasks:
            invalid_deps = [dep for dep in task.dependencies if dep not in task_ids]
            if invalid_deps:
                logger.warning(f"Task {task.id} has invalid dependencies {invalid_deps}. Removing them.")
                task.dependencies = [dep for dep in task.dependencies if dep in task_ids]

        # 2. Enforce Strategy Constraints
        if strategy == PlanningStrategy.PARALLEL:
            for task in plan.tasks:
                if task.dependencies:
                    logger.warning(f"Parallel strategy violation: Task {task.id} has dependencies. Clearing them.")
                    task.dependencies = []

        # 3. Cycle Detection (Simple DFS)
        if strategy in [PlanningStrategy.SEQUENTIAL, PlanningStrategy.TREE]:
            if self._has_cycle(plan.tasks):
                logger.error("Cycle detected in research plan dependencies.")
                # In a production system, we might attempt to break the cycle or retry generation.
                # Here we log it; the execution engine should handle or fail gracefully.

    def _has_cycle(self, tasks: List[SubTask]) -> bool:
        """Detects if the task dependency graph contains a cycle."""
        adj = {t.id: t.dependencies for t in tasks}
        visited = set()
        recursion_stack = set()

        def visit(node_id):
            visited.add(node_id)
            recursion_stack.add(node_id)
            
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    if visit(neighbor):
                        return True
                elif neighbor in recursion_stack:
                    return True
            
            recursion_stack.remove(node_id)
            return False

        for task in tasks:
            if task.id not in visited:
                if visit(task.id):
                    return True
        return False