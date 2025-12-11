# DeepResearch Agent: Modularized LLM System for Complex Inquiry

The DeepResearch Agent is a robust, modularized system designed to execute complex, multi-step research queries by leveraging advanced Large Language Models (LLMs) and structured workflow management. This project implements a highly structured architecture, inspired by the principles of efficient, verifiable, and adaptive research processes.

## Table of Contents

1.  [Project Overview](#project-overview)
2.  [Features](#features)
3.  [Installation](#installation)
4.  [Configuration](#configuration)
5.  [Usage](#usage)
6.  [Core Architecture and Data Flow](#core-architecture-and-data-flow)
7.  [Project Structure](#project-structure)
8.  [Contributing](#contributing)
9.  [License](#license)

---

## 1. Project Overview

The DeepResearch Agent addresses the limitations of monolithic LLM systems by separating the research process into four distinct, specialized modules: **Query Planning**, **Information Acquisition**, **Memory Management**, and **Answer Generation**. This modularity ensures clarity, verifiability, and allows for sophisticated strategies like Adaptive Planning and a comprehensive Memory Evolution Lifecycle.

The goal of this system is to take a high-level research question and systematically decompose it, gather evidence, consolidate findings, and synthesize a final, well-supported answer.

## 2. Features

### Modular Agent Architecture
The system is built around four independent core modules, allowing for clear separation of concerns:

1.  **Query Planning:** Implements an **Adaptive Planning Strategy** (Sequential, Parallel, or Tree-based decomposition) based on the initial query complexity.
2.  **Information Acquisition:** Executes planned sub-tasks using external tools (e.g., Search Engine APIs) to gather raw data.
3.  **Memory Management:** Manages the **Memory Evolution Lifecycle**, including consolidation (synthesizing raw data into insights), indexing, updating, and strategic forgetting.
4.  **Answer Generation:** Synthesizes the final response based on the validated insights stored in memory.

### Structured Data Flow
All inter-module communication is strictly enforced using `pydantic` models, ensuring data integrity and consistency throughout the complex workflow (e.g., Tasks, Evidence, Validated Insights).

### Workflow Prompt Engineering
Utilizes detailed, specialized prompt templates for each stage (Planning, Consolidation, Synthesis) stored in a dedicated module, optimizing LLM performance for specific tasks.

## 3. Installation

### Prerequisites

*   Python 3.9+

### Step-by-Step Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/deepresearch-agent.git
    cd deepresearch-agent
    ```

2.  **Install dependencies:**
    The project relies on `pydantic` for data structuring, `requests` for external API calls, and `python-dotenv` for configuration management.
    ```bash
    pip install -r requirements.txt
    ```

## 4. Configuration

The system requires API keys and specific model configurations.

### 4.1. Environment Variables (`.env`)

Create a file named `.env` in the root directory of the project to store sensitive keys:

```ini
# .env file example
OPENAI_API_KEY="sk-..."
# Add other necessary API keys (e.g., SERP_API_KEY for search tools)
```

### 4.2. System Configuration (`config.py`)

The `config.py` file manages system parameters, including model selection and operational thresholds. Ensure your preferred LLM and search engine settings are correctly defined here.

```python
# config.py snippet
LLM_MODEL_NAME = "gpt-4-turbo"  # Specify the LLM used for complex reasoning
PLANNER_MODEL_NAME = "gpt-3.5-turbo" # Specify the LLM used for task planning
SEARCH_ENGINE_URL = "https://api.external-search.com/v1"
```

## 5. Usage

The `src/main.py` file serves as the entry point, initializing the `DeepResearchAgent` and executing the end-to-end research workflow based on a predefined or user-input query.

### Running the Agent

1.  **Define the Query:** Modify the initial research query within `src/main.py`.
2.  **Execute the system:**

    ```bash
    python src/main.py
    ```

### Example Workflow Execution

The agent will sequentially execute the following steps:

1.  **Planning:** Decompose the query into sub-tasks.
2.  **Acquisition:** Fetch raw information for each sub-task.
3.  **Memory Consolidation:** Synthesize raw data into validated insights.
4.  **Synthesis:** Generate the final answer based on the consolidated memory state.

## 6. Core Architecture and Data Flow

### 6.1. Modular Components (`src/modules`)

| Module | File | Responsibility |
| :--- | :--- | :--- |
| **Query Planner** | `src/modules/query_planner.py` | Determines the Adaptive Planning Strategy (Sequential/Parallel/Tree-based) and breaks down the initial query into structured tasks. |
| **Information Acquisition** | `src/modules/information_acquisition.py` | Interfaces with external search and retrieval tools (`src/utils/tools.py`) to gather evidence for planned tasks. |
| **Memory Manager** | `src/modules/memory_manager.py` | Implements the Memory Evolution Lifecycle: consolidation of raw data, indexing of insights, and state updates. |
| **Answer Generator** | `src/modules/answer_generator.py` | Formulates the final, comprehensive answer based on the current state of the Memory Manager. |

### 6.2. Structured Data Flow (`src/utils/models.py`)

The system relies heavily on Pydantic models to ensure a reliable contract between modules. Key models include:

*   `Task`: Defines a planned research step (input to Acquisition).
*   `RawInformation`: Unprocessed data gathered from external tools (output of Acquisition).
*   `ValidatedInsight`: Structured, synthesized information derived from raw data (output of Memory Consolidation).
*   `MemoryState`: The cumulative, indexed knowledge base of the agent.

## 7. Project Structure

```
deepresearch-agent/
├── README.md
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (API keys)
├── config.py                  # System configuration and parameters
└── src/
    ├── main.py                # Main entry point and workflow initialization
    ├── core/
    │   └── agent.py           # Orchestrates the four core modules (The DeepResearchAgent)
    ├── modules/
    │   ├── query_planner.py   # Adaptive planning logic
    │   ├── information_acquisition.py # External tool execution
    │   ├── memory_manager.py  # Memory Evolution Lifecycle implementation
    │   └── answer_generator.py# Final synthesis logic
    ├── prompts/
    │   └── workflow_prompts.py# Detailed prompt templates for planning, consolidation, etc.
    └── utils/
        ├── models.py          # Pydantic models defining structured data flow
        └── tools.py           # Definitions and interfaces for external tools (Search, Retrieval)
```

## 8. Contributing

We welcome contributions to enhance the DeepResearch Agent!

1.  Fork the repository.
2.  Create a new feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

Please ensure your code adheres to the existing modular structure and includes relevant documentation and tests where appropriate.

## 9. License

This project is licensed under the MIT License. See the LICENSE file for details.