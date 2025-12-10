# DeepCodeResearch - Onboarding Guide

## Project Overview

DeepCodeResearch is a multi-agent code generation system that combines:
1. **Research Layer** (Agent 1) - Parses documentation, builds RAG indexes, extracts structured info
2. **CodeGen Layer** (Agent 2) - Plans, generates, debugs, and tests code
3. **Orchestration Layer** (Agent 3) - Coordinates pipeline, handles iteration/refinement, produces output

## Project Structure

```
deep_code_research/
├── contracts.py           # Shared data contracts (ResearchContext, FileSpec, CodePlan)
├── run.py                 # Main CLI entry point
├── research/              # Agent 1: Research Layer
│   ├── __init__.py        # Main entry: research_references()
│   ├── document_parser.py # Parse docs from ZIP files
│   ├── rag_engine.py      # LlamaIndex RAG indexing
│   ├── adaptive_rag.py    # Adaptive retrieval with requirement graphs
│   └── info_extractor.py  # Extract APIs, patterns, architecture
├── codegen/               # Agent 2: Code Generation Layer
│   ├── __init__.py        # Main entry: generate_repository()
│   ├── code_planner.py    # Plan file structure
│   ├── code_generator.py  # Generate code files
│   ├── self_debugger.py   # Basic syntax validation
│   ├── simulation_debugger.py  # CODESIM pattern simulation
│   ├── test_generator.py  # AgentCoder pattern test generation
│   └── readme_generator.py     # Generate README.md
├── orchestrator/          # Agent 3: Orchestration Layer
│   ├── __init__.py        # Main entry: run_pipeline()
│   ├── pipeline.py        # Pipeline coordinator with stages
│   └── output_formatter.py # ZIP/directory output generation
├── tests/
│   ├── test_research.py   # Research layer tests
│   ├── test_codegen.py    # CodeGen layer tests
│   └── test_orchestrator.py # Orchestrator tests
└── extracted_references/  # Sample reference files
```

## Quick Start

### 1. Install Dependencies

```bash
cd projects/deep_code_research
uv pip install openai llama-index pytest pytest-asyncio pyyaml
```

### 2. Set Environment Variables

**Option A: .env (recommended)**

Create a `.env` file at the repo root:

```
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL=gemini-flash-lite-latest
```

Use it when running:

```bash
uv run --env-file .env python run.py --prompt "Create a REST API client" --references agent_competition_examples/references
```

**Option B: shell exports**

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"  # For Gemini
export OPENAI_MODEL="gemini-flash-lite-latest"
```

### 3. Run the CLI

```bash
# Basic usage
python run.py --prompt "Create a REST API client" --references ./agent_competition_examples/references

# With options
python run.py --prompt "Build a CLI tool" --references ./agent_competition_examples/references --output ./generated --format directory

# Show help
python run.py --help
```

### 4. Run Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test files
uv run pytest tests/test_research.py -v
uv run pytest tests/test_codegen.py -v
uv run pytest tests/test_orchestrator.py -v
```

## Implementation Status

### Research Layer (Agent 1) ✅
- [x] DocumentParser - Parse ZIP files with docs
- [x] RAGEngine - Build LlamaIndex indexes
- [x] AdaptiveRAGEngine - Requirement-graph based retrieval
- [x] InfoExtractor - Extract structured information
- [x] Tests passing (11 tests)

### CodeGen Layer (Agent 2) ✅
- [x] CodePlanner - Plan code structure
- [x] CodeGenerator - Generate files with RAG context
- [x] SelfDebugger - Syntax validation and fixing
- [x] SimulationDebugger - CODESIM pattern execution simulation
- [x] TestGenerator - AgentCoder pattern test generation
- [x] ReadmeGenerator - Generate documentation
- [x] Tests passing (18 tests)

### Orchestration Layer (Agent 3) ✅
- [x] Pipeline - Stage-based execution coordinator
- [x] PipelineConfig - YAML/dict configuration
- [x] Refinement Loop - Iterate based on test results
- [x] OutputFormatter - ZIP and directory output
- [x] CLI Interface - Full command-line support
- [x] Tests passing (15 tests)

