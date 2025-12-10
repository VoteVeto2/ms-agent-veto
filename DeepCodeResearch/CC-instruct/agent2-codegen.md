# Agent 2: Code Generation Layer

## Role

You are responsible for building the **Code Generation Layer** of the DeepCodeResearch system. Your code takes a `ResearchContext` (from Agent 1) and a user prompt, then generates a complete code repository with all files and README.md.

**Key Innovations (2025)**: This layer now implements:
1. **Simulation-Based Debugging** (CODESIM pattern) - Catches logical errors before execution
2. **Auto Test Generation** (AgentCoder pattern) - Generates and runs tests to validate code

---

## API Configuration

Use this for all LLM calls:

```python
import os
os.environ["OPENAI_API_KEY"] = "AIzaSyDmTcj4-ujVOIswqGLvt0fTZiVe49SU3ZY"
os.environ["OPENAI_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
os.environ["OPENAI_MODEL"] = "gemini-flash-lite-latest"
```

---

## Literature Context (December 2025)

Based on latest research in multi-agent code generation:

| Framework | Architecture | Key Innovation | Performance | Source |
|-----------|--------------|----------------|-------------|--------|
| **CODESIM** | Planning + Coding + Debugging | Input-output simulation before execution | SOTA benchmarks | [Paper](https://huggingface.co/papers/2502.05664) |
| **CodeCoR** | Self-reflective multi-agent | Auto test generation + solution pruning | 77.8% pass@1 | [Survey](https://arxiv.org/html/2508.00083v1) |
| **AgentCoder** | Programmer + Test Designer + Executor | Iterative testing loop | 96.3% pass@1 | [Paper](https://arxiv.org/abs/2312.13010) |

**Key Insight**: Modern frameworks use **3-4 specialized agents** rather than monolithic approaches. Simulation-based debugging catches errors **before** actual execution.

---

## Directory Structure

Create these files:

```
projects/deep_code_research/
├── codegen/
│   ├── __init__.py
│   ├── code_planner.py         # Plan code structure
│   ├── code_generator.py       # Generate code files
│   ├── self_debugger.py        # Basic validation & fix code
│   ├── simulation_debugger.py  # NEW: CODESIM pattern simulation
│   ├── test_generator.py       # NEW: AgentCoder pattern test generation
│   └── readme_generator.py     # Generate README.md
└── tests/
    └── test_codegen.py         # CREATE THIS FIRST
```

---

## Shared Interfaces (from contracts.py)

You receive `ResearchContext` from Agent 1, and use these dataclasses. Agent 3 creates `contracts.py`:

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ResearchContext:
    """Input from Research Layer"""
    api_specs: List[Dict] = field(default_factory=list)
    code_patterns: List[Dict] = field(default_factory=list)
    architecture: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    documents: List[Any] = field(default_factory=list)
    rag_index: Any = None  # Query engine for retrieval

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
```

---

## Task 1: CodePlanner

**File**: `codegen/code_planner.py`

```python
from typing import List
from openai import OpenAI

# Import from contracts when available
# from ..contracts import ResearchContext, CodePlan, FileSpec

class CodePlanner:
    """Plan code structure based on research context"""

    def __init__(self):
        self.client = OpenAI()

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

        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
            messages=[{"role": "user", "content": plan_prompt}],
            temperature=0.3
        )

        # Parse JSON response
        plan_json = self._parse_json(response.choices[0].message.content)

        from ..contracts import CodePlan, FileSpec
        return CodePlan(
            files=[FileSpec(**f) for f in plan_json.get("files", [])],
            dependencies=plan_json.get("dependencies", [])
        )

    def _parse_json(self, text: str) -> dict:
        """Extract JSON from LLM response"""
        import json
        import re

        # Try to find JSON block
        json_match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Try direct parse
        try:
            return json.loads(text)
        except:
            return {"files": [], "dependencies": []}

    def get_default_plan(self) -> "CodePlan":
        """Fallback default plan"""
        from ..contracts import CodePlan, FileSpec
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
```

---

## Task 2: CodeGenerator

**File**: `codegen/code_generator.py`

```python
from typing import Dict, Any
from openai import OpenAI

class CodeGenerator:
    """Generate code files based on plan and research context"""

    def __init__(self):
        self.client = OpenAI()

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
        # Query RAG for relevant context
        relevant_context = ""
        if research_context.rag_index:
            try:
                rag_result = research_context.rag_index.query(file_spec.description)
                relevant_context = str(rag_result)[:3000]
            except:
                pass

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

        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
            messages=[{"role": "user", "content": gen_prompt}],
            temperature=0.3
        )

        return self._extract_code(response.choices[0].message.content)

    def _get_existing_context(
        self,
        file_spec: "FileSpec",
        existing_files: Dict[str, str]
    ) -> str:
        """Get context from already generated files"""
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
        """Extract code from LLM response"""
        import re

        # Try to find code block
        code_match = re.search(r'```(?:python)?\n(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # Return as-is if no code block
        return text.strip()
```

---

## Task 3: SelfDebugger (Basic)

**File**: `codegen/self_debugger.py`

```python
from typing import Dict, Tuple
from openai import OpenAI

class SelfDebugger:
    """Validate and fix generated code (basic syntax checking)"""

    def __init__(self, max_attempts: int = 5):
        self.client = OpenAI()
        self.max_attempts = max_attempts

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

            # Try to fix
            code = await self._fix_code(file_path, code, validation["error"])

        # Return last attempt even if failed
        return code, False, self.max_attempts

    def _validate_syntax(self, file_path: str, code: str) -> Dict:
        """Validate Python syntax"""
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
        """Use LLM to fix code"""
        fix_prompt = f"""Fix the following code error:

File: {file_path}
Error: {error}

Code:
```python
{code}
```

Output ONLY the fixed code, no explanations.
"""

        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
            messages=[{"role": "user", "content": fix_prompt}],
            temperature=0.2
        )

        return self._extract_code(response.choices[0].message.content)

    def _extract_code(self, text: str) -> str:
        """Extract code from LLM response"""
        import re
        code_match = re.search(r'```(?:python)?\n(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        return text.strip()
```

---

## Task 3B: SimulationDebugger (NEW - CODESIM Pattern)

**File**: `codegen/simulation_debugger.py`

**Priority**: 🔴 P1 - High Impact (from Agent 4's improvement roadmap)

```python
"""
Simulation-Based Debugger - CODESIM Pattern

Simulates code execution on sample inputs BEFORE actual execution.
Catches logical errors early, reducing debug iterations.
"""

from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from openai import OpenAI
import os


@dataclass
class SimulationResult:
    """Result of simulating code execution"""
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
        self.client = OpenAI()

    async def generate_test_inputs(
        self,
        task_description: str,
        code: str,
        num_samples: int = 3
    ) -> List[Dict]:
        """Generate sample inputs for simulation"""
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
        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return self._parse_json(response.choices[0].message.content)

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
        prompt = f"""Simulate executing this code step-by-step.

Code:
```python
{code}
```

Input: {test_input['input']}
Expected Output: {test_input['expected_output']}

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
        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        result = self._parse_json(response.choices[0].message.content)
        return SimulationResult(
            input_data=test_input['input'],
            expected_output=test_input['expected_output'],
            simulated_output=result.get('simulated_output'),
            trace=result.get('trace', []),
            is_correct=result.get('is_correct', False),
            error=result.get('error_explanation')
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

        for iteration in range(max_iterations):
            # Generate test inputs
            test_inputs = await self.generate_test_inputs(task_description, code)

            # Simulate each test
            results = []
            for test in test_inputs:
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
        """Fix code based on simulation failures"""
        errors = "\n".join([
            f"Input: {r.input_data}\n"
            f"Expected: {r.expected_output}\n"
            f"Got: {r.simulated_output}\n"
            f"Error: {r.error}\n"
            f"Trace: {r.trace[-3:]}"  # Last 3 steps
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
        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return self._extract_code(response.choices[0].message.content)

    def _parse_json(self, text: str) -> Any:
        import json
        import re
        match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        try:
            return json.loads(text)
        except:
            return []

    def _extract_code(self, text: str) -> str:
        import re
        match = re.search(r'```python\n(.*?)```', text, re.DOTALL)
        return match.group(1) if match else text
```

**Integration Point**: Use `SimulationDebugger.debug_with_simulation()` alongside or instead of basic `SelfDebugger._validate_code()`.

---

## Task 3C: TestGenerator (NEW - AgentCoder Pattern)

**File**: `codegen/test_generator.py`

**Priority**: 🔴 P1 - High Impact (from Agent 4's improvement roadmap)

```python
"""
Auto Test Generator - AgentCoder Pattern

Automatically generates test cases from task description,
then uses them to validate and prune code solutions.
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
from openai import OpenAI
import subprocess
import tempfile
import os


@dataclass
class TestCase:
    """A single test case"""
    name: str
    input_code: str  # Setup + assertion
    expected_behavior: str


@dataclass
class TestResult:
    """Result of running a test"""
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
        self.client = OpenAI()

    async def generate_tests(
        self,
        task_description: str,
        code: str,
        function_name: str = None
    ) -> List[TestCase]:
        """Generate comprehensive test cases"""
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
        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        test_code = self._extract_code(response.choices[0].message.content)
        return self._parse_tests(test_code)

    def _parse_tests(self, test_code: str) -> List[TestCase]:
        """Parse test code into TestCase objects"""
        import re
        tests = []
        pattern = r'def (test_\w+)\([^)]*\):\s*(?:#[^\n]*)?\n(.*?)(?=\ndef |$)'
        matches = re.findall(pattern, test_code, re.DOTALL)

        for name, body in matches:
            tests.append(TestCase(
                name=name,
                input_code=f"def {name}():\n{body}",
                expected_behavior=name.replace('_', ' ')
            ))

        return tests

    def _extract_code(self, text: str) -> str:
        import re
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
        """Run all tests and return results"""
        results = []

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write code file
            code_path = os.path.join(tmpdir, "solution.py")
            with open(code_path, 'w') as f:
                f.write(code)

            # Write test file
            test_code = "import pytest\n"
            test_code += f"from solution import *\n\n"
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
        scored = []

        for code in code_candidates:
            results = await self.run_tests(code, tests)
            pass_rate = sum(1 for r in results if r.passed) / len(results)
            scored.append((code, pass_rate))

        # Sort by pass rate descending
        return sorted(scored, key=lambda x: x[1], reverse=True)
```

**Integration Point**: Add to `generate_repository()` after code generation, before returning.

---

## Task 4: ReadmeGenerator

**File**: `codegen/readme_generator.py`

```python
from typing import Dict, List
from openai import OpenAI

class ReadmeGenerator:
    """Generate README.md for the project"""

    def __init__(self):
        self.client = OpenAI()

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
        readme_prompt = f"""Generate a README.md for this project:

## Project Description
{prompt}

## File Structure
{list(generated_files.keys())}

## Dependencies
{code_plan.dependencies}

## Key Components
{[f.description for f in code_plan.files[:10]]}

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

        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
            messages=[{"role": "user", "content": readme_prompt}],
            temperature=0.5
        )

        content = response.choices[0].message.content

        # Remove markdown code block if present
        if content.startswith("```markdown"):
            content = content[11:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        return content.strip()
```

---

## Main Interface

**File**: `codegen/__init__.py`

```python
from typing import Dict, Tuple
from .code_planner import CodePlanner
from .code_generator import CodeGenerator
from .self_debugger import SelfDebugger
from .simulation_debugger import SimulationDebugger
from .test_generator import TestGenerator, TestExecutor
from .readme_generator import ReadmeGenerator

async def generate_repository(
    prompt: str,
    research_context: "ResearchContext",
    use_simulation_debug: bool = True,
    use_auto_tests: bool = True
) -> Tuple[Dict[str, str], Dict]:
    """
    Main entry point for Code Generation Layer.

    Args:
        prompt: User's task description
        research_context: Research results from Agent 1
        use_simulation_debug: Use CODESIM simulation debugging (default: True)
        use_auto_tests: Use AgentCoder auto test generation (default: True)

    Returns:
        Tuple of (files_dict, metrics_dict)
        - files_dict: Dict mapping file paths to file contents
        - metrics_dict: Debug iterations, test results, etc.
    """
    metrics = {
        "total_debug_iterations": 0,
        "simulation_results": [],
        "test_results": []
    }

    # 1. Create code plan
    planner = CodePlanner()
    code_plan = await planner.create_plan(prompt, research_context)

    if not code_plan.files:
        code_plan = planner.get_default_plan()

    # 2. Generate code files
    generator = CodeGenerator()
    basic_debugger = SelfDebugger()
    simulation_debugger = SimulationDebugger() if use_simulation_debug else None
    test_generator = TestGenerator() if use_auto_tests else None
    test_executor = TestExecutor() if use_auto_tests else None

    generated_files = {}

    for file_spec in code_plan.files:
        # Generate code
        code = await generator.generate_file(
            file_spec,
            research_context,
            generated_files
        )

        # Basic syntax validation
        fixed_code, success, attempts = await basic_debugger.validate_and_fix(
            file_spec.path,
            code
        )
        metrics["total_debug_iterations"] += attempts

        # NEW: Simulation-based debugging (CODESIM pattern)
        if simulation_debugger and file_spec.path.endswith('.py'):
            fixed_code, sim_results = await simulation_debugger.debug_with_simulation(
                prompt,
                fixed_code
            )
            metrics["simulation_results"].extend(sim_results)

        generated_files[file_spec.path] = fixed_code

    # 3. NEW: Auto test generation and validation (AgentCoder pattern)
    if test_generator and test_executor:
        # Generate tests for main code files
        main_files = [f for f in generated_files.keys() if f.endswith('.py') and 'test' not in f]
        for file_path in main_files[:3]:  # Limit to first 3 main files
            tests = await test_generator.generate_tests(
                prompt,
                generated_files[file_path]
            )
            if tests:
                results = await test_executor.run_tests(generated_files[file_path], tests)
                metrics["test_results"].extend([
                    {"file": file_path, "test": r.test_name, "passed": r.passed}
                    for r in results
                ])

    # 4. Generate requirements.txt if not present
    if "requirements.txt" not in generated_files:
        deps = code_plan.dependencies + research_context.dependencies[:10]
        generated_files["requirements.txt"] = "\n".join(set(deps))

    # 5. Generate README.md
    readme_gen = ReadmeGenerator()
    readme = await readme_gen.generate(
        prompt,
        code_plan,
        generated_files,
        research_context
    )
    generated_files["README.md"] = readme

    return generated_files, metrics
```

---

## Test First!

**File**: `tests/test_codegen.py`

```python
import pytest
import asyncio
import os

# Set up API before tests
os.environ["OPENAI_API_KEY"] = "AIzaSyDmTcj4-ujVOIswqGLvt0fTZiVe49SU3ZY"
os.environ["OPENAI_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
os.environ["OPENAI_MODEL"] = "gemini-flash-lite-latest"


@pytest.fixture
def mock_research_context():
    """Create mock ResearchContext for testing"""
    from dataclasses import dataclass, field
    from typing import List, Dict, Any

    @dataclass
    class MockResearchContext:
        api_specs: List[Dict] = field(default_factory=lambda: [
            {"endpoint": "/users", "method": "GET", "description": "Get users"}
        ])
        code_patterns: List[Dict] = field(default_factory=lambda: [
            {"pattern": "Repository", "description": "Data access layer"}
        ])
        architecture: Dict = field(default_factory=lambda: {
            "modules": ["api", "services", "models"]
        })
        dependencies: List[str] = field(default_factory=lambda: [
            "requests", "pydantic"
        ])
        documents: List[Any] = field(default_factory=list)
        rag_index: Any = None
        adaptive_rag: Any = None

    return MockResearchContext()


@pytest.mark.asyncio
async def test_code_planner(mock_research_context):
    from codegen.code_planner import CodePlanner

    planner = CodePlanner()
    plan = await planner.create_plan(
        "Create a simple REST API client",
        mock_research_context
    )

    assert plan is not None
    assert len(plan.files) > 0 or plan == planner.get_default_plan()


@pytest.mark.asyncio
async def test_code_generator(mock_research_context):
    from codegen.code_generator import CodeGenerator
    from dataclasses import dataclass
    from typing import List

    @dataclass
    class MockFileSpec:
        path: str = "src/main.py"
        description: str = "Main entry point"
        depends_on: List[str] = None

        def __post_init__(self):
            if self.depends_on is None:
                self.depends_on = []

    generator = CodeGenerator()
    code = await generator.generate_file(
        MockFileSpec(),
        mock_research_context,
        {}
    )

    assert code is not None
    assert len(code) > 0


@pytest.mark.asyncio
async def test_self_debugger():
    from codegen.self_debugger import SelfDebugger

    debugger = SelfDebugger(max_attempts=2)

    # Valid code
    valid_code = "print('hello')"
    fixed, success, attempts = await debugger.validate_and_fix("test.py", valid_code)
    assert success == True
    assert attempts == 1

    # Invalid code
    invalid_code = "print('hello'"  # Missing closing paren
    fixed, success, attempts = await debugger.validate_and_fix("test.py", invalid_code)
    # Should attempt to fix
    assert attempts >= 1


@pytest.mark.asyncio
async def test_simulation_debugger():
    """Test CODESIM-style simulation debugging"""
    from codegen.simulation_debugger import SimulationDebugger

    debugger = SimulationDebugger()

    # Test input generation
    code = """
def add(a, b):
    return a + b
"""
    inputs = await debugger.generate_test_inputs(
        "Function that adds two numbers",
        code
    )
    assert len(inputs) > 0

    # Test simulation
    if inputs:
        result = await debugger.simulate_execution(code, inputs[0])
        assert result.simulated_output is not None


@pytest.mark.asyncio
async def test_simulation_debug_loop():
    """Test full simulation debug loop"""
    from codegen.simulation_debugger import SimulationDebugger

    debugger = SimulationDebugger()

    # Code with a bug (off-by-one)
    buggy_code = """
def factorial(n):
    if n <= 0:
        return 1
    result = 1
    for i in range(1, n):  # Bug: should be range(1, n+1)
        result *= i
    return result
"""
    fixed_code, results = await debugger.debug_with_simulation(
        "Calculate factorial of a number",
        buggy_code,
        max_iterations=2
    )

    assert len(results) > 0


@pytest.mark.asyncio
async def test_test_generator():
    """Test AgentCoder-style test generation"""
    from codegen.test_generator import TestGenerator

    generator = TestGenerator()

    code = """
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
"""
    tests = await generator.generate_tests(
        "Function to check if a number is prime",
        code
    )

    assert len(tests) > 0
    assert all(t.name.startswith('test_') for t in tests)


@pytest.mark.asyncio
async def test_readme_generator(mock_research_context):
    from codegen.readme_generator import ReadmeGenerator
    from dataclasses import dataclass, field
    from typing import List

    @dataclass
    class MockFileSpec:
        path: str
        description: str
        depends_on: List[str] = field(default_factory=list)

    @dataclass
    class MockCodePlan:
        files: List[MockFileSpec] = field(default_factory=list)
        dependencies: List[str] = field(default_factory=list)

    generator = ReadmeGenerator()
    readme = await generator.generate(
        "Create a REST API client",
        MockCodePlan(
            files=[MockFileSpec("src/main.py", "Main entry")],
            dependencies=["requests"]
        ),
        {"src/main.py": "print('hello')"},
        mock_research_context
    )

    assert readme is not None
    assert "README" in readme or "#" in readme  # Has markdown headers


@pytest.mark.asyncio
async def test_generate_repository(mock_research_context):
    from codegen import generate_repository

    files, metrics = await generate_repository(
        "Create a simple utility library",
        mock_research_context,
        use_simulation_debug=False,  # Faster for basic test
        use_auto_tests=False
    )

    assert "README.md" in files
    assert len(files) > 1
    assert "total_debug_iterations" in metrics


@pytest.mark.asyncio
async def test_generate_repository_with_simulation(mock_research_context):
    """Test full pipeline with simulation debugging enabled"""
    from codegen import generate_repository

    files, metrics = await generate_repository(
        "Create a calculator with add, subtract, multiply functions",
        mock_research_context,
        use_simulation_debug=True,
        use_auto_tests=True
    )

    assert "README.md" in files
    assert "simulation_results" in metrics
    assert "test_results" in metrics
```

**Run tests**:
```bash
cd projects/deep_code_research
pytest tests/test_codegen.py -v
```

---

## Dependencies

Add to your environment:

```bash
pip install openai pytest pytest-asyncio
```

---

## Checklist

- [ ] Read `contracts.py` from Agent 3
- [ ] Create `tests/test_codegen.py` FIRST
- [ ] Implement `CodePlanner`
- [ ] Implement `CodeGenerator`
- [ ] Implement `SelfDebugger` (basic)
- [ ] **NEW**: Implement `SimulationDebugger` (CODESIM pattern)
- [ ] **NEW**: Implement `TestGenerator` + `TestExecutor` (AgentCoder pattern)
- [ ] Implement `ReadmeGenerator`
- [ ] Implement `generate_repository()` main function
- [ ] All tests pass
- [ ] Ready for integration with Agent 3

---

## Testing Checklist (from Agent 4's Improvement Roadmap)

```
□ Task 3B: Simulation Debugger
  □ test_generate_test_inputs()
  □ test_simulate_execution()
  □ test_debug_with_simulation()

□ Task 3C: Test Generator
  □ test_generate_tests()
  □ test_run_tests()
  □ test_validate_and_prune()
```

---

## Integration Point

Agent 3 will call your code like this:

```python
from codegen import generate_repository

files, metrics = await generate_repository(
    prompt="Build a REST API client",
    research_context=research_context,  # From Agent 1
    use_simulation_debug=True,  # NEW: Enable CODESIM pattern
    use_auto_tests=True  # NEW: Enable AgentCoder pattern
)
# files = {"src/main.py": "...", "README.md": "...", ...}
# metrics = {"total_debug_iterations": 3, "simulation_results": [...], "test_results": [...]}
```

Make sure this interface works!
