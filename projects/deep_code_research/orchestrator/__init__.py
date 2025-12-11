"""
Orchestration Layer (Agent 3) - Main Interface

Coordinates the full pipeline:
1. Research Layer - Parse docs, build RAG, extract info
2. CodeGen Layer - Plan, generate, debug, test code
3. Output - Package results into ZIP

Key Features:
- Pipeline orchestration with iteration/refinement
- Progress callbacks for UI integration
- Configurable via YAML or dict
- ZIP output generation
"""

import os
import sys
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .pipeline import Pipeline, PipelineConfig, PipelineResult
from .output_formatter import OutputFormatter, OutputConfig

if TYPE_CHECKING:
    from contracts import ResearchContext


async def run_pipeline(
    prompt: str,
    references_path: str,
    output_dir: str = "./output",
    config: Optional[Dict[str, Any]] = None,
    on_progress: Optional[Callable[[str, float], None]] = None,
    run_id: Optional[str] = None,
) -> PipelineResult:
    """
    Main entry point for the full DeepCodeResearch pipeline.

    Args:
        prompt: User's task description
        references_path: Path to references.zip or directory
        output_dir: Directory for output files
        config: Optional configuration dict
        on_progress: Optional callback for progress updates (stage, percent)

    Returns:
        PipelineResult with generated files, metrics, and output path
    """
    pipeline_config = PipelineConfig.from_dict(config or {})
    pipeline = Pipeline(pipeline_config, run_id=run_id)

    if on_progress:
        pipeline.on_progress = on_progress

    return await pipeline.run(prompt, references_path, output_dir)


__all__ = [
    "run_pipeline",
    "Pipeline",
    "PipelineConfig",
    "PipelineResult",
    "OutputFormatter",
    "OutputConfig",
]
