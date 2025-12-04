# MS-Agent DeepCodeResearch Onboarding Guide

> **项目目标**：基于 MS-Agent 框架构建 DeepCodeResearch Agent - 一个能够自主进行深度研究并生成代码的智能代理系统

## 📚 目录

- [项目概述](#项目概述)
- [框架架构分析](#框架架构分析)
- [核心模块详解](#核心模块详解)
- [一周开发计划](#一周开发计划)
- [技术选型建议](#技术选型建议)
- [快速开始](#快速开始)
- [评分策略](#评分策略)
- [参考资源](#参考资源)

---

## 项目概述

### MS-Agent 框架简介

MS-Agent 是阿里巴巴 ModelScope 团队开发的轻量级 Agent 框架，专为赋予智能代理自主探索能力而设计。

**核心特性：**
- 🤖 **Multi-Agent 通用能力**：支持基于 MCP 协议的工具调用
- 🔍 **Deep Research**：自主探索和复杂任务执行
- 💻 **Code Generation**：支持代码生成任务
- 🎬 **Video Generation**：支持短视频生成
- 🧠 **Agent Skills**：实现 Anthropic Agent Skills 协议
- 🔧 **轻量可扩展**：易于扩展和定制

### 现有项目参考

| 项目 | 功能 | 位置 |
|------|------|------|
| **Deep Research** | 多模态深度研究框架 | `projects/deep_research/` |
| **Doc Research** | 文档分析研究 | `projects/doc_research/` |
| **Code Scratch** | 代码项目生成 | `projects/code_genesis/` |
| **Agent Skills** | Anthropic Skills 协议实现 | `projects/agent_skills/` |
| **Fin Research** | 金融研究多代理工作流 | `projects/fin_research/` |
| **Singularity Cinema** | 短视频生成 | `projects/singularity_cinema/` |

---

## 框架架构分析

### 目录结构

```
ms_agent/
├── agent/              # Agent 核心实现
│   ├── base.py         # Agent 基类（所有 Agent 继承此类）
│   ├── llm_agent.py    # LLM Agent 实现（主要使用）
│   ├── agent_skill.py  # Agent Skills 实现
│   ├── code_agent.py   # 代码 Agent
│   ├── loader.py       # Agent 加载器
│   └── runtime.py      # 运行时环境
│
├── workflow/           # 工作流模块
│   ├── base.py         # Workflow 基类
│   ├── chain_workflow.py  # 链式工作流
│   ├── dag_workflow.py    # DAG 工作流（支持并行）
│   ├── loader.py       # 工作流加载器
│   └── deep_research/  # 深度研究工作流实现
│
├── tools/              # 工具模块
│   ├── base.py         # Tool 基类
│   ├── mcp_client.py   # MCP 客户端（核心）
│   ├── tool_manager.py # 工具管理器
│   ├── search/         # 搜索工具
│   ├── code/           # 代码执行工具
│   ├── docling/        # 文档解析
│   ├── exa/            # Exa 搜索
│   └── findata/        # 金融数据
│
├── memory/             # 记忆模块
│   ├── base.py         # Memory 基类
│   ├── default_memory.py  # 默认记忆实现（基于 mem0）
│   └── memory_manager.py  # 记忆管理器
│
├── callbacks/          # 回调钩子系统
│   ├── base.py         # Callback 基类
│   └── input_callback.py  # 输入回调
│
├── llm/                # LLM 接口
├── rag/                # RAG 检索增强生成
├── skill/              # Agent Skills
├── sandbox/            # 沙箱执行环境
├── config/             # 配置管理
│   ├── config.py       # 配置加载与生命周期
│   └── env.py          # 环境变量管理
│
├── cli/                # 命令行工具
├── app/                # 应用入口
└── utils/              # 工具函数
```

---

## 核心模块详解

### 1. Agent 基类 (`ms_agent/agent/base.py`)

所有 Agent 必须继承此基类：

```python
class Agent(ABC):
    """Base class for all agents."""
    
    def __init__(self, config: DictConfig, tag: str, trust_remote_code: bool = False):
        self.config = config
        self.tag = tag
        self.trust_remote_code = trust_remote_code
    
    @abstractmethod
    async def run(self, inputs: Union[str, List[Message]], **kwargs) -> List[Message]:
        """Main method to execute the agent."""
        raise NotImplementedError()
    
    def next_flow(self, idx: int) -> int:
        """Used in workflow, decide which agent goes next."""
        return idx + 1
```

**关键点：**
- 必须实现 `run()` 方法
- 支持异步执行
- `next_flow()` 用于工作流控制

### 2. LLMAgent (`ms_agent/agent/llm_agent.py`)

主要使用的 Agent 实现，提供完整的 LLM 交互生命周期：

```python
class LLMAgent(Agent):
    """Agent with LLM, tools, memory, planning, and callbacks support."""
    
    # 关键组件
    callbacks: List[Callback]       # 回调钩子
    tool_manager: ToolManager       # 工具管理
    memory_tools: List[Memory]      # 记忆工具
    rag: RAG                        # RAG 组件
    llm: LLM                        # LLM 模型
    runtime: Runtime                # 运行时
```

**生命周期钩子：**
1. `on_task_begin` - 任务开始
2. `on_generate_response` - LLM 生成响应前
3. `on_tool_call` - 工具调用前
4. `after_tool_call` - 工具调用后
5. `on_task_end` - 任务结束

### 3. Workflow 基类 (`ms_agent/workflow/base.py`)

工作流定义：

```python
class Workflow(ABC):
    """Base class for workflows that define agent processing steps."""
    
    def __init__(self, config_dir_or_id: str, trust_remote_code: bool = False, **kwargs):
        self.config = Config.from_task(config_dir_or_id)
        self.workflow_chains = []
        self.build_workflow()
    
    @abstractmethod
    def build_workflow(self):
        """Build the execution chain based on configuration."""
        pass
    
    @abstractmethod
    async def run(self, inputs, **kwargs):
        """Execute the workflow."""
        pass
```

### 4. DAG Workflow (`ms_agent/workflow/dag_workflow.py`)

支持 DAG（有向无环图）执行的工作流：

```python
class DagWorkflow(Workflow):
    """Workflow supporting multiple `next` tasks (DAG) with dynamic execution."""
    
    # 支持并行任务执行
    # 自动拓扑排序
    # 多输入聚合
```

**配置示例 (`workflow.yaml`)：**
```yaml
type: DagWorkflow

orchestrator:
  next:
    - collector
    - searcher
  agent_config: orchestrator.yaml

collector:
  next:
    - analyst
  agent_config: collector.yaml

analyst:
  next:
    - aggregator
  agent_config: analyst.yaml

aggregator:
  agent_config: aggregator.yaml
```

### 5. Tool 基类 (`ms_agent/tools/base.py`)

工具接口定义：

```python
class ToolBase:
    """Base class for all tools."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect the tool."""
        pass
    
    async def get_tools(self) -> Dict[str, Any]:
        """List available tools."""
        pass
    
    @abstractmethod
    async def call_tool(self, server_name: str, tool_name: str, tool_args: dict) -> str:
        """Call a tool."""
        pass
```

### 6. MCP Client (`ms_agent/tools/mcp_client.py`)

核心的 MCP 协议客户端：

```python
class MCPClient(ToolBase):
    """MCP client for managing multiple MCP servers."""
    
    # 支持多种传输方式：
    # - stdio: 标准输入输出
    # - sse: Server-Sent Events
    # - streamable_http: HTTP 流式传输
    # - websocket: WebSocket
```

**MCP 配置示例：**
```python
mcp = {
    "mcpServers": {
        "fetch": {
            "type": "streamable_http",
            "url": "https://mcp.api-inference.modelscope.net/{uuid}/mcp"
        },
        "search": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-search-server"],
            "env": {"API_KEY": "$SEARCH_API_KEY"}
        }
    }
}
```

### 7. Memory 基类 (`ms_agent/memory/base.py`)

记忆接口：

```python
class Memory(ABC):
    """Memory refinement tool."""
    
    @abstractmethod
    async def run(self, messages: List[Message]) -> List[Message]:
        """Refine the messages."""
        pass
```

### 8. Callback 系统 (`ms_agent/callbacks/base.py`)

回调钩子系统：

```python
class Callback:
    """Callback hooks for agent lifecycle."""
    
    async def on_task_begin(self, runtime: Runtime, messages: List[Message]) -> None:
        pass
    
    async def on_generate_response(self, runtime: Runtime, messages: List[Message]):
        pass
    
    async def on_tool_call(self, runtime: Runtime, messages: List[Message]):
        pass
    
    async def after_tool_call(self, runtime: Runtime, messages: List[Message]):
        pass
    
    async def on_task_end(self, runtime: Runtime, messages: List[Message]):
        pass
```

### 9. Config 系统 (`ms_agent/config/config.py`)

配置生命周期管理：

```python
class ConfigLifecycleHandler:
    """Handler for config modifications during task lifecycle."""
    
    def task_begin(self, config: DictConfig, tag: str) -> DictConfig:
        """Modify config when task begins."""
        return config
    
    def task_end(self, config: DictConfig, tag: str) -> DictConfig:
        """Modify config when task ends."""
        return config
```

---

## 一周开发计划

### Day 1：研究与架构设计（架构分30%）

#### 上午：深度研究
- [x] 研读 MS-Agent 框架源码结构
  - `ms_agent/agent/` - Agent 实现
  - `ms_agent/workflow/` - 工作流
  - `ms_agent/tools/` - 工具系统
  - `ms_agent/memory/` - 记忆系统
- [ ] 研究 MCP（Model Context Protocol）规范
- [ ] 调研现有 Deep Research 实现（`projects/deep_research/`）

#### 下午：架构设计文档
设计 DeepCodeResearch 四阶段架构：

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Planner   │ ──> │  Researcher │ ──> │    Coder    │ ──> │   Debugger  │
│ (任务规划)   │     │  (信息收集)  │     │  (代码生成)  │     │  (调试修复)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**模块分层设计：**
```
deepcode_research/
├── core/                   # 核心模块
│   ├── workflow.py         # DAG 工作流编排
│   └── state.py            # 状态管理
│
├── agents/                 # Agent 实现
│   ├── planner.py          # 任务规划 Agent
│   ├── researcher.py       # 研究收集 Agent
│   ├── coder.py            # 代码生成 Agent
│   └── debugger.py         # 调试修复 Agent
│
├── tools/                  # 工具集成
│   ├── web_search.py       # Web 搜索
│   ├── doc_parser.py       # 文档解析
│   └── code_executor.py    # 代码执行
│
├── memory/                 # 记忆系统
│   ├── short_term.py       # 短期记忆（会话）
│   └── long_term.py        # 长期记忆（向量存储）
│
├── mcp/                    # MCP 适配
│   └── servers.py          # MCP Server 适配器
│
└── config/                 # 配置文件
    ├── workflow.yaml       # 工作流配置
    └── *.yaml              # 各 Agent 配置
```

### Day 2：核心数据结构与基础模块

#### 上午：定义核心接口

```python
# agents/base.py
from ms_agent.agent.base import Agent
from ms_agent.callbacks.base import Callback

class ResearchAgent(Agent):
    """研究型 Agent 基类"""
    
    async def research(self, query: str) -> ResearchResult:
        """执行研究任务"""
        pass

class CodeAgent(Agent):
    """代码生成 Agent 基类"""
    
    async def generate(self, spec: CodeSpec) -> CodeResult:
        """生成代码"""
        pass

# hooks/lifecycle.py
class ResearchHooks(Callback):
    """研究生命周期钩子"""
    
    async def on_research_start(self, runtime, query):
        pass
    
    async def on_source_found(self, runtime, source):
        pass
    
    async def on_research_complete(self, runtime, result):
        pass
```

#### 下午：多模态文档解析

参考 `ms_agent/rag/extraction.py` 和 `projects/deep_research/`：

```python
# tools/doc_parser.py
from ms_agent.rag.extraction import ExtractionManager

class MultimodalDocParser:
    """多模态文档解析器"""
    
    async def parse_pdf(self, file_path: str) -> Document:
        """解析 PDF 文档"""
        pass
    
    async def parse_image(self, image_path: str) -> ImageAnalysis:
        """解析图片（架构图/流程图）"""
        pass
    
    async def build_rag_index(self, documents: List[Document]):
        """构建 RAG 索引"""
        pass
```

### Day 3-4：核心 Workflow 实现（代码实现分50%）

#### Day 3：Deep Research 模块

参考 `ms_agent/workflow/deep_research/research_workflow.py`：

```python
# core/research_workflow.py
from ms_agent.workflow.deep_research.research_workflow import ResearchWorkflow

class DeepCodeResearch(ResearchWorkflow):
    """深度代码研究工作流"""
    
    async def run(self, user_prompt: str):
        # 1. 生成搜索查询
        queries = await self.generate_search_queries(user_prompt)
        
        # 2. Web 搜索与信息提取
        sources = await self.search_and_extract(queries)
        
        # 3. 文档深度理解
        learnings = await self.extract_learnings(sources)
        
        # 4. 技术点提取
        tech_points = await self.extract_tech_points(learnings)
        
        return ResearchResult(learnings=learnings, tech_points=tech_points)
```

#### Day 4：Code Generation 模块

参考 `projects/code_genesis/`：

```python
# core/code_workflow.py
from ms_agent.workflow.dag_workflow import DagWorkflow

class CodeGenerationWorkflow(DagWorkflow):
    """代码生成工作流"""
    
    async def design_phase(self, research_result: ResearchResult):
        """设计阶段：PRD → 模块设计 → 任务分解"""
        pass
    
    async def coding_phase(self, design: Design):
        """编码阶段：按文件组生成代码"""
        pass
    
    async def refine_phase(self, code_result: CodeResult):
        """精炼阶段：编译 → 错误分析 → 修复"""
        pass
```

**Self-Debugging Loop：**
```python
async def self_debug_loop(self, code: str, max_retries: int = 3):
    """自我调试循环"""
    for attempt in range(max_retries):
        # 1. 执行代码
        result = await self.execute(code)
        
        if result.success:
            return code
        
        # 2. 分析错误
        analysis = await self.analyze_error(result.error)
        
        # 3. 修复代码
        code = await self.fix_code(code, analysis)
    
    return code
```

### Day 5：工具集成与 MCP 适配

```python
# mcp/servers.py
from ms_agent.tools.mcp_client import MCPClient

class MCPServerAdapter:
    """MCP Server 适配器"""
    
    @staticmethod
    def from_openapi(spec_path: str) -> Dict:
        """从 OpenAPI spec 自动生成 MCP 配置"""
        pass
    
    @staticmethod
    def get_modelscope_servers() -> Dict:
        """获取 ModelScope MCP 广场的服务器"""
        return {
            "mcpServers": {
                "web_search": {
                    "type": "streamable_http",
                    "url": "https://mcp.api-inference.modelscope.net/xxx/mcp"
                },
                "code_executor": {
                    "type": "streamable_http", 
                    "url": "https://mcp.api-inference.modelscope.net/yyy/mcp"
                }
            }
        }
```

### Day 6：测试与性能验证

#### 测试环境设置（使用 uv）

```bash
# 安装测试依赖
uv pip install pytest pytest-asyncio

# 运行测试
uv run pytest tests/ -v

# 运行特定测试
uv run pytest tests/test_deepcode_research.py -v
```

#### 测试用例

```python
# tests/test_deepcode_research.py
import pytest
from deepcode_research import DeepCodeResearchAgent

class TestDeepCodeResearch:
    
    @pytest.mark.asyncio
    async def test_simple_cli_tool(self):
        """简单：根据 README 实现 CLI 工具"""
        agent = DeepCodeResearchAgent()
        result = await agent.run(
            "根据这个 README 实现一个简单的 CLI 工具",
            documents=["sample_readme.md"]
        )
        assert result.code is not None
        assert result.success
    
    @pytest.mark.asyncio
    async def test_algorithm_from_paper(self):
        """中等：根据 paper 实现算法"""
        agent = DeepCodeResearchAgent()
        result = await agent.run(
            "实现这篇论文中描述的排序算法",
            documents=["algorithm_paper.pdf"]
        )
        assert "def sort" in result.code
    
    @pytest.mark.asyncio
    async def test_complete_module(self):
        """复杂：根据技术文档实现完整功能模块"""
        agent = DeepCodeResearchAgent()
        result = await agent.run(
            "根据 API 文档实现完整的客户端 SDK",
            documents=["api_docs.pdf"]
        )
        assert len(result.files) > 1
```

### Day 7：文档与 Demo

#### README 结构

```markdown
# DeepCodeResearch Agent

## 🌟 Features
- 自主深度研究能力
- 多模态文档理解
- 代码生成与调试
- Human-in-the-loop 支持

## 🚀 Quick Start
...

## 🏗️ Architecture
...

## 📖 API Reference
...

## 🧪 Examples
...
```

---

## 技术选型建议

| 组件 | 推荐方案 | 说明 |
|------|----------|------|
| **Agent 框架** | MS-Agent | 比赛要求 |
| **LLM** | **gemini-flash-lite-latest** | Prototype 阶段统一使用 Gemini |
| **Vector Store** | FAISS / Chroma | 本地轻量，已有 RAG 集成 |
| **Web Search** | ModelScope MCP / Exa / Tavily | 参考 `ms_agent/tools/search/` |
| **文档解析** | docling / pymupdf | 已集成在 research requirements |
| **Code Execution** | ms-enclave / Docker | 安全沙箱执行 |
| **Memory** | mem0 | 已集成在框架中 |

---

## 快速开始

### 1. 环境安装（使用 uv）

[uv](https://docs.astral.sh/uv/) 是一个极速的 Python 包管理器，推荐使用它来管理项目虚拟环境。

#### 安装 uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

#### 创建虚拟环境并安装依赖

```bash
# 克隆仓库
git clone https://github.com/modelscope/ms-agent.git
cd ms-agent

# 创建虚拟环境 (Python 3.10+)
uv venv --python 3.11

# 激活虚拟环境
# Windows PowerShell:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装基础依赖
uv pip install -e .

# 安装研究功能依赖
uv pip install -r requirements/research.txt

# 或通过 PyPI 一步安装
uv pip install 'ms-agent[research]'
```

#### 使用 uv 运行脚本（无需激活虚拟环境）

```bash
# 直接运行 Python 脚本
uv run python ms_agent/cli/cli.py run --config projects/deep_research --query "your query"

# 或使用 uv 的 tool 运行
uv run --with ms-agent python your_script.py
```

### 2. 环境变量配置

```bash
# .env 文件

# ========== Gemini API (Prototype 阶段必需) ==========
# 获取地址：https://aistudio.google.com/apikey
GEMINI_API_KEY=your_gemini_api_key

# ========== 可选：DashScope API（用于嵌入服务）==========
# ⚠️ 注意：ModelScope API-Inference 暂不支持嵌入接口，框架默认使用 DashScope 提供嵌入服务
# 获取地址：https://bailian.console.aliyun.com/?tab=api#/api/?type=model&url=2712195
DASHSCOPE_API_KEY=your_dashscope_api_key
```

**Prototype 阶段 LLM 配置说明：**

1. **LLM 调用**：统一使用 Google Gemini，通过 OpenAI 兼容接口调用
   - 模型：`gemini-flash-lite-latest`（推荐，性价比最优）
   - Base URL：`https://generativelanguage.googleapis.com/v1beta/openai/`
2. **嵌入服务**：框架的 Memory 模块（基于 mem0）默认使用 DashScope 的 `text-embedding-v4` 模型
3. **配置方式**：
   - 在 `.env` 文件中设置 `GEMINI_API_KEY`
   - 或在 agent 配置 YAML 中指定 `llm.openai_api_key`

**示例配置（agent.yaml）：**
```yaml
llm:
  service: openai
  model: gemini-flash-lite-latest
  openai_base_url: https://generativelanguage.googleapis.com/v1beta/openai/
  openai_api_key: ${GEMINI_API_KEY}  # 自动从环境变量读取
```

### 3. 运行示例

```python
import asyncio
from ms_agent import LLMAgent

async def main():
    # 配置 MCP
    mcp = {
        "mcpServers": {
            "fetch": {
                "type": "streamable_http",
                "url": "https://mcp.api-inference.modelscope.net/{your_uuid}/mcp"
            }
        }
    }
    
    # 创建 Agent
    agent = LLMAgent(mcp_config=mcp)
    
    # 运行任务
    result = await agent.run("请帮我分析这个项目的架构")
    print(result)

asyncio.run(main())
```

### 4. 使用 CLI

```bash
# 运行 Deep Research (使用 uv)
uv run python ms_agent/cli/cli.py run \
    --config projects/deep_research \
    --query "Survey of AI Agent frameworks" \
    --trust_remote_code true

# 运行 Code Generation (使用 uv)
uv run python ms_agent/cli/cli.py run \
    --config projects/code_genesis \
    --query "Build a REST API server" \
    --trust_remote_code true

# 如果已激活虚拟环境，可省略 uv run
python ms_agent/cli/cli.py run \
    --config projects/deep_research \
    --query "Survey of AI Agent frameworks" \
    --trust_remote_code true
```

### 5. 常用 uv 命令

```bash
# 查看已安装包
uv pip list

# 添加新依赖
uv pip install package_name

# 升级依赖
uv pip install --upgrade package_name

# 导出依赖
uv pip freeze > requirements.lock

# 同步依赖（从 requirements.txt）
uv pip sync requirements/framework.txt

# 删除虚拟环境
rm -rf .venv  # Linux/macOS
Remove-Item -Recurse -Force .venv  # Windows PowerShell
```

---

## 评分策略

基于评分标准的重点关注：

### 1. 扩展性与模块化（15分）

**亮点实现：**
- Hooks + Plugin 架构
- 自定义 Callback 系统
- ConfigLifecycleHandler 动态配置
- MCP Server 适配器

```python
# 示例：自定义 Callback
class MyCallback(Callback):
    async def on_task_begin(self, runtime, messages):
        # 自定义逻辑
        pass

agent.register_callback(MyCallback(config))
```

### 2. 核心流程实现（20分）

**完整链路：**
```
Research → Design → Code → Debug → Review
    ↓         ↓        ↓       ↓       ↓
  搜索     PRD/模块   生成    修复    人工
  提取     任务分解   编译    重试    确认
```

### 3. 可复现性（15分）

**要求：**
- 清晰的测试用例（`tests/`）
- 完整的 examples（`examples/`）
- 详细的文档说明
- Docker 部署支持

---

## 参考资源

### 框架文档
- [MS-Agent 官方文档（英文）](https://ms-agent-en.readthedocs.io)
- [MS-Agent 官方文档（中文）](https://ms-agent.readthedocs.io/zh-cn)
- [MCP Playground](https://modelscope.cn/mcp/playground)

### 现有项目参考
- [Deep Research README](projects/deep_research/README.md)
- [Code Scratch README](projects/code_genesis/README.md)
- [Agent Skills README](projects/agent_skills/README.md)
- [Fin Research README](projects/fin_research/README.md)

### 外部资源
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [Anthropic Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills)
- [ModelScope API Inference](https://modelscope.cn/docs/model-service/API-Inference/intro)

### API Keys 获取
- [ModelScope Access Token](https://modelscope.cn/my/myaccesstoken)
- [Exa Search API](https://exa.ai)
- [SerpApi](https://serpapi.com)

---

## 常见问题

### Q: 如何添加自定义工具？

```python
# 1. 继承 ToolBase
from ms_agent.tools.base import ToolBase

class MyTool(ToolBase):
    async def connect(self):
        pass
    
    async def _get_tools_inner(self):
        return {"my_server": [{"tool_name": "my_tool", ...}]}
    
    async def call_tool(self, server_name, tool_name, tool_args):
        return "result"

# 2. 或使用 MCP 配置
mcp = {
    "mcpServers": {
        "my_tool": {
            "command": "python",
            "args": ["my_tool_server.py"]
        }
    }
}
```

### Q: 如何实现 Human-in-the-loop？

```python
# 使用 input_callback
from ms_agent.callbacks.input_callback import InputCallback

# 在 agent.yaml 中配置
callbacks:
  - input_callback

# 或自定义实现
class HumanReviewCallback(Callback):
    async def after_tool_call(self, runtime, messages):
        if self.needs_review(messages):
            user_input = input("请确认是否继续 (y/n): ")
            if user_input != 'y':
                runtime.should_stop = True
```

### Q: 如何使用 Memory？

```python
# 配置 memory
from ms_agent.agent.loader import AgentLoader
from omegaconf import OmegaConf

config = OmegaConf.create({
    'memory': [{
        'path': 'output/memory',
        'user_id': 'user_001'
    }]
})

agent = AgentLoader.build(
    config_dir_or_id='ms-agent/simple_agent',
    config=config
)
```

---

> 💡 **提示**：开发过程中遇到问题，可以参考 `tests/` 目录下的测试用例，以及 `examples/` 目录下的示例代码。