"""
Simulation-Based Debugger - CODESIM Pattern

Simulates code execution on sample inputs BEFORE actual execution.
Catches logical errors early, reducing debug iterations.
"""
import os
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from openai import OpenAI


DEBUG_LOG_PATH = Path(__file__).resolve().parents[3] / ".cursor" / "debug.log"


@dataclass
class SimulationResult:
    """Result of simulating code execution."""
    input_data: Any
    expected_output: Any
    simulated_output: Any
    trace: List[str]
    is_correct: bool
    error: str = None


class SimulationDebugger:
    """
    CODESIM-style simulation debugger.

    Instead of just checking syntax, we:
    1. Generate sample inputs from the task description
    2. Simulate step-by-step execution mentally (via LLM)
    3. Compare simulated outputs with expected behavior
    4. Identify logical errors before running code
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

    async def generate_test_inputs(
        self,
        task_description: str,
        code: str,
        num_samples: int = 3
    ) -> List[Dict]:
        """Generate sample inputs for simulation."""
        client = self._get_client()
        if not client:
            return []

        prompt = f"""Given this task and code, generate {num_samples} test inputs.

Task: {task_description}

Code:
```python
{code}
```

Output JSON array of test cases:
[
    {{"input": <input_value>, "expected_output": <expected_value>}},
    ...
]

Include edge cases and typical cases.
"""
        try:
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            raw_content = response.choices[0].message.content
            parsed = self._parse_json(raw_content)

            # Normalize to list[dict]; drop invalid items to avoid downstream type errors.
            if isinstance(parsed, dict):
                parsed = [parsed]
            elif not isinstance(parsed, list):
                parsed = []
            parsed = [item for item in parsed if isinstance(item, dict)]

            # region agent log
            try:
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
                    _f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "pre-fix",
                        "hypothesisId": "H5",
                        "location": "simulation_debugger.generate_test_inputs",
                        "message": "parsed_tests",
                        "data": {
                            "count": len(parsed) if hasattr(parsed, "__len__") else None,
                            "type": type(parsed).__name__,
                            "first_item_type": type(parsed[0]).__name__ if isinstance(parsed, list) and parsed else None
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # endregion

            # region agent log
            try:
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
                    _f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "pre-fix",
                        "hypothesisId": "H5_raw",
                        "location": "simulation_debugger.generate_test_inputs",
                        "message": "raw_llm_content",
                        "data": {
                            "raw_preview": raw_content[:200] if isinstance(raw_content, str) else None,
                            "raw_type": type(raw_content).__name__ if raw_content is not None else None
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # endregion

            return parsed
        except Exception:
            return []

    async def simulate_execution(
        self,
        code: str,
        test_input: Dict
    ) -> SimulationResult:
        """
        Simulate code execution step-by-step.

        This is the KEY innovation from CODESIM:
        - LLM traces through code like a human debugger
        - Tracks variable states at each step
        - Identifies where logic diverges from expected
        """
        input_val = test_input.get('input') if isinstance(test_input, dict) else None
        expected_val = test_input.get('expected_output') if isinstance(test_input, dict) else None

        # region agent log
        try:
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
                _f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "pre-fix",
                    "hypothesisId": "H5",
                    "location": "simulation_debugger.simulate_execution",
                    "message": "input_received",
                    "data": {
                        "test_type": type(test_input).__name__,
                        "has_input_key": isinstance(test_input, dict) and 'input' in test_input,
                            "has_expected_key": isinstance(test_input, dict) and 'expected_output' in test_input,
                            "value_preview": str(test_input)[:150]
                    },
                    "timestamp": int(time.time() * 1000)
                }) + "\n")
        except Exception:
            pass
        # endregion

        if not isinstance(test_input, dict):
            raise TypeError(f"simulate_execution expected dict, got {type(test_input).__name__}")

        client = self._get_client()
        if not client:
            return SimulationResult(
                input_data=input_val,
                expected_output=expected_val,
                simulated_output=None,
                trace=[],
                is_correct=False,
                error="No API client available"
            )

        prompt = f"""Simulate executing this code step-by-step.

