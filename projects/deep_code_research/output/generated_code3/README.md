# Deep Research REST API Client

This project provides a robust and structured Python client for interacting with a hypothetical Deep Research (DR) REST API. It handles complex query planning, submission, and retrieval of synthesized answers using modern Python practices, including data validation via Pydantic.

## 1. Project Description

This is a dedicated REST API client designed to manage the workflow of submitting complex research inquiries to an external service. The workflow involves two primary asynchronous steps: **Query Planning** and **Answer Generation**. The client encapsulates the logic for structuring requests, managing API communication, and validating responses.

## 2. Installation

### Prerequisites

You need Python 3.7+ installed on your system.

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   deep-research-client
   cd deep-research-client
   ```

2. **Install dependencies:**
   This project relies on `requests` for HTTP communication and `pydantic` for data modeling.

   ```bash
   pip install -r requirements.txt
   ```

   *(Assuming `requirements.txt` contains `requests` and `pydantic`)*

## 3. Usage Examples

The core interaction is managed through the `DeepResearchClient` class located in `src/client.py`.

### Example Workflow

The following demonstrates how to initialize the client and execute a full research query:

```python
# src/main.py (or similar execution script)

import asyncio
from src.client import DeepResearchClient
from src.models import ResearchQuery

# Configuration (Replace with actual API details)
API_BASE_URL = "https://api.deepresearch.com/v1"
API_KEY = "YOUR_SECRET_API_KEY"

async def run_client_example():
    client = DeepResearchClient(
        base_url=API_BASE_URL,
        api_key=API_KEY
    )

    # 1. Define the complex query
    query_input = ResearchQuery(
        topic="The impact of quantum computing on modern cryptography",
        depth_level=3,
        required_sources=["academic", "patent"]
    )

    print(f"Submitting query: {query_input.topic}...")

    try:
        # 2. Initiate Query Planning
        planning_response = await client.plan_query(query_input)
        print(f"Query Planning successful. Job ID: {planning_response.job_id}")

        # 3. Poll/Retrieve Answer (In a real scenario, this would involve polling logic)
        # For demonstration, we assume the answer retrieval is handled by the client's orchestration
        
        # Note: The actual retrieval mechanism (polling vs. direct wait) depends on API design.
        # Assuming the client handles the necessary waiting/polling internally:
        final_answer = await client.get_final_answer(planning_response.job_id)
        
        print("\n--- Final Synthesized Answer ---")
        print(final_answer.content)
        print(f"Sources Cited: {len(final_answer.sources)}")

    except Exception as e:
        print(f"An error occurred during the research process: {e}")

if __name__ == "__main__":
    asyncio.run(run_client_example())
```

## 4. Project Structure

The project is organized into a `src` directory containing modular components:

```
.
├── src/
│   ├── models.py             # Defines Pydantic models for request/response serialization and validation.
│   ├── client.py             # The main REST API Client class that orchestrates interactions.
│   ├── main.py               # Main entry point demonstrating client usage.
│   ├── modules/
│   │   ├── query_planner.py  # Client module responsible for submitting the initial complex problem.
│   │   └── answer_generator.py # Client module responsible for polling/retrieving the final answer.
└── requirements.txt          # Lists project dependencies.
```

### Key Components Breakdown

| File/Component | Description |
| :--- | :--- |
| `src/models.py` | Defines Pydantic models for request/response serialization and validation, structuring complex inputs/outputs expected by the DR API. |
| `src/modules/query_planner.py` | Client module responsible for submitting the initial complex problem to the API's Query Planning endpoint. |
| `src/modules/answer_generator.py` | Client module responsible for polling or retrieving the final synthesized answer from the API, corresponding to the Answer Generation phase. |
| `src/client.py` | The main REST API Client class that orchestrates interactions between the functional modules (Query Planning, Answer Generation) and the external API. |
| `src/main.py` | Main entry point demonstrating the instantiation and usage of the DeepResearchClient to execute a complex query workflow. |

## 5. API Documentation (Conceptual)

This client is built around two primary API endpoints:

| Endpoint | Method | Function | Pydantic Model Used |
| :--- | :--- | :--- | :--- |
| `/v1/plan` | `POST` | Initiates the research workflow by submitting the complex query structure. Returns a `JobStatus` object. | `ResearchQuery` (Request), `JobStatus` (Response) |
| `/v1/answer/{job_id}` | `GET` | Retrieves the final synthesized result once processing is complete. | `FinalAnswer` (Response) |

*Note: Actual endpoint paths and response structures are defined within `src/client.py` and `src/models.py`.*

## 6. Contributing Guidelines

We welcome contributions! If you find bugs, have suggestions for improvements, or want to add new features:

1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

Please ensure all new code is accompanied by appropriate tests (if a testing framework is added later) and adheres to PEP 8 standards.

## 7. License

This project is currently under the **MIT License**. See the `LICENSE` file for more details.