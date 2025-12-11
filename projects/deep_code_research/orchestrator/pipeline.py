"""
Pipeline Coordinator - Orchestrates research → codegen flow.

Implements:
- Stage-based execution
- Progress tracking
- Iteration/refinement loops
- Error handling with retries
"""

import os
import sys
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List
from enum import Enum

from debug_logger import log_event

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PipelineStage(Enum):
    """Pipeline execution stages."""
    INIT = "init"
    RESEARCH = "research"
    PLANNING = "planning"
    CODEGEN = "codegen"
    DEBUGGING = "debugging"
    TESTING = "testing"
    OUTPUT = "output"
    COMPLETE = "complete"


@dataclass
class PipelineConfig:
    """Pipeline configuration."""
    # Research settings
    use_adaptive_rag: bool = True

    # CodeGen settings
    use_simulation_debug: bool = True
    use_auto_tests: bool = True

    # Iteration settings
    max_refinement_iterations: int = 3
    refinement_threshold: float = 0.8  # Pass rate threshold

    # Output settings
    output_format: str = "zip"  # "zip" or "directory"
    include_metrics: bool = True

    # Retry settings
    max_retries: int = 2
    retry_delay: float = 1.0

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PipelineConfig":
        """Create config from dictionary."""
        return cls(**{k: v for k, v in d.items() if hasattr(cls, k)})

    @classmethod
    def from_yaml(cls, path: str) -> "PipelineConfig":
        """Load config from YAML file."""
        try:
            import yaml
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            return cls.from_dict(data.get('pipeline', data))
        except Exception:
            return cls()


@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    success: bool
    files: Dict[str, str] = field(default_factory=dict)
    output_path: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    stages_completed: List[str] = field(default_factory=list)


