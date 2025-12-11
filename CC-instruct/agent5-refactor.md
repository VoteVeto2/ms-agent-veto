# Refactor `deep_code_reserach`

## Key Highlights
- Scope: ~8,150 lines of code across 37 files implementing a general-purpose research agent framework.
- Architecture:
  - ✅ Core abstractions — Task models, Evidence/Citation/Uncertainty models, ABCs for all components.
  - ✅ Multimodal parsers — Text (reuse DocumentParser), Image, Formula, Code with plugin registry.
  - ✅ Knowledge layer — SQLite-backed multimodal knowledge graph with cross-modal relationships.
  - ✅ Reasoning engines — Chain-of-Research, conflict resolution, uncertainty quantification.
  - ✅ Agent orchestration — Planner, Executor, Reviewer, Coordinator.
- Implementation strategy:
  - 7 phases over 4 weeks.
  - Standalone system (minimal ms-agent dependencies).
  - Extensive code reuse from `deep_code_research` (~1,200 LOC).
  - MVP options if full scope is too large (MVP1: 2,500 LOC, 15 files).
- Critical innovations:
  1. Cross-modal KG — Evidence nodes with typed edges (DESCRIBES, CONTRADICTS, SUPPORTS, etc.).
  2. Conflict resolution — Multi-source reconciliation with credibility weighting.
  3. Plugin architecture — Extensible parsers, reasoners, and domain plugins.
- Status: User approved Claude's plan. Plan saved to `~\.claude\plans\inherited-sniffing-karp.md` (`/plan` to edit).

## Overview
- Build a standalone, general-purpose research agent framework at `projects/deepresearch/` with comprehensive multimodal support, advanced reasoning capabilities, and a knowledge graph backend.
- Scope: ~8,150 LOC across 37 files.
- Approach: Standalone system (minimal ms-agent dependencies).
- Strategy: Phased MVP implementation over 4 weeks.

## Project Goals
- ✅ Core abstractions for tasks, evidence, citations, and uncertainty.
- ✅ Multimodal parsers for text, images, formulas, code (plugin architecture).
- ✅ Reasoning engines including Chain-of-Research, conflict resolution, uncertainty quantification.
- ✅ Knowledge layer with local graph storage, public KB integration (PubMed/ArXiv), and domain plugins.
- ✅ Agent orchestration for planning, execution, review, and coordination.

## Directory Structure
```
projects/deepresearch/
├── core/                          # Core abstractions (800 LOC)
│   ├── base.py                    # ABCs: ResearchAgent, ModalParser, Reasoner, KnowledgeSource
│   ├── task.py                    # Task/Subtask/Plan/Step models
│   ├── evidence.py                # Evidence, EvidenceChain, Citation, Uncertainty
│   └── session.py                 # ResearchSession (stateful context)
├── modal/                         # Multimodal parsers (1,800 LOC)
│   ├── registry.py                # Plugin registration system
│   ├── text.py                    # PDF/HTML/TeX (reuse DocumentParser)
│   ├── image.py                   # Figure/table extraction + VQA
│   ├── formula.py                 # LaTeX/SymPy parsing + embeddings
│   ├── code.py                    # Code parsing + sandbox execution
│   ├── audio.py                   # Audio transcription (optional)
│   └── three_d.py                 # PDB/CIF/STL (optional)
├── knowledge/                     # Knowledge layer (2,200 LOC)
│   ├── base.py                    # KB abstract interface
│   ├── local_kb.py                # SQLite-backed storage
│   ├── multimodal_kg.py           # Cross-modal knowledge graph ⭐
│   ├── public_kb.py               # PubMed/ArXiv/S2 integration
│   └── domain_plugins/
│       ├── base_plugin.py         # DomainPlugin ABC
│       ├── bio_plugin.py          # Biomedical ontology
│       └── chem_plugin.py         # Chemistry rules
├── reasoning/                     # Reasoning engines (1,500 LOC)
│   ├── registry.py                # Reasoner registration
│   ├── chain_of_research.py       # CoR strategy (reuse adaptive_rag patterns)
│   ├── uncertainty.py             # MC Dropout, Ensemble, Calibration
│   ├── conflict_resolver.py       # Multi-source reconciliation ⭐
│   └── causal_inference.py        # Causal/counterfactual reasoning
├── agents/                        # Agent layer (1,400 LOC)
│   ├── planner.py                 # Task decomposition
│   ├── executor.py                # Step execution
│   ├── reviewer.py                # Self-critique
│   └── coordinator.py             # Multi-agent orchestration
├── io/                            # I/O layer (700 LOC)
│   ├── input_parser.py            # Multimodal input parsing
│   └── output_formatter.py        # Markdown/HTML/LaTeX/JSON output
├── tests/                         # Testing (600 LOC)
│   ├── conftest.py                # Shared fixtures
│   ├── test_core.py
│   ├── test_modal.py
│   ├── test_knowledge.py
│   ├── test_reasoning.py
│   └── test_agents.py
├── run.py                         # CLI entry point
├── config.yaml                    # Default configuration
└── README.md
```

