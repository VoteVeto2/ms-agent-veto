Here is a comprehensive `README.md` designed for the project structure and architecture you described.

```markdown
# DeepResearch-Py 🧠📚

**An autonomous AI research agent implementation based on the "Deep Research" architecture.**

DeepResearch-Py is a modular Python framework designed to perform complex, multi-step research tasks. By orchestrating Large Language Models (LLMs) with web search tools and a sophisticated memory management system, it decomposes high-level queries into actionable sub-tasks, gathers evidence, and synthesizes comprehensive research reports.

---

## 🚀 Features

*   **Structured Query Planning:** Decomposes complex user prompts into manageable sub-tasks using Parallel, Sequential, or Tree-based topologies.
*   **Intelligent Acquisition:** Utilizes `duckduckgo-search` and `beautifulsoup4` to scrape, parse, and filter web content for relevance.
*   **Dynamic Memory Management:** Implements a cognitive cycle of Consolidation (summarizing), Indexing, and Forgetting (pruning) to maintain context within LLM limits.
*   **Pydantic Validation:** Enforces strict data schemas for Evidence, SubTasks, and Reports to ensure robust data flow.
*   **Rich CLI Interface:** Features a beautiful command-line interface using `typer` and `rich` for real-time research progress tracking.

---

## 📂 Project Structure

```text
.
├── .env.example                # Template for environment variables
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
└── src
    ├── __init__.py             # Package initialization
    ├── acquisition.py          # Tools for search and web scraping
    ├── agent.py                # Main orchestration logic
    ├── config.py               # Configuration settings (Model, Depth, etc.)
    ├── generation.py           # Report synthesis and writing logic
    ├── llm_client.py           # Wrapper for OpenAI/LLM interactions
    ├── main.py                 # CLI entry point
    ├── memory.py               # Context management (Consolidation/Pruning)
    ├── planning.py             # Query decomposition logic
    └── schemas.py              # Pydantic models (SubTasks, Evidence, etc.)
```

---

## 🛠️ Architecture

This project implements the workflow described in the **Deep Research** methodology:

1.  **Planner:** The `planning.py` module analyzes the user request and generates a Directed Acyclic Graph (DAG) of sub-questions.
2.  **Agent:** The `agent.py` orchestrator iterates through the plan.
3.  **Acquisition:** For each sub-task, `acquisition.py` performs web searches and scrapes content, filtering noise using heuristic and semantic checks.
4.  **Memory:** `memory.py` ingests raw data. It summarizes key findings (Consolidation) and removes outdated info (Forgetting) to keep the context window optimized.
5.  **Generation:** Once sufficient evidence is gathered, `generation.py` synthesizes the final answer into a structured markdown report.

---

## 📦 Installation

### Prerequisites
*   Python 3.10+
*   An OpenAI API Key (or compatible LLM provider)

### Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/deepresearch-py.git
    cd deepresearch-py
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**
    Copy the example environment file and add your API keys.
    ```bash
    cp .env.example .env
    ```
    
    Open `.env` and configure:
    ```ini
    OPENAI_API_KEY=sk-proj-...
    # Optional: TAVILY_API_KEY=... (if using Tavily instead of DDG)
    RESEARCH_DEPTH=3
    MAX_MEMORY_TOKENS=4000
    ```

---

## 💻 Usage

### Command Line Interface (CLI)

The project uses `typer` to provide a robust CLI. To start a research session:

```bash
python src/main.py "What are the latest breakthroughs in Solid State Batteries as of 2024?"
```

**Options:**
*   `--depth`: Control how many layers of sub-questions to generate (Default: 3).
*   `--output`: Specify a filename to save the report (Default: `report.md`).

### Library Usage

You can import the `ResearchAgent` directly into your own Python scripts:

```python
import asyncio
from src.agent import ResearchAgent
from src.config import settings

async def run_research():
    agent = ResearchAgent(
        model=settings.DEFAULT_MODEL,
        memory_limit=settings.MAX_MEMORY_TOKENS
    )
    
    report = await agent.run("Analyze the economic impact of AI in healthcare.")
    print(report.content)

if __name__ == "__main__":
    asyncio.run(run_research())
```

---

## 🧩 Key Components & Configuration

### `src/config.py`
Manage global settings such as:
*   `LLM_MODEL`: e.g., `gpt-4o` or `gpt-3.5-turbo`.
*   `SEARCH_PROVIDER`: Toggle between `duckduckgo` or other implemented providers.

### `src/schemas.py`
Defines the data structures that ensure type safety:
*   **`SubTask`**: A specific question to answer.
*   **`Evidence`**: Raw text + citation URL + relevance score.
*   **`ResearchReport`**: The final structured output.

### `src/memory.py`
Handles the "Cognitive Cycle". It ensures the agent doesn't get overwhelmed by data by periodically summarizing the `MemoryContext` and pruning low-relevance evidence.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

Please ensure all new modules utilize `pydantic` for data validation and include type hints.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Built with 💙 using Python, OpenAI, and Typer.*