class Pipeline:
    """
    Main pipeline coordinator.

    Orchestrates:
    1. Research - Parse docs, build RAG, extract info
    2. CodeGen - Plan, generate, debug, test
    3. Refinement - Iterate based on test results
    4. Output - Package into ZIP
    """

    def __init__(self, config: Optional[PipelineConfig] = None, run_id: Optional[str] = None):
        self.config = config or PipelineConfig()
        self.run_id = run_id or "run1"
        self.on_progress: Optional[Callable[[str, float], None]] = None
        self._current_stage = PipelineStage.INIT
        self._research_context = None

    def _report_progress(self, stage: str, percent: float):
        """Report progress to callback if set."""
        if self.on_progress:
            self.on_progress(stage, percent)

    async def run(
        self,
        prompt: str,
        references_path: str,
        output_dir: str
    ) -> PipelineResult:
        """
        Run the full pipeline.

        Args:
            prompt: User's task description
            references_path: Path to references.zip or directory
            output_dir: Directory for output files

        Returns:
            PipelineResult with all outputs
        """
        result = PipelineResult(success=False)

        # region agent log
        log_event(
            location="pipeline.run",
            message="run_start",
            data={
                "prompt_chars": len(prompt) if prompt else 0,
                "references_path": references_path,
                "output_dir": output_dir,
                "config": {
                    "use_adaptive_rag": self.config.use_adaptive_rag,
                    "use_simulation_debug": self.config.use_simulation_debug,
                    "use_auto_tests": self.config.use_auto_tests,
                    "max_refinement_iterations": self.config.max_refinement_iterations,
                    "output_format": self.config.output_format,
                },
            },
            run_id=self.run_id,
            hypothesis_id="H0",
        )
        # endregion

        try:
            # Stage 1: Research
            # region agent log
            log_event(
                location="pipeline.run",
                message="stage_start",
                data={"stage": "research"},
                run_id=self.run_id,
                hypothesis_id="H0",
            )
            # endregion
            self._report_progress("research", 0.0)
            research_context = await self._run_research(references_path)
            result.stages_completed.append("research")
            self._report_progress("research", 1.0)

            if not research_context:
                result.errors.append("Research stage failed")
                # region agent log
                log_event(
                    location="pipeline.run",
                    message="stage_failed",
                    data={"stage": "research"},
                    run_id=self.run_id,
                    hypothesis_id="H0",
                )
                # endregion
                return result
            # region agent log
            log_event(
                location="pipeline.run",
                message="stage_done",
                data={"stage": "research"},
                run_id=self.run_id,
                hypothesis_id="H0",
            )
            # endregion

            # Stage 2: Initial Code Generation
            # region agent log
            log_event(
                location="pipeline.run",
                message="stage_start",
                data={"stage": "codegen"},
                run_id=self.run_id,
                hypothesis_id="H0",
            )
            # endregion
            self._report_progress("codegen", 0.0)
            files, metrics = await self._run_codegen(prompt, research_context)
            result.stages_completed.append("codegen")
            result.metrics.update(metrics)
            self._report_progress("codegen", 1.0)
            # region agent log
            log_event(
                location="pipeline.run",
                message="stage_done",
                data={
                    "stage": "codegen",
                    "file_count": len(files) if files else 0,
                    "tests": len(metrics.get("test_results", [])) if metrics else 0,
                },
                run_id=self.run_id,
                hypothesis_id="H0",
            )
            # endregion

            # Stage 3: Refinement Loop
            if self.config.max_refinement_iterations > 0:
                # region agent log
                log_event(
                    location="pipeline.run",
                    message="stage_start",
                    data={"stage": "refinement"},
                    run_id=self.run_id,
                    hypothesis_id="H0",
                )
                # endregion
                self._report_progress("refinement", 0.0)
                files, refinement_metrics = await self._run_refinement(
                    prompt, research_context, files, metrics
                )
                result.stages_completed.append("refinement")
                result.metrics["refinement"] = refinement_metrics
                self._report_progress("refinement", 1.0)
                # region agent log
                log_event(
                    location="pipeline.run",
                    message="stage_done",
                    data={
                        "stage": "refinement",
                        "iterations": refinement_metrics.get("iterations", 0),
                    },
                    run_id=self.run_id,
                    hypothesis_id="H0",
                )
                # endregion

            # Stage 4: Output
            # region agent log
            log_event(
                location="pipeline.run",
                message="stage_start",
                data={"stage": "output"},
                run_id=self.run_id,
                hypothesis_id="H0",
            )
            # endregion
            self._report_progress("output", 0.0)
            output_path = await self._generate_output(files, output_dir, result.metrics)
            result.stages_completed.append("output")
            self._report_progress("output", 1.0)
            # region agent log
            log_event(
                location="pipeline.run",
                message="stage_done",
                data={"stage": "output", "output_path": output_path},
                run_id=self.run_id,
                hypothesis_id="H0",
            )
            # endregion

            result.success = True
            result.files = files
            result.output_path = output_path

        except Exception as e:
            import traceback
            result.errors.append(f"{str(e)}\n{traceback.format_exc()}")
            # region agent log
            log_event(
                location="pipeline.run",
                message="run_error",
                data={"error": str(e)},
                run_id=self.run_id,
                hypothesis_id="H0",
            )
            # endregion

        return result

    async def _run_research(self, references_path: str) -> Optional[Any]:
        """Run research stage with retry logic."""
        from research import research_references

        for attempt in range(self.config.max_retries + 1):
            try:
                return await research_references(
                    references_path,
                    use_adaptive_rag=self.config.use_adaptive_rag
                )
            except Exception as e:
                if attempt == self.config.max_retries:
                    raise
                await asyncio.sleep(self.config.retry_delay)

        return None

    async def _run_codegen(
        self,
        prompt: str,
        research_context: Any
    ) -> tuple:
        """Run code generation stage."""
        from codegen import generate_repository

        return await generate_repository(
            prompt=prompt,
            research_context=research_context,
            use_simulation_debug=self.config.use_simulation_debug,
            use_auto_tests=self.config.use_auto_tests
        )

    async def _run_refinement(
        self,
        prompt: str,
        research_context: Any,
        files: Dict[str, str],
        initial_metrics: Dict[str, Any]
    ) -> tuple:
        """
        Run refinement loop based on test results.

        Implements iteration pattern:
        1. Check test pass rate
        2. If below threshold, regenerate failing components
        3. Repeat until threshold met or max iterations
        """
        refinement_metrics = {
            "iterations": 0,
            "improvements": []
        }

        current_files = files.copy()
        test_results = initial_metrics.get("test_results", [])

        for iteration in range(self.config.max_refinement_iterations):
            # Calculate pass rate
            if not test_results:
                break

            passed = sum(1 for r in test_results if r.get("passed", False))
            total = len(test_results)
            pass_rate = passed / total if total > 0 else 1.0

            if pass_rate >= self.config.refinement_threshold:
                break

            refinement_metrics["iterations"] += 1

            # Identify failing files
            failing_files = set()
            for r in test_results:
                if not r.get("passed", False):
                    failing_files.add(r.get("file", ""))

            # Regenerate failing files
            from codegen import CodeGenerator, SelfDebugger

            generator = CodeGenerator()
            debugger = SelfDebugger()

            for file_path in failing_files:
                if file_path in current_files and file_path.endswith('.py'):
                    # Create a simple FileSpec for regeneration
                    from contracts import FileSpec
                    file_spec = FileSpec(
                        path=file_path,
                        description=f"Fix failing tests for {file_path}",
                        depends_on=[]
                    )

                    # Regenerate
                    new_code = await generator.generate_file(
                        file_spec,
                        research_context,
                        current_files
                    )

                    # Debug
                    fixed_code, success, _ = await debugger.validate_and_fix(
                        file_path,
                        new_code
                    )

                    if success:
                        current_files[file_path] = fixed_code
                        refinement_metrics["improvements"].append({
                            "iteration": iteration + 1,
                            "file": file_path,
                            "success": True
                        })

            # Re-run tests would happen here in a full implementation
            # For now, we just track the iteration

        return current_files, refinement_metrics

    async def _generate_output(
        self,
        files: Dict[str, str],
        output_dir: str,
        metrics: Dict[str, Any]
    ) -> str:
        """Generate output files or ZIP."""
        from .output_formatter import OutputFormatter, OutputConfig

        formatter = OutputFormatter(OutputConfig(
            format=self.config.output_format,
            include_metrics=self.config.include_metrics
        ))

        return await formatter.write(files, output_dir, metrics)
