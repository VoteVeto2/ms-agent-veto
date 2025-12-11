import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

# --- Data Structures ---

class SearchResult:
    """Represents a single result item from a search or retrieval operation."""
    def __init__(self, title: str, snippet: str, url: str, source: str):
        self.title = title
        self.snippet = snippet
        self.url = url
        self.source = source

    def to_dict(self) -> Dict[str, str]:
        """Returns the result as a dictionary."""
        return {
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "source": self.source,
        }

    def __repr__(self):
        return f"SearchResult(title='{self.title[:30]}...', source='{self.source}')"

class ToolResponse:
    """Standardized response wrapper for tool execution."""
    def __init__(self, success: bool, results: List[SearchResult], error: Optional[str] = None):
        self.success = success
        self.results = results
        self.error = error

    def __repr__(self):
        return f"ToolResponse(success={self.success}, results_count={len(self.results)}, error={self.error})"

# --- Base Tool Interface ---

class Tool(ABC):
    """
    Abstract Base Class for all external tools used in the Information Acquisition module.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, query: str, **kwargs) -> ToolResponse:
        """
        Executes the tool with the given query and returns a standardized response.

        Args:
            query: The input query or instruction for the tool.
            **kwargs: Additional parameters specific to the tool execution.

        Returns:
            A ToolResponse object.
        """
        pass

# --- Specific Tool Implementations ---

class SearchEngineTool(Tool):
    """
    A tool interface for interacting with an external search engine API (e.g., Google Search, Bing, custom API).
    
    This implementation simulates the structure of an API call using the requests library.
    """
    
    def __init__(self, api_url: str, api_key: str, name: str = "SearchEngine", description: str = "Performs real-time web search for up-to-date information."):
        super().__init__(name, description)
        self.api_url = api_url
        self.api_key = api_key
        self.session = requests.Session()

    def run(self, query: str, num_results: int = 5, timeout: int = 10) -> ToolResponse:
        """
        Executes the search query against the external API.

        Args:
            query: The search term or question.
            num_results: Maximum number of results to retrieve.
            timeout: Request timeout in seconds.

        Returns:
            A ToolResponse object containing the results or error information.
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        params = {
            "q": query,
            "limit": num_results
        }
        
        try:
            # Note: This URL is a placeholder. Replace with actual search API endpoint.
            response = self.session.get(
                self.api_url, 
                params=params, 
                headers=headers, 
                timeout=timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Assuming the API returns a list of results under a 'results' key
            raw_results: List[Dict[str, Any]] = data.get("results", [])
            
            search_results: List[SearchResult] = []
            for item in raw_results:
                # Standardize the result structure
                result = SearchResult(
                    title=item.get("title", "No Title"),
                    snippet=item.get("snippet", "No snippet available."),
                    url=item.get("url", "#"),
                    source=self.name 
                )
                search_results.append(result)
                
            return ToolResponse(success=True, results=search_results)

        except requests.exceptions.Timeout:
            error_msg = f"Search request timed out after {timeout} seconds."
            return ToolResponse(success=False, results=[], error=error_msg)
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error {e.response.status_code} for {self.name}: {e}"
            return ToolResponse(success=False, results=[], error=error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed for {self.name}: {e}"
            return ToolResponse(success=False, results=[], error=error_msg)
        except Exception as e:
            error_msg = f"An unexpected error occurred during search execution: {type(e).__name__}: {e}"
            return ToolResponse(success=False, results=[], error=error_msg)


class RetrievalTool(Tool):
    """
    A tool interface for retrieving information from an internal or specialized knowledge base (RAG system).
    This simulates interaction with an indexed memory store or vector database.
    """
    
    def __init__(self, kb_name: str, name: str = "RetrievalTool", description: str = "Retrieves relevant documents or context from the internal knowledge base."):
        super().__init__(name, description)
        self.kb_name = kb_name
        
    def run(self, query: str, top_k: int = 3, **kwargs) -> ToolResponse:
        """
        Simulates retrieving documents based on the query from the knowledge base.
        
        Args:
            query: The query used for semantic search against the KB.
            top_k: The number of top documents to retrieve.
        
        Returns:
            A ToolResponse object.
        """
        
        # --- Simulation/Placeholder for actual RAG implementation ---
        
        # FIX: Explicitly check if the 'simulate_failure' flag is set to True
        # to ensure the failure path is correctly triggered during simulation testing.
        if kwargs.get("simulate_failure") is True:
            return ToolResponse(success=False, results=[], error=f"Simulated connection failure to {self.kb_name}.")

        simulated_results = [
            SearchResult(
                title=f"KB Document {i+1} ({self.kb_name})",
                snippet=f"Retrieved context snippet related to '{query[:50]}...'. This information is sourced internally.",
                url=f"internal://{self.kb_name}/{i+1}",
                source=self.kb_name
            ) for i in range(top_k)
        ]
        
        return ToolResponse(success=True, results=simulated_results)