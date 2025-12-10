# Agent 1: Research Layer

## Role

You are responsible for building the **Research Layer** of the DeepCodeResearch system. Your code takes `references.zip` as input and outputs a `ResearchContext` object containing parsed documents, RAG index, and extracted structured information.

**Key Innovation (2025)**: This layer now implements **Adaptive RAG** based on CodeRAG + SELF-RAG patterns for smarter retrieval that reduces noise and improves code generation quality.

---

## API Configuration

Use this for all LLM calls:

```python
import os
os.environ["OPENAI_API_KEY"] = 
os.environ["OPENAI_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
os.environ["OPENAI_MODEL"] = "gemini-flash-lite-latest"
```

---

## Literature Context (December 2025)

Based on latest research in RAG for code generation:

| Approach | Innovation | Impact | Source |
|----------|------------|--------|--------|
| **CodeRAG** | Bigraph requirement-to-code mapping | +40% Pass@1 | [Paper](https://arxiv.org/html/2504.10046v1) |
| **AllianceCoder** | CoT decomposition + API semantic matching | +20% Pass@1 | [Paper](https://arxiv.org/abs/2503.20589) |
| **SELF-RAG** | Dynamic retrieval with reflection tokens | Retrieves only when needed | [Guide](https://www.promptingguide.ai/research/rag) |

**Key Insight**: Retrieved similar code often introduces **noise (-15%)**. In-context code + API docs are more valuable than similar code snippets.

---

## Directory Structure

Create these files:

```
projects/deep_code_research/
├── research/
│   ├── __init__.py
│   ├── document_parser.py    # Parse PDF/MD/PY/YAML/DOCX/PPTX
│   ├── rag_engine.py         # Build & query RAG index (basic)
│   ├── adaptive_rag.py       # NEW: Adaptive RAG (CodeRAG + SELF-RAG)
│   └── info_extractor.py     # Extract API specs, code patterns, deps
└── tests/
    └── test_research.py      # CREATE THIS FIRST
```

---

## Shared Interface (from contracts.py)

You MUST output this dataclass. Agent 3 will create `contracts.py`, import from there:

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ResearchContext:
    """Output of Research Layer - passed to CodeGen Layer"""
    api_specs: List[Dict] = field(default_factory=list)
    code_patterns: List[Dict] = field(default_factory=list)
    architecture: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    documents: List[Any] = field(default_factory=list)  # LlamaIndex Documents
    rag_index: Any = None  # LlamaIndex query engine
```

---

## Task 1: DocumentParser

**File**: `research/document_parser.py`

```python
import zipfile
from pathlib import Path
from typing import List, Any

class DocumentParser:
    """Parse multiple document formats from references.zip"""

    def __init__(self, extract_dir: str = "./extracted_references"):
        self.extract_dir = Path(extract_dir)

    async def parse_zip(self, zip_path: str) -> List[Any]:
        """
        Extract zip and parse all documents.

        Supported formats:
        - .pdf (use LlamaParse or PyPDF2)
        - .md, .txt, .py, .yaml, .yml, .json (text files)
        - .docx, .pptx (use unstructured or python-docx)

        Returns:
            List of LlamaIndex Document objects
        """
        # TODO: Implement
        pass

    async def _parse_file(self, file_path: Path) -> List[Any]:
        """Parse single file based on extension"""
        # TODO: Implement per-format parsing
        pass
```

**Requirements**:
- Handle zip extraction
- Support at least: `.pdf`, `.md`, `.txt`, `.py`, `.yaml`, `.json`
- Return LlamaIndex `Document` objects with metadata (source path)
- Handle encoding errors gracefully

---

## Task 2: RAGEngine (Basic)

**File**: `research/rag_engine.py`

```python
from typing import List, Any, Optional

class RAGEngine:
    """Build and query RAG index from documents (basic implementation)"""

    def __init__(self, persist_dir: str = "./rag_index"):
        self.persist_dir = persist_dir
        self.index = None
        self.query_engine = None

    async def build_index(self, documents: List[Any]) -> Any:
        """
        Build vector index from documents.

        Use:
        - LlamaIndex VectorStoreIndex
        - HuggingFace embeddings (runs on GPU if available)
        - Hybrid search (vector + BM25) if possible

        Returns:
            Query engine for retrieval
        """
        # TODO: Implement
        pass

    async def query(self, question: str, top_k: int = 5) -> str:
        """
        Query the RAG index.

        Returns:
            Retrieved context as string
        """
        # TODO: Implement
        pass
```

**Requirements**:
- Use LlamaIndex for indexing
- Support GPU acceleration for embeddings
- Return a query engine that Agent 2 can use

---

## Task 2B: AdaptiveRAG (NEW - CodeRAG + SELF-RAG Pattern)

**File**: `research/adaptive_rag.py`

**Priority**: 🟡 P3 - Medium Impact (from Agent 4's improvement roadmap)

```python
"""
Adaptive RAG - CodeRAG + SELF-RAG Pattern

Key improvements over basic RAG:
1. Requirement graph (not just vector similarity)
2. Dynamic retrieval (only when needed)
3. Filters out noisy similar code
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from openai import OpenAI
import os


@dataclass
class Requirement:
    """A parsed requirement from task description"""
    id: str
    description: str
    type: str  # "functional", "api", "data", "error_handling"
    dependencies: List[str]


@dataclass
class CodeMapping:
    """Mapping from requirement to code pattern"""
    requirement_id: str
    code_pattern: str
    confidence: float
    source: str  # Document source


class RequirementGraphBuilder:
    """
    Build requirement graph from task description.

    CodeRAG insight: Map requirements to code, not just similar text.
    """

    def __init__(self):
        self.client = OpenAI()

    async def build_graph(self, task_description: str) -> List[Requirement]:
        """Parse task into structured requirements"""
        prompt = f"""Parse this task into structured requirements.

Task: {task_description}

Output JSON array:
[
    {{
        "id": "req_1",
        "description": "Handle user authentication",
        "type": "functional",
        "dependencies": []
    }},
    {{
        "id": "req_2",
        "description": "Return JSON response",
        "type": "api",
        "dependencies": ["req_1"]
    }}
]

Types: functional, api, data, error_handling, performance
"""
        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        reqs = self._parse_json(response.choices[0].message.content)
        return [Requirement(**r) for r in reqs]

    def _parse_json(self, text: str) -> List[Dict]:
        import json
        import re
        match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        try:
            return json.loads(text)
        except:
            return []


class AdaptiveRetriever:
    """
    SELF-RAG style adaptive retrieval.

    Key insight: Don't always retrieve. Check if retrieval is needed.
    """

    def __init__(self, rag_index):
        self.client = OpenAI()
        self.rag_index = rag_index

    async def should_retrieve(self, query: str, context: str) -> bool:
        """
        Determine if retrieval is needed (SELF-RAG reflection).

        Returns True if:
        - Query requires external knowledge
        - Current context is insufficient
        """
        prompt = f"""Determine if external retrieval is needed.

Query: {query}

Current Context:
{context[:1000]}

Answer with JSON:
{{"needs_retrieval": true/false, "reason": "..."}}

Retrieve if:
- Specific API details needed
- Implementation patterns unclear
- Domain knowledge required

Don't retrieve if:
- Context already sufficient
- Query is about general programming
- Similar code would just add noise
"""
        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        result = self._parse_json(response.choices[0].message.content)
        return result.get("needs_retrieval", True)

    async def retrieve_for_requirement(
        self,
        requirement: Requirement,
        filter_noise: bool = True
    ) -> List[CodeMapping]:
        """
        Retrieve code patterns for a specific requirement.

        AllianceCoder insight: API docs > similar code.
        """
        # Query for API/docs first (more valuable)
        api_query = f"API documentation for: {requirement.description}"
        api_results = self.rag_index.query(api_query) if self.rag_index else []

        # Query for patterns (filter carefully)
        pattern_query = f"Implementation pattern for: {requirement.description}"
        pattern_results = self.rag_index.query(pattern_query) if self.rag_index else []

        # Combine and filter
        mappings = []

        for r in api_results[:3]:  # API docs are valuable
            mappings.append(CodeMapping(
                requirement_id=requirement.id,
                code_pattern=str(r),
                confidence=0.9,
                source="api_doc"
            ))

        if not filter_noise:
            for r in pattern_results[:2]:  # Similar code may be noisy
                mappings.append(CodeMapping(
                    requirement_id=requirement.id,
                    code_pattern=str(r),
                    confidence=0.6,
                    source="similar_code"
                ))

        return mappings

    def _parse_json(self, text: str) -> Dict:
        import json
        import re
        match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        try:
            return json.loads(text)
        except:
            return {}


class AdaptiveRAGEngine:
    """
    Combined adaptive RAG engine.

    Usage:
        engine = AdaptiveRAGEngine(rag_index)
        context = await engine.get_context_for_task(task_description)
    """

    def __init__(self, rag_index):
        self.graph_builder = RequirementGraphBuilder()
        self.retriever = AdaptiveRetriever(rag_index)

    async def get_context_for_task(
        self,
        task_description: str,
        existing_context: str = ""
    ) -> Dict[str, List[CodeMapping]]:
        """
        Get relevant context for entire task.

        Returns: {requirement_id: [CodeMapping, ...]}
        """
        # Build requirement graph
        requirements = await self.graph_builder.build_graph(task_description)

        # Retrieve for each requirement (if needed)
        context_map = {}

        for req in requirements:
            # Check if retrieval needed
            should_retrieve = await self.retriever.should_retrieve(
                req.description,
                existing_context
            )

            if should_retrieve:
                mappings = await self.retriever.retrieve_for_requirement(req)
                context_map[req.id] = mappings
            else:
                context_map[req.id] = []  # Use existing context

        return context_map
```

**Integration Point**: Use `AdaptiveRAGEngine` alongside basic `RAGEngine` for improved retrieval quality.

---

## Task 3: InfoExtractor

**File**: `research/info_extractor.py`

```python
from typing import List, Dict, Any
from openai import OpenAI

class InfoExtractor:
    """Extract structured information from documents using LLM"""

    def __init__(self):
        self.client = OpenAI()  # Uses env vars

    async def extract_api_specs(self, documents: List[Any]) -> List[Dict]:
        """
        Extract API specifications from documents.

        Returns:
            List of dicts with: endpoint, method, params, response
        """
        # TODO: Use LLM to extract
        pass

    async def extract_code_patterns(self, documents: List[Any]) -> List[Dict]:
        """
        Extract code patterns and best practices.

        Returns:
            List of dicts with: pattern_name, description, example
        """
        # TODO: Use LLM to extract
        pass

    async def extract_architecture(self, documents: List[Any]) -> Dict:
        """
        Extract system architecture information.

        Returns:
            Dict with: modules, components, data_flow
        """
        # TODO: Use LLM to extract
        pass

    async def extract_dependencies(self, documents: List[Any]) -> List[str]:
        """
        Extract dependency list from documents.

        Looks for:
        - import statements in .py files
        - requirements.txt format
        - package.json dependencies

        Returns:
            List of package names
        """
        # TODO: Implement (regex + LLM)
        pass
```

**Requirements**:
- Use OpenAI client with Gemini API
- Return structured JSON from LLM
- Handle LLM response parsing errors

---

## Main Interface

**File**: `research/__init__.py`

```python
from .document_parser import DocumentParser
from .rag_engine import RAGEngine
from .adaptive_rag import AdaptiveRAGEngine, Requirement, CodeMapping
from .info_extractor import InfoExtractor

# Import from contracts when available
# from ..contracts import ResearchContext

async def research_references(zip_path: str, use_adaptive_rag: bool = True) -> "ResearchContext":
    """
    Main entry point for Research Layer.

    Args:
        zip_path: Path to references.zip
        use_adaptive_rag: Whether to use adaptive RAG (default: True)

    Returns:
        ResearchContext with all extracted information
    """
    # 1. Parse documents
    parser = DocumentParser()
    documents = await parser.parse_zip(zip_path)

    # 2. Build RAG index
    rag = RAGEngine()
    query_engine = await rag.build_index(documents)

    # 3. Optional: Build adaptive RAG engine
    adaptive_engine = None
    if use_adaptive_rag:
        adaptive_engine = AdaptiveRAGEngine(query_engine)

    # 4. Extract structured info
    extractor = InfoExtractor()
    api_specs = await extractor.extract_api_specs(documents)
    code_patterns = await extractor.extract_code_patterns(documents)
    architecture = await extractor.extract_architecture(documents)
    dependencies = await extractor.extract_dependencies(documents)

    # 5. Return ResearchContext
    from ..contracts import ResearchContext
    return ResearchContext(
        api_specs=api_specs,
        code_patterns=code_patterns,
        architecture=architecture,
        dependencies=dependencies,
        documents=documents,
        rag_index=query_engine,
        adaptive_rag=adaptive_engine  # NEW: Include adaptive RAG engine
    )
```

---

## Test First!

**File**: `tests/test_research.py`

```python
import pytest
import asyncio
from pathlib import Path

# Create test before implementing!

@pytest.fixture
def sample_zip(tmp_path):
    """Create a sample references.zip for testing"""
    import zipfile

    # Create sample files
    (tmp_path / "api_doc.md").write_text("""
    # API Documentation

    ## GET /users
    Returns list of users.

    ## POST /users
    Create a new user.
    Request body: {"name": "string", "email": "string"}
    """)

    (tmp_path / "example.py").write_text("""
    import requests
    from typing import List

    class UserClient:
        def get_users(self) -> List[dict]:
            return requests.get('/users').json()
    """)

    # Create zip
    zip_path = tmp_path / "references.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.write(tmp_path / "api_doc.md", "api_doc.md")
        zf.write(tmp_path / "example.py", "example.py")

    return zip_path


@pytest.mark.asyncio
async def test_document_parser(sample_zip):
    from research.document_parser import DocumentParser

    parser = DocumentParser()
    documents = await parser.parse_zip(str(sample_zip))

    assert len(documents) >= 2
    assert any("API" in doc.text for doc in documents)


@pytest.mark.asyncio
async def test_rag_engine(sample_zip):
    from research.document_parser import DocumentParser
    from research.rag_engine import RAGEngine

    parser = DocumentParser()
    documents = await parser.parse_zip(str(sample_zip))

    rag = RAGEngine()
    query_engine = await rag.build_index(documents)

    result = await rag.query("How do I get users?")
    assert "users" in result.lower()


@pytest.mark.asyncio
async def test_adaptive_rag():
    """Test adaptive RAG components"""
    from research.adaptive_rag import (
        RequirementGraphBuilder,
        AdaptiveRetriever,
        AdaptiveRAGEngine
    )

    # Test requirement graph builder
    builder = RequirementGraphBuilder()
    requirements = await builder.build_graph("Build a REST API client for user management")

    assert len(requirements) > 0
    assert all(hasattr(r, 'id') and hasattr(r, 'description') for r in requirements)


@pytest.mark.asyncio
async def test_adaptive_retriever_should_retrieve():
    """Test SELF-RAG style retrieval decision"""
    from research.adaptive_rag import AdaptiveRetriever

    retriever = AdaptiveRetriever(None)  # No index needed for this test

    # Should need retrieval for specific API questions
    needs = await retriever.should_retrieve(
        "How to authenticate with OAuth2?",
        ""  # No existing context
    )
    assert needs == True

    # May not need retrieval if context is sufficient
    needs = await retriever.should_retrieve(
        "How to print hello world?",
        "Basic Python tutorial with print examples..."
    )
    # Result depends on LLM judgment


@pytest.mark.asyncio
async def test_info_extractor():
    from research.info_extractor import InfoExtractor

    extractor = InfoExtractor()

    # Mock document
    class MockDoc:
        text = "import requests\nimport pandas as pd"

    deps = await extractor.extract_dependencies([MockDoc()])
    assert "requests" in deps or "pandas" in deps


@pytest.mark.asyncio
async def test_research_references(sample_zip):
    from research import research_references

    context = await research_references(str(sample_zip))

    assert context.documents is not None
    assert len(context.documents) > 0
    assert context.rag_index is not None
    assert context.adaptive_rag is not None  # NEW: Check adaptive RAG
```

**Run tests**:
```bash
cd projects/deep_code_research
pytest tests/test_research.py -v
```

---

## Dependencies

Add to your environment:

```bash
pip install llama-index llama-index-embeddings-huggingface
pip install pypdf2 python-docx unstructured
pip install openai
```

---

## Checklist

- [ ] Read `contracts.py` from Agent 3
- [ ] Create `tests/test_research.py` FIRST
- [ ] Implement `DocumentParser`
- [ ] Implement `RAGEngine` (basic)
- [ ] **NEW**: Implement `AdaptiveRAGEngine` (CodeRAG + SELF-RAG pattern)
- [ ] Implement `InfoExtractor`
- [ ] Implement `research_references()` main function
- [ ] All tests pass
- [ ] Ready for integration with Agent 3

---

## Testing Checklist (from Agent 4's Improvement Roadmap)

```
□ Task 2B: Adaptive RAG
  □ test_build_requirement_graph()
  □ test_should_retrieve()
  □ test_retrieve_for_requirement()
```

---

## Integration Point

Agent 3 will call your code like this:

```python
from research import research_references

context = await research_references("./references.zip")
# context is ResearchContext object
# context.adaptive_rag is AdaptiveRAGEngine for smarter retrieval
```

Make sure this interface works!
