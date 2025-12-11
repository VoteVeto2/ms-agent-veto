from typing import List, Dict, Any, Optional, Tuple
from src.llm_interface import LLMInterface
from src.components.memory_management import MemoryManager, MemoryEntry

class AnswerGeneration:
    """
    Implements the Answer Generation component, synthesizing validated insights 
    from memory into a coherent long-form answer.

    This component follows the progressive stages outlined in advanced DR workflows:
    1. Integration of Upstream Information (Evidence, Context, Plan).
    2. Synthesis of Evidence & Maintenance of Coherence.
    3. Structuring the Reasoning and Narrative.
    4. Final Output Generation.
    """

    def __init__(self, llm_interface: LLMInterface, memory_manager: MemoryManager):
        """
        Initializes the Answer Generation component.

        Args:
            llm_interface: Interface to the underlying Large Language Model.
            memory_manager: Interface to the system's long-term and working memory.
        """
        self.llm = llm_interface
        self.memory = memory_manager
        self.system_prompt_base = (
            "You are an expert research synthesis engine. Your task is to generate a "
            "comprehensive, well-supported, and coherent long-form answer based ONLY on the "
            "provided evidence and context. Ensure every claim is grounded. "
            "Structure your response logically, citing sources where applicable."
        )

    def _integrate_upstream_information(
        self,
        original_query: str,
        validated_evidence: List[Dict[str, Any]],
        query_plan_state: Dict[str, Any]
    ) -> str:
        """
        Stage 1: Integrates diverse information sources (evidence, memory state, plan)
        into a unified context block for synthesis.

        Args:
            original_query: The user's initial question.
            validated_evidence: List of retrieved and validated passages/facts.
            query_plan_state: Current state of the query plan (e.g., sub-goal status, explored paths).

        Returns:
            A single, structured string containing all integrated context.
        """
        print("AnswerGeneration: Stage 1 - Integrating upstream information...")
        
        # 1. Retrieve relevant long-term context from memory
        memory_context_entries: List[MemoryEntry] = self.memory.retrieve_contextual_state(
            query=original_query, k=5
        )
        memory_summary = "\n".join(
            [f"Memory Snippet: {entry.content[:200]}..." for entry in memory_context_entries]
        )

        # 2. Format retrieved evidence
        evidence_str = "\n---\n".join(
            [f"Source {i+1} (Relevance Score: {e.get('score', 'N/A')}): {e['text']}" 
             for i, e in enumerate(validated_evidence)]
        )

        # 3. Format query plan state (e.g., from MCTS or PoG)
        plan_state_str = f"Current Plan Status: {query_plan_state.get('status', 'Active')}\n"
        plan_state_str += f"Next Steps/Goals: {query_plan_state.get('next_goals', 'N/A')}"

        # 4. Combine into a cohesive context block
        integrated_context = (
            f"--- ORIGINAL QUERY ---\n{original_query}\n\n"
            f"--- EVOLVING MEMORY CONTEXT ---\n{memory_summary}\n\n"
            f"--- CURRENT QUERY PLAN STATE ---\n{plan_state_str}\n\n"
            f"--- VALIDATED EVIDENCE FOR SYNTHESIS ---\n{evidence_str}\n\n"
            "END OF CONTEXT. Begin synthesis now."
        )
        return integrated_context

    def _synthesize_and_structure(
        self,
        integrated_context: str,
        original_query: str
    ) -> str:
        """
        Stage 2 & 3: Synthesizes evidence, maintains coherence, and structures the reasoning.

        Args:
            integrated_context: The combined context string from Stage 1.
            original_query: The user's initial question.

        Returns:
            The final, structured answer text.
        """
        print("AnswerGeneration: Stages 2 & 3 - Synthesizing evidence and structuring output...")
        
        # System prompt tailored for synthesis and structure
        synthesis_system_prompt = (
            self.system_prompt_base +
            " Your output MUST be structured with clear headings, logical flow, and "
            "must directly address the original query. Do not include meta-commentary "
            "about the evidence integration process in the final answer."
        )

        # The prompt focuses the LLM on the synthesis task using the provided context
        synthesis_prompt = (
            f"Based on the INTEGRATED CONTEXT provided below, generate the final, "
            f"comprehensive answer to the ORIGINAL QUERY: '{original_query}'.\n\n"
            f"INTEGRATED CONTEXT:\n{integrated_context}"
        )

        try:
            final_answer = self.llm.generate_text(
                prompt=synthesis_prompt,
                system_prompt=synthesis_system_prompt,
                temperature=0.2,  # Lower temperature for factual synthesis
                max_tokens=4096
            )
            return final_answer
        except Exception as e:
            print(f"Error during LLM synthesis: {e}")
            return f"Error: Could not generate final answer due to synthesis failure. Context provided: {integrated_context[:500]}..."

    def generate_final_answer(
        self,
        original_query: str,
        validated_evidence: List[Dict[str, Any]],
        query_plan_state: Dict[str, Any]
    ) -> str:
        """
        Executes the full answer generation pipeline.

        Args:
            original_query: The initial question posed by the user.
            validated_evidence: List of evidence objects (e.g., from Information Acquisition).
                                Expected format: [{'text': '...', 'score': 0.9, 'source_id': '...'}]
            query_plan_state: The current state derived from Query Planning (e.g., MCTS tree status).

        Returns:
            The synthesized, long-form answer string.
        """
        if not validated_evidence:
            return "Could not generate an answer. No validated evidence was provided for synthesis."

        # Stage 1: Integration
        integrated_context = self._integrate_upstream_information(
            original_query,
            validated_evidence,
            query_plan_state
        )

        # Stages 2 & 3: Synthesis and Structuring
        final_answer = self._synthesize_and_structure(
            integrated_context,
            original_query
        )
        
        # Stage 4 (Implicit): Output is generated. In advanced systems, this might involve
        # cross-modal checks or citation formatting, which we simulate via the LLM prompt.

        # Update memory with the final answer for future reference
        self.memory.add_entry(
            content=f"Final Answer to Query '{original_query}': {final_answer}",
            metadata={"type": "FinalAnswer", "query": original_query}
        )
        
        print("AnswerGeneration: Pipeline complete.")
        return final_answer

