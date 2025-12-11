DeepCodeResearch
================

Overview
--------
Pipeline that ingests reference docs, runs RAG-style research, plans code, generates a repo, and packages output. Entry point: `run.py`.


Set up api
------ 
write the following in `.env` under the same working directory

```
OPENAI_API_KEY="AIzaSyAeumyg6QcxiNxYtJ0OnTLiMV1dY9kp5q0"
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL=gemini-3-pro-preview
```

You can choose two other models from gemini-family, namely 
```
OPENAI_MODEL=gemini-flash-latest
# Or 
OPENAI_MODEL=gemini-flash-lite-latest
```
For testing purpose, we strongly suggest you go with `OPENAI_MODEL=gemini-flash-lite-latest`: it save both your time and our wallets.


Folder Structure
----------------
```
deep_code_research/
├── run.py                  # Entry point
├── contracts.py            # Shared data contracts
├── debug_logger.py         # NDJSON logging utility
├── .env                    # API configuration
│
├── research/               # Agent 1: Research
│   ├── adaptive_rag.py     # Adaptive RAG orchestration
│   ├── document_parser.py  # Doc/ZIP parsing
│   ├── info_extractor.py   # Structured info extraction
│   └── rag_engine.py       # RAG index & retrieval
│
├── codegen/                # Agent 2: Code Generation
│   ├── code_planner.py     # Architecture planning
│   ├── code_generator.py   # Code synthesis
│   ├── test_generator.py   # Auto test generation
│   ├── simulation_debugger.py  # CODESIM pattern
│   ├── self_debugger.py    # Self-healing refinement
│   └── readme_generator.py # README generation
│
├── orchestrator/           # Agent 3: Core
│   ├── pipeline.py         # Pipeline coordination
│   └── output_formatter.py # Output packaging
│
├── extracted_references/   # Parsed reference docs
├── output/                 # Generated code repos
├── tests/                  # Unit tests
└── agent_competition_examples/  # Example references
```





Setup Virtual Environment
-------------------------
Navigate to the project directory and create a virtual environment using `uv`:
```powershell
cd projects\deep_code_research
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt
```

Run the Pipeline
----------------
PowerShell from repo root:
```
cd projects\deep_code_research
uv run --env-file .env python run.py --prompt "<your prompt>" --references <path_to_references>
```
Example prompt: `Read DeepResearch.pdf first, design a possible architecture to demonstrate that, output including a complete code repo and a README.md`.
- `DEBUG_RUN_ID` is auto-set per run; optionally set it yourself to group logs.

Logging & Monitoring
--------------------
- Logger: `projects/deep_code_research/debug_logger.py` writes NDJSON to `.cursor\debug.log` (repo root).
- Live tail options (PowerShell):
```
Get-Content -Path ".cursor\debug.log" -Tail 50 -Wait
Get-Content -Path "c:\Users\votev\Documents\Git\ms-agent-veto\.cursor\debug.log" -Wait
```
- For a clean run, delete `.cursor\debug.log` before starting (**manual step**).
- Captured events: pipeline stage start/done (research, codegen, refinement, output), run start/error, invocation context (prompt length, references path, output dir, config), and codegen checkpoints keyed by `runId`.

Tests
-----
From repo root:
```
cd projects\deep_code_research
uv run pytest tests -q
```

Output Results and Timing
---

| Model | Duration | Output Folder |
|-------|----------|---------------|
| `gemini-flash-lite-latest` | ~10 min | `generated_code4_DeepResearch-pdf_gemini-flash-lite-latest` |
| `gemini-flash-latest` | ~35 min | `generated_code5_DeepResearch-pdf_Gemini-flash-latest` |
| `gemini-3-pro-preview` | ~ 90 min | `generated_code6_DeepResearch-pdf_Gemini-3-pro-preview` |