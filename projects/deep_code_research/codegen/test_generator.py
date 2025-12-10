"""
Auto Test Generator - AgentCoder Pattern

Automatically generates test cases from task description,
then uses them to validate and prune code solutions.
"""
import os
import re
import subprocess
import tempfile
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from openai import OpenAI


@dataclass
class TestCase:
    """A single test case."""
    name: str
    input_code: str  # Setup + assertion
    expected_behavior: str


@dataclass
class TestResult:
    """Result of running a test."""
    test_name: str
    passed: bool
    output: str
    error: str = None


class TestGenerator:
    """
    AgentCoder-style test generation.

    Specialized agent that generates comprehensive test cases
    from task description + generated code.
    """

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

    async def generate_tests(
        self,
        task_description: str,
        code: str,
        function_name: str = None
    ) -> List[TestCase]:
        """Generate comprehensive test cases."""
        client = self._get_client()
        if not client:
            return []

        prompt = f"""Generate pytest test cases for this code.

Task: {task_description}

Code:
```python
{code}
```

Generate 5-7 test cases covering:
1. Normal/happy path (2-3 tests)
2. Edge cases (2 tests)
3. Error handling (1-2 tests)

Output format:
```python
import pytest

def test_normal_case_1():
    # Test description
    result = function_name(input)
    assert result == expected

def test_edge_case_empty():
    # Test edge case
    ...

def test_error_invalid_input():
    with pytest.raises(ValueError):
        ...
```

Output ONLY the test code.
"""
        try:
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            test_code = self._extract_code(response.choices[0].message.content)
            return self._parse_tests(test_code)
        except Exception:
            return []

    def _parse_tests(self, test_code: str) -> List[TestCase]:
        """Parse test code into TestCase objects."""
        tests = []
        # Match test functions
        pattern = r'def (test_\w+)\([^)]*\):\s*(?:#[^\n]*)?\n(.*?)(?=\ndef test_|\ndef \w+|\Z)'
        matches = re.findall(pattern, test_code, re.DOTALL)

        for name, body in matches:
            # Clean up body
            body = body.strip()
            if body:
                tests.append(TestCase(
                    name=name,
                    input_code=f"def {name}():\n    " + body.replace('\n', '\n    '),
                    expected_behavior=name.replace('_', ' ')
                ))

        return tests

    def _extract_code(self, text: str) -> str:
        """Extract code from LLM response."""
        match = re.search(r'```python\n(.*?)```', text, re.DOTALL)
        return match.group(1) if match else text


class TestExecutor:
    """
    Execute generated tests against code.

    Runs tests in isolated environment and reports results.
    """

    async def run_tests(
        self,
        code: str,
        tests: List[TestCase]
    ) -> List[TestResult]:
        """Run all tests and return results."""
        if not tests:
            return []

        results = []

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write code file
            code_path = os.path.join(tmpdir, "solution.py")
            with open(code_path, 'w') as f:
                f.write(code)

            # Write test file
            test_code = "import pytest\n"
            test_code += "import sys\n"
            test_code += f"sys.path.insert(0, '{tmpdir}')\n"
            test_code += "from solution import *\n\n"
            test_code += "\n\n".join(t.input_code for t in tests)

            test_path = os.path.join(tmpdir, "test_solution.py")
            with open(test_path, 'w') as f:
                f.write(test_code)

            # Run pytest
            try:
                result = subprocess.run(
                    ["pytest", test_path, "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=tmpdir
                )

                # Parse results
                for test in tests:
                    passed = f"{test.name} PASSED" in result.stdout
                    results.append(TestResult(
                        test_name=test.name,
                        passed=passed,
                        output=result.stdout,
                        error=result.stderr if not passed else None
                    ))

            except subprocess.TimeoutExpired:
                for test in tests:
                    results.append(TestResult(
                        test_name=test.name,
                        passed=False,
                        output="",
                        error="Test execution timed out"
                    ))
            except FileNotFoundError:
                # pytest not available
                for test in tests:
                    results.append(TestResult(
                        test_name=test.name,
                        passed=False,
                        output="",
                        error="pytest not found"
                    ))

        return results

    async def validate_and_prune(
        self,
        code_candidates: List[str],
        tests: List[TestCase]
    ) -> List[Tuple[str, float]]:
        """
        Validate multiple code candidates and return pass rates.

        This implements the CodeCoR pruning strategy:
        - Run tests on each candidate
        - Prune candidates that fail
        - Return sorted by pass rate
        """
        if not tests:
            return [(code, 0.0) for code in code_candidates]

        scored = []

        for code in code_candidates:
            results = await self.run_tests(code, tests)
            if results:
                pass_rate = sum(1 for r in results if r.passed) / len(results)
            else:
                pass_rate = 0.0
            scored.append((code, pass_rate))

        # Sort by pass rate descending
        return sorted(scored, key=lambda x: x[1], reverse=True)
