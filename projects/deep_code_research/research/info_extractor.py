"""
InfoExtractor - Extract structured information from documents using LLM
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from openai import OpenAI
import os
import json
import re
import time


DEBUG_LOG_PATH = Path(__file__).resolve().parents[3] / ".cursor" / "debug.log"


class InfoExtractor:
    """Extract structured information from documents using LLM"""

    def __init__(self):
        self.client: Optional[OpenAI] = None
        self.model = os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest")
        # Lazy initialization of OpenAI client
        self._client_initialized = False

    def _get_client(self) -> Optional[OpenAI]:
        """Lazy initialization of OpenAI client"""
        if not self._client_initialized:
            api_key = os.environ.get("OPENAI_API_KEY")
            base_url = os.environ.get("OPENAI_BASE_URL")
            if api_key:
                try:
                    self.client = OpenAI(api_key=api_key, base_url=base_url)
                except Exception as e:
                    print(f"Warning: Failed to initialize OpenAI client: {e}")
                    self.client = None
            else:
                # region agent log
                try:
                    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
                        _f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "pre-fix",
                            "hypothesisId": "H4",
                            "location": "info_extractor._get_client",
                            "message": "missing_api_key",
                            "data": {},
                            "timestamp": int(time.time() * 1000)
                        }) + "\n")
                except Exception:
                    pass
                # endregion
            self._client_initialized = True
        return self.client

    async def extract_api_specs(self, documents: List[Any]) -> List[Dict]:
        """
        Extract API specifications from documents.

        Returns:
            List of dicts with: endpoint, method, params, response
        """
        # Combine document texts (limit to avoid token limits)
        doc_text = self._combine_documents(documents, max_chars=10000)

        if not doc_text.strip():
            return []

        client = self._get_client()
        if not client:
            return []

        prompt = f"""Extract API specifications from this documentation.

Documentation:
{doc_text}

Output JSON array of API endpoints:
[
    {{
        "endpoint": "/users",
        "method": "GET",
        "params": [],
        "response": "List of users"
    }},
    {{
        "endpoint": "/users",
        "method": "POST",
        "params": ["name", "email"],
        "response": "Created user object"
    }}
]

If no APIs found, return empty array [].
Return ONLY the JSON array, no markdown formatting."""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return self._parse_json_array(response.choices[0].message.content)
        except Exception as e:
            print(f"Warning: API extraction failed: {e}")
            return []

    async def extract_code_patterns(self, documents: List[Any]) -> List[Dict]:
        """
        Extract code patterns and best practices.

        Returns:
            List of dicts with: pattern_name, description, example
        """
        doc_text = self._combine_documents(documents, max_chars=10000)

        if not doc_text.strip():
            return []

        client = self._get_client()
        if not client:
            return []

        prompt = f"""Extract code patterns and best practices from this documentation.

Documentation:
{doc_text}

Output JSON array of patterns:
[
    {{
        "pattern_name": "Client Pattern",
        "description": "Use a client class to wrap API calls",
        "example": "class UserClient: ..."
    }}
]

If no patterns found, return empty array [].
Return ONLY the JSON array, no markdown formatting."""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return self._parse_json_array(response.choices[0].message.content)
        except Exception as e:
            print(f"Warning: Pattern extraction failed: {e}")
            return []

    async def extract_architecture(self, documents: List[Any]) -> Dict:
        """
        Extract system architecture information.

        Returns:
            Dict with: modules, components, data_flow
        """
        doc_text = self._combine_documents(documents, max_chars=10000)

        if not doc_text.strip():
            return {"modules": [], "components": [], "data_flow": []}

        client = self._get_client()
        if not client:
            return {"modules": [], "components": [], "data_flow": []}

        prompt = f"""Extract system architecture information from this documentation.

Documentation:
{doc_text}

Output JSON object:
{{
    "modules": ["module1", "module2"],
    "components": ["component1", "component2"],
    "data_flow": ["step1 -> step2", "step2 -> step3"]
}}

If no architecture info found, return empty lists.
Return ONLY the JSON object, no markdown formatting."""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            result = self._parse_json_object(response.choices[0].message.content)
            # Ensure required keys exist
            return {
                "modules": result.get("modules", []),
                "components": result.get("components", []),
                "data_flow": result.get("data_flow", [])
            }
        except Exception as e:
            print(f"Warning: Architecture extraction failed: {e}")
            return {"modules": [], "components": [], "data_flow": []}

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
        dependencies = set()

        for doc in documents:
            text = getattr(doc, 'text', str(doc))

            # Extract Python imports
            python_imports = self._extract_python_imports(text)
            dependencies.update(python_imports)

            # Extract from requirements.txt format
            req_deps = self._extract_requirements_format(text)
            dependencies.update(req_deps)

        return list(dependencies)

    def _extract_python_imports(self, text: str) -> List[str]:
        """Extract package names from Python import statements"""
        imports = set()

        # Match: import foo, from foo import bar
        import_patterns = [
            r'^import\s+(\w+)',
            r'^from\s+(\w+)',
        ]

        for pattern in import_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                # Filter out standard library modules (basic list)
                stdlib = {'os', 'sys', 're', 'json', 'typing', 'pathlib',
                         'collections', 'itertools', 'functools', 'asyncio',
                         'dataclasses', 'abc', 'copy', 'io', 'time', 'datetime'}
                if match not in stdlib:
                    imports.add(match)

        return list(imports)

    def _extract_requirements_format(self, text: str) -> List[str]:
        """Extract package names from requirements.txt format"""
        deps = []

        # Match: package==version, package>=version, package
        pattern = r'^([a-zA-Z0-9_-]+)(?:[=<>!~]|$)'
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                match = re.match(pattern, line)
                if match:
                    deps.append(match.group(1))

        return deps

    def _combine_documents(self, documents: List[Any], max_chars: int = 10000) -> str:
        """Combine document texts with character limit"""
        combined = []
        total_chars = 0

        for doc in documents:
            text = getattr(doc, 'text', str(doc))
            if total_chars + len(text) > max_chars:
                remaining = max_chars - total_chars
                if remaining > 100:
                    combined.append(text[:remaining] + "...")
                break
            combined.append(text)
            total_chars += len(text)

        return "\n\n---\n\n".join(combined)

    def _parse_json_array(self, text: str) -> List[Dict]:
        """Parse JSON array from LLM response"""
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

    def _parse_json_object(self, text: str) -> Dict:
        """Parse JSON object from LLM response"""
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