## CLI Reference

```bash
python run.py [OPTIONS]

Options:
  -p, --prompt TEXT        Task description for code generation (required)
  -r, --references PATH    Path to docs directory (e.g., ./agent_competition_examples/references) (required)
  -o, --output PATH        Output directory (default: ./output)
  -c, --config PATH        Path to YAML configuration file
  -f, --format [zip|dir]   Output format (default: zip)
  --no-tests               Disable automatic test generation
  --no-simulation          Disable simulation-based debugging
  --no-adaptive-rag        Disable adaptive RAG
  --max-iterations N       Maximum refinement iterations (default: 3)
  -v, --verbose            Enable verbose output
  -q, --quiet              Suppress progress output
```

## Usage Examples

### Full Pipeline (CLI)

```bash
python run.py \
  --prompt "Create a REST API client with authentication" \
  --references ./agent_competition_examples/references \
  --output ./generated \
  --verbose
```

### Full Pipeline (Python)

```python
from orchestrator import run_pipeline

result = await run_pipeline(
    prompt="Create a REST API client",
    references_path="./agent_competition_examples/references",
    output_dir="./output",
    config={
        "use_simulation_debug": True,
        "use_auto_tests": True,
        "max_refinement_iterations": 3
    }
)

print(f"Success: {result.success}")
print(f"Output: {result.output_path}")
print(f"Files: {len(result.files)}")
```

### Research Layer Only

```python
from research import research_references

context = await research_references("agent_competition_examples/references")

print(context.api_specs)      # List of API specs
print(context.code_patterns)  # List of code patterns
print(context.dependencies)   # List of dependencies

# Query RAG
result = context.rag_index.query("How to authenticate?")
```

### CodeGen Layer Only

```python
from codegen import generate_repository

files, metrics = await generate_repository(
    prompt="Create a REST API client",
    research_context=context,
    use_simulation_debug=True,
    use_auto_tests=True
)

for path, content in files.items():
    print(f"{path}: {len(content)} bytes")
```

## Configuration

### YAML Config File

```yaml
# pipeline.yaml
pipeline:
  use_adaptive_rag: true
  use_simulation_debug: true
  use_auto_tests: true
  max_refinement_iterations: 3
  output_format: zip
  include_metrics: true

# Can also include prompt/references
prompt: "Create a REST API client"
references: "./agent_competition_examples/references"
```

### Pipeline Stages

1. **Research** - Parse docs, build RAG, extract info
2. **CodeGen** - Plan structure, generate files
3. **Debugging** - Syntax validation, simulation debugging
4. **Testing** - Auto test generation and execution
5. **Refinement** - Iterate based on test results
6. **Output** - Package into ZIP or directory

## Key Patterns

### Lazy Initialization
All LLM clients use lazy initialization:

```python
def _get_client(self) -> Optional[OpenAI]:
    if self._client_initialized:
        return self.client
    self._client_initialized = True
    # ... initialize client
```

### Graceful Fallbacks
Components provide defaults when LLM unavailable:

```python
client = self._get_client()
if not client:
    return self.get_default_plan()
```

### Progress Callbacks
Track pipeline progress:

```python
def on_progress(stage: str, percent: float):
    print(f"{stage}: {percent*100:.0f}%")

result = await run_pipeline(..., on_progress=on_progress)
```

## Test Categories

1. **Non-LLM Tests** (31 tests, always run)
   - Contract imports
   - Default plans/fallbacks
   - JSON parsing
   - Syntax validation
   - Output formatting

2. **LLM Tests** (13 tests, skipped without API)
   - Plan generation
   - Code generation
   - Debugging
   - Test generation

## Next Steps (Future Enhancements)

- [ ] Add logging framework
- [ ] Performance benchmarks
- [ ] Example workflow templates
- [ ] Web UI interface
- [ ] Parallel file generation
- [ ] Custom tool integration
