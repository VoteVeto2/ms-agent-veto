"""
Tests for Orchestration Layer (Agent 3).

Run with: cd projects/deep_code_research && uv run pytest tests/test_orchestrator.py -v
"""
import pytest
import asyncio
import os
import sys
import tempfile
import json
import zipfile

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up API configuration
os.environ["OPENAI_API_KEY"] = "AIzaSyDmTcj4-ujVOIswqGLvt0fTZiVe49SU3ZY"
os.environ["OPENAI_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
os.environ["OPENAI_MODEL"] = "gemini-flash-lite-latest"


def _check_api_available() -> bool:
    """Check if API is available and not leaked."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key.startswith("AIzaSy"):
        return False
    return bool(api_key)


# ============= Fixtures =============

@pytest.fixture
def mock_research_context():
    """Create mock ResearchContext for testing."""
    from contracts import ResearchContext

    return ResearchContext(
        api_specs=[
            {"endpoint": "/users", "method": "GET", "description": "Get users"}
        ],
        code_patterns=[
            {"pattern": "Repository", "description": "Data access layer"}
        ],
        architecture={
            "modules": ["api", "services", "models"]
        },
        dependencies=["requests", "pydantic"],
        documents=[],
        rag_index=None,
        adaptive_rag=None
    )


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_files():
    """Sample generated files for testing."""
    return {
        "src/__init__.py": '"""Package init."""\n',
        "src/main.py": 'def main():\n    print("Hello")\n\nif __name__ == "__main__":\n    main()\n',
        "README.md": "# Project\n\nA sample project.\n",
        "requirements.txt": "pytest\nrequests\n"
    }


@pytest.fixture
def sample_metrics():
    """Sample metrics for testing."""
    return {
        "total_debug_iterations": 3,
        "simulation_results": [
            {"input": 1, "expected": 2, "simulated": 2, "is_correct": True}
        ],
        "test_results": [
            {"file": "src/main.py", "test": "test_main", "passed": True}
        ]
    }


# ============= Non-LLM Tests =============

def test_pipeline_config_defaults():
    """Test PipelineConfig default values."""
    from orchestrator.pipeline import PipelineConfig

    config = PipelineConfig()

    assert config.use_adaptive_rag == True
    assert config.use_simulation_debug == True
    assert config.use_auto_tests == True
    assert config.max_refinement_iterations == 3
    assert config.output_format == "zip"


def test_pipeline_config_from_dict():
    """Test PipelineConfig.from_dict()."""
    from orchestrator.pipeline import PipelineConfig

    config = PipelineConfig.from_dict({
        "use_auto_tests": False,
        "max_refinement_iterations": 5,
        "output_format": "directory"
    })

    assert config.use_auto_tests == False
    assert config.max_refinement_iterations == 5
    assert config.output_format == "directory"
    # Defaults preserved
    assert config.use_adaptive_rag == True


def test_pipeline_config_ignores_unknown_keys():
    """Test that unknown keys are ignored."""
    from orchestrator.pipeline import PipelineConfig

    config = PipelineConfig.from_dict({
        "unknown_key": "value",
        "use_auto_tests": False
    })

    assert config.use_auto_tests == False
    assert not hasattr(config, "unknown_key")


def test_pipeline_result_defaults():
    """Test PipelineResult default values."""
    from orchestrator.pipeline import PipelineResult

    result = PipelineResult(success=False)

    assert result.success == False
    assert result.files == {}
    assert result.output_path is None
    assert result.metrics == {}
    assert result.errors == []
    assert result.stages_completed == []


def test_output_config_defaults():
    """Test OutputConfig default values."""
    from orchestrator.output_formatter import OutputConfig

    config = OutputConfig()

    assert config.format == "zip"
    assert config.include_metrics == True
    assert config.include_timestamp == True


@pytest.mark.asyncio
async def test_output_formatter_write_directory(temp_output_dir, sample_files, sample_metrics):
    """Test OutputFormatter directory output."""
    from orchestrator.output_formatter import OutputFormatter, OutputConfig

    formatter = OutputFormatter(OutputConfig(
        format="directory",
        include_timestamp=False
    ))

    output_path = await formatter.write(sample_files, temp_output_dir, sample_metrics)

    # Check output exists
    assert os.path.exists(output_path)
    assert os.path.isdir(output_path)

    # Check files written
    assert os.path.exists(os.path.join(output_path, "src", "__init__.py"))
    assert os.path.exists(os.path.join(output_path, "src", "main.py"))
    assert os.path.exists(os.path.join(output_path, "README.md"))

    # Check metrics written
    metrics_path = os.path.join(output_path, "_metrics.json")
    assert os.path.exists(metrics_path)
    with open(metrics_path) as f:
        loaded_metrics = json.load(f)
    assert loaded_metrics["total_debug_iterations"] == 3

    # Check manifest written
    manifest_path = os.path.join(output_path, "_manifest.json")
    assert os.path.exists(manifest_path)
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert manifest["file_count"] == 4


@pytest.mark.asyncio
async def test_output_formatter_write_zip(temp_output_dir, sample_files, sample_metrics):
    """Test OutputFormatter ZIP output."""
    from orchestrator.output_formatter import OutputFormatter, OutputConfig

    formatter = OutputFormatter(OutputConfig(
        format="zip",
        include_timestamp=False
    ))

    output_path = await formatter.write(sample_files, temp_output_dir, sample_metrics)

    # Check ZIP exists
    assert os.path.exists(output_path)
    assert output_path.endswith(".zip")

    # Check ZIP contents
    with zipfile.ZipFile(output_path, 'r') as zf:
        names = zf.namelist()
        assert "src/__init__.py" in names
        assert "src/main.py" in names
        assert "README.md" in names
        assert "_metrics.json" in names
        assert "_manifest.json" in names

        # Verify metrics content
        with zf.open("_metrics.json") as f:
            metrics = json.load(f)
        assert metrics["total_debug_iterations"] == 3


@pytest.mark.asyncio
async def test_output_formatter_no_metrics(temp_output_dir, sample_files):
    """Test OutputFormatter without metrics."""
    from orchestrator.output_formatter import OutputFormatter, OutputConfig

    formatter = OutputFormatter(OutputConfig(
        format="directory",
        include_metrics=False,
        include_timestamp=False
    ))

    output_path = await formatter.write(sample_files, temp_output_dir, None)

    # Metrics should not be written
    metrics_path = os.path.join(output_path, "_metrics.json")
    assert not os.path.exists(metrics_path)

    # Manifest should still exist
    manifest_path = os.path.join(output_path, "_manifest.json")
    assert os.path.exists(manifest_path)


def test_output_formatter_get_file_type():
    """Test file type detection."""
    from orchestrator.output_formatter import OutputFormatter

    formatter = OutputFormatter()

    assert formatter._get_file_type("main.py") == "python"
    assert formatter._get_file_type("app.js") == "javascript"
    assert formatter._get_file_type("config.yaml") == "yaml"
    assert formatter._get_file_type("README.md") == "markdown"
    assert formatter._get_file_type("data.unknown") == "unknown"


def test_pipeline_stage_enum():
    """Test PipelineStage enum values."""
    from orchestrator.pipeline import PipelineStage

    assert PipelineStage.INIT.value == "init"
    assert PipelineStage.RESEARCH.value == "research"
    assert PipelineStage.CODEGEN.value == "codegen"
    assert PipelineStage.COMPLETE.value == "complete"


def test_pipeline_init():
    """Test Pipeline initialization."""
    from orchestrator.pipeline import Pipeline, PipelineConfig

    # Default config
    pipeline = Pipeline()
    assert pipeline.config is not None
    assert pipeline.on_progress is None

    # Custom config
    config = PipelineConfig(max_refinement_iterations=5)
    pipeline = Pipeline(config)
    assert pipeline.config.max_refinement_iterations == 5


def test_generate_manifest(sample_files):
    """Test manifest generation."""
    from orchestrator.output_formatter import OutputFormatter

    formatter = OutputFormatter()
    manifest = formatter._generate_manifest(sample_files, {"test": "data"})

    assert manifest["file_count"] == 4
    assert manifest["metrics_included"] == True
    assert "generated_at" in manifest
    assert len(manifest["files"]) == 4

    # Check file entries
    file_paths = [f["path"] for f in manifest["files"]]
    assert "src/main.py" in file_paths


# ============= Integration Tests (with mocks) =============

@pytest.mark.asyncio
async def test_pipeline_progress_callback():
    """Test that progress callback is called."""
    from orchestrator.pipeline import Pipeline, PipelineConfig

    progress_calls = []

    def on_progress(stage: str, percent: float):
        progress_calls.append((stage, percent))

    config = PipelineConfig(max_refinement_iterations=0)
    pipeline = Pipeline(config)
    pipeline.on_progress = on_progress

    # We can't run full pipeline without mocking, but we can test callback mechanism
    pipeline._report_progress("test", 0.5)

    assert len(progress_calls) == 1
    assert progress_calls[0] == ("test", 0.5)


def test_orchestrator_imports():
    """Test that orchestrator module imports correctly."""
    from orchestrator import (
        run_pipeline,
        Pipeline,
        PipelineConfig,
        PipelineResult,
        OutputFormatter,
        OutputConfig
    )

    assert run_pipeline is not None
    assert Pipeline is not None
    assert PipelineConfig is not None
    assert PipelineResult is not None
    assert OutputFormatter is not None
    assert OutputConfig is not None


# ============= LLM Tests (skipped without API) =============

@pytest.mark.skipif(not _check_api_available(), reason="API key not available or leaked")
@pytest.mark.asyncio
async def test_full_pipeline_basic(temp_output_dir):
    """Test full pipeline execution (requires API)."""
    from orchestrator import run_pipeline

    # This would require a real references.zip
    # For now, we skip if no API available
    pass
