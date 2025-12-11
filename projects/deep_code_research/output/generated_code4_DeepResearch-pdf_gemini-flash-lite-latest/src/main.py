# src/main.py
import os
import sys
from typing import Dict, Any, List

# Ensure the root directory is in the path for relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Import the main system class
    from src.deep_research_system import DeepResearchSystem
    # Import necessary components for initialization (even if DeepResearchSystem handles instantiation)
    from src.llm_interface import LLMInterface
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure 'src/deep_research_system.py' and 'src/llm_interface.py' exist and dependencies are met.")
    sys.exit(1)

def initialize_system(config: Dict[str, Any]) -> DeepResearchSystem:
    """
    Initializes the Deep Research System with necessary configurations.

    Args:
        config: A dictionary containing system configuration parameters.

    Returns:
        An initialized DeepResearchSystem instance.
    """
    print("--- Initializing Deep Research System ---")
    
    # 1. Initialize LLM Interface (Mocked or Real)
    try:
        llm_interface = LLMInterface(api_key=config.get("llm_api_key", "MOCK_KEY"))
        print(f"LLM Interface initialized using model: {config.get('llm_model', 'default-model')}")
    except Exception as e:
        print(f"Warning: Could not initialize actual LLMInterface. Using mock/default. Error: {e}")
        # In a real scenario, this might raise an error, but for demonstration, we proceed if possible.
        llm_interface = LLMInterface() 

    # 2. Initialize DeepResearchSystem
    try:
        drs = DeepResearchSystem(
            llm_interface=llm_interface,
            config=config.get("drs_config", {})
        )
        print("Deep Research System core components loaded successfully.")
        return drs
    except Exception as e:
        print(f"FATAL: Failed to initialize DeepResearchSystem: {e}")
        raise

def run_complex_query(drs: DeepResearchSystem, query: str, context: Dict[str, Any]):
    """
    Runs a complex, multi-stage research query through the Deep Research System.

    Args:
        drs: The initialized DeepResearchSystem instance.
        query: The complex research question.
        context: Initial context or parameters for the research run.
    """
    print("\n" + "="*60)
    print(f"STARTING COMPLEX RESEARCH QUERY:")
    print(f"Query: {query}")
    print("="*60)

    try:
        # Execute the research pipeline
        # Based on the System Architecture Decomposition pattern, the run method orchestrates
        # Query Planning -> Information Acquisition -> Memory Management -> Answer Generation.
        
        results = drs.run_research(
            initial_query=query,
            context=context
        )

        print("\n" + "="*60)
        print("RESEARCH EXECUTION COMPLETE")
        print("="*60)
        
        # Display key results based on expected output structure
        if results and isinstance(results, dict):
            print(f"Final Report Title: {results.get('report_title', 'N/A')}")
            print(f"Fidelity Score (Simulated): {results.get('fidelity_score', 'N/A')}")
            print(f"Total Steps Executed: {results.get('execution_steps', 'N/A')}")
            
            # Display a snippet of the generated report
            final_report = results.get('final_report', 'No final report generated.')
            print("\n--- Final Report Snippet ---")
            print(final_report[:500] + ("..." if len(final_report) > 500 else ""))
            print("----------------------------")
        else:
            print("Research run returned an unexpected result format.")

    except Exception as e:
        print(f"\nAn error occurred during the research execution: {e}")


if __name__ == "__main__":
    # --- Configuration ---
    # This configuration simulates loading settings from a file (e.g., YAML/JSON)
    SYSTEM_CONFIG: Dict[str, Any] = {
        "llm_model": "gpt-4o-mini",
        "llm_api_key": os.environ.get("OPENAI_API_KEY", "DUMMY_KEY"),
        "drs_config": {
            "max_iterations": 10,
            "search_depth": 3,
            "memory_retention_policy": "relevance_decay",
            "evaluation_metric": "F1/Fidelity"
        }
    }

    # --- Sample Complex Query ---
    # This query requires synthesis across multiple domains, referencing concepts from the documentation (Table 5).
    COMPLEX_QUERY = (
        "Analyze the current state-of-the-art benchmarks for Deep Research Systems, "
        "specifically contrasting the evaluation metrics used in 'Report Generation' tasks "
        "(e.g., DeepResearch Bench) against those used in 'Survey Generation' tasks (e.g., AutoSurvey). "
        "Propose a unified evaluation framework that could accommodate both."
    )
    
    # Context for the research run
    RUN_CONTEXT: Dict[str, Any] = {
        "user_priority": "Academic Rigor",
        "target_output_format": "Structured Report"
    }

    try:
        # 1. Initialize System
        drs_system = initialize_system(SYSTEM_CONFIG)
        
        # 2. Run Query
        run_complex_query(drs_system, COMPLEX_QUERY, RUN_CONTEXT)

    except Exception as e:
        print(f"\nApplication failed during main execution: {e}")
        sys.exit(1)