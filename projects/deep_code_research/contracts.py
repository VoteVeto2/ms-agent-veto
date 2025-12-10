"""
Shared contracts/interfaces for DeepCodeResearch system.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ResearchContext:
    """Output of Research Layer - passed to CodeGen Layer"""
    api_specs: List[Dict] = field(default_factory=list)
    code_patterns: List[Dict] = field(default_factory=list)
    architecture: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    documents: List[Any] = field(default_factory=list)  # LlamaIndex Documents
    rag_index: Any = None  # LlamaIndex query engine
    adaptive_rag: Any = None  # AdaptiveRAGEngine instance


@dataclass
class FileSpec:
    """Specification for a single file to generate"""
    path: str
    description: str
    depends_on: List[str] = field(default_factory=list)


@dataclass
class CodePlan:
    """Plan for the entire code repository"""
    files: List[FileSpec] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
