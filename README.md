# DeepCodeResearch 
Group: *La Tourisete polonais*

> DeepCodeResearch 是一个基于 MS-Agent 框架的智能代码生成管道，能够解析参考文档、执行 RAG 风格的研究、规划代码架构并生成完整的代码仓库。

## 运行条件

> 列出运行该项目所必须的条件和相关依赖

- Python ≥ 3.10
- uv（Python 包管理器）
- Gemini API Key（或其他兼容 OpenAI 格式的 API）

## 运行说明

> 说明如何运行和使用你的项目，建议给出具体的步骤说明

**项目位置**：`deep_code_research` 位于 `projects/deep_code_research` 文件夹下

1. **配置 API**：在 `projects/deep_code_research` 目录下创建 `.env` 文件，填入以下内容：
   ```
   OPENAI_API_KEY="your-api-key"
   OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
   OPENAI_MODEL=gemini-flash-lite-latest
   ```

2. **设置虚拟环境**：
   ```powershell
   cd projects\deep_code_research
   uv venv
   .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

3. **运行管道**：
   ```powershell
   cd projects\deep_code_research
   uv run --env-file .env python run.py --prompt "<your prompt>" --references <path_to_references>
   ```

## 测试说明

> 如果有测试相关内容需要说明，请填写在这里

从项目根目录运行测试：
```powershell
cd projects\deep_code_research
uv run pytest tests -q
```

## 技术架构

> 使用的技术框架或系统架构图等相关说明，请填写在这里

**项目位置**：`deep_code_research` 位于 `projects/deep_code_research` 文件夹下
```
deep_code_research/
├── run.py                  # 入口文件
├── contracts.py            # 共享数据契约
├── research/               # Agent 1: 研究模块
│   ├── adaptive_rag.py     # 自适应 RAG 编排
│   ├── document_parser.py  # 文档解析
│   └── rag_engine.py       # RAG 索引与检索
├── codegen/                # Agent 2: 代码生成模块
│   ├── code_planner.py     # 架构规划
│   ├── code_generator.py   # 代码合成
│   └── self_debugger.py    # 自我调试
└── orchestrator/           # Agent 3: 核心编排模块
    ├── pipeline.py         # 管道协调
    └── output_formatter.py # 输出格式化
```

---

**Landing Page**: [在线演示](https://cjozjn1wl1s40uee13y5smgd1.bolt.host/)