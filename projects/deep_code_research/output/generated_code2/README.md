# DR System REST API Client

A Python client library designed to interact with a hypothetical "DR System" REST API. This client handles configuration, request/response serialization using Pydantic, and provides a structured interface for common API operations.

## 🚀 Project Description

This project provides a robust and type-safe client for interacting with a backend system (referred to as the "DR System"). It encapsulates the complexity of HTTP requests, ensuring that request bodies and response data adhere to predefined schemas using Pydantic.

The client supports the core workflow of the DR System, likely involving submitting queries, checking processing status, and retrieving final results.

## 📦 Installation

### Prerequisites

You must have Python 3.7+ installed on your system.

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd dr-api-client
   ```

2. **Install dependencies:**
   This project uses `pip` and relies on the packages listed in `requirements.txt`.

   ```bash
   pip install -r requirements.txt
   ```
   *(This will install `requests` for HTTP handling and `pydantic` for data validation.)*

## 💡 Usage Examples

The main entry point for demonstration and usage is typically `src/main.py`.

### 1. Initialization

The client requires configuration settings (like the base URL and any necessary authentication tokens) loaded from `src/config.py`.

```python
from src.client import DRAPIClient
from src.config import settings

# Initialize the client using settings loaded from the configuration file
client = DRAPIClient(
    base_url=settings.API_BASE_URL,
    api_key=settings.API_KEY
)
```

### 2. Submitting a Query

Assuming you have a Pydantic model for the query submission (e.g., `QueryPlan`):

```python
from src.models import QueryPlan, SubmissionResponse

# 1. Prepare the data object
query_data = QueryPlan(
    user_id="user-123",
    search_term="What is the capital of France?",
    priority="High"
)

try:
    # 2. Submit the query to the API
    response: SubmissionResponse = client.submit_query(query_data)
    print(f"Query submitted successfully. Job ID: {response.job_id}")

except Exception as e:
    print(f"Error submitting query: {e}")
```

### 3. Retrieving Results

Using the `job_id` obtained from submission:

```python
from src.models import FinalAnswer

job_id = "job-abc-456"

try:
    # 1. Check status (optional, but good practice)
    status = client.get_status(job_id)
    print(f"Job {job_id} status: {status.current_state}")

    # 2. Retrieve final results
    if status.current_state == "COMPLETED":
        result: FinalAnswer = client.retrieve_results(job_id)
        print(f"Final Answer: {result.answer_text}")
        print(f"Evidence Count: {len(result.evidence_records)}")

except Exception as e:
    print(f"Error retrieving results: {e}")
```

## 📂 Project Structure

The project is organized into distinct modules reflecting common client architecture patterns:

```
dr-api-client/
├── src/
│   ├── config.py       # Configuration settings (Base URL, API Keys, timeouts)
│   ├── models.py       # Pydantic models defining request/response schemas (QueryPlan, EvidenceRecord, FinalAnswer)
│   ├── client.py       # The core DRAPIClient class implementing API interaction logic
│   ├── main.py         # Main entry point for demonstration and testing
│   └── __init__.py
└── requirements.txt    # Project dependencies
└── README.md           # This file
```

## 📚 API Documentation (Client Methods)

The `DRAPIClient` class in `src/client.py` exposes the following key methods:

| Method | Description | Request Body (Model) | Response Model |
| :--- | :--- | :--- | :--- |
| `submit_query(query_plan)` | Submits a new processing request to the DR system. | `QueryPlan` | `SubmissionResponse` |
| `get_status(job_id)` | Retrieves the current processing status of a submitted job. | N/A (uses `job_id` in path) | `JobStatus` |
| `retrieve_results(job_id)` | Fetches the final processed results for a completed job. | N/A (uses `job_id` in path) | `FinalAnswer` |
| `get_evidence(record_id)` | Retrieves detailed evidence associated with a specific record. | N/A | `EvidenceRecord` |

*Note: Specific model definitions for request/response types are located in `src/models.py`.*

## 🤝 Contributing Guidelines

We welcome contributions to improve the robustness, documentation, or features of this API client.

1.  **Fork** the repository.
2.  **Clone** your fork locally.
3.  Create a new **feature branch** (`git checkout -b feature/AmazingFeature`).
4.  Make your changes and ensure all existing tests pass (if tests are implemented).
5.  Commit your changes (`git commit -m 'feat: Add new feature X'`).
6.  **Push** to the branch (`git push origin feature/AmazingFeature`).
7.  Open a **Pull Request**.

Please ensure any new features or bug fixes include appropriate documentation updates.

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details. (If a LICENSE file is not present, assume MIT for placeholder purposes).