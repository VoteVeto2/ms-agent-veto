import logging
from typing import Optional, Dict, Any, List
from uuid import UUID

# Configuration and Utilities
from config import AgentConfig, LLMConfig
from src.utils.models import (
    ResearchResult, Task, Plan, MemoryState, TaskStatus, RawInformation
)

# Specialized Modules
from src.modules.query_planner import QueryPlanner
from src.modules.information_acquisition import InformationAcquisition
from src.modules.memory_manager import MemoryManager
from src.modules.answer_generator import AnswerGenerator

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DeepResearchAgent:
    """
    The central orchestration class (DeepResearchAgent).

    Manages the iterative data flow between the four specialized modules 
    (Planning -> Acquisition -> Memory -> Synthesis) until the research goal is met.
    It implements the core research loop, handling task scheduling, state evolution, 
    and final report generation, ensuring verifiable reasoning and attribution.
    """

    def __init__(
        self,
        agent_config: AgentConfig,
        llm_config: LLMConfig,
        query_planner: QueryPlanner,
        acquisition_module: InformationAcquisition,
        memory_manager: MemoryManager,
        answer_generator: AnswerGenerator,
    ):
        """
        Initializes the DeepResearchAgent with specialized modules and configuration.

        Args:
            agent_config: Configuration settings specific to the agent's operation (e.g., max iterations).
            llm_config: Configuration settings for LLM interactions.
            query_planner: The module responsible for task decomposition and planning.
            acquisition_module: The module responsible for executing tool calls (search, code, etc.).
            memory_manager: The module responsible for state consolidation and knowledge indexing.
            answer_generator: The module responsible for final synthesis and report generation.
        """
        self.config = agent_config
        self.llm_config = llm_config
        
        self.planner = query_planner
        self.acquisition = acquisition_module
        self.memory = memory_manager
        self.synthesizer = answer_generator

        self.max_iterations = agent_config.max_research_iterations
        self.current_iteration = 0
        
        # Internal state tracking
        self.initial_query: str = ""
        # A simple list acting as a task queue/registry for the current research session
        self.task_queue: List[Task] = []

    def _get_pending_tasks(self) -> List[Task]:
        """Retrieves all tasks that are PENDING and ready to run (if dependencies are met)."""
        # Simplification: Assume all PENDING tasks are ready to run immediately.
        return [t for t in self.task_queue if t.status == TaskStatus.PENDING]

    def _update_task_status(self, task_id: UUID, status: TaskStatus):
        """Updates the status of a task in the queue."""
        for task in self.task_queue:
            if task.task_id == task_id:
                task.status = status
                break

    def _check_goal_met(self, current_state: MemoryState) -> bool:
        """
        Determines if the research goal has been sufficiently met.

        This check relies on the Memory Manager's assessment of knowledge sufficiency 
        and the exhaustion of the research budget (iterations).
        """
        if self.current_iteration >= self.max_iterations:
            logger.warning(f"Max iterations ({self.max_iterations}) reached. Terminating.")
            return True

        if not self._get_pending_tasks() and self.current_iteration > 0:
             # Ask the memory manager if the consolidated knowledge is sufficient
             return self.memory.is_answer_ready(current_state)

        return False

    def _planning_step(self, initial_query: str, memory_state: Optional[MemoryState] = None):
        """
        Executes the Planning step (initial decomposition or adaptive refinement).
        """
        if memory_state is None:
            logger.info(f"[{self.current_iteration}] Initial Planning.")
            plan = self.planner.create_initial_plan(initial_query)
        else:
            logger.info(f"[{self.current_iteration}] Adaptive Planning (Refinement).")
            # Adaptive Planning: Identify knowledge gaps and generate new tasks
            plan = self.planner.refine_plan(initial_query, memory_state)

        # Add new tasks to the queue
        existing_task_ids = {t.task_id for t in self.task_queue}
        new_tasks = [t for t in plan.tasks if t.task_id not in existing_task_ids]
        
        if new_tasks:
            self.task_queue.extend(new_tasks)
            logger.info(f"[{self.current_iteration}] Plan generated. Added {len(new_tasks)} new tasks.")
        elif memory_state is not None:
            logger.info(f"[{self.current_iteration}] Refinement planning yielded no new tasks.")


    def _acquisition_step(self, tasks_to_run: List[Task]) -> List[Task]:
        """
        Executes the Information Acquisition step by running pending tasks.
        """
        completed_tasks_with_results = []
        
        for task in tasks_to_run:
            self._update_task_status(task.task_id, TaskStatus.IN_PROGRESS)
            
            try:
                # Execute tool use and gather raw information
                raw_info_list: List[RawInformation] = self.acquisition.execute_task(task)
                
                # Attach raw info to the task object temporarily for memory processing
                setattr(task, 'raw_results', raw_info_list) 
                
                self._update_task_status(task.task_id, TaskStatus.COMPLETED)
                completed_tasks_with_results.append(task)
                
            except Exception as e:
                logger.error(f"Task {task.task_id} failed during acquisition: {e}")
                self._update_task_status(task.task_id, TaskStatus.FAILED)

        return completed_tasks_with_results

    def _memory_step(self, completed_tasks: List[Task], current_state: MemoryState) -> MemoryState:
        """
        Executes the Memory Management step: Validation, Consolidation, and State Updating.
        """
        new_evidence = []
        for task in completed_tasks:
            raw_info_list = getattr(task, 'raw_results', [])
            
            # Process raw data into structured, validated evidence
            processed_evidence = self.memory.process_raw_information(raw_info_list, task)
            new_evidence.extend(processed_evidence)

        # Update the overall knowledge base (Consolidation, Indexing, Forgetting)
        updated_state = self.memory.update_state(current_state, new_evidence)
        
        logger.info(f"[{self.current_iteration}] Memory updated. {len(new_evidence)} new pieces of evidence processed.")
        
        return updated_state

    def _synthesis_step(self, final_state: MemoryState) -> ResearchResult:
        """
        Executes the final Synthesis step, generating the coherent, grounded report 
        with attribution.
        """
        logger.info("Synthesis phase initiated: Generating final report.")
        
        result = self.synthesizer.generate_answer(
            query=self.initial_query,
            memory_state=final_state
        )
        
        return result

    def run_research(self, initial_query: str) -> ResearchResult:
        """
        The main entry point for the Deep Research Agent. 
        Manages the iterative research loop (Planning -> Acquisition -> Memory -> Refinement).

        Args:
            initial_query: The user's research question.

        Returns:
            A ResearchResult object containing the final synthesized answer and attribution.
        """
        self.initial_query = initial_query
        self.current_iteration = 0
        self.task_queue = []
        
        # Initialize Memory State (Section 3.3)
        current_state = self.memory.initialize_state(initial_query)
        
        # 1. Initial Planning (Section 3.1)
        self._planning_step(initial_query)

        while True:
            self.current_iteration += 1
            logger.info(f"\n--- Starting Iteration {self.current_iteration}/{self.max_iterations} ---")

            # Check termination conditions early
            if self._check_goal_met(current_state):
                break

            pending_tasks = self._get_pending_tasks()
            
            if not pending_tasks:
                # If no tasks are pending, trigger adaptive planning to find gaps
                logger.info(f"[{self.current_iteration}] Task queue empty. Triggering Adaptive Planning.")
                self._planning_step(initial_query, current_state)
                pending_tasks = self._get_pending_tasks()
                
                if not pending_tasks:
                    logger.warning(f"[{self.current_iteration}] Adaptive planning failed to generate new tasks. Terminating loop.")
                    break

            # 2. Information Acquisition (Section 3.2)
            completed_tasks = self._acquisition_step(pending_tasks)
            
            if completed_tasks:
                # 3. Memory Management (Section 3.3)
                current_state = self._memory_step(completed_tasks, current_state)
            else:
                logger.info(f"[{self.current_iteration}] Acquisition completed zero tasks. Skipping memory update.")
                # If tasks failed, the next planning step will re-evaluate them.
                
            # 4. Adaptive Planning for Next Iteration
            # This ensures continuous refinement based on the latest knowledge
            if not self._check_goal_met(current_state):
                self._planning_step(initial_query, current_state)

        logger.info("--- Research Loop Finished. Proceeding to Synthesis. ---")
        
        # 5. Final Synthesis (Section 3.4)
        final_result = self._synthesis_step(current_state)
        
        return final_result