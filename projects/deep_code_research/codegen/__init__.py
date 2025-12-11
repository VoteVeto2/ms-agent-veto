"""
Code Generation Layer (Agent 2) - Main Interface

This module provides code generation capabilities using:
1. CodePlanner - Plans code structure
2. CodeGenerator - Generates code files
3. SelfDebugger - Basic syntax validation and fixing
4. SimulationDebugger - CODESIM pattern simulation debugging
5. TestGenerator - AgentCoder pattern auto test generation
6. ReadmeGenerator - Generates README.md
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Tuple, TYPE_CHECKING

# Add parent dir to path for contracts import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .code_planner import CodePlanner
from .code_generator import CodeGenerator
from .self_debugger import SelfDebugger
from .simulation_debugger import SimulationDebugger, SimulationResult
from .test_generator import TestGenerator, TestExecutor, TestCase, TestResult
from .readme_generator import ReadmeGenerator

if TYPE_CHECKING:
    from contracts import ResearchContext


DEBUG_LOG_PATH = Path(__file__).resolve().parents[3] / ".cursor" / "debug.log"


async def generate_repository(
    prompt: str,
    research_context: "ResearchContext",
    use_simulation_debug: bool = True,
    use_auto_tests: bool = True
) -> Tuple[Dict[str, str], Dict]:
    """
    Main entry point for Code Generation Layer.

    Args:
        prompt: User's task description
        research_context: Research results from Agent 1
        use_simulation_debug: Use CODESIM simulation debugging (default: True)
        use_auto_tests: Use AgentCoder auto test generation (default: True)

    Returns:
        Tuple of (files_dict, metrics_dict)
        - files_dict: Dict mapping file paths to file contents
        - metrics_dict: Debug iterations, test results, etc.
    """
    metrics = {
        "total_debug_iterations": 0,
        "simulation_results": [],
        "test_results": []
    }

    # 1. Create code plan
    planner = CodePlanner()
    # region agent log
    try:
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
            _f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H1",
                "location": "codegen.generate_repository",
                "message": "plan_start",
                "data": {
                    "use_simulation_debug": use_simulation_debug,
                    "use_auto_tests": use_auto_tests
                },
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except Exception:
        pass
    # endregion
    code_plan = await planner.create_plan(prompt, research_context)

    if not code_plan.files:
        code_plan = planner.get_default_plan()

    # 2. Generate code files
    generator = CodeGenerator()
    basic_debugger = SelfDebugger()
    simulation_debugger = SimulationDebugger() if use_simulation_debug else None
    test_generator = TestGenerator() if use_auto_tests else None
    test_executor = TestExecutor() if use_auto_tests else None

    generated_files = {}

    for file_spec in code_plan.files:
        # Generate code
        code = await generator.generate_file(
            file_spec,
            research_context,
            generated_files
        )

        # Basic syntax validation
        fixed_code, success, attempts = await basic_debugger.validate_and_fix(
            file_spec.path,
            code
        )
        metrics["total_debug_iterations"] += attempts

        # Simulation-based debugging (CODESIM pattern)
        if simulation_debugger and file_spec.path.endswith('.py'):
            fixed_code, sim_results = await simulation_debugger.debug_with_simulation(
                prompt,
                fixed_code
            )
            metrics["simulation_results"].extend([
                {
                    "input": r.input_data,
                    "expected": r.expected_output,
                    "simulated": r.simulated_output,
                    "is_correct": r.is_correct
                }
                for r in sim_results
            ])

        generated_files[file_spec.path] = fixed_code

    # 3. Auto test generation and validation (AgentCoder pattern)
    if test_generator and test_executor:
        # Generate tests for main code files
        main_files = [f for f in generated_files.keys() if f.endswith('.py') and 'test' not in f]
        for file_path in main_files[:3]:  # Limit to first 3 main files
            tests = await test_generator.generate_tests(
                prompt,
                generated_files[file_path]
            )
            if tests:
                results = await test_executor.run_tests(generated_files[file_path], tests)
                metrics["test_results"].extend([
                    {"file": file_path, "test": r.test_name, "passed": r.passed}
                    for r in results
                ])

    # 4. Generate requirements.txt if not present
    if "requirements.txt" not in generated_files:
        deps = code_plan.dependencies + research_context.dependencies[:10]
        generated_files["requirements.txt"] = "\n".join(sorted(set(deps)))

    # 5. Generate README.md
    readme_gen = ReadmeGenerator()
    readme = await readme_gen.generate(
        prompt,
        code_plan,
        generated_files,
        research_context
    )
    generated_files["README.md"] = readme

    return generated_files, metrics


__all__ = [
    "generate_repository",
    "CodePlanner",
    "CodeGenerator",
    "SelfDebugger",
    "SimulationDebugger",
    "SimulationResult",
    "TestGenerator",
    "TestExecutor",
    "TestCase",
    "TestResult",
    "ReadmeGenerator",
]
