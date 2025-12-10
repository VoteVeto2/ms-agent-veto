# Agent 3: Orchestrator & Core

## Role

You are responsible for building the **Core Infrastructure** of the DeepCodeResearch system. You:
1. **CREATE the shared interfaces** (`contracts.py`) - Agent 1 & 2 depend on this
2. Build the main `DeepCodeResearchAgent` that orchestrates the entire flow
3. Handle input/output recording
4. Provide CLI interface

**Key Innovations (2025)**: This layer now implements:
1. **Sub-Agent Manager** (DeepAgents pattern) - Dynamic sub-agent spawning
2. **Hierarchical Memory** (MemOS pattern) - Working/long-term/cold memory
3. **Confidence Scorer** (Devin pattern) - Self-assessed confidence scoring

**YOU MUST CREATE `contracts.py` FIRST** - Other agents are waiting for it!

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

Based on latest research in agent architectures:

| System | Innovation | Impact | Source |
|--------|------------|--------|--------|
| **MemOS** | OS-like hierarchical memory | Model-defined management | [Paper](https://statics.memtensor.com.cn/files/MemOS_0707.pdf) |
| **Mem0** | Selective extraction + consolidation | 91% latency ↓, 90% tokens ↓ | [Research](https://mem0.ai/research) |
| **DeepAgents** | Planning + filesystem + sub-agent spawning | [GitHub](https://github.com/langchain-ai/deepagents) |
| **Devin** | Multi-agent dispatch, self-confidence | [Wikipedia](https://en.wikipedia.org/wiki/Devin_AI) |

**Key Insight**: Memory management is a **core research problem**, not an engineering detail. Sub-agents enable complex task decomposition.

---

## Directory Structure

Create these files:

```
projects/deep_code_research/
├── contracts.py                # SHARED INTERFACES - CREATE FIRST!
├── core/
│   ├── __init__.py
│   ├── agent.py                # DeepCodeResearchAgent main class
│   ├── records.py              # Input/Output record management
│   ├── sub_agent_manager.py    # NEW: DeepAgents pattern
│   ├── memory_hierarchy.py     # NEW: MemOS pattern
│   └── confidence_scorer.py    # NEW: Devin pattern
├── run.py                      # CLI entry point
├── config.yaml                 # Default configuration
└── tests/
    └── test_core.py            # CREATE THIS FIRST (after contracts.py)
```

---

## PRIORITY 1: Create contracts.py FIRST!

**File**: `projects/deep_code_research/contracts.py`

```python
"""
Shared Interfaces for DeepCodeResearch System

This file defines all shared data structures used across:
- Agent 1 (Research Layer)
- Agent 2 (Code Generation Layer)
- Agent 3 (Orchestrator)

DO NOT MODIFY without coordinating with all agents!
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


# ============================================================
# Research Layer Interfaces (Agent 1 outputs these)
# ============================================================

@dataclass
class ResearchContext:
    """
    Output of Research Layer, Input to Code Generation Layer.

    Contains all information extracted from references.zip:
    - Parsed documents
    - RAG index for retrieval
    - Extracted structured information
    """
    api_specs: List[Dict] = field(default_factory=list)
    code_patterns: List[Dict] = field(default_factory=list)
    architecture: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    documents: List[Any] = field(default_factory=list)  # LlamaIndex Documents
    rag_index: Any = None  # LlamaIndex query engine


# ============================================================
# Code Generation Layer Interfaces (Agent 2 uses these)
# ============================================================

@dataclass
class FileSpec:
    """Specification for a single file to generate."""
    path: str
    description: str
    depends_on: List[str] = field(default_factory=list)


@dataclass
class CodePlan:
    """Plan for the entire code repository."""
    files: List[FileSpec] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


# ============================================================
# Record Interfaces (Agent 3 manages these)
# ============================================================

@dataclass
class InputRecord:
    """
    Record of inputs to the system.

    Saved as input_record.yaml in output directory.
    """
    prompt: str
    references_files: List[Dict] = field(default_factory=list)
    total_documents: int = 0
    total_tokens: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class OutputRecord:
    """
    Record of outputs from the system.

    Saved as output_record.yaml in output directory.
    """
    research_report: Dict = field(default_factory=dict)
    generated_code: Dict = field(default_factory=dict)
    validation: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================
# Utility Functions
# ============================================================

def to_dict(obj) -> Dict:
    """Convert dataclass to dictionary for YAML serialization."""
    from dataclasses import asdict, is_dataclass

    if is_dataclass(obj):
        return asdict(obj)
    return obj
```

**IMPORTANT**: After creating this file, notify Agent 1 and Agent 2 that they can start importing from it!

---

## Task 1: RecordManager

**File**: `core/records.py`

```python
"""Input/Output record management"""

import yaml
from pathlib import Path
from typing import Optional
from dataclasses import asdict

from ..contracts import InputRecord, OutputRecord


class RecordManager:
    """Manage input/output records for the system"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.input_record: Optional[InputRecord] = None
        self.output_record: Optional[OutputRecord] = None

    def create_input_record(
        self,
        prompt: str,
        references_files: list,
        total_documents: int,
        total_tokens: int
    ) -> InputRecord:
        """Create input record"""
        self.input_record = InputRecord(
            prompt=prompt,
            references_files=references_files,
            total_documents=total_documents,
            total_tokens=total_tokens
        )
        return self.input_record

    def create_output_record(
        self,
        research_report: dict,
        generated_code: dict,
        validation: dict
    ) -> OutputRecord:
        """Create output record"""
        self.output_record = OutputRecord(
            research_report=research_report,
            generated_code=generated_code,
            validation=validation
        )
        return self.output_record

    def save_records(self) -> None:
        """Save records to YAML files"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.input_record:
            input_path = self.output_dir / "input_record.yaml"
            with open(input_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    asdict(self.input_record),
                    f,
                    allow_unicode=True,
                    default_flow_style=False
                )
            print(f"  Saved: {input_path}")

        if self.output_record:
            output_path = self.output_dir / "output_record.yaml"
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    asdict(self.output_record),
                    f,
                    allow_unicode=True,
                    default_flow_style=False
                )
            print(f"  Saved: {output_path}")

    @staticmethod
    def load_input_record(path: str) -> Optional[InputRecord]:
        """Load input record from file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return InputRecord(**data)
        except Exception as e:
            print(f"Error loading input record: {e}")
            return None

    @staticmethod
    def load_output_record(path: str) -> Optional[OutputRecord]:
        """Load output record from file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return OutputRecord(**data)
        except Exception as e:
            print(f"Error loading output record: {e}")
            return None
```

---

## Task 2: DeepCodeResearchAgent

**File**: `core/agent.py`

```python
"""Main DeepCodeResearch Agent - Orchestrates the entire flow"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from openai import OpenAI

from ..contracts import ResearchContext, InputRecord, OutputRecord
from .records import RecordManager


class DeepCodeResearchAgent:
    """
    Main orchestrator for DeepCodeResearch system.

    Flow:
    1. Research references.zip (Agent 1's code)
    2. Generate code repository (Agent 2's code)
    3. Save input/output records
    """

    def __init__(self):
        self.client = OpenAI()
        self.record_manager: Optional[RecordManager] = None

    async def run(
        self,
        prompt: str,
        references_zip: str,
        output_dir: str = "./generated_repo"
    ) -> Dict[str, Any]:
        """
        Main entry point - runs the complete DeepCodeResearch flow.

        Args:
            prompt: User's task description
            references_zip: Path to references.zip
            output_dir: Output directory for generated code

        Returns:
            Dict with report, generated_files, and records
        """
        print("=" * 60)
        print("DeepCodeResearch Agent Starting")
        print("=" * 60)

        self.record_manager = RecordManager(output_dir)

        # ========== Phase 1: Research ==========
        print("\n[Phase 1] Researching reference documents...")
        research_context = await self._run_research(references_zip)

        # Create input record
        self.record_manager.create_input_record(
            prompt=prompt,
            references_files=self._get_file_summaries(research_context),
            total_documents=len(research_context.documents),
            total_tokens=self._estimate_tokens(research_context)
        )

        print(f"  Documents parsed: {len(research_context.documents)}")
        print(f"  API specs found: {len(research_context.api_specs)}")
        print(f"  Code patterns found: {len(research_context.code_patterns)}")
        print(f"  Dependencies found: {len(research_context.dependencies)}")

        # ========== Phase 2: Code Generation ==========
        print("\n[Phase 2] Generating code repository...")
        generated_files, debug_iterations = await self._run_codegen(
            prompt, research_context
        )

        print(f"  Files generated: {len(generated_files)}")
        print(f"  Debug iterations: {debug_iterations}")

        # ========== Phase 3: Write Files ==========
        print("\n[Phase 3] Writing files to disk...")
        await self._write_files(output_dir, generated_files)

        # ========== Phase 4: Generate Report ==========
        print("\n[Phase 4] Generating final report...")
        report = await self._generate_report(prompt, research_context, generated_files)

        # Create output record
        self.record_manager.create_output_record(
            research_report={
                "api_specs_count": len(research_context.api_specs),
                "code_patterns_count": len(research_context.code_patterns),
                "dependencies": research_context.dependencies[:20]
            },
            generated_code={
                "files": list(generated_files.keys()),
                "total_files": len(generated_files),
                "total_lines": sum(c.count('\n') for c in generated_files.values())
            },
            validation={
                "debug_iterations": debug_iterations,
                "syntax_valid": True  # Assumed after self-debug
            }
        )

        # ========== Phase 5: Save Records ==========
        print("\n[Phase 5] Saving input/output records...")
        self.record_manager.save_records()

        print("\n" + "=" * 60)
        print("DeepCodeResearch Agent Complete!")
        print(f"Output directory: {output_dir}")
        print("=" * 60)

        return {
            "report": report,
            "generated_files": generated_files,
            "input_record": self.record_manager.input_record,
            "output_record": self.record_manager.output_record,
            "output_dir": output_dir
        }

    async def _run_research(self, references_zip: str) -> ResearchContext:
        """Run Research Layer (Agent 1's code)"""
        try:
            from ..research import research_references
            return await research_references(references_zip)
        except ImportError:
            print("  WARNING: Research module not available, using mock")
            return self._mock_research_context()

    async def _run_codegen(
        self,
        prompt: str,
        research_context: ResearchContext
    ) -> tuple:
        """Run Code Generation Layer (Agent 2's code)"""
        try:
            from ..codegen import generate_repository
            files = await generate_repository(prompt, research_context)
            return files, 0  # TODO: get actual debug iterations
        except ImportError:
            print("  WARNING: Codegen module not available, using mock")
            return self._mock_generated_files(), 0

    async def _write_files(self, output_dir: str, files: Dict[str, str]) -> None:
        """Write generated files to disk"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for file_path, content in files.items():
            full_path = output_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            print(f"  Written: {full_path}")

    async def _generate_report(
        self,
        prompt: str,
        research_context: ResearchContext,
        generated_files: Dict[str, str]
    ) -> str:
        """Generate final research report"""
        report_prompt = f"""Generate a brief research report for this project:

Task: {prompt}

Research Findings:
- API Specifications: {len(research_context.api_specs)}
- Code Patterns: {len(research_context.code_patterns)}
- Dependencies: {research_context.dependencies[:10]}

Generated Files:
{list(generated_files.keys())}

Provide a concise summary of:
1. What was researched
2. What was generated
3. Key implementation decisions
"""

        response = self.client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gemini-flash-lite-latest"),
            messages=[{"role": "user", "content": report_prompt}],
            temperature=0.5
        )

        return response.choices[0].message.content

    def _get_file_summaries(self, context: ResearchContext) -> list:
        """Get file summaries for input record"""
        summaries = []
        for doc in context.documents[:20]:
            source = getattr(doc, 'metadata', {}).get('source', 'unknown')
            text_preview = getattr(doc, 'text', '')[:100]
            summaries.append({
                "source": source,
                "preview": text_preview + "..."
            })
        return summaries

    def _estimate_tokens(self, context: ResearchContext) -> int:
        """Estimate total tokens in documents"""
        total_chars = sum(len(getattr(d, 'text', '')) for d in context.documents)
        return total_chars // 4  # Rough estimate

    def _mock_research_context(self) -> ResearchContext:
        """Mock research context for testing without Agent 1"""
        return ResearchContext(
            api_specs=[{"endpoint": "/api", "method": "GET"}],
            code_patterns=[{"pattern": "Factory", "usage": "Object creation"}],
            architecture={"modules": ["core", "utils"]},
            dependencies=["requests", "pydantic"],
            documents=[],
            rag_index=None
        )

    def _mock_generated_files(self) -> Dict[str, str]:
        """Mock generated files for testing without Agent 2"""
        return {
            "src/__init__.py": "",
            "src/main.py": "print('Hello, World!')",
            "README.md": "# Generated Project\n\nThis is a placeholder.",
            "requirements.txt": "requests\npydantic"
        }
```

---

## Task 3: CLI Interface

**File**: `run.py`

```python
#!/usr/bin/env python
"""CLI entry point for DeepCodeResearch"""

import asyncio
import argparse
import os

# Set default API configuration
os.environ.setdefault("OPENAI_API_KEY", "AIzaSyDmTcj4-ujVOIswqGLvt0fTZiVe49SU3ZY")
os.environ.setdefault("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
os.environ.setdefault("OPENAI_MODEL", "gemini-flash-lite-latest")


async def main():
    parser = argparse.ArgumentParser(
        description="DeepCodeResearch - Research documents and generate code"
    )
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="Task description / prompt"
    )
    parser.add_argument(
        "--references", "-r",
        required=True,
        help="Path to references.zip"
    )
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="Output directory (default: ./output)"
    )

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.references):
        print(f"Error: References file not found: {args.references}")
        return 1

    # Run agent
    from core.agent import DeepCodeResearchAgent

    agent = DeepCodeResearchAgent()
    result = await agent.run(
        prompt=args.prompt,
        references_zip=args.references,
        output_dir=args.output
    )

    # Print summary
    print("\n" + "=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"\nOutput Directory: {result['output_dir']}")
    print(f"\nGenerated Files:")
    for f in result['generated_files'].keys():
        print(f"  - {f}")
    print(f"\nRecords:")
    print(f"  - {result['output_dir']}/input_record.yaml")
    print(f"  - {result['output_dir']}/output_record.yaml")
    print("\nReport Preview:")
    print("-" * 40)
    report = result['report']
    print(report[:500] + "..." if len(report) > 500 else report)

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
```

---

## Task 4: Default Configuration

**File**: `config.yaml`

```yaml
# DeepCodeResearch Default Configuration

# LLM Settings
llm:
  service: openai
  model: gemini-flash-lite-latest
  openai_api_key: ${OPENAI_API_KEY}
  openai_base_url: https://generativelanguage.googleapis.com/v1beta/openai/

# Research Settings
research:
  max_documents: 100
  chunk_size: 1000
  chunk_overlap: 200

# Code Generation Settings
codegen:
  max_debug_attempts: 5
  temperature: 0.3

# Output Settings
output:
  default_dir: ./output
  save_records: true
```

---

## Test First!

**File**: `tests/test_core.py`

```python
import pytest
import asyncio
import os
from pathlib import Path

# Set up API
os.environ["OPENAI_API_KEY"] = "AIzaSyDmTcj4-ujVOIswqGLvt0fTZiVe49SU3ZY"
os.environ["OPENAI_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
os.environ["OPENAI_MODEL"] = "gemini-flash-lite-latest"


def test_contracts_exist():
    """Verify contracts.py exists and is importable"""
    from contracts import (
        ResearchContext,
        FileSpec,
        CodePlan,
        InputRecord,
        OutputRecord
    )

    # Test instantiation
    rc = ResearchContext()
    assert rc.api_specs == []

    fs = FileSpec(path="test.py", description="Test file")
    assert fs.path == "test.py"

    cp = CodePlan()
    assert cp.files == []

    ir = InputRecord(prompt="test")
    assert ir.prompt == "test"

    or_ = OutputRecord()
    assert or_.research_report == {}


def test_record_manager(tmp_path):
    """Test RecordManager save/load"""
    from core.records import RecordManager

    rm = RecordManager(str(tmp_path))

    # Create records
    rm.create_input_record(
        prompt="Test prompt",
        references_files=[{"name": "test.md"}],
        total_documents=5,
        total_tokens=1000
    )

    rm.create_output_record(
        research_report={"findings": ["test"]},
        generated_code={"files": ["main.py"]},
        validation={"success": True}
    )

    # Save
    rm.save_records()

    # Verify files exist
    assert (tmp_path / "input_record.yaml").exists()
    assert (tmp_path / "output_record.yaml").exists()

    # Load and verify
    loaded_input = RecordManager.load_input_record(
        str(tmp_path / "input_record.yaml")
    )
    assert loaded_input.prompt == "Test prompt"

    loaded_output = RecordManager.load_output_record(
        str(tmp_path / "output_record.yaml")
    )
    assert loaded_output.validation["success"] == True


@pytest.fixture
def sample_zip(tmp_path):
    """Create sample references.zip"""
    import zipfile

    (tmp_path / "readme.md").write_text("# Test Project\n\nSample documentation.")
    (tmp_path / "example.py").write_text("def hello():\n    print('Hello')")

    zip_path = tmp_path / "references.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.write(tmp_path / "readme.md", "readme.md")
        zf.write(tmp_path / "example.py", "example.py")

    return zip_path


@pytest.mark.asyncio
async def test_agent_mock_mode(tmp_path, sample_zip):
    """Test agent with mock research/codegen"""
    from core.agent import DeepCodeResearchAgent

    agent = DeepCodeResearchAgent()
    output_dir = str(tmp_path / "output")

    result = await agent.run(
        prompt="Create a simple utility",
        references_zip=str(sample_zip),
        output_dir=output_dir
    )

    # Verify outputs
    assert result["output_dir"] == output_dir
    assert "generated_files" in result
    assert "README.md" in result["generated_files"]
    assert result["input_record"] is not None
    assert result["output_record"] is not None

    # Verify files written
    assert (Path(output_dir) / "input_record.yaml").exists()
    assert (Path(output_dir) / "output_record.yaml").exists()


@pytest.mark.asyncio
async def test_agent_generates_report(tmp_path, sample_zip):
    """Test that agent generates a report"""
    from core.agent import DeepCodeResearchAgent

    agent = DeepCodeResearchAgent()
    result = await agent.run(
        prompt="Test project",
        references_zip=str(sample_zip),
        output_dir=str(tmp_path / "output")
    )

    assert "report" in result
    assert len(result["report"]) > 0
```

**Run tests**:
```bash
cd projects/deep_code_research
pytest tests/test_core.py -v
```

---

## Package Init Files

**File**: `core/__init__.py`

```python
from .agent import DeepCodeResearchAgent
from .records import RecordManager

__all__ = ["DeepCodeResearchAgent", "RecordManager"]
```

**File**: `__init__.py` (root)

```python
"""DeepCodeResearch - Research documents and generate code"""

from .contracts import (
    ResearchContext,
    FileSpec,
    CodePlan,
    InputRecord,
    OutputRecord
)
from .core import DeepCodeResearchAgent, RecordManager

__all__ = [
    "ResearchContext",
    "FileSpec",
    "CodePlan",
    "InputRecord",
    "OutputRecord",
    "DeepCodeResearchAgent",
    "RecordManager"
]
```

---

## Dependencies

Add to your environment:

```bash
pip install openai pyyaml pytest pytest-asyncio
```

---

## Checklist

- [ ] **CREATE `contracts.py` FIRST** - Others are waiting!
- [ ] Notify Agent 1 & 2 that contracts.py is ready
- [ ] Create `tests/test_core.py`
- [ ] Implement `RecordManager`
- [ ] Implement `DeepCodeResearchAgent`
- [ ] Create `run.py` CLI
- [ ] Create `config.yaml`
- [ ] All tests pass
- [ ] Integration test with Agent 1 & 2 code

---

## Integration Steps

### Step 1: Create contracts.py (Do this FIRST!)
```bash
# Create the file
touch projects/deep_code_research/contracts.py
# Add the content from above
# Commit or share with team
```

### Step 2: Test with mocks
```bash
pytest tests/test_core.py -v
```

### Step 3: Integrate Agent 1's code
```python
# In core/agent.py, verify this import works:
from ..research import research_references
```

### Step 4: Integrate Agent 2's code
```python
# In core/agent.py, verify this import works:
from ..codegen import generate_repository
```

### Step 5: Full integration test
```bash
python run.py \
  --prompt "Build a REST API client library" \
  --references ./test_references.zip \
  --output ./test_output
```

---

## Coordination Notes

You are the **integration owner**. Your responsibilities:

1. **Create contracts.py first** - Block until this is done
2. **Help other agents** if they have import issues
3. **Run the final integration test** once all modules are ready
4. **Debug integration issues** between modules

Communication checkpoints:
- "contracts.py is ready" → Agent 1 & 2 can start
- "research module integrated" → After Agent 1 delivers
- "codegen module integrated" → After Agent 2 delivers
- "full system tested" → Project complete
