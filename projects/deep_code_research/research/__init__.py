"""
Research module for DeepCodeResearch system.

Main entry point: research_references()
"""
from .document_parser import DocumentParser
from .rag_engine import RAGEngine
from .adaptive_rag import (
    AdaptiveRAGEngine,
    AdaptiveRetriever,
    RequirementGraphBuilder,
    Requirement,
    CodeMapping
)
from .info_extractor import InfoExtractor

import sys
from pathlib import Path

# Add parent directory to path for contracts import
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from contracts import ResearchContext


DEBUG_LOG_PATH = Path(__file__).resolve().parents[3] / ".cursor" / "debug.log"


async def research_references(zip_path: str, use_adaptive_rag: bool = True) -> ResearchContext:
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

    # region agent log
    try:
        import json, time
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
            _f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "pre-fix",
                "hypothesisId": "H1",
                "location": "research.research_references",
                "message": "documents_parsed",
                "data": {
                    "zip_path": str(zip_path),
                    "doc_count": len(documents)
                },
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except Exception:
        pass
    # endregion

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
    return ResearchContext(
        api_specs=api_specs,
        code_patterns=code_patterns,
        architecture=architecture,
        dependencies=dependencies,
        documents=documents,
        rag_index=query_engine,
        adaptive_rag=adaptive_engine
    )


__all__ = [
    'DocumentParser',
    'RAGEngine',
    'AdaptiveRAGEngine',
    'AdaptiveRetriever',
    'RequirementGraphBuilder',
    'Requirement',
    'CodeMapping',
    'InfoExtractor',
    'ResearchContext',
    'research_references',
]
