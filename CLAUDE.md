# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MS-Agent is a lightweight framework for building AI agents with autonomous exploration capabilities. It supports multiple LLM providers (ModelScope, OpenAI, Anthropic, DashScope, DeepSeek), tool calling via MCP (Model Context Protocol), and complex workflow orchestration.

## Build & Development Commands

```bash
# Installation from source
pip install -e .

# Install with specific features
pip install -e '.[research]'    # Research features (deep_research, doc_research)
pip install -e '.[code]'        # Code generation features
pip install -e '.[all]'         # All features

# Build wheel
make whl

# Run linting (pre-commit hooks)
make lint
# Or directly:
pre-commit run --all-files

# Build documentation
make docs        # Both English and Chinese
make docs-en     # English only
make docs-zh     # Chinese only
```

## Running the Framework

```bash
# CLI entry point
ms-agent run --config <config_path> --query "<query>" [--trust_remote_code true]

# Example: Run deep research
python projects/deep_research/run.py

# Example: Run code genesis
python ms_agent/cli/cli.py run --config projects/code_genesis --query "Build a todo app" --trust_remote_code true
```

## Architecture Overview

### Core Components

**Agent System** (`ms_agent/agent/`)
- `LLMAgent`: Primary agent implementation with tool calling, memory, and MCP support
- `AgentSkill`: Anthropic Agent Skills protocol implementation
- `CodeAgent`: Pure code execution agent
- Key method: `async run(inputs: Union[str, List[Message]]) -> List[Message]`

**Workflow System** (`ms_agent/workflow/`)
- `ChainWorkflow`: Sequential execution (step1 → step2 → step3)
- `DagWorkflow`: DAG-based parallel execution with topological sorting
- Configured via `workflow.yaml` files

**LLM Integration** (`ms_agent/llm/`)
- Unified interface via OpenAI-compatible API
- Providers: OpenAI, ModelScope, Anthropic, DashScope, DeepSeek
- Configuration: `llm.service`, `llm.model`, `llm.[service]_api_key`

**Tool System** (`ms_agent/tools/`)
- `ToolManager`: Central tool orchestration
- MCP Client for Model Context Protocol
- Search: Exa, SerpAPI, ArXiv
- Code execution: Local or sandboxed (Docker)

**Memory** (`ms_agent/memory/`): mem0-based long/short-term memory
**RAG** (`ms_agent/rag/`): LlamaIndex-based retrieval augmentation
**Skills** (`ms_agent/skill/`): Anthropic Skills protocol with semantic retrieval

### Configuration Pattern

All agents/workflows use YAML configuration:

```yaml
llm:
  service: modelscope|openai|anthropic|dashscope
  model: <model_id>
  [service]_api_key: <key>
  [service]_base_url: <url>

generation_config:
  temperature: 0.3
  max_tokens: 64000

prompt:
  system: |
    <system_prompt>

tools:
  file_system:
    mcp: false
    include: [read_file, write_file]

max_chat_round: 20
```

## Key Projects

| Project | Path | Purpose |
|---------|------|---------|
| Deep Research | `projects/deep_research/` | Autonomous research with multimodal reports |
| Code Genesis | `projects/code_genesis/` | AI code generation (Design → Code → Refine) |
| Fin Research | `projects/fin_research/` | Multi-agent financial research (DAG workflow) |
| Doc Research | `projects/doc_research/` | Document analysis and summarization |
| Agent Skills | `projects/agent_skills/` | Anthropic Skills protocol examples |

## Code Style

- **Linting**: flake8 (max-line-length: 120)
- **Formatting**: yapf (PEP8-based)
- **Imports**: isort (line_length: 79)
- Run `pre-commit run --all-files` before committing

## Key Patterns

### Creating Custom Agents
```python
from ms_agent.agent import LLMAgent

class CustomAgent(LLMAgent):
    async def run(self, inputs, **kwargs):
        # Custom implementation
        pass
```

### Creating Callbacks
```python
from ms_agent.callbacks import Callback

class CustomCallback(Callback):
    def on_task_begin(self, runtime, **kwargs): pass
    def on_generate_response(self, runtime, messages): pass
    def on_tool_call(self, runtime, tool_name, tool_args): pass
```

## Important Files

- `ms_agent/agent/agent.yaml`: Default agent configuration template
- `ms_agent/cli/cli.py`: CLI entry point (`ms-agent` command)
- `ms_agent/config/config.py`: Configuration loading with lifecycle handlers
- `setup.py`: Package definition, entry points, dependencies

## Session Changes Log

### Gemini API Configuration

Configured both `deep_research` and `code_genesis` projects to use Gemini API:

**deep_research** (`projects/deep_research/run.py`):
```python
chat_client = OpenAIChat(
    api_key='AIzaSyDmTcj4-ujVOIswqGLvt0fTZiVe49SU3ZY',
    base_url='https://generativelanguage.googleapis.com/v1beta/openai/',
    model='gemini-flash-lite-latest',
)
```

**code_genesis** (all YAML files in `projects/code_genesis/`):
```yaml
llm:
  service: openai
  model: gemini-flash-lite-latest
  openai_api_key:  AIzaSyDmTcj4-ujVOIswqGLvt0fTZiVe49SU3ZY # Set via environment or leave empty
  openai_base_url: https://generativelanguage.googleapis.com/v1beta/openai/
```

### GPU Acceleration (NVIDIA 4060)

Enabled GPU acceleration across multiple components:

1. **Docling Document Loader** (`ms_agent/tools/docling/doc_loader.py`):
   - Enabled Flash Attention 2 for faster document processing
   ```python
   accelerator_options.cuda_use_flash_attention2 = True
   ```

2. **LlamaIndex RAG** (`ms_agent/rag/llama_index_rag.py`):
   - Changed embedding model to use CUDA
   ```python
   Settings.embed_model = HuggingFaceEmbedding(model_name=self.embedding_model, device='cuda')
   ```

3. **Ray Extraction Manager** (`ms_agent/rag/extraction_manager.py`):
   - Added GPU to Ray cluster initialization
   - Configured workers to share GPU (0.25 GPU per worker = 4 workers per GPU)
   ```python
   ray.init(num_gpus=1, ...)
   _ExtractionWorker.options(num_cpus=..., num_gpus=0.25).remote(...)
   ```

### Bug Fixes

**JSON Serialization Fix** (`ms_agent/llm/openai_llm.py`):
- Changed `self.args.copy()` to `deepcopy(self.args)` to properly deep-copy nested structures like `extra_body` with `stop_sequences` lists
- This ensures all nested objects are converted to native Python types which are JSON serializable

### Prerequisites for GPU Support

```bash
# PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Ray for parallel processing
pip install "ray[default]"
```

### Editable Mode Installation (Critical)

**Issue**: When running code_genesis, encountered error:
```
omegaconf.errors.ConfigAttributeError: Missing key provider
    full_key: memory[0].llm.provider
```

**Root Cause**:
- The installed package at `.venv/Lib/site-packages/ms_agent/memory/diversity.py` had outdated code requiring `config.llm.provider`
- Local source code had already been fixed
- Running `uv run ms-agent` used the installed package, not local source

**Solution**: Reinstall in editable mode:
```bash
uv pip install -e .
```

**Why Editable Mode Matters**:
- Without `-e`: `uv run ms-agent` uses `.venv/Lib/site-packages/ms_agent/` (frozen snapshot)
- With `-e`: `uv run ms-agent` uses local source `ms_agent/` (live changes)
- Required when developing or when local source has bug fixes not in installed version

This information has been added to ONBOARD.md as a warning note in the installation section.
