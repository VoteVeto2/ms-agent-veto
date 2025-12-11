import requests
from typing import Any, Dict, List, Optional

from .models import Query, Plan, Answer
from .modules.query_planner import QueryPlanner
from .modules.answer_generator import AnswerGenerator

# Assume external API interaction is handled via a dedicated service or directly here
# For this client, we'll simulate the external API interaction using 'requests'

class ResearchAPIClient:
    """
    The main REST API Client class that orchestrates interactions between the 
    functional modules (Query Planning, Answer Generation) and the external API 
    (simulated or real).

    This client manages the flow:
    1. Receives an initial complex query.
    2. Uses the QueryPlanner to decompose it into an execution plan (e.g., Tree-based plan).
    3. Executes the plan, potentially involving external information acquisition (simulated).
    4. Uses the AnswerGenerator to synthesize the final response based on intermediate results.
    """

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initializes the ResearchAPIClient.

        Args:
            base_url: The base URL for the external research API endpoints.
            timeout: Default timeout for HTTP requests in seconds.
        """
        self.base_url = base_url
        self.timeout = timeout
        
        # Initialize functional modules (System Component Decomposition)
        self.planner = QueryPlanner()
        self.generator = AnswerGenerator()
        
        print(f"Client initialized for base URL: {base_url}")

    def _make_api_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Internal helper method to handle HTTP requests to the external API.
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == 'POST':
                response = requests.post(url, json=data, timeout=self.timeout)
            elif method == 'GET':
                response = requests.get(url, params=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            return response.json()

        except requests.exceptions.Timeout:
            raise ConnectionError(f"API request timed out after {self.timeout} seconds to {url}")
        except requests.exceptions.RequestException as e:
            # Catch all other requests-related errors (connection, HTTP errors)
            raise ConnectionError(f"Error communicating with API endpoint {url}: {e}")

    def execute_research_workflow(self, initial_query: str) -> Answer:
        """
        Orchestrates the full research workflow: Planning -> Execution -> Generation.

        Args:
            initial_query: The complex question or task provided by the user.

        Returns:
            The final synthesized Answer object.
        """
        print(f"Starting workflow for query: '{initial_query[:50]}...'")
        
        # 1. Query Planning (Decomposition)
        query_obj = Query(text=initial_query)
        try:
            # The planner decides the structure (e.g., Tree-based planning)
            execution_plan: Plan = self.planner.plan_query(query_obj)
            print(f"Query successfully decomposed into a plan with {len(execution_plan.steps)} steps.")
        except Exception as e:
            raise RuntimeError(f"Query Planning failed: {e}")

        # 2. Information Acquisition & Execution (Simulated/Orchestrated)
        # In a real system, this loop would traverse the Plan structure (DAG/Tree)
        # executing sub-queries, potentially calling external APIs for retrieval.
        
        intermediate_results: List[Dict[str, Any]] = []
        
        for step in execution_plan.steps:
            print(f"Executing step: {step.description}")
            
            # --- Simulation of Information Acquisition / Sub-task Execution ---
            
            if step.action == "RETRIEVE":
                # Simulate calling an external search API based on the sub-query
                try:
                    # Example: Call an external search endpoint
                    search_data = self._make_api_request(
                        endpoint="search", 
                        method='POST', 
                        data={"sub_query": step.sub_query}
                    )
                    # Search data is treated as retrieved evidence
                    intermediate_results.append({
                        "source": "External Retrieval",
                        "content": search_data.get("documents", []),
                        "related_to": step.step_id
                    })
                    print(f"Retrieved {len(search_data.get('documents', []))} documents.")
                except ConnectionError as ce:
                    print(f"Warning: Retrieval failed for step {step.step_id}. Using fallback. Error: {ce}")
                    intermediate_results.append({
                        "source": "Fallback",
                        "content": [f"Error retrieving data for sub-query: {step.sub_query}"],
                        "related_to": step.step_id
                    })
            
            elif step.action == "COMPUTE":
                # Simulate local computation or calling a specialized internal module
                # (e.g., a specific calculator or knowledge graph query)
                result = {"computation_output": f"Result for {step.sub_query}"}
                intermediate_results.append({
                    "source": "Internal Computation",
                    "content": result,
                    "related_to": step.step_id
                })
                
            # --- End Simulation ---

        # 3. Answer Generation
        try:
            final_answer = self.generator.generate_answer(
                original_query=initial_query,
                context=intermediate_results
            )
            print("Final answer generated successfully.")
            return final_answer
            
        except Exception as e:
            raise RuntimeError(f"Answer Generation failed: {e}")

# Example Usage (if this file were run directly, though typically imported)
if __name__ == '__main__':
    # Mock setup for demonstration purposes
    
    # Mock the external API responses for testing the client structure
    def mock_request(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = str(json_data)

            def json(self):
                return self.json_data

            def raise_for_status(self):
                if 400 <= self.status_code < 600:
                    raise requests.exceptions.HTTPError(f"HTTP Error: {self.status_code}")
        
        endpoint = args[0].split('/')[-1]
        
        if endpoint == "search":
            return MockResponse({
                "documents": [
                    {"id": 1, "text": "Tree-based planning balances efficiency and effectiveness."},
                    {"id": 2, "text": "MAO-ARAG uses a DAG structure for dynamic orchestration."}
                ]
            }, 200)
        
        raise Exception(f"Unhandled mock endpoint: {endpoint}")

    # Monkey-patch requests.post for testing
    requests.post = mock_request
    
    try:
        client = ResearchAPIClient(base_url="http://mock-api.com/v1")
        
        complex_query = "Compare the advantages of Tree-based planning versus Sequential planning in DR systems, and suggest how MAO-ARAG improves upon them."
        
        final_result = client.execute_research_workflow(complex_query)
        
        print("\n--- FINAL RESULT ---")
        print(f"Answer Text: {final_result.text}")
        print(f"Confidence: {final_result.confidence}")
        
    except (ConnectionError, RuntimeError) as e:
        print(f"\nWorkflow execution failed: {e}")