"""
RAGEngine - Build and query RAG index from documents (basic implementation)
"""
from typing import List, Any, Optional
from pathlib import Path
import os


class RAGEngine:
    """Build and query RAG index from documents (basic implementation)"""

    def __init__(self, persist_dir: str = "./rag_index"):
        self.persist_dir = persist_dir
        self.index = None
        self.query_engine = None

    async def build_index(self, documents: List[Any]) -> Any:
        """
        Build vector index from documents.

        Uses:
        - LlamaIndex VectorStoreIndex
        - HuggingFace embeddings (runs on GPU if available)

        Returns:
            The RAGEngine itself (for retrieval operations)
        """
        from llama_index.core import VectorStoreIndex, Settings
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding

        # Check for GPU availability
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"RAGEngine: Using device '{device}' for embeddings")

        # Configure embedding model
        embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            device=device
        )
        Settings.embed_model = embed_model

        # Set LLM to None to avoid LLM resolution issues
        Settings.llm = None

        # Build index
        self.index = VectorStoreIndex.from_documents(documents)

        # Return self for retrieval operations (no query_engine needed)
        return self

    async def query(self, question: str, top_k: int = 5) -> str:
        """
        Query the RAG index (retrieval-only mode, no LLM synthesis).

        Returns:
            Retrieved context as string
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")

        # Use retrieval-only mode to avoid LLM dependency
        nodes = await self.retrieve(question, top_k)

        # Combine retrieved text
        texts = []
        for node in nodes:
            if hasattr(node, 'text'):
                texts.append(node.text)
            elif hasattr(node, 'node') and hasattr(node.node, 'text'):
                texts.append(node.node.text)

        return "\n\n---\n\n".join(texts) if texts else ""

    async def retrieve(self, question: str, top_k: int = 5) -> List[Any]:
        """
        Retrieve relevant nodes without generating response.

        Returns:
            List of retrieved nodes
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")

        retriever = self.index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(question)
        return nodes
