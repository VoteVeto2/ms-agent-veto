# Agent 4: Improvement Specialist

## Role

You are responsible for **improving the DeepCodeResearch system** based on the latest 2025 research in Deep Research + Code Generation agents. Your mission is to bridge the gap between the current implementation and state-of-the-art approaches.

---

## API Configuration

Use this for all LLM calls:

```python
import os
os.environ["OPENAI_API_KEY"] = 
os.environ["OPENAI_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
os.environ["OPENAI_MODEL"] = "gemini-flash-lite-latest"
```

---

## Literature Review: State of the Art (December 2025)

### 1. Multi-Agent Code Generation Frameworks

| Framework | Architecture | Key Innovation | Performance | Source |
|-----------|--------------|----------------|-------------|--------|
| **CODESIM** | Planning + Coding + Debugging | Input-output simulation before execution | SOTA benchmarks | [Paper](https://huggingface.co/papers/2502.05664) |
| **CodeCoR** | Self-reflective multi-agent | Auto test generation + solution pruning | 77.8% pass@1 | [Survey](https://arxiv.org/html/2508.00083v1) |
| **AgentCoder** | Programmer + Test Designer + Executor | Iterative testing loop | 96.3% pass@1 | [Paper](https://arxiv.org/abs/2312.13010) |
| **MapCoder** | Recall + Plan + Generate + Debug | Example retrieval + planning | Competitive | [ACL 2024](https://aclanthology.org/2024.acl-long.269.pdf) |
| **SEIDR** | Synthesize → Execute → Debug → Repair | Near-miss syndrome handling | Balanced | [Survey](https://arxiv.org/html/2508.11126v1) |

**Key Insight**: Modern frameworks use **3-4 specialized agents** rather than monolithic approaches. Simulation-based debugging catches errors **before** actual execution.

### 2. RAG for Code Generation

| Approach | Innovation | Impact | Source |
|----------|------------|--------|--------|
| **CodeRAG** | Bigraph requirement-to-code mapping | +40% Pass@1 | [Paper](https://arxiv.org/html/2504.10046v1) |
| **AllianceCoder** | CoT decomposition + API semantic matching | +20% Pass@1 | [Paper](https://arxiv.org/abs/2503.20589) |
| **SELF-RAG** | Dynamic retrieval with reflection tokens | Retrieves only when needed | [Guide](https://www.promptingguide.ai/research/rag) |
| **Long RAG** | Section/document-level retrieval units | Better context | [Guide](https://www.edenai.co/post/the-2025-guide-to-retrieval-augmented-generation-rag) |

**Key Insight**: Retrieved similar code often introduces **noise (-15%)**. In-context code + API docs are more valuable than similar code snippets.

### 3. Memory & Context Management

| System | Innovation | Metrics | Source |
|--------|------------|---------|--------|
| **MemOS** | OS-like hierarchical memory | Model-defined management | [Paper](https://statics.memtensor.com.cn/files/MemOS_0707.pdf) |
| **Mem0** | Selective extraction + consolidation | 91% latency ↓, 90% tokens ↓ | [Research](https://mem0.ai/research) |
| **AWS AgentCore** | Human cognitive-inspired pipeline | Enterprise-scale | [Blog](https://aws.amazon.com/blogs/machine-learning/building-smarter-ai-agents-agentcore-long-term-memory-deep-dive/) |
| **JetBrains** | Observation masking + summarization | NeurIPS 2025 | [Blog](https://blog.jetbrains.com/research/2025/12/efficient-context-management/) |

**Key Insight**: Memory management is a **core research problem**, not an engineering detail. Context grows → models struggle.

### 4. Code Execution Sandboxes

| Tool | Features | Isolation Level | Source |
|------|----------|-----------------|--------|
| **Docker Sandboxes** | Official feature, workspace persistence | Container | [Blog](https://www.docker.com/blog/docker-sandboxes-a-new-approach-for-coding-agent-safety/) |
| **gVisor** | User-space kernel, syscall interception | Enhanced | [Guide](https://www.codeant.ai/blogs/agentic-rag-shell-sandboxing) |
| **AIO Sandbox** | Browser + Shell + File + MCP + VSCode | All-in-one | [GitHub](https://github.com/agent-infra/sandbox) |

**Key Insight**: Runtime security is critical. Build-time checks don't protect against execution-time attacks.

### 5. Notable Agent Architectures

| Agent | Key Features | Source |
|-------|--------------|--------|
| **OpenHands** | Event-driven, 50%+ GitHub issue resolution | [GitHub](https://github.com/OpenHands/OpenHands) |
| **Devin** | Multi-agent dispatch, self-confidence, Wiki | [Wikipedia](https://en.wikipedia.org/wiki/Devin_AI) |
| **DeepAgents** | Planning + filesystem + sub-agent spawning | [GitHub](https://github.com/langchain-ai/deepagents) |
| **AlphaEvolve** | Evolutionary coding, algorithm invention | [DeepMind](https://deepmind.google/blog/introducing-codemender-an-ai-agent-for-code-security/) |

---

## Gap Analysis: Current vs. State of Art

| Area | Current Implementation | State of Art (2025) | Gap | Priority |
|------|------------------------|---------------------|-----|----------|
| **Debugging** | Syntax validation (`compile()`) | Simulation-based I/O debugging | Large | 🔴 P1 |
| **Test Generation** | None | Auto test generation + execution | Large | 🔴 P1 |
| **Sub-agents** | Single agent per layer | Dynamic sub-agent spawning | Large | 🔴 P2 |
| **RAG Strategy** | Vector + BM25 hybrid | Requirement graph + adaptive retrieval | Medium | 🟡 P3 |
| **Memory** | Basic mem0 | Hierarchical (working/long-term/cold) | Medium | 🟡 P4 |
| **Confidence** | None | Self-assessed confidence scoring | Medium | 🟡 P5 |
| **Sandbox** | Basic Docker config | gVisor + network isolation | Low | 🟢 P6 |

---

## Implementation Tasks

### Task 1: Simulation-Based Debugging (CODESIM Pattern)

**Priority**: 🔴 P1 - High Impact
**Pattern**: CODESIM three-agent design
**File**: `codegen/simulation_debugger.py`

```python
"""
Simulation-Based Debugger - CODESIM Pattern

Simulates code execution on sample inputs BEFORE actual execution.
Catches logical errors early, reducing debug iterations.
"""

from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from openai import OpenAI
import ast
import traceback


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

**Integration Point**: Replace `SelfDebugger._validate_code()` with `SimulationDebugger.debug_with_simulation()`

---

### Task 2: Auto Test Generation (AgentCoder Pattern)

**Priority**: 🔴 P1 - High Impact
**Pattern**: AgentCoder test designer + executor
**File**: `codegen/test_generator.py`

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

**Integration Point**: Add to `generate_code_repository()` after code generation, before returning.

---

### Task 3: Adaptive RAG (CodeRAG + SELF-RAG Pattern)

**Priority**: 🟡 P3 - Medium Impact
**Pattern**: CodeRAG bigraph + SELF-RAG dynamic retrieval
**File**: `research/adaptive_rag.py`

```python
"""
Adaptive RAG - CodeRAG + SELF-RAG Pattern

Key improvements over basic RAG:
1. Requirement graph (not just vector similarity)
2. Dynamic retrieval (only when needed)
3. Filters out noisy similar code
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from openai import OpenAI


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


class RequirementGraphBuilder:
    """
    Build requirement graph from task description.

    CodeRAG insight: Map requirements to code, not just similar text.
    """

    def __init__(self):
        self.client = OpenAI()

    async def build_graph(self, task_description: str) -> List[Requirement]:
        """Parse task into structured requirements"""
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
"""
        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        reqs = self._parse_json(response.choices[0].message.content)
        return [Requirement(**r) for r in reqs]

    def _parse_json(self, text: str) -> List[Dict]:
        import json
        import re
        match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        try:
            return json.loads(text)
        except:
            return []


class AdaptiveRetriever:
    """
    SELF-RAG style adaptive retrieval.

    Key insight: Don't always retrieve. Check if retrieval is needed.
    """

    def __init__(self, rag_index):
        self.client = OpenAI()
        self.rag_index = rag_index

    async def should_retrieve(self, query: str, context: str) -> bool:
        """
        Determine if retrieval is needed (SELF-RAG reflection).

        Returns True if:
        - Query requires external knowledge
        - Current context is insufficient
        """
        prompt = f"""Determine if external retrieval is needed.

Query: {query}

Current Context:
{context[:1000]}

Answer with JSON:
{{"needs_retrieval": true/false, "reason": "..."}}

Retrieve if:
- Specific API details needed
- Implementation patterns unclear
- Domain knowledge required

Don't retrieve if:
- Context already sufficient
- Query is about general programming
- Similar code would just add noise
"""
        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        result = self._parse_json(response.choices[0].message.content)
        return result.get("needs_retrieval", True)

    async def retrieve_for_requirement(
        self,
        requirement: Requirement,
        filter_noise: bool = True
    ) -> List[CodeMapping]:
        """
        Retrieve code patterns for a specific requirement.

        AllianceCoder insight: API docs > similar code.
        """
        # Query for API/docs first (more valuable)
        api_query = f"API documentation for: {requirement.description}"
        api_results = self.rag_index.query(api_query) if self.rag_index else []

        # Query for patterns (filter carefully)
        pattern_query = f"Implementation pattern for: {requirement.description}"
        pattern_results = self.rag_index.query(pattern_query) if self.rag_index else []

        # Combine and filter
        mappings = []

        for r in api_results[:3]:  # API docs are valuable
            mappings.append(CodeMapping(
                requirement_id=requirement.id,
                code_pattern=str(r),
                confidence=0.9,
                source="api_doc"
            ))

        if not filter_noise:
            for r in pattern_results[:2]:  # Similar code may be noisy
                mappings.append(CodeMapping(
                    requirement_id=requirement.id,
                    code_pattern=str(r),
                    confidence=0.6,
                    source="similar_code"
                ))

        return mappings

    def _parse_json(self, text: str) -> Dict:
        import json
        import re
        match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        try:
            return json.loads(text)
        except:
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
```

**Integration Point**: Replace `RAGEngine` in `research/rag_engine.py` with `AdaptiveRAGEngine`.

---

### Task 4: Sub-Agent Manager (DeepAgents Pattern)

**Priority**: 🟡 P2 - High Impact
**Pattern**: DeepAgents sub-agent spawning
**File**: `core/sub_agent_manager.py`

```python
"""
Sub-Agent Manager - DeepAgents Pattern

Enables main agent to spawn specialized sub-agents for complex sub-tasks.
"""

from typing import Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio


class SubAgentType(Enum):
    """Types of specialized sub-agents"""
    RESEARCHER = "researcher"
    CODER = "coder"
    DEBUGGER = "debugger"
    TESTER = "tester"
    DOCUMENTER = "documenter"


@dataclass
class SubAgentTask:
    """A task to delegate to a sub-agent"""
    agent_type: SubAgentType
    task_description: str
    context: Dict[str, Any]
    timeout: int = 60


@dataclass
class SubAgentResult:
    """Result from a sub-agent"""
    agent_type: SubAgentType
    success: bool
    result: Any
    error: str = None


class SubAgentManager:
    """
    Manage spawning and coordination of sub-agents.

    DeepAgents pattern:
    - Main agent identifies sub-tasks
    - Spawns specialized agents
    - Collects and merges results
    """

    def __init__(self):
        self.client = OpenAI()
        self.active_agents: Dict[str, asyncio.Task] = {}

    async def spawn_agent(self, task: SubAgentTask) -> SubAgentResult:
        """Spawn a single sub-agent"""
        try:
            if task.agent_type == SubAgentType.RESEARCHER:
                result = await self._run_researcher(task)
            elif task.agent_type == SubAgentType.CODER:
                result = await self._run_coder(task)
            elif task.agent_type == SubAgentType.DEBUGGER:
                result = await self._run_debugger(task)
            elif task.agent_type == SubAgentType.TESTER:
                result = await self._run_tester(task)
            elif task.agent_type == SubAgentType.DOCUMENTER:
                result = await self._run_documenter(task)
            else:
                raise ValueError(f"Unknown agent type: {task.agent_type}")

            return SubAgentResult(
                agent_type=task.agent_type,
                success=True,
                result=result
            )
        except Exception as e:
            return SubAgentResult(
                agent_type=task.agent_type,
                success=False,
                result=None,
                error=str(e)
            )

    async def spawn_parallel(
        self,
        tasks: List[SubAgentTask]
    ) -> List[SubAgentResult]:
        """Spawn multiple sub-agents in parallel"""
        coroutines = [self.spawn_agent(task) for task in tasks]
        return await asyncio.gather(*coroutines)

    async def _run_researcher(self, task: SubAgentTask) -> Dict:
        """Research sub-agent"""
        prompt = f"""You are a research specialist. {task.task_description}

Context:
{task.context}

Provide detailed research findings in JSON format.
"""
        response = await self._call_llm(prompt)
        return {"research": response}

    async def _run_coder(self, task: SubAgentTask) -> str:
        """Coding sub-agent"""
        prompt = f"""You are a coding specialist. {task.task_description}

Context:
{task.context}

Output ONLY the code.
"""
        return await self._call_llm(prompt)

    async def _run_debugger(self, task: SubAgentTask) -> Dict:
        """Debugging sub-agent"""
        prompt = f"""You are a debugging specialist. {task.task_description}

Context:
{task.context}

Identify issues and provide fixes in JSON format:
{{"issues": [...], "fixes": [...]}}
"""
        response = await self._call_llm(prompt)
        return self._parse_json(response)

    async def _run_tester(self, task: SubAgentTask) -> str:
        """Testing sub-agent"""
        prompt = f"""You are a testing specialist. {task.task_description}

Context:
{task.context}

Generate comprehensive test code.
"""
        return await self._call_llm(prompt)

    async def _run_documenter(self, task: SubAgentTask) -> str:
        """Documentation sub-agent"""
        prompt = f"""You are a documentation specialist. {task.task_description}

Context:
{task.context}

Generate clear documentation.
"""
        return await self._call_llm(prompt)

    async def _call_llm(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content

    def _parse_json(self, text: str) -> Dict:
        import json
        import re
        match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        try:
            return json.loads(text)
        except:
            return {}
```

**Integration Point**: Add to `core/agent.py` as `self.sub_agent_manager`.

---

### Task 5: Hierarchical Memory (MemOS Pattern)

**Priority**: 🟡 P4 - Medium Impact
**Pattern**: MemOS layered architecture
**File**: `core/memory_hierarchy.py`

```python
"""
Hierarchical Memory - MemOS Pattern

Three-tier memory system:
1. Working Memory: Current task context
2. Long-Term Memory: Cross-session learnings
3. Cold Archive: Infrequent but valuable insights
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class MemoryItem:
    """A single memory item"""
    id: str
    content: Any
    importance: float  # 0-1
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    created: datetime = field(default_factory=datetime.now)


class WorkingMemory:
    """
    Short-term, high-access memory for current task.

    Characteristics:
    - Fast access
    - Limited capacity (context window)
    - Cleared between tasks
    """

    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.items: List[MemoryItem] = []

    def add(self, item: MemoryItem) -> None:
        """Add item, evicting oldest if at capacity"""
        if len(self.items) >= self.capacity:
            # Evict least recently accessed
            self.items.sort(key=lambda x: x.last_accessed)
            evicted = self.items.pop(0)
            return evicted  # Return for potential promotion
        self.items.append(item)
        return None

    def get(self, query: str) -> List[MemoryItem]:
        """Get relevant items (simple keyword match)"""
        results = []
        for item in self.items:
            if query.lower() in str(item.content).lower():
                item.access_count += 1
                item.last_accessed = datetime.now()
                results.append(item)
        return results

    def clear(self) -> List[MemoryItem]:
        """Clear and return all items"""
        items = self.items
        self.items = []
        return items


class LongTermMemory:
    """
    Persistent memory across sessions.

    Characteristics:
    - Selective storage (important items only)
    - Semantic retrieval
    - Promotes frequently accessed items
    """

    def __init__(self, storage_path: str = "./long_term_memory.json"):
        self.storage_path = storage_path
        self.items: Dict[str, MemoryItem] = {}
        self._load()

    def add(self, item: MemoryItem) -> None:
        """Add item if important enough"""
        if item.importance >= 0.5:  # Threshold
            self.items[item.id] = item
            self._save()

    def get(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        """Retrieve relevant items"""
        # Simple relevance scoring
        scored = []
        for item in self.items.values():
            if query.lower() in str(item.content).lower():
                score = item.importance * (1 + item.access_count * 0.1)
                scored.append((item, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for item, _ in scored[:top_k]:
            item.access_count += 1
            item.last_accessed = datetime.now()
            results.append(item)

        self._save()
        return results

    def promote_from_working(self, items: List[MemoryItem]) -> None:
        """Promote important items from working memory"""
        for item in items:
            if item.access_count >= 3 or item.importance >= 0.7:
                self.add(item)

    def _save(self) -> None:
        data = {
            id: {
                "id": item.id,
                "content": item.content,
                "importance": item.importance,
                "access_count": item.access_count,
                "last_accessed": item.last_accessed.isoformat(),
                "created": item.created.isoformat()
            }
            for id, item in self.items.items()
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f)

    def _load(self) -> None:
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            self.items = {
                id: MemoryItem(
                    id=d["id"],
                    content=d["content"],
                    importance=d["importance"],
                    access_count=d["access_count"],
                    last_accessed=datetime.fromisoformat(d["last_accessed"]),
                    created=datetime.fromisoformat(d["created"])
                )
                for id, d in data.items()
            }
        except FileNotFoundError:
            self.items = {}


class ColdArchive:
    """
    Archived memory for infrequent access.

    Characteristics:
    - Compressed storage
    - Slow retrieval
    - Preserves valuable but rarely needed info
    """

    def __init__(self, storage_path: str = "./cold_archive.json"):
        self.storage_path = storage_path
        self.items: Dict[str, MemoryItem] = {}
        self._load()

    def archive(self, item: MemoryItem) -> None:
        """Archive an item"""
        self.items[item.id] = item
        self._save()

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve specific item"""
        return self.items.get(item_id)

    def _save(self) -> None:
        # Similar to LongTermMemory._save()
        pass

    def _load(self) -> None:
        # Similar to LongTermMemory._load()
        pass


class HierarchicalMemoryManager:
    """
    Unified interface for hierarchical memory.

    Usage:
        memory = HierarchicalMemoryManager()
        memory.remember(content, importance=0.8)
        results = memory.recall("API authentication")
    """

    def __init__(self):
        self.working = WorkingMemory()
        self.long_term = LongTermMemory()
        self.archive = ColdArchive()

    def remember(self, content: Any, importance: float = 0.5) -> None:
        """Store a new memory"""
        import uuid
        item = MemoryItem(
            id=str(uuid.uuid4()),
            content=content,
            importance=importance
        )

        evicted = self.working.add(item)
        if evicted:
            self.long_term.promote_from_working([evicted])

    def recall(self, query: str) -> List[Any]:
        """Recall relevant memories"""
        results = []

        # Check working memory first (fastest)
        results.extend([i.content for i in self.working.get(query)])

        # Check long-term memory
        results.extend([i.content for i in self.long_term.get(query)])

        return results

    def end_task(self) -> None:
        """Called at end of task to promote memories"""
        working_items = self.working.clear()
        self.long_term.promote_from_working(working_items)
```

**Integration Point**: Replace basic memory in `core/agent.py` with `HierarchicalMemoryManager`.

---

### Task 6: Confidence Scorer (Devin Pattern)

**Priority**: 🟡 P5 - Medium Impact
**Pattern**: Devin self-assessment
**File**: `core/confidence_scorer.py`

```python
"""
Confidence Scorer - Devin Pattern

Self-assess confidence before outputting code.
Request clarification when confidence is low.
"""

from typing import Tuple, List
from dataclasses import dataclass
from openai import OpenAI


@dataclass
class ConfidenceScore:
    """Confidence assessment"""
    overall: float  # 0-1
    understanding: float  # Task understanding
    completeness: float  # Solution completeness
    correctness: float  # Likely correctness
    reasons: List[str]
    clarification_needed: List[str]


class ConfidenceScorer:
    """
    Devin-style confidence self-assessment.

    Before outputting code:
    1. Assess confidence in understanding
    2. Assess confidence in solution
    3. Request clarification if low confidence
    """

    def __init__(self, threshold: float = 0.7):
        self.client = OpenAI()
        self.threshold = threshold

    async def assess_confidence(
        self,
        task_description: str,
        generated_code: str,
        context: str = ""
    ) -> ConfidenceScore:
        """Assess confidence in generated code"""
        prompt = f"""Assess your confidence in this solution.

Task: {task_description}

Generated Code:
```python
{generated_code}
```

Context:
{context[:1000]}

Rate confidence (0-1) on:
1. understanding: Do you fully understand the task requirements?
2. completeness: Does the code address all requirements?
3. correctness: Is the code likely to work correctly?

Also identify:
- reasons: Why this confidence level?
- clarification_needed: What clarifications would help?

Output JSON:
{{
    "understanding": 0.8,
    "completeness": 0.7,
    "correctness": 0.6,
    "reasons": ["...", "..."],
    "clarification_needed": ["What format should the output be?"]
}}
"""
        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        result = self._parse_json(response.choices[0].message.content)

        understanding = result.get("understanding", 0.5)
        completeness = result.get("completeness", 0.5)
        correctness = result.get("correctness", 0.5)

        return ConfidenceScore(
            overall=(understanding + completeness + correctness) / 3,
            understanding=understanding,
            completeness=completeness,
            correctness=correctness,
            reasons=result.get("reasons", []),
            clarification_needed=result.get("clarification_needed", [])
        )

    async def should_proceed(
        self,
        score: ConfidenceScore
    ) -> Tuple[bool, List[str]]:
        """
        Determine if we should proceed or ask for clarification.

        Returns: (should_proceed, clarification_questions)
        """
        if score.overall >= self.threshold:
            return True, []
        else:
            return False, score.clarification_needed

    async def generate_clarification_request(
        self,
        questions: List[str]
    ) -> str:
        """Format clarification request for user"""
        if not questions:
            return ""

        request = "I have some questions before proceeding:\n\n"
        for i, q in enumerate(questions, 1):
            request += f"{i}. {q}\n"

        return request

    def _parse_json(self, text: str) -> dict:
        import json
        import re
        match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        try:
            return json.loads(text)
        except:
            return {}
```

**Integration Point**: Add to `generate_code()` before returning generated code.

---

## Integration Checklist

Update `contracts.py` with new interfaces:

```python
# Add to contracts.py

@dataclass
class SimulationResult:
    input_data: Any
    expected_output: Any
    simulated_output: Any
    is_correct: bool
    error: str = None

@dataclass
class TestCase:
    name: str
    input_code: str
    expected_behavior: str

@dataclass
class ConfidenceScore:
    overall: float
    understanding: float
    completeness: float
    correctness: float
    clarification_needed: List[str]
```

---

## Testing Checklist

```
□ Task 1: Simulation Debugger
  □ test_generate_test_inputs()
  □ test_simulate_execution()
  □ test_debug_with_simulation()

□ Task 2: Test Generator
  □ test_generate_tests()
  □ test_run_tests()
  □ test_validate_and_prune()

□ Task 3: Adaptive RAG
  □ test_build_requirement_graph()
  □ test_should_retrieve()
  □ test_retrieve_for_requirement()

□ Task 4: Sub-Agent Manager
  □ test_spawn_agent()
  □ test_spawn_parallel()
  □ test_agent_coordination()

□ Task 5: Hierarchical Memory
  □ test_working_memory()
  □ test_long_term_memory()
  □ test_memory_promotion()

□ Task 6: Confidence Scorer
  □ test_assess_confidence()
  □ test_should_proceed()
  □ test_clarification_request()
```

---

## Benchmark Comparisons

After implementing improvements, measure:

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Pass@1 | ~60% | | 80%+ |
| Debug iterations | ~5 | | <3 |
| Token usage | Baseline | | -50% |
| Latency | Baseline | | -30% |

---

## Sources

- [CODESIM Paper](https://huggingface.co/papers/2502.05664) - Simulation-based debugging
- [CodeRAG Paper](https://arxiv.org/html/2504.10046v1) - Requirement-to-code mapping
- [AI Agentic Programming Survey](https://arxiv.org/html/2508.11126v1) - Comprehensive 2025 survey
- [AgentCoder](https://arxiv.org/abs/2312.13010) - Test generation pattern
- [MemOS](https://statics.memtensor.com.cn/files/MemOS_0707.pdf) - Hierarchical memory
- [Mem0 Research](https://mem0.ai/research) - Memory optimization
- [OpenHands](https://github.com/OpenHands/OpenHands) - Event-driven agent architecture
- [Docker Sandboxes](https://www.docker.com/blog/docker-sandboxes-a-new-approach-for-coding-agent-safety/) - Sandbox best practices
- [JetBrains Context Management](https://blog.jetbrains.com/research/2025/12/efficient-context-management/) - Context optimization
- [DeepAgents](https://github.com/langchain-ai/deepagents) - Sub-agent pattern