# Example Usage (Requires mock setup for LLMInterface)
if __name__ == '__main__':
    from src.llm_interface import LLMInterface
    from src.components.memory_management import MemoryManager

    # Setup Mock Components
    mock_llm = LLMInterface()
    mock_memory = MemoryManager()

    # Populate memory with some historical context
    mock_memory.add_entry(
        content="The initial hypothesis focused on quantum entanglement, but later evidence suggested classical correlation was more relevant for this specific domain.",
        metadata={"topic": "initial_hypothesis"}
    )

    # Instantiate Answer Generation
    answer_gen = AnswerGeneration(mock_llm, mock_memory)

    # Mock Inputs
    user_query = "What are the primary factors influencing the stability of perovskite solar cells, and how does the recent 2024 paper address moisture degradation?"
    
    mock_evidence = [
        {"text": "Moisture ingress is the leading cause of degradation in hybrid perovskites, primarily through the formation of methylammonium iodide (MAI) hydrates.", "score": 0.95, "source_id": "R101"},
        {"text": "Thermal stress accelerates ion migration, leading to phase segregation (e.g., from the desired black phase to the yellow phase).", "score": 0.88, "source_id": "R102"},
        {"text": "The 2024 paper by Chen et al. introduced a novel hydrophobic passivation layer using long-chain alkylammonium halides, reducing moisture uptake by 70%.", "score": 0.98, "source_id": "R103"},
    ]

    mock_plan_state = {
        "status": "Synthesis Phase Complete",
        "next_goals": "Draft final summary and verify citations.",
        "sub_goal_success": True
    }

    # Run Generation
    final_response = answer_gen.generate_final_answer(
        original_query=user_query,
        validated_evidence=mock_evidence,
        query_plan_state=mock_plan_state
    )

    print("\n" + "="*50)
    print("FINAL GENERATED ANSWER:")
    print("="*50)
    print(final_response)
    print("="*50)