⭐ = Critical complexity points

## Implementation Phases
### Phase 1: Foundation (Core Abstractions) — Week 1
- Files: 4 | LOC: ~800 | Priority: CRITICAL
- Build order:
  1. `core/task.py` — Task/Subtask/Plan/Step dataclasses.
  2. `core/evidence.py` — Evidence/Citation/Uncertainty models.
  3. `core/session.py` — ResearchSession with save/load.
  4. `core/base.py` — ABCs: ResearchAgent, ModalParser, Reasoner, KnowledgeSource, DomainPlugin.
- Key interfaces:
```
# ResearchAgent ABC
async def run(task: Task, session: ResearchSession) -> Task
async def plan(task: Task) -> Plan

# ModalParser ABC
async def parse(input_data: Any, **kwargs) -> List[Evidence]
async def validate(input_data: Any) -> bool

# Reasoner ABC
async def reason(evidence: List[Evidence], query: str) -> EvidenceChain
async def estimate_uncertainty(chain: EvidenceChain) -> Uncertainty

# KnowledgeSource ABC
async def search(query: str, filters: Dict) -> List[Evidence]
async def add_evidence(evidence: Evidence) -> str
async def get_related(evidence_id: str, relation_type: str) -> List[Evidence]
```
- Testing: 100% coverage (dataclasses + ABCs).

### Phase 2: Modal Processing — Week 2
- Files: 7 | LOC: ~1,800 | Priority: HIGH
- Build order:
  1. `modal/registry.py` — Plugin registration with auto-discovery.
  2. `modal/text.py` — Reuse `deep_code_research/research/document_parser.py` and wrap in Evidence.
  3. `modal/image.py` — Figure/table extraction (Docling integration).
  4. `modal/formula.py` — LaTeX/SymPy parsing + embeddings.
  5. `modal/code.py` — AST parsing + sandbox execution.
  6. `modal/audio.py` — Whisper transcription (optional, defer).
  7. `modal/three_d.py` — PDB/molecular parsing (optional, defer).
- Code reuse:
  - Copy `DocumentParser._parse_file()` logic to `text.py`.
  - Reuse lazy LLM init pattern throughout.
  - Adapt content-addressable ID pattern: `{filename}@{hash}@{ref}`.
- Testing: 85% coverage (skip VQA/complex models in unit tests).

### Phase 3: Knowledge Layer — Week 2–3
- Files: 7 | LOC: ~2,200 | Priority: CRITICAL
- Build order:
  1. `knowledge/base.py` — KB interface.
  2. `knowledge/local_kb.py` — Basic CRUD with embeddings.
  3. `knowledge/multimodal_kg.py` — Cross-modal graph with SQLite (critical).
  4. `knowledge/public_kb.py` — PubMed/ArXiv API integration.
  5. `knowledge/domain_plugins/base_plugin.py` — Plugin ABC.
  6. `knowledge/domain_plugins/bio_plugin.py` — Example plugin.
  7. `knowledge/domain_plugins/chem_plugin.py` — Example plugin.
