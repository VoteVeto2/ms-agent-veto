# src/agent.py
import logging
import time
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# Internal module imports
from src.llm_client import LLMClient
from src.planning import Planner, PlanningStrategy
from src.acquisition import InformationAcquisition
from src.memory import MemoryManager
from src.generation import Generator

# Attempt to import shared schemas, fallback if not available
try:
    from src.schemas import TaskStatus
except ImportError:
    TaskStatus = None

# Configure logging
logger = logging.getLogger(__name__)

class AgentConfig(BaseModel):
    """
    Configuration parameters for the Deep Research Agent.
    
    Attributes:
        planning_strategy: The topology used for query decomposition (Parallel vs Sequential).
        max_subtasks: Safety limit on the number of sub-tasks to execute per query.
        timeout: Global execution timeout in seconds.
    """
    planning_strategy: PlanningStrategy = Field(
        default=PlanningStrategy.PARALLEL,
        description="Strategy for decomposing the research query."
    )
    max_subtasks: int = Field(
        default=10,
        description="Maximum number of sub-tasks to execute."
    )
    timeout: int = Field(
        default=600,
        description="Global timeout for the research process in seconds."
    )

class DeepResearchAgent:
    """
    The central Orchestrator for the Deep Research system.
    
    This agent implements the 'Agentic Optimization Pipeline', coordinating
    the flow of information between Planning, Acquisition, Memory, and Generation
    modules to produce high-quality, grounded research reports.
    
    Architecture:
        1. Plan: Decompose user query into executable sub-tasks.
        2. Acquire: Gather information from external sources for each task.
        3. Update Memory: Consolidate, index, and refine gathered information.
        4. Generate: Synthesize the final answer using the consolidated memory context.
    """

    def __init__(
        self, 
        llm_client: LLMClient, 
        config: Optional[AgentConfig] = None
    ):
        """
        Initialize the agent with necessary components.

        Args:
            llm_client: The interface to the Large Language Model.
            config: Configuration settings for the agent.
        """
        self.llm_client = llm_client
        self.config = config or AgentConfig()

        # Initialize Modular Components
        # 1. Planner: Responsible for breaking down complex queries
        self.planner = Planner(llm_client=self.llm_client)
        
        # 2. Acquisition: Responsible for external tool usage and scraping
        self.acquisition = InformationAcquisition()
        
        # 3. Memory: Responsible for context management (Lifecycle: Index -> Update -> Consolidate)
        self.memory = MemoryManager(llm_client=self.llm_client)
        
        # 4. Generator: Responsible for final report synthesis
        self.generator = Generator(llm_client=self.llm_client)

        logger.info("DeepResearchAgent initialized successfully.")

    def run(self, user_query: str) -> Dict[str, Any]:
        """
        Execute the end-to-end research pipeline.

        Args:
            user_query: The main research topic or question.

        Returns:
            A dictionary containing the final report, the plan, and execution metadata.
        """
        start_time = time.time()
        logger.info(f"Starting research task for query: '{user_query}'")

        try:
            # ----------------------------------------------------------------
            # Phase 1: Planning
            # ----------------------------------------------------------------
            logger.info("Phase 1: Planning - Decomposing query.")
            plan = self.planner.create_plan(
                query=user_query,
                strategy=self.config.planning_strategy
            )
            logger.info(f"Plan created with {len(plan.sub_tasks)} sub-tasks.")

            # ----------------------------------------------------------------
            # Phase 2 & 3: Acquisition & Memory Update
            # ----------------------------------------------------------------
            logger.info("Phase 2: Acquisition - Executing sub-tasks.")
            self._execute_acquisition_loop(plan, user_query)

            # ----------------------------------------------------------------
            # Phase 4: Generation
            # ----------------------------------------------------------------
            logger.info("Phase 4: Generation - Synthesizing report.")
            # The generator pulls context directly from the memory manager
            final_report = self.generator.generate_report(
                query=user_query,
                memory_manager=self.memory
            )

            execution_time = time.time() - start_time
            logger.info(f"Research completed successfully in {execution_time:.2f}s.")

            return {
                "status": "success",
                "query": user_query,
                "report": final_report,
                "plan": plan.dict(),
                "execution_time": execution_time
            }

        except Exception as e:
            logger.error(f"Research process failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "query": user_query,
                "error": str(e),
                "execution_time": time.time() - start_time
            }

    def _execute_acquisition_loop(self, plan: Any, original_query: str) -> None:
        """
        Orchestrates the Acquisition -> Memory loop based on the plan.
        
        Iterates through sub-tasks, fetches data, and updates the agent's memory.
        Handles the 'Acquire' and 'Update Memory' steps of the pipeline.
        """
        # Limit tasks to avoid runaway execution
        tasks_to_process = plan.sub_tasks[:self.config.max_subtasks]

        for i, task in enumerate(tasks_to_process):
            logger.debug(f"Processing sub-task {i+1}/{len(tasks_to_process)}: {task.description}")
            
            try:
                # 1. Acquire Data
                # Construct a specific query for the search engine
                # Fallback to description if specific search_query is not generated
                search_query = getattr(task, 'search_query', task.description)
                
                results = self.acquisition.perform_search(
                    query=search_query,
                    # Pass original query as context to help filter relevance
                    context=original_query 
                )

                if not results:
                    logger.warning(f"No results found for task: {task.description}")
                    continue

                # 2. Update Memory
                # Ingest results into the memory system
                for result in results:
                    self.memory.add_observation(
                        content=result.content,
                        source=result.source_url,
                        metadata={
                            "title": result.title,
                            "task_id": getattr(task, 'id', 'unknown'),
                            "relevance": result.relevance_score,
                            "evidence_type": result.evidence_type
                        }
                    )
                
                # Update task status if supported
                if hasattr(task, 'status') and TaskStatus:
                    task.status = TaskStatus.COMPLETED
                
                logger.debug(f"Integrated {len(results)} evidence items into memory for task.")

            except Exception as e:
                logger.error(f"Error processing task '{task.description}': {e}")
                if hasattr(task, 'status') and TaskStatus:
                    task.status = TaskStatus.FAILED
                continue
        
        # Trigger memory consolidation (summarization/deduplication) after bulk updates
        logger.info("Consolidating memory after acquisition phase.")
        self.memory.consolidate_memory()