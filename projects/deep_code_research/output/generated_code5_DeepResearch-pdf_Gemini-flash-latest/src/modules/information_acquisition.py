from typing import List, Dict, Any
from src.utils.models import Task, ToolCall, RawInformation, ToolType, TaskStatus
from src.utils.tools import ToolResponse, SearchResult, BaseTool

class InformationAcquisition:
    """
    The Information Acquisition module is responsible for executing planned sub-tasks 
    by interacting with external resources (External Tools) and internal knowledge 
    stores (Retrieval Tools) to gather raw, unstructured data.

    This module implements the 'tool use' phase of the research workflow, converting 
    ToolCalls into executable actions and structuring the results into RawInformation.
    """

    def __init__(self, tool_registry: Dict[ToolType, BaseTool]):
        """
        Initializes the InformationAcquisition module with a registry of executable tools.

        Args:
            tool_registry: A dictionary mapping ToolType enums to concrete BaseTool instances.
        """
        self.tool_registry = tool_registry

    def _process_tool_response(self, tool_call: ToolCall, response: ToolResponse) -> List[RawInformation]:
        """
        Converts a standardized ToolResponse containing SearchResults into 
        structured RawInformation objects, linking them back to the originating task.

        Args:
            tool_call: The ToolCall object that generated the response.
            response: The standardized response from the executed tool.

        Returns:
            A list of RawInformation objects.
        """
        raw_info_list = []
        
        if not response.success:
            # Log the failure but return an empty list of results
            print(f"Tool execution failed for {tool_call.tool_type.value} (Task ID: {tool_call.task_id}): {response.error}")
            return []

        for result in response.results:
            # Combine title, URL, and snippet into the main content field for easy processing later
            content = f"Title: {result.title}\nURL: {result.url}\nSnippet: {result.snippet}"
            
            # Store additional metadata
            metadata = {
                "url": result.url,
                "original_query": tool_call.arguments.get('query', 'N/A'),
                "tool_type": tool_call.tool_type.value
            }
            
            # Create RawInformation instance
            try:
                raw_info = RawInformation(
                    task_id=tool_call.task_id,
                    content=content,
                    source=result.source,
                    metadata=metadata
                )
                raw_info_list.append(raw_info)
            except Exception as e:
                print(f"Error creating RawInformation object from search result: {e}")

        return raw_info_list

    def acquire_information(self, task: Task) -> List[RawInformation]:
        """
        Executes all necessary tool calls defined within a Task object to gather 
        Raw Information.

        This method iterates through the planned ToolCalls, executes the corresponding 
        tool, and aggregates the results.

        Args:
            task: The Task object containing the list of ToolCall specifications.

        Returns:
            A list of RawInformation objects gathered during the acquisition phase.
        """
        if task.status not in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
            # Only process tasks that are ready for execution
            return []

        all_raw_information: List[RawInformation] = []

        if not task.tool_calls:
            return []

        for tool_call in task.tool_calls:
            tool_type = tool_call.tool_type
            
            if tool_type not in self.tool_registry:
                print(f"Warning: Tool type {tool_type.value} required by task {task.task_id} is not registered.")
                continue

            tool_instance = self.tool_registry[tool_type]
            
            try:
                # Execute the tool using arguments provided in the ToolCall
                response = tool_instance.run(**tool_call.arguments)
                
                # Process and structure the results
                raw_data = self._process_tool_response(tool_call, response)
                all_raw_information.extend(raw_data)

            except Exception as e:
                # Catch execution errors specific to the tool's implementation
                print(f"Critical execution error for tool {tool_instance.name} (Task ID: {task.task_id}): {e}")
                continue

        return all_raw_information