"""
Code Generator - Generate code files based on plan and research context.
"""
import os
import re
import json
import time
import inspect
from pathlib import Path
from typing import Dict, Optional
from openai import OpenAI


DEBUG_LOG_PATH = Path(__file__).resolve().parents[3] / ".cursor" / "debug.log"


class CodeGenerator:
    """Generate code files based on plan and research context."""

    def __init__(self):
        self.client: Optional[OpenAI] = None
        self._client_initialized = False

    def _get_client(self) -> Optional[OpenAI]:
        """Lazily initialize OpenAI client."""
        if self._client_initialized:
            return self.client

        self._client_initialized = True
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            base_url = os.environ.get("OPENAI_BASE_URL")

            if not api_key:
                return None

            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url
            ) if base_url else OpenAI(api_key=api_key)
            return self.client
        except Exception:
            return None

    async def generate_file(
        self,
        file_spec: "FileSpec",
        research_context: "ResearchContext",
        existing_files: Dict[str, str] = None
    ) -> str:
        """
        Generate code for a single file.

        Args:
            file_spec: Specification for the file
            research_context: Research results with RAG index
            existing_files: Already generated files (for context)

        Returns:
            Generated code as string
        """
        client = self._get_client()
        # region agent log
        try:
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
                _f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H2",
                    "location": "code_generator.generate_file",
                    "message": "generator_client_status",
                    "data": {
                        "file_path": file_spec.path,
                        "client_available": bool(client),
                        "model": os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
                        "base_url_set": bool(os.environ.get("OPENAI_BASE_URL"))
                    },
                    "timestamp": int(time.time() * 1000)
                }) + "\n")
        except Exception:
            pass
        # endregion
        if not client:
            return self._get_default_code(file_spec)

        # Query RAG for relevant context
        relevant_context = ""
        if research_context.rag_index:
            try:
                # region agent log
                try:
                    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
                        _f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "post-fix",
                            "hypothesisId": "H3",
                            "location": "code_generator.generate_file",
                            "message": "rag_query_start",
                            "data": {
                                "file_path": file_spec.path,
                                "has_rag_index": bool(research_context.rag_index),
                                "is_coroutine_function": inspect.iscoroutinefunction(
                                    getattr(research_context.rag_index, "query", None)
                                )
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + "\n")
                except Exception:
                    pass
                # endregion
                rag_result = research_context.rag_index.query(file_spec.description)
                if inspect.iscoroutine(rag_result):
                    rag_result = await rag_result
                relevant_context = str(rag_result)[:3000] if rag_result is not None else ""
            except Exception:
                pass
            else:
                # region agent log
                try:
                    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
                        _f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "post-fix",
                            "hypothesisId": "H3",
                            "location": "code_generator.generate_file",
                            "message": "rag_query_result",
                            "data": {
                                "file_path": file_spec.path,
                                "context_length": len(relevant_context),
                                "rag_result_type": type(rag_result).__name__ if rag_result is not None else "NoneType"
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + "\n")
                except Exception:
                    pass
                # endregion

        # Build prompt
        gen_prompt = f"""Generate code for the following file:

File: {file_spec.path}
Purpose: {file_spec.description}
Dependencies: {file_spec.depends_on}

Reference Documentation:
{relevant_context}

API Specifications:
{research_context.api_specs[:3]}

Code Patterns to Follow:
{research_context.code_patterns[:3]}

{self._get_existing_context(file_spec, existing_files)}

Generate complete, production-ready code. Include:
- Proper imports
- Type hints
- Docstrings
- Error handling

Output ONLY the code, no explanations.
"""

        try:
            # region agent log
            try:
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
                    _f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "H2",
                        "location": "code_generator.generate_file",
                        "message": "generator_llm_start",
                        "data": {
                            "file_path": file_spec.path,
                            "prompt_chars": len(gen_prompt)
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # endregion
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
                messages=[{"role": "user", "content": gen_prompt}],
                temperature=0.3
            )

            code_out = self._extract_code(response.choices[0].message.content)
            # region agent log
            try:
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
                    _f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "H2",
                        "location": "code_generator.generate_file",
                        "message": "generator_llm_done",
                        "data": {
                            "file_path": file_spec.path,
                            "code_length": len(code_out)
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # endregion
            return code_out
        except Exception:
            return self._get_default_code(file_spec)

    def _get_existing_context(
        self,
        file_spec: "FileSpec",
        existing_files: Dict[str, str]
    ) -> str:
        """Get context from already generated files."""
        if not existing_files or not file_spec.depends_on:
            return ""

        context_parts = []
        for dep in file_spec.depends_on:
            if dep in existing_files:
                context_parts.append(f"# {dep}\n{existing_files[dep][:1000]}")

        if context_parts:
            return f"\nExisting Files for Reference:\n" + "\n\n".join(context_parts)
        return ""

    def _extract_code(self, text: str) -> str:
        """Extract code from LLM response."""
        # Try to find code block
        code_match = re.search(r'```(?:python)?\n(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # Return as-is if no code block
        return text.strip()

    def _get_default_code(self, file_spec: "FileSpec") -> str:
        """Generate default code based on file type."""
        path = file_spec.path

        if path.endswith("__init__.py"):
            return '"""Package initialization."""\n'

        if path.endswith("requirements.txt"):
            return "# Requirements\npytest\n"

        if path.endswith(".py"):
            return f'''"""
{file_spec.description}
"""


def main():
    """Main entry point."""
    print("Hello, World!")


if __name__ == "__main__":
    main()
'''

        return f"# {file_spec.description}\n"
