"""
Self Debugger - Validate and fix generated code (basic syntax checking).
"""
import os
import re
from typing import Dict, Tuple, Optional
from openai import OpenAI


class SelfDebugger:
    """Validate and fix generated code (basic syntax checking)."""

    def __init__(self, max_attempts: int = 5):
        self.max_attempts = max_attempts
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

    async def validate_and_fix(
        self,
        file_path: str,
        code: str
    ) -> Tuple[str, bool, int]:
        """
        Validate code and fix if needed.

        Args:
            file_path: Path of the file
            code: Generated code

        Returns:
            Tuple of (fixed_code, success, attempts)
        """
        for attempt in range(self.max_attempts):
            validation = self._validate_syntax(file_path, code)

            if validation["success"]:
                return code, True, attempt + 1

            # Try to fix with LLM
            client = self._get_client()
            if not client:
                # Can't fix without LLM, return as-is
                return code, False, attempt + 1

            code = await self._fix_code(file_path, code, validation["error"])

        # Return last attempt even if failed
        return code, False, self.max_attempts

    def _validate_syntax(self, file_path: str, code: str) -> Dict:
        """Validate Python syntax."""
        if not file_path.endswith('.py'):
            return {"success": True}

        try:
            compile(code, file_path, 'exec')
            return {"success": True}
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"SyntaxError at line {e.lineno}: {e.msg}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _fix_code(
        self,
        file_path: str,
        code: str,
        error: str
    ) -> str:
        """Use LLM to fix code."""
        client = self._get_client()
        if not client:
            return code

        fix_prompt = f"""Fix the following code error:

File: {file_path}
Error: {error}

Code:
```python
{code}
```

Output ONLY the fixed code, no explanations.
"""

        try:
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
                messages=[{"role": "user", "content": fix_prompt}],
                temperature=0.2
            )

            return self._extract_code(response.choices[0].message.content)
        except Exception:
            return code

    def _extract_code(self, text: str) -> str:
        """Extract code from LLM response."""
        code_match = re.search(r'```(?:python)?\n(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        return text.strip()
