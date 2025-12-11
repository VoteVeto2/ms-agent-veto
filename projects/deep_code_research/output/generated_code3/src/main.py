# src/main.py

import json
from typing import List, Dict, Any

from client import DeepResearchClient
from models import ResearchQuery, ResearchResult, QueryPlan, KnowledgeChunk

# --- Mock Data Setup (Simulating a complex research scenario) ---

def setup_complex_query() -> ResearchQuery:
    """Sets up a complex, multi-hop research query."""
    return ResearchQuery(
        query_id="DRQ-2024-001",
        initial_question="Analyze the comparative advantages of sequential vs. tree-based planning paradigms in advanced Retrieval-Augmented Generation systems, focusing on computational cost and error propagation.",
        target_domain="LLM Query Planning & RAG Architectures",
        max_iterations=5
    )

def setup_mock_client() -> DeepResearchClient:
    """Initializes and configures the DeepResearchClient with mock behavior."""
    client = DeepResearchClient()

    # Mocking the core planning and execution steps based on the provided documentation context
    def mock_planner(query: ResearchQuery, memory: List[KnowledgeChunk]) -> QueryPlan:
        print(f"--- Planner Executing for Iteration {len(memory) // 2 + 1} ---")
        
        if len(memory) == 0:
            # Initial Query (Mimicking initial decomposition)
            return QueryPlan(
                plan_id="P001",
                next_queries=["What are the core features of Sequential Planning in RAG?", 
                              "Define Tree-based Planning in the context of multi-hop reasoning."],
                strategy="Initial Decomposition (RAISE/Sequential)",
                status="IN_PROGRESS"
            )
        elif len(memory) < 4:
            # Mid-process query refinement (Mimicking LLatrieval/DRAGIN style refinement)
            last_chunk_text = memory[-1].content if memory else "No prior context."
            
            if "computational cost" in last_chunk_text:
                return QueryPlan(
                    plan_id="P002",
                    next_queries=["Quantify the latency impact of excessive reasoning turns.", 
                                  "How does error propagation manifest in sequential planning chains?"],
                    strategy="Refinement based on Cost/Error gap (LLatrieval/ReSP)",
                    status="IN_PROGRESS"
                )
            else:
                 return QueryPlan(
                    plan_id="P003",
                    next_queries=["Contrast Tree-based search algorithms (DAG vs Tree) [51]."],
                    strategy="Deeper dive into Tree Structure (Tree-based Planning)",
                    status="IN_PROGRESS"
                )
        else:
            # Final synthesis trigger
            return QueryPlan(
                plan_id="P_FINAL",
                next_queries=[],
                strategy="SYNTHESIZE_ANSWER",
                status="COMPLETE"
            )

    def mock_acquirer(queries: List[str]) -> List[KnowledgeChunk]:
        print(f"--- Information Acquisition for {len(queries)} queries ---")
        chunks = []
        for i, q in enumerate(queries):
            if "Sequential Planning" in q:
                chunks.append(KnowledgeChunk(
                    source_id=f"S{i+1}",
                    content="Sequential planning allows dynamic, context-aware reasoning but incurs substantial computational costs and latency due to deep reasoning chains.",
                    relevance_score=0.95
                ))
            elif "Tree-based Planning" in q:
                chunks.append(KnowledgeChunk(
                    source_id=f"S{i+2}",
                    content="Tree-based planning uses DAG structures, enabling advanced search algorithms, integrating parallel and sequential features.",
                    relevance_score=0.92
                ))
            elif "Quantify the latency impact" in q:
                 chunks.append(KnowledgeChunk(
                    source_id=f"S{i+3}",
                    content="Excessive reasoning turns can lead to latency increases of up to 300% compared to static pipelines.",
                    relevance_score=0.88
                ))
            elif "Contrast Tree-based search algorithms" in q:
                 chunks.append(KnowledgeChunk(
                    source_id=f"S{i+4}",
                    content="Tree-based methods leverage advanced search algorithms on structured spaces (DAGs), offering better control than purely sequential methods.",
                    relevance_score=0.90
                ))
            else:
                chunks.append(KnowledgeChunk(
                    source_id=f"S{i+5}",
                    content=f"General context retrieved for: {q}.",
                    relevance_score=0.75
                ))
        return chunks

    def mock_generator(final_context: List[KnowledgeChunk]) -> str:
        print("--- Answer Generation Phase ---")
        # Simple aggregation for demonstration
        context_summary = "\n".join([f"- [{c.source_id}] {c.content[:80]}..." for c in final_context])
        
        return f"""
        Final Verified Answer:
        The comparative analysis reveals that Sequential Planning offers dynamic, context-aware reasoning but suffers from high computational costs and latency due to deep chains. Tree-based Planning mitigates some of these issues by structuring the search space as a DAG, allowing for more controlled, hybrid search strategies. The primary disadvantage of sequential methods is the risk of cumulative error propagation over many turns.
        
        --- Context Used ---
        {context_summary}
        """

    client.set_planner(mock_planner)
    client.set_information_acquirer(mock_acquirer)
    client.set_answer_generator(mock_generator)
    
    return client

# --- Main Execution Logic ---

def execute_deep_research_workflow():
    """
    Demonstrates the instantiation and usage of the DeepResearchClient 
    to execute a complex, iterative research workflow.
    """
    print("--- Deep Research Workflow Simulation Started ---")
    
    try:
        # 1. Setup Component Decomposition (System Initialization)
        client = setup_mock_client()
        query = setup_complex_query()
        
        print(f"\n[System Component Mapping]")
        print("Query Planning: Handled by client.plan_query()")
        print("Information Acquisition: Handled by client.acquire_information()")
        print("Memory Management: Handled internally by client.execute_workflow()")
        print("Answer Generation: Handled by client.generate_answer()")
        
        print(f"\n[Initial Query Setup]")
        print(f"Question: {query.initial_question}")
        print(f"Max Iterations: {query.max_iterations}")
        
        # 2. Execute the Workflow (Paradigm in Action)
        result: ResearchResult = client.execute_workflow(query)
        
        # 3. Display Results
        print("\n" + "="*50)
        print("WORKFLOW EXECUTION COMPLETE")
        print("="*50)
        
        print(f"Total Iterations Run: {result.iterations_run}")
        print(f"Final Status: {result.status}")
        
        print("\n--- Final Answer ---")
        print(result.final_answer)
        
        print("\n--- Plan Trace Summary ---")
        for step in result.plan_trace:
            print(f"Iter {step.iteration}: Strategy='{step.plan.strategy}', Queries={len(step.plan.next_queries)}")

    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred during the research workflow:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Details: {e}")

if __name__ == "__main__":
    execute_deep_research_workflow()