import asyncio
from typing import Any, Dict, List, Optional, Tuple

# Mocking the RAGEngine for demonstration purposes, as the actual implementation
# is external and not provided, but the reference suggests an async method 'query'.
class MockRAGEngine:
    """A mock class simulating the RAGEngine with an async query method."""
    async def query(self, query_text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Simulates an asynchronous query execution."""
        await asyncio.sleep(0.01)  # Simulate network/processing delay
        if "failing" in query_text.lower():
            return f"Error: Failed to process query '{query_text}' due to an internal system fault."
        return f"Result for '{query_text}': Successfully processed via RAGEngine."

# Assuming RAGEngine is the primary dependency for the client.
RAGEngine = MockRAGEngine

class ClientError(Exception):
    """Base exception for client-side errors."""
    pass

class QueryExecutionError(ClientError):
    """Exception raised when the RAGEngine query fails or returns an error state."""
    pass

class Client:
    """
    Client interface for interacting with the RAGEngine system.

    This client manages the interaction lifecycle, ensuring robust error handling
    and adherence to system architecture principles by abstracting the core
    query execution logic.
    """
    def __init__(self, engine: RAGEngine, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the client with the RAGEngine instance.

        Args:
            engine: The RAGEngine instance responsible for core processing.
            config: Configuration dictionary for the client (e.g., timeouts).
        """
        self.engine: RAGEngine = engine
        self.config: Dict[str, Any] = config if config is not None else {}
        self.max_retries: int = self.config.get("max_retries", 3)

    async def execute_query(self, query_text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Executes a query against the RAGEngine with retry logic.

        This method embodies the 'Query Planning' and 'Information Acquisition'
        stages conceptually by managing the execution flow.

        Args:
            query_text: The input query string.
            context: Optional context dictionary to pass to the engine.

        Returns:
            The successful result string from the engine.

        Raises:
            QueryExecutionError: If all retries fail or the engine returns an
                                 unrecoverable error.
        """
        if not query_text:
            raise ValueError("Query text cannot be empty.")

        attempt = 0
        while attempt < self.max_retries:
            try:
                # Reference: <coroutine object RAGEngine.query at ...>
                result = await self.engine.query(query_text, context)

                # Basic check for common failure indicators in the response text
                if "Error:" in result or "Failed to process" in result:
                    raise QueryExecutionError(
                        f"Engine returned an error response for '{query_text}': {result}"
                    )

                # Success path
                return result

            except QueryExecutionError as e:
                print(f"Attempt {attempt + 1}/{self.max_retries} failed due to engine error: {e}")
                attempt += 1
                if attempt >= self.max_retries:
                    raise QueryExecutionError(
                        f"All {self.max_retries} attempts failed for query: {query_text}"
                    ) from e
                # Implement backoff strategy if needed (e.g., asyncio.sleep(2 ** attempt))

            except Exception as e:
                # Catch unexpected connection errors, timeouts, etc.
                print(f"Attempt {attempt + 1}/{self.max_retries} failed due to unexpected exception: {e}")
                attempt += 1
                if attempt >= self.max_retries:
                    raise ClientError(
                        f"Failed to execute query after {self.max_retries} attempts due to system exception: {e}"
                    ) from e
                await asyncio.sleep(1) # Simple fixed delay for unexpected errors

        # Should be unreachable if logic is sound, but kept for completeness
        raise ClientError("Query execution terminated unexpectedly.")

# Example Usage (for testing the fix):
async def main():
    engine = RAGEngine()
    client = Client(engine)

    # 1. Test a successful query
    try:
        success_query = "What is the capital of France?"
        result = await client.execute_query(success_query)
        print(f"\n[SUCCESS TEST] Query: {success_query}\nResult: {result}")
    except ClientError as e:
        print(f"[SUCCESS TEST FAILED] Unexpected error: {e}")

    # 2. Test a query designed to fail (to test retry logic and error handling)
    try:
        failing_query = "This query is intentionally failing."
        print(f"\n[FAILURE TEST] Attempting query designed to fail: {failing_query}")
        await client.execute_query(failing_query)
    except QueryExecutionError as e:
        print(f"[FAILURE TEST PASSED] Caught expected QueryExecutionError:\n{e}")
    except ClientError as e:
        print(f"[FAILURE TEST FAILED] Caught wrong error type: {type(e).__name__}: {e}")

if __name__ == '__main__':
    # Running the main async function
    try:
        asyncio.run(main())
    except RuntimeError as e:
        # Handle RuntimeError if running in environments like Jupyter/IPython
        if "cannot run in a different thread" in str(e):
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.run(main())
        else:
            raise