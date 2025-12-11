from typing import Callable, Any, Dict, List, Optional

# Assuming MemoryState, ResearchResult, ValidityStatus are defined in models.py
from src.utils.models import MemoryState, ResearchResult, ValidityStatus 

# Assuming ANSWER_GENERATION_PROMPT_TEMPLATE is defined here
from src.prompts.workflow_prompts import ANSWER_GENERATION_PROMPT_TEMPLATE 

# Define the signature for the LLM client abstraction
LLM_CALL_SIGNATURE = Callable[[str, Dict[str, Any]], str] 

class AnswerGenerator:
    """
    Implements the Answer Generation module (Section 3.4).

    This module synthesizes the final, comprehensive answer based solely on the 
    validated insights stored in the Memory State. It integrates upstream information 
    (verified evidence and consolidated knowledge) to generate a coherent, grounded, 
    and well-supported response.
    """
    def __init__(self, llm_client: LLM_CALL_SIGNATURE, llm_config: Optional[Dict[str, Any]] = None):
        """
        Initializes the AnswerGenerator with an LLM client function.

        Args:
            llm_client: A callable function representing the LLM API interaction.
                        Signature: llm_client(prompt: str, config: Dict) -> str
            llm_config: Configuration parameters for the LLM call (e.g., model name, temperature).
        """
        self.llm_client = llm_client
        self.llm_config = llm_config if llm_config is not None else {"model": "gpt-4-turbo", "temperature": 0.1}

    def _format_evidence(self, evidence_list: List[Any]) -> str:
        """
        Formats a list of evidence objects (assuming they have source_id and content) 
        into a readable string for the LLM, maintaining source traceability.
        
        FIX: Added defensive dictionary access for simulation compatibility.
        """
        formatted_items = []
        for i, evidence in enumerate(evidence_list):
            
            if isinstance(evidence, dict):
                source_id = evidence.get('source_id', f"Unknown Source {i+1}")
                content = evidence.get('content', "Content unavailable.")
            else:
                # Use getattr for robustness, assuming Evidence model structure
                source_id = getattr(evidence, 'source_id', f"Unknown Source {i+1}")
                content = getattr(evidence, 'content', "Content unavailable.")
            
            formatted_items.append(
                f"--- Source ID: {source_id} ---\n"
                f"{content}\n"
            )
        return "\n".join(formatted_items)

    def _extract_validated_insights(self, memory_state: MemoryState) -> Dict[str, Any]:
        """
        Extracts and formats all verified and consolidated insights from the memory state.
        
        FIX: Ensures robust access to top-level attributes (evidence_pool, consolidated_knowledge) 
             by checking if memory_state is a dictionary (common in simulation environments) 
             before attempting attribute access.
        """
        
        # 1. Access attributes defensively (Handles dict inputs common in simulation)
        if isinstance(memory_state, dict):
            evidence_pool = memory_state.get('evidence_pool', [])
            consolidated_knowledge = memory_state.get('consolidated_knowledge', None)
        else:
            # Use getattr for robustness if it is an object or mock object
            evidence_pool = getattr(memory_state, 'evidence_pool', [])
            consolidated_knowledge = getattr(memory_state, 'consolidated_knowledge', None)

        validated_evidence = []
        for e in evidence_pool:
            # Determine validation status defensively (handles dict vs object access)
            if isinstance(e, dict):
                status = e.get('validation_status', ValidityStatus.UNCHECKED)
            else:
                status = getattr(e, 'validation_status', ValidityStatus.UNCHECKED)
            
            # Handle cases where status might be the Enum value or its string representation (e.g., 'VERIFIED')
            is_verified = status == ValidityStatus.VERIFIED
            if not is_verified and isinstance(status, str):
                # Ensure comparison is robust against string representations
                is_verified = status.upper() == ValidityStatus.VERIFIED.name
            
            if is_verified:
                validated_evidence.append(e)
        
        # 2. Format verified evidence
        formatted_evidence = self._format_evidence(validated_evidence)

        # 3. Extract consolidated knowledge
        consolidated_knowledge_str = consolidated_knowledge if consolidated_knowledge else "No high-level synthesis available in memory."

        return {
            "consolidated_knowledge": consolidated_knowledge_str,
            "verified_evidence": formatted_evidence,
            "has_data": bool(validated_evidence) or bool(consolidated_knowledge)
        }

    def generate_answer(self, initial_query: str, memory_state: MemoryState) -> ResearchResult:
        """
        Synthesizes the final answer using the LLM based on the validated memory state.

        The process ensures the answer is grounded by integrating the verified evidence 
        and the consolidated knowledge from the memory state.

        Args:
            initial_query: The user's original research query.
            memory_state: The current state of the research memory, containing validated insights.

        Returns:
            A ResearchResult object containing the final answer and supporting context.
        """
        try:
            # 1. Prepare the grounding context
            insights = self._extract_validated_insights(memory_state)
            
            if not insights["has_data"]:
                error_msg = "Research yielded no verified insights or consolidated knowledge. Cannot generate a grounded answer."
                return ResearchResult(
                    query=initial_query,
                    final_answer=error_msg,
                    supporting_context=error_msg,
                    is_complete=True
                )

            grounding_context = (
                f"--- CONSOLIDATED KNOWLEDGE (Synthesis & Coherence) ---\n{insights['consolidated_knowledge']}\n\n"
                f"--- VERIFIED EVIDENCE (Grounding Sources) ---\n{insights['verified_evidence']}"
            )

            # 2. Format the prompt
            prompt = ANSWER_GENERATION_PROMPT_TEMPLATE.format(
                initial_query=initial_query,
                grounding_context=grounding_context
            )

            # 3. Call the LLM for synthesis
            raw_answer = self.llm_client(prompt, self.llm_config)

            # FIX: Ensure the LLM output is a string, handling potential None return from the client/mock,
            # which prevents silent failures during ResearchResult instantiation.
            if raw_answer is None:
                raw_answer = "LLM failed to return a response."
            else:
                raw_answer = str(raw_answer)

            # 4. Process and return the result
            result = ResearchResult(
                query=initial_query,
                final_answer=raw_answer,
                supporting_context=grounding_context,
                is_complete=True,
            )
            return result

        except Exception as e:
            # Catch general errors (LLM failure, API issues, formatting errors)
            error_msg = f"Critical Error during answer generation: {type(e).__name__} - {e}"
            print(error_msg) 
            
            return ResearchResult(
                query=initial_query,
                final_answer=f"A critical error occurred during final answer synthesis.",
                supporting_context=error_msg,
                is_complete=False
            )