- MultimodalKG schema:
  - Evidence: `id, content, evidence_type, citation, modal_metadata, embedding`.
  - Edges: `source_id, target_id, edge_type, confidence, metadata`.
  - Edge types: DESCRIBES, IMPLIES, CONTRADICTS, SUPPORTS, DERIVES_FROM, etc.
- Key features:
  - Content-addressable evidence IDs.
  - Cross-modal relationship edges (text ↔ image ↔ formula).
  - Conflict detection via CONTRADICTS edges + semantic similarity.
  - Hybrid search (vector + metadata filters).
- Testing: 90% coverage (full CRUD + relationships).

### Phase 4: Reasoning Engines — Week 3
- Files: 5 | LOC: ~1,500 | Priority: HIGH
- Build order:
  1. `reasoning/registry.py` — Reasoner registration.
  2. `reasoning/chain_of_research.py` — Adapt `adaptive_rag.py` RequirementGraphBuilder pattern.
  3. `reasoning/uncertainty.py` — Ensemble/MC Dropout implementation.
  4. `reasoning/conflict_resolver.py` — Multi-source reconciliation with NLI (critical).
  5. `reasoning/causal_inference.py` — Causal reasoning (advanced, defer).
- ConflictResolver strategies:
  - `credibility_weighted` — Journal impact, h-index, citation count.
  - `recency` — Prefer recent evidence.
  - `consensus` — Majority voting.
  - `domain_expert` — Plugin-based reconciliation.
- Testing: 75% coverage (mock LLM calls for reasoning).

### Phase 5: Agent Layer — Week 3–4
- Files: 4 | LOC: ~1,400 | Priority: HIGH
- Build order:
  1. `agents/planner.py` — Task decomposition (reuse `adaptive_rag.py` patterns).
  2. `agents/executor.py` — Step execution with dispatching.
  3. `agents/reviewer.py` — Self-critique agent.
  4. `agents/coordinator.py` — Stage-based orchestration (adapt `pipeline.py`).
- Execution flow:
  - Planner: Query → Task → Subtasks (topologically sorted).
  - Executor: Subtask → Steps → Dispatch to Modal/Knowledge/Reasoning.
  - Reviewer: Results → Critique → Refinement suggestions.
  - Coordinator: Orchestrate all agents + handle retries/refinement.
- Testing: 70% coverage (integration tests).

### Phase 6: I/O & Integration — Week 4
- Files: 3 | LOC: ~700 | Priority: MEDIUM
- Build order:
  1. `io/input_parser.py` — Multi-format input (file/URL/text/audio).
  2. `io/output_formatter.py` — Templates for MD/HTML/LaTeX/JSON.
  3. `run.py` — CLI with argparse (similar to `deep_code_research/run.py`).
- Output sections:
  - Executive summary.
  - Evidence chains with citations.
  - Conflict analysis.
  - Uncertainty quantification.
  - Methodology used.
- Testing: 90% coverage.

### Phase 7: Testing & Documentation — Week 4
- Files: 6 | LOC: ~600
- Build order:
  1. `tests/conftest.py` — Fixtures (sample docs, mock KG, mock LLM).
  2. Unit tests for each layer.
  3. Integration tests for full pipeline.
  4. `README.md` with examples.
  5. `config.yaml` with comments.
- Test strategy:
  - Non-LLM tests always run (parsing, CRUD, data models).
  - LLM tests skip if no API key (`@pytest.mark.skipif`).
  - Use fixtures from `deep_code_research/tests/` as templates.

## MVP Phasing (if full scope is too large)
### MVP1: Core Research Pipeline (2,500 LOC, 15 files)
- Components: Phase 1; text parser only; local KB only; Chain-of-Research reasoner only; basic planner + executor; CLI + markdown output.
- Capabilities: ingest PDF/MD documents; build knowledge graph; execute text-based research queries; generate markdown reports.
- Skips: image/formula/code parsers; public KB; conflict resolution; domain plugins.

### MVP2: Multimodal Support (+1,500 LOC)
- Add: image parser (basic, no VQA); formula parser; cross-modal KG edges; HTML/LaTeX output.

### MVP3: Advanced Reasoning (+1,800 LOC)
- Add: conflict resolver; uncertainty estimation; public KB (PubMed/ArXiv); domain plugins; multi-agent coordination.

## Code Reuse Matrix
| Source                                      | Target                              | What to Reuse                                   |
|---------------------------------------------|-------------------------------------|-------------------------------------------------|
| `deep_code_research/research/document_parser.py` | `modal/text.py`                     | Document parsing logic (~250 LOC)               |
| `deep_code_research/research/adaptive_rag.py`    | `reasoning/chain_of_research.py`    | RequirementGraphBuilder pattern (~300 LOC)      |
| `deep_code_research/research/rag_engine.py`      | `knowledge/local_kb.py`             | Embedding setup, GPU detection (~80 LOC)        |
| `deep_code_research/orchestrator/pipeline.py`    | `agents/coordinator.py`             | Stage-based execution, retry logic (~300 LOC)   |
| `deep_code_research/contracts.py`                | `core/*.py`                         | Dataclass pattern (~30 LOC)                     |
| `deep_code_research/tests/`                      | `tests/`                            | Fixture patterns, async structure (~250 LOC)    |

### Patterns from `ms-agent`
- Hash-based deduplication (`ms_agent/memory/`).
- Content-addressable IDs (`ms_agent/rag/`).
- Multimodal resource placeholders (`ms_agent/rag/extraction.py`).
- Lazy LLM initialization (throughout `deep_code_research`).

## Critical Implementation Details
1) Evidence model (`core/evidence.py`):
```
@dataclass
class Evidence:
    id: str  # Content-addressable: {doc}@{hash}@{ref}
    content: str
    evidence_type: EvidenceType  # TEXT, IMAGE, TABLE, FORMULA, CODE
    citation: Citation
    uncertainty: Optional[Uncertainty] = None
    modal_metadata: Dict[str, Any] = field(default_factory=dict)
    supports: List[str] = field(default_factory=list)
    contradicts: List[str] = field(default_factory=list)
```
2) MultimodalKG schema (`knowledge/multimodal_kg.py`):
```
CREATE TABLE evidence (
    id TEXT PRIMARY KEY,
    content TEXT,
    evidence_type TEXT,
    citation JSON,
    modal_metadata JSON,
    embedding BLOB
);

CREATE TABLE edges (
    source_id TEXT,
    target_id TEXT,
    edge_type TEXT,  -- DESCRIBES, IMPLIES, CONTRADICTS, SUPPORTS
    confidence REAL,
    metadata JSON
);
```
3) Parser registry (`modal/registry.py`):
```
class ModalParserRegistry:
    _parsers: Dict[str, Type[ModalParser]] = {}

    @classmethod
    def register(cls, parser_class):
        cls._parsers[parser_class.__name__] = parser_class

    @classmethod
    async def get_parser_for_file(cls, file_path) -> Optional[ModalParser]:
        for parser_class in cls._parsers.values():
            parser = parser_class()
            if await parser.validate(file_path):
                return parser
```
4) Conflict resolution (`reasoning/conflict_resolver.py`):
```
async def _assess_credibility(evidence: Evidence) -> float:
    score = 0.5  # Base
    # + 0.3 for top-tier journal (Nature, Science, Cell)
    # + 0.1 for recency (>= 2020)
    # + min(0.2, citations/1000)
    return min(1.0, score)
```

## Configuration (`config.yaml`)
```yaml
llm:
  service: openai
  model: gemini-flash-lite-latest
  api_key: ${OPENAI_API_KEY}
  base_url: ${OPENAI_BASE_URL}

parsers:
  enabled: [text, image, formula, code]
  text:
    use_docling: true
    gpu_acceleration: true
  image:
    enable_vqa: false  # Disable for MVP
  code:
    enable_execution: false  # Safety

knowledge:
  local_kb:
    db_path: ./knowledge/local.db
    embedding_device: cuda
  public_kb:
    enabled_sources: [pubmed, arxiv, semantic_scholar]
  domain_plugins:
    enabled: [biology, chemistry]

reasoning:
  default_strategy: chain_of_research
  uncertainty:
    method: ensemble
    num_samples: 5
  conflict_resolution:
    strategy: credibility_weighted

agents:
  max_iterations: 10
  enable_self_review: true

output:
  default_format: markdown
  include_citations: true
  include_uncertainty: true
```

## Dependencies
- Core: `pydantic>=2.0`, `omegaconf>=2.3`.
- Document processing (reuse from `deep_code_research`): `llama-index-core>=0.10`, `pypdf>=3.0`, `python-docx>=1.0`.
- Embeddings & ML: `sentence-transformers>=2.2`, `torch>=2.0`, `numpy>=1.24`.
- Knowledge graph: sqlite3 (built-in).
- Optional: Image — `Pillow>=10.0`.
- Optional: Formula — `sympy>=1.12`.
- Public KB: `requests>=2.31`, `aiohttp>=3.9`.
- Testing: `pytest>=7.4`, `pytest-asyncio>=0.21`.

## Integration Flow
```
User Query
    ↓
[input_parser] → Parse query
    ↓
[planner] → Create Task → Decompose to Subtasks
    ↓
[executor] → Execute Steps:
    ├─ [modal/*] → Parse inputs → Extract Evidence
    ├─ [knowledge/*] → Store/Retrieve Evidence
    └─ [reasoning/*] → Build EvidenceChains
    ↓
[reviewer] → Self-critique
    ↓
[coordinator] → Orchestrate refinement loop
    ↓
[output_formatter] → Generate report
    ↓
Final Report (MD/HTML/LaTeX/JSON)
```

## Risk Mitigation
| Risk                  | Mitigation                             |
|-----------------------|----------------------------------------|
| LLM API failures      | Lazy init, graceful fallbacks, caching |
| GPU unavailable       | CPU fallback for embeddings            |
| Large doc OOM         | Chunking, streaming                    |
| Code sandbox security | Disable by default, Docker required    |
| Scope creep           | Strict MVP phases                      |

## Testing Strategy
1. Unit tests: Every module has non-LLM tests (100% of data models, 85%+ of logic).
2. Integration tests: Full pipeline with mock LLM.
3. Fixtures: Reuse patterns from `deep_code_research/tests/`.
4. Skip LLM tests: Use `@pytest.mark.skipif(not check_api_available())`.

## Critical Files (implementation priority)
1. `projects/deepresearch/core/base.py` — ABCs (foundation).
2. `projects/deepresearch/core/evidence.py` — Core data model.
3. `projects/deepresearch/modal/registry.py` — Plugin architecture.
4. `projects/deepresearch/knowledge/multimodal_kg.py` — Central knowledge storage.
5. `projects/deepresearch/agents/coordinator.py` — End-to-end orchestration.

## Success Criteria
### MVP1 complete
- ✅ Ingest PDF/MD documents.
- ✅ Build knowledge graph from text evidence.
- ✅ Execute research queries with Chain-of-Research.
- ✅ Generate markdown reports with citations.
- ✅ 25+ passing tests.

### Full implementation complete
- ✅ All 7 phases implemented (~8,150 LOC).
- ✅ Multimodal support (text, image, formula, code).
- ✅ Cross-modal knowledge graph with relationship types.
- ✅ Advanced reasoning (conflict resolution, uncertainty quantification).
- ✅ Public KB integration (PubMed, ArXiv).
- ✅ Domain plugins (biology, chemistry).
- ✅ Multi-agent coordination.
- ✅ 40+ passing tests (unit + integration).
- ✅ Documentation + examples.

## Next Steps
1. Create directory structure.
2. Implement Phase 1 (core abstractions).
3. Write initial tests.
4. Iterate through Phases 2–7.
5. Continuous testing and refinement.
