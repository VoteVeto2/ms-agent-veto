#!/usr/bin/env python
"""
DeepCodeResearch - Main Entry Point

Usage:
    python run.py --prompt "Create a REST API client" --references ./refs.zip
    python run.py --prompt "Build a CLI tool" --references ./docs/ --output ./out
    python run.py --config config.yaml
"""

import os
import sys
import asyncio
import argparse
import time
from typing import Optional

from debug_logger import log_event

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set default API configuration (Gemini)
os.environ.setdefault("OPENAI_API_KEY", "AIzaSyDmTcj4-ujVOIswqGLvt0fTZiVe49SU3ZY")
os.environ.setdefault("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
os.environ.setdefault("OPENAI_MODEL", "gemini-flash-lite-latest")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="DeepCodeResearch - AI-powered code generation from documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate code from documentation
  python run.py --prompt "Create a REST API client" --references ./refs.zip

  # Use directory of docs instead of ZIP
  python run.py --prompt "Build a CLI tool" --references ./docs/

  # Custom output directory
  python run.py --prompt "Create utils" --references ./refs.zip --output ./generated

  # Use config file
  python run.py --config pipeline.yaml

  # Disable features
  python run.py --prompt "Simple script" --references ./refs.zip --no-tests --no-simulation
        """
    )

    parser.add_argument(
        "--prompt", "-p",
        type=str,
        help="Task description for code generation"
    )

    parser.add_argument(
        "--references", "-r",
        type=str,
        help="Path to references.zip or documentation directory"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./output",
        help="Output directory (default: ./output)"
    )

    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to YAML configuration file"
    )

    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["zip", "directory"],
        default="zip",
        help="Output format (default: zip)"
    )

    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Disable automatic test generation"
    )

    parser.add_argument(
        "--no-simulation",
        action="store_true",
        help="Disable simulation-based debugging"
    )

    parser.add_argument(
        "--no-adaptive-rag",
        action="store_true",
        help="Disable adaptive RAG (use basic RAG)"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum refinement iterations (default: 3)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress output"
    )

    return parser.parse_args()


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    try:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        print("Warning: PyYAML not installed, using defaults")
        return {}
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
        return {}


def progress_callback(stage: str, percent: float):
    """Default progress callback."""
    bar_width = 30
    filled = int(bar_width * percent)
    bar = "=" * filled + "-" * (bar_width - filled)
    print(f"\r[{bar}] {stage}: {percent*100:.0f}%", end="", flush=True)
    if percent >= 1.0:
        print()


async def main():
    """Main entry point."""
    args = parse_args()
    run_id = os.environ.get("DEBUG_RUN_ID") or str(int(time.time() * 1000))
    os.environ["DEBUG_RUN_ID"] = run_id

    # Build config
    config = {}

    # Load from file if specified
    if args.config:
        config = load_config(args.config)

    # Override with CLI args
    if args.no_tests:
        config["use_auto_tests"] = False
    if args.no_simulation:
        config["use_simulation_debug"] = False
    if args.no_adaptive_rag:
        config["use_adaptive_rag"] = False
    if args.max_iterations:
        config["max_refinement_iterations"] = args.max_iterations
    if args.format:
        config["output_format"] = args.format

    # Get prompt and references
    prompt = args.prompt or config.get("prompt")
    references = args.references or config.get("references")

    if not prompt:
        print("Error: --prompt is required")
        print("Use --help for usage information")
        sys.exit(1)

    if not references:
        print("Error: --references is required")
        print("Use --help for usage information")
        sys.exit(1)

    if not os.path.exists(references):
        print(f"Error: References path does not exist: {references}")
        sys.exit(1)

    # Set up progress callback
    on_progress = None if args.quiet else progress_callback

    if args.verbose:
        print(f"Prompt: {prompt}")
        print(f"References: {references}")
        print(f"Output: {args.output}")
        print(f"Config: {config}")
        print()

    # Run pipeline
    from orchestrator import run_pipeline

    print("Starting DeepCodeResearch pipeline...")
    print()

    try:
        # region agent log
        log_event(
            location="run.main",
            message="invoke_pipeline",
            data={
                "prompt_chars": len(prompt) if prompt else 0,
                "references_path": references,
                "output_dir": args.output,
                "config": config,
            },
            run_id=run_id,
            hypothesis_id="H0",
        )
        # endregion

        result = await run_pipeline(
            prompt=prompt,
            references_path=references,
            output_dir=args.output,
            config=config,
            on_progress=on_progress,
            run_id=run_id,
        )

        print()
        if result.success:
            print(f"Success! Generated {len(result.files)} files")
            print(f"Output: {result.output_path}")

            if args.verbose:
                print()
                print("Files generated:")
                for path in sorted(result.files.keys()):
                    print(f"  - {path}")

                if result.metrics:
                    print()
                    print("Metrics:")
                    print(f"  Debug iterations: {result.metrics.get('total_debug_iterations', 0)}")
                    print(f"  Simulation results: {len(result.metrics.get('simulation_results', []))}")
                    print(f"  Test results: {len(result.metrics.get('test_results', []))}")
        else:
            print("Pipeline failed!")
            for error in result.errors:
                print(f"  Error: {error}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nAborted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
