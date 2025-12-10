# DeepCodeResearch - Multi-Agent Development Guide

## Overview

This directory contains instructions for 3 Claude Code agents to collaboratively build the DeepCodeResearch system.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DeepCodeResearch Architecture                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐                                                    │
│  │  references.zip │                                                    │
│  │  + prompt       │                                                    │
│  └────────┬────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐  ResearchContext   ┌─────────────────┐            │
│  │   AGENT 1       │ ─────────────────▶ │   AGENT 2       │            │
│  │   Research      │                    │   CodeGen       │            │
│  │   Layer         │                    │   Layer         │            │
│  └─────────────────┘                    └────────┬────────┘            │
│                                                  │                      │
│                                         Dict[str, str]                  │
│                                                  │                      │
│                                                  ▼                      │
│                                        ┌─────────────────┐             │
│                                        │   AGENT 3       │             │
│                                        │   Orchestrator  │             │
│                                        └────────┬────────┘             │
│                                                 │                       │
│                                                 ▼                       │
│                                        ┌─────────────────┐             │
│                                        │  OUTPUT:        │             │
│                                        │  - code repo/   │             │
│                                        │  - README.md    │             │
│                                        │  - records.yaml │             │
│                                        └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Assignments

| Agent | Role | Directory | Key Deliverable |
|-------|------|-----------|-----------------|
| **Agent 1** | Research Layer | `research/` | `research_references()` → `ResearchContext` |
| **Agent 2** | Code Generation | `codegen/` | `generate_repository()` → `Dict[str, str]` |
| **Agent 3** | Orchestrator | `core/` + `contracts.py` | `DeepCodeResearchAgent.run()` |
| **Agent 4** | Improvement Specialist | `codegen/` + `core/` | SOTA enhancements (simulation, tests, memory) |

---

## Execution Order

```
Time     Agent 1          Agent 2          Agent 3
─────    ───────          ───────          ───────
  0      WAIT             WAIT             CREATE contracts.py ← CRITICAL
  │                                        │
  5      ◄────────────────────────────────┘ (contracts.py ready)
  │      │                │
 10      Start research/  Start codegen/   Start core/
  │      │                │                │
 30      DocumentParser   CodePlanner      RecordManager
  │      │                │                │
 60      RAGEngine        CodeGenerator    DeepCodeResearchAgent
  │      │                │                │
 90      InfoExtractor    SelfDebugger     CLI (run.py)
  │      │                │                │
120      ✓ Tests pass     ✓ Tests pass     ✓ Tests pass
  │      │                │                │
         └────────────────┴────────────────┘
                          │
                    INTEGRATION
                          │
                          ▼
                    Full system test
```

---

## Quick Start for Each Agent

### Agent 1 (Research)
```bash
# Read your instructions
cat DeepCodeResearch/CC-instruct/agent1-research.md

# Wait for Agent 3 to create contracts.py, then:
cd projects/deep_code_research
# Create research/ directory and implement
```

### Agent 2 (CodeGen)
```bash
# Read your instructions
cat DeepCodeResearch/CC-instruct/agent2-codegen.md

# Wait for Agent 3 to create contracts.py, then:
cd projects/deep_code_research
# Create codegen/ directory and implement
```

### Agent 3 (Orchestrator) - START HERE
```bash
# Read your instructions
cat DeepCodeResearch/CC-instruct/agent3-orchestrator.md

# CREATE contracts.py FIRST!
cd projects/deep_code_research
# Create contracts.py, then notify others
```

### Agent 4 (Improvement Specialist) - AFTER INITIAL BUILD
```bash
# Read your instructions
cat DeepCodeResearch/CC-instruct/agent4-improve.md

# Enhance existing code with SOTA patterns:
# - Simulation-based debugging (CODESIM)
# - Auto test generation (AgentCoder)
# - Adaptive RAG (CodeRAG + SELF-RAG)
# - Hierarchical memory (MemOS)
```

---

## Shared API Configuration

All agents use the same LLM configuration:

```python
import os
os.environ["OPENAI_API_KEY"] = "AIzaSyDmTcj4-ujVOIswqGLvt0fTZiVe49SU3ZY"
os.environ["OPENAI_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
os.environ["OPENAI_MODEL"] = "gemini-flash-lite-latest"
```

---

## Final Project Structure

```
projects/deep_code_research/
├── contracts.py              # Agent 3 creates FIRST
├── __init__.py
│
├── research/                 # Agent 1
│   ├── __init__.py
│   ├── document_parser.py
│   ├── rag_engine.py
│   └── info_extractor.py
│
├── codegen/                  # Agent 2
│   ├── __init__.py
│   ├── code_planner.py
│   ├── code_generator.py
│   ├── self_debugger.py
│   └── readme_generator.py
│
├── core/                     # Agent 3
│   ├── __init__.py
│   ├── agent.py
│   └── records.py
│
├── tests/
│   ├── test_research.py      # Agent 1
│   ├── test_codegen.py       # Agent 2
│   └── test_core.py          # Agent 3
│
├── run.py                    # Agent 3 (CLI)
└── config.yaml               # Agent 3
```

---

## Integration Interfaces

### Agent 1 → Agent 3
```python
# Agent 3 calls:
from research import research_references
context: ResearchContext = await research_references("./refs.zip")
```

### Agent 3 → Agent 2
```python
# Agent 3 calls:
from codegen import generate_repository
files: Dict[str, str] = await generate_repository(prompt, context)
```

---

## Testing Strategy

### Individual Tests (Each Agent)
```bash
# Agent 1
pytest tests/test_research.py -v

# Agent 2
pytest tests/test_codegen.py -v

# Agent 3
pytest tests/test_core.py -v
```

### Integration Test (Agent 3 runs)
```bash
python run.py \
  --prompt "Build a REST API client" \
  --references ./test_refs.zip \
  --output ./test_output
```

---

## Communication Protocol

1. **Agent 3 announces**: "contracts.py is ready"
2. **Agent 1 & 2 start**: Work in parallel
3. **Agent 1 announces**: "research module ready for integration"
4. **Agent 2 announces**: "codegen module ready for integration"
5. **Agent 3 integrates**: Pulls both modules, runs full test
6. **All agents**: Fix any integration issues

---

## Troubleshooting

### Import Errors
```python
# If relative imports fail, try:
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### contracts.py Not Found
```bash
# Ensure you're in the right directory:
cd projects/deep_code_research
ls contracts.py  # Should exist
```

### API Errors
```bash
# Verify API key is set:
python -c "import os; print(os.environ.get('OPENAI_API_KEY', 'NOT SET'))"
```

---

## Success Criteria

- [ ] `contracts.py` exists and is importable
- [ ] All 3 test files pass independently
- [ ] `python run.py --prompt "test" --references test.zip --output out` works
- [ ] Output contains: code files, README.md, input_record.yaml, output_record.yaml
