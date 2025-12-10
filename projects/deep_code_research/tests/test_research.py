import pytest
import asyncio
from pathlib import Path
import os


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

    (tmp_path / "config.yaml").write_text("""
    database:
      host: localhost
      port: 5432
    api:
      version: v1
    """)

    # Create zip
    zip_path = tmp_path / "references.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.write(tmp_path / "api_doc.md", "api_doc.md")
        zf.write(tmp_path / "example.py", "example.py")
        zf.write(tmp_path / "config.yaml", "config.yaml")

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
    """Test RAG engine with retrieval-only mode (no LLM)"""
    from research.document_parser import DocumentParser
    from research.rag_engine import RAGEngine

    parser = DocumentParser()
    documents = await parser.parse_zip(str(sample_zip))

    rag = RAGEngine()
    query_engine = await rag.build_index(documents)

    # Test retrieval-only query (no LLM needed)
    result = await rag.query("How do I get users?")
    assert "user" in result.lower()


@pytest.mark.asyncio
async def test_rag_retrieve(sample_zip):
    """Test RAG retrieve method"""
    from research.document_parser import DocumentParser
    from research.rag_engine import RAGEngine

    parser = DocumentParser()
    documents = await parser.parse_zip(str(sample_zip))

    rag = RAGEngine()
    await rag.build_index(documents)

    # Test retrieve
    nodes = await rag.retrieve("API documentation")
    assert len(nodes) > 0


def _check_api_available():
    """Check if API is available for LLM-dependent tests"""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    # Skip if no key or if key is known to be invalid
    if not api_key or api_key.startswith("AIza"):
        return False
    return True


@pytest.mark.asyncio
@pytest.mark.skipif(not _check_api_available(), reason="API key not available")
async def test_adaptive_rag():
    """Test adaptive RAG components (requires LLM)"""
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
@pytest.mark.skipif(not _check_api_available(), reason="API key not available")
async def test_adaptive_retriever_should_retrieve():
    """Test SELF-RAG style retrieval decision (requires LLM)"""
    from research.adaptive_rag import AdaptiveRetriever

    retriever = AdaptiveRetriever(None)  # No index needed for this test

    # Should need retrieval for specific API questions
    needs = await retriever.should_retrieve(
        "How to authenticate with OAuth2?",
        ""  # No existing context
    )
    assert needs == True


@pytest.mark.asyncio
async def test_adaptive_rag_classes_exist():
    """Test that adaptive RAG classes can be instantiated"""
    from research.adaptive_rag import (
        RequirementGraphBuilder,
        AdaptiveRetriever,
        AdaptiveRAGEngine,
        Requirement,
        CodeMapping
    )

    # Test dataclasses
    req = Requirement(
        id="req_1",
        description="Test requirement",
        type="functional",
        dependencies=[]
    )
    assert req.id == "req_1"

    mapping = CodeMapping(
        requirement_id="req_1",
        code_pattern="def test(): pass",
        confidence=0.9,
        source="test"
    )
    assert mapping.confidence == 0.9

    # Test class instantiation
    builder = RequirementGraphBuilder()
    assert builder is not None

    retriever = AdaptiveRetriever(None)
    assert retriever is not None

    engine = AdaptiveRAGEngine(None)
    assert engine is not None


@pytest.mark.asyncio
async def test_info_extractor():
    """Test info extractor dependency extraction (no LLM needed)"""
    from research.info_extractor import InfoExtractor

    extractor = InfoExtractor()

    # Mock document
    class MockDoc:
        text = "import requests\nimport pandas as pd"

    deps = await extractor.extract_dependencies([MockDoc()])
    assert "requests" in deps or "pandas" in deps


@pytest.mark.asyncio
async def test_info_extractor_python_imports():
    """Test Python import extraction"""
    from research.info_extractor import InfoExtractor

    extractor = InfoExtractor()

    class MockDoc:
        text = """
import numpy as np
from sklearn import metrics
import tensorflow as tf
from pytorch import nn
"""

    deps = await extractor.extract_dependencies([MockDoc()])
    assert "numpy" in deps
    assert "sklearn" in deps
    assert "tensorflow" in deps
    assert "pytorch" in deps


@pytest.mark.asyncio
async def test_research_references_no_llm(sample_zip):
    """Test research_references with adaptive RAG disabled (no LLM)"""
    from research import research_references

    context = await research_references(str(sample_zip), use_adaptive_rag=False)

    assert context.documents is not None
    assert len(context.documents) > 0
    assert context.rag_index is not None
    assert context.adaptive_rag is None  # Should be None when disabled


@pytest.mark.asyncio
async def test_research_references_with_adaptive(sample_zip):
    """Test research_references with adaptive RAG enabled"""
    from research import research_references

    context = await research_references(str(sample_zip), use_adaptive_rag=True)

    assert context.documents is not None
    assert len(context.documents) > 0
    assert context.rag_index is not None
    assert context.adaptive_rag is not None  # Check adaptive RAG is created


@pytest.mark.asyncio
async def test_contracts():
    """Test ResearchContext dataclass"""
    from contracts import ResearchContext

    ctx = ResearchContext(
        api_specs=[{"endpoint": "/test"}],
        code_patterns=[{"name": "pattern1"}],
        architecture={"modules": ["mod1"]},
        dependencies=["requests"],
        documents=[],
        rag_index=None,
        adaptive_rag=None
    )

    assert len(ctx.api_specs) == 1
    assert ctx.dependencies == ["requests"]
