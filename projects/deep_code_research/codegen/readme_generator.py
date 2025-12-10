"""
README Generator - Generate README.md for the project.
"""
import os
import re
from typing import Dict, Optional
from openai import OpenAI


class ReadmeGenerator:
    """Generate README.md for the project."""

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

    async def generate(
        self,
        prompt: str,
        code_plan: "CodePlan",
        generated_files: Dict[str, str],
        research_context: "ResearchContext"
    ) -> str:
        """
        Generate README.md.

        Args:
            prompt: Original task description
            code_plan: The code structure plan
            generated_files: All generated files
            research_context: Research results

        Returns:
            README.md content as string
        """
        client = self._get_client()
        if not client:
            return self._get_default_readme(prompt, code_plan, generated_files)

        file_descriptions = []
        for f in code_plan.files[:10]:
            file_descriptions.append(f.description)

        readme_prompt = f"""Generate a README.md for this project:

## Project Description
{prompt}

## File Structure
{list(generated_files.keys())}

## Dependencies
{code_plan.dependencies}

## Key Components
{file_descriptions}

Generate a comprehensive README.md including:
1. Project Title and Description
2. Installation Instructions
3. Usage Examples
4. Project Structure
5. API Documentation (if applicable)
6. Contributing Guidelines
7. License

Output markdown format.
"""

        try:
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
                messages=[{"role": "user", "content": readme_prompt}],
                temperature=0.5
            )

            content = response.choices[0].message.content
            return self._clean_markdown(content)
        except Exception:
            return self._get_default_readme(prompt, code_plan, generated_files)

    def _clean_markdown(self, content: str) -> str:
        """Clean markdown content from LLM response."""
        # Remove markdown code block if present
        if content.startswith("```markdown"):
            content = content[11:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        return content.strip()

    def _get_default_readme(
        self,
        prompt: str,
        code_plan: "CodePlan",
        generated_files: Dict[str, str]
    ) -> str:
        """Generate default README.md."""
        files_list = "\n".join([f"- `{f}`" for f in generated_files.keys()])
        deps_list = "\n".join([f"- {d}" for d in code_plan.dependencies]) if code_plan.dependencies else "- None"

        return f"""# Project

## Description

{prompt}

## Installation

```bash
pip install -r requirements.txt
```

## Project Structure

{files_list}

## Dependencies

{deps_list}

## Usage

```python
from src.main import main

main()
```

## License

MIT
"""