Code:
```python
{code}
```

Input: {input_val}
Expected Output: {expected_val}

Trace through the code like a debugger:
1. Show variable values at each step
2. Show the final output
3. Identify if it matches expected output
4. If wrong, identify WHERE the logic error occurs

Output format:
{{
    "trace": ["step 1: x = 5", "step 2: y = x + 1 = 6", ...],
    "simulated_output": <value>,
    "is_correct": true/false,
    "error_location": "line X" or null,
    "error_explanation": "..." or null
}}
"""
        try:
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )

            result = self._parse_json(response.choices[0].message.content)
            if isinstance(result, list):
                result = result[0] if result else {}

            return SimulationResult(
                input_data=input_val,
                expected_output=expected_val,
                simulated_output=result.get('simulated_output'),
                trace=result.get('trace', []),
                is_correct=result.get('is_correct', False),
                error=result.get('error_explanation')
            )
        except Exception as e:
            return SimulationResult(
                input_data=input_val,
                expected_output=expected_val,
                simulated_output=None,
                trace=[],
                is_correct=False,
                error=str(e)
            )

    async def debug_with_simulation(
        self,
        task_description: str,
        code: str,
        max_iterations: int = 3
    ) -> Tuple[str, List[SimulationResult]]:
        """
        Full simulation-based debugging loop.

        Returns: (fixed_code, simulation_results)
        """
        all_results = []
        client = self._get_client()
        if not client:
            return code, all_results

        # region agent log
        try:
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
                _f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H3",
                    "location": "simulation_debugger.debug_with_simulation",
                    "message": "simulation_start",
                    "data": {
                        "max_iterations": max_iterations,
                        "code_preview": code[:80]
                    },
                    "timestamp": int(time.time() * 1000)
                }) + "\n")
        except Exception:
            pass
        # endregion

        for iteration in range(max_iterations):
            # Generate test inputs
            test_inputs = await self.generate_test_inputs(task_description, code)

            if not test_inputs:
                return code, all_results

            # Simulate each test
            results = []
            for test in test_inputs:
                # region agent log
                try:
                    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
                        _f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "pre-fix",
                            "hypothesisId": "H5",
                            "location": "simulation_debugger.debug_with_simulation",
                            "message": "simulate_start",
                            "data": {
                                "iteration": iteration,
                                "test_type": type(test).__name__,
                                "test_preview": str(test)[:120]
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + "\n")
                except Exception:
                    pass
                # endregion
                result = await self.simulate_execution(code, test)
                results.append(result)

            all_results.extend(results)

            # Check if all simulations pass
            if all(r.is_correct for r in results):
                return code, all_results

            # Fix code based on simulation errors
            failed = [r for r in results if not r.is_correct]
            code = await self._fix_from_simulation(code, failed)

        return code, all_results

    async def _fix_from_simulation(
        self,
        code: str,
        failed_results: List[SimulationResult]
    ) -> str:
        """Fix code based on simulation failures."""
        client = self._get_client()
        if not client:
            return code

        errors = "\n".join([
            f"Input: {r.input_data}\n"
            f"Expected: {r.expected_output}\n"
            f"Got: {r.simulated_output}\n"
            f"Error: {r.error}\n"
            f"Trace: {r.trace[-3:] if r.trace else 'N/A'}"
            for r in failed_results
        ])

        prompt = f"""Fix this code based on simulation results:

Code:
```python
{code}
```

Simulation Failures:
{errors}

Output ONLY the fixed code.
"""
        try:
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return self._extract_code(response.choices[0].message.content)
        except Exception:
            return code

    def _parse_json(self, text: str) -> Any:
        """Parse JSON from LLM response."""
        # Try to find JSON in markdown block
        match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON array or object
        for pattern in [r'\[.*\]', r'\{.*\}']:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

        # Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return []

    def _extract_code(self, text: str) -> str:
        """Extract code from LLM response."""
        match = re.search(r'```python\n(.*?)```', text, re.DOTALL)
        return match.group(1).strip() if match else text.strip()
