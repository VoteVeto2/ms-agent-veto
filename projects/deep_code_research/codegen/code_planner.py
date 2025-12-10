"""
Code Planner - Plan code structure based on research context.
"""
import os
import re
import json
from typing import Optional
from openai import OpenAI


class CodePlanner:
    """Plan code structure based on research context."""

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

    async def create_plan(
        self,
        prompt: str,
        research_context: "ResearchContext"
    ) -> "CodePlan":
        """
        Create a code structure plan.

        Args:
            prompt: User's task description
            research_context: Research results from Agent 1

        Returns:
            CodePlan with list of FileSpec objects
        """
        client = self._get_client()
        if not client:
            return self.get_default_plan()

        # Import here to avoid circular import
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from contracts import CodePlan, FileSpec

        plan_prompt = f"""Based on the following task and research context, plan the code structure.

Task: {prompt}

Research Context:
- Architecture: {research_context.architecture}
- Code Patterns: {research_context.code_patterns[:5]}
- Dependencies: {research_context.dependencies[:20]}
- API Specs: {research_context.api_specs[:5]}

Output a JSON structure with:
{{
    "files": [
        {{
            "path": "src/main.py",
            "description": "Main entry point",
            "depends_on": []
        }},
        ...
    ],
    "dependencies": ["requests", "pydantic", ...]
}}

Include all necessary files for a complete, runnable project.
"""

        try:
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
                messages=[{"role": "user", "content": plan_prompt}],
                temperature=0.3
            )

            # Parse JSON response
            plan_json = self._parse_json(response.choices[0].message.content)

            return CodePlan(
                files=[FileSpec(**f) for f in plan_json.get("files", [])],
                dependencies=plan_json.get("dependencies", [])
            )
        except Exception:
            return self.get_default_plan()

    def _parse_json(self, text: str) -> dict:
        """Extract JSON from LLM response."""
        # Try to find JSON block
        json_match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"files": [], "dependencies": []}

    def get_default_plan(self) -> "CodePlan":
        """Fallback default plan."""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from contracts import CodePlan, FileSpec

        return CodePlan(
            files=[
                FileSpec(path="src/__init__.py", description="Package init"),
                FileSpec(path="src/main.py", description="Main entry point"),
                FileSpec(path="src/utils.py", description="Utility functions"),
                FileSpec(path="tests/__init__.py", description="Test package"),
                FileSpec(path="tests/test_main.py", description="Main tests"),
                FileSpec(path="requirements.txt", description="Dependencies"),
            ],
            dependencies=["pytest"]
        )
