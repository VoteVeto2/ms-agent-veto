"""
Adaptive RAG - CodeRAG + SELF-RAG Pattern

Key improvements over basic RAG:
1. Requirement graph (not just vector similarity)
2. Dynamic retrieval (only when needed)
3. Filters out noisy similar code
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import os
import json
import re


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


def _get_openai_client():
    """Get OpenAI client with lazy initialization"""
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if api_key:
        try:
            return OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
    return None


class RequirementGraphBuilder:
    """
    Build requirement graph from task description.

    CodeRAG insight: Map requirements to code, not just similar text.
    """

    def __init__(self):
        self._client = None
        self._client_initialized = False

    def _get_client(self):
        """Lazy client initialization"""
        if not self._client_initialized:
            self._client = _get_openai_client()
            self._client_initialized = True
        return self._client

    async def build_graph(self, task_description: str) -> List[Requirement]:
        """Parse task into structured requirements"""
        client = self._get_client()
        if not client:
            return []

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

Return ONLY the JSON array, no markdown formatting."""

        try:
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            reqs = self._parse_json(response.choices[0].message.content)
            return [Requirement(**r) for r in reqs]
        except Exception as e:
            print(f"Warning: Failed to build requirement graph: {e}")
            return []

    def _parse_json(self, text: str) -> List[Dict]:
        # Try to extract from markdown code block
        match = re.search(r'```(?:json)?\n?(.*?)```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()

        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
            return []
        except json.JSONDecodeError:
            # Try to find array in text
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            return []


class AdaptiveRetriever:
    """
    SELF-RAG style adaptive retrieval.

    Key insight: Don't always retrieve. Check if retrieval is needed.
    """

    def __init__(self, rag_index):
        self._client = None
        self._client_initialized = False
        self.rag_index = rag_index

    def _get_client(self):
        """Lazy client initialization"""
        if not self._client_initialized:
            self._client = _get_openai_client()
            self._client_initialized = True
        return self._client

    async def should_retrieve(self, query: str, context: str) -> bool:
        """
        Determine if retrieval is needed (SELF-RAG reflection).

        Returns True if:
        - Query requires external knowledge
        - Current context is insufficient
        """
        client = self._get_client()
        if not client:
            return True  # Default to retrieve if no client

        prompt = f"""Determine if external retrieval is needed.

Query: {query}

Current Context:
{context[:1000] if context else "(empty)"}

Answer with JSON:
{{"needs_retrieval": true, "reason": "..."}}

Retrieve if:
- Specific API details needed
- Implementation patterns unclear
- Domain knowledge required

Don't retrieve if:
- Context already sufficient
- Query is about general programming
- Similar code would just add noise

Return ONLY the JSON object, no markdown formatting."""

        try:
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            result = self._parse_json(response.choices[0].message.content)
            return result.get("needs_retrieval", True)
        except Exception as e:
            print(f"Warning: Failed to check retrieval need: {e}")
            return True

    async def retrieve_for_requirement(
        self,
        requirement: Requirement,
        filter_noise: bool = True
    ) -> List[CodeMapping]:
        """
        Retrieve code patterns for a specific requirement.

        AllianceCoder insight: API docs > similar code.
        """
        mappings = []

        if self.rag_index is None:
            return mappings

        # Query for API/docs first (more valuable)
        api_query = f"API documentation for: {requirement.description}"
        try:
            api_results = self.rag_index.query(api_query)
            if api_results:
                mappings.append(CodeMapping(
                    requirement_id=requirement.id,
                    code_pattern=str(api_results),
                    confidence=0.9,
                    source="api_doc"
                ))
        except Exception as e:
            print(f"Warning: API query failed: {e}")

        # Query for patterns (filter carefully)
        if not filter_noise:
            pattern_query = f"Implementation pattern for: {requirement.description}"
            try:
                pattern_results = self.rag_index.query(pattern_query)
                if pattern_results:
                    mappings.append(CodeMapping(
                        requirement_id=requirement.id,
                        code_pattern=str(pattern_results),
                        confidence=0.6,
                        source="similar_code"
                    ))
            except Exception as e:
                print(f"Warning: Pattern query failed: {e}")

        return mappings

    def _parse_json(self, text: str) -> Dict:
        # Try to extract from markdown code block
        match = re.search(r'```(?:json)?\n?(.*?)```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()

        try:
            result = json.loads(text)
            if isinstance(result, dict):
                return result
            return {}
        except json.JSONDecodeError:
            # Try to find object in text
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
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
        self.rag_index = rag_index

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
