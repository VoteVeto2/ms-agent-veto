import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from src.llm_client import LLMClient
from src.schemas import MemoryType, EvidenceType

# Configure module logger
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Internal Data Structures for Generation Planning
# -----------------------------------------------------------------------------

class SectionPlan(BaseModel):
    """Blueprint for a specific section of the report."""
    heading: str = Field(..., description="The heading of the section.")
    description: str = Field(..., description="Brief description of what this section covers.")
    key_evidence_ids: List[str] = Field(
        default_factory=list, 
        description="IDs of evidence items critical for this section."
    )

class ReportOutline(BaseModel):
    """Structured outline for the final research report."""
    title: str = Field(..., description="The title of the research report.")
    executive_summary_plan: str = Field(..., description="Plan for the executive summary.")
    sections: List[SectionPlan] = Field(..., description="Ordered list of content sections.")
    conclusion_plan: str = Field(..., description="Plan for the conclusion and future outlook.")

# -----------------------------------------------------------------------------
# Answer Generation Module
# -----------------------------------------------------------------------------

class AnswerGenerator:
    """
    Implements the 'Answer Generation' module of the Deep Research system.
    
    This component synthesizes information from upstream components (Query Planning,
    Information Acquisition, Memory) to generate a coherent, comprehensive, and 
    well-supported response.
    
    Key Capabilities:
    - Integrating diverse upstream information (Memories, Evidence).
    - Structuring reasoning and narrative via dynamic outlining.
    - Synthesizing evidence while maintaining long-range coherence.
    - Generating citations and reconciling conflicting data.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize the AnswerGenerator.

        Args:
            llm_client: Configured client for LLM interactions.
        """
        self.llm = llm_client

    async def generate_report(
        self, 
        query: str, 
        memories: List[Any], 
        evidence: List[Any]
    ) -> str:
        """
        Orchestrates the generation of the final research report.

        Args:
            query: The original user research query.
            memories: List of MemoryItem objects or dicts containing insights.
            evidence: List of Evidence objects or dicts containing raw data.

        Returns:
            A markdown-formatted string containing the final report.
        """
        logger.info(f"Starting answer generation for query: {query}")
        
        # 1. Integrate Upstream Information
        # Consolidate memory and evidence into a context window format
        context_str = self._prepare_context(memories, evidence)
        
        # 2. Structure Reasoning (Outlining)
        # Generate a logical plan for the report before writing full text
        outline = await self._generate_outline(query, context_str)
        
        # 3. Synthesize and Generate
        # Draft the content based on the outline and context
        report_content = await self._draft_report_content(query, outline, context_str)
        
        logger.info("Report generation completed successfully.")
        return report_content

    def _prepare_context(self, memories: List[Any], evidence: List[Any]) -> str:
        """
        Formats memory and evidence into a unified string for the LLM context.
        Handles both Pydantic models and dictionary inputs.
        """
        context_parts = []
        
        # Process Memories
        if memories:
            context_parts.append("## Key Insights & Evolving Memory")
            for mem in memories:
                # Extract attributes safely whether dict or object
                content = mem.get("content") if isinstance(mem, dict) else getattr(mem, "content", str(mem))
                m_type = mem.get("type", "general") if isinstance(mem, dict) else getattr(mem, "type", "general")
                context_parts.append(f"- [{str(m_type).upper()}] {content}")
        
        # Process Evidence
        if evidence:
            context_parts.append("\n## Retrieved Evidence & Sources")
            for idx, ev in enumerate(evidence):
                # Extract attributes safely
                content = ev.get("content", "") if isinstance(ev, dict) else getattr(ev, "content", "")
                source = ev.get("url") if isinstance(ev, dict) else getattr(ev, "url", getattr(ev, "source", "Unknown"))
                ev_id = ev.get("id") if isinstance(ev, dict) else getattr(ev, "id", f"source_{idx+1}")
                
                # Truncate very long evidence to manage context window if necessary
                # (Assuming LLMClient handles token limits, but good practice here)
                snippet = content[:800] + "..." if len(content) > 800 else content
                
                context_parts.append(f"Source ID: [{ev_id}]\nSource: {source}\nContent: {snippet}\n")
                
        return "\n".join(context_parts)

    async def _generate_outline(self, query: str, context_str: str) -> ReportOutline:
        """
        Generates a structured outline to guide the report writing process.
        This step ensures logical flow and coverage of all sub-topics.
        """
        logger.debug("Generating report outline...")
        
        system_prompt = (
            "You are an expert research architect. Your goal is to design a structure for a "
            "comprehensive research report based on the provided context and user query.\n"
            "The structure should:\n"
            "1. Be logical and hierarchical.\n"
            "2. Address the user's intent directly.\n"
            "3. Plan for the reconciliation of any conflicting evidence found in the context.\n"
            "4. Ensure a narrative flow from introduction to conclusion."
        )
        
        user_prompt = (
            f"User Research Query: {query}\n\n"
            f"Gathered Research Context:\n{context_str}\n\n"
            "Create a detailed outline for the final report."
        )
        
        try:
            outline = await self.llm.get_structured_output(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_model=ReportOutline
            )
            return outline
        except Exception as e:
            logger.error(f"Failed to generate structured outline: {e}. Falling back to default.")
            # Fallback structure if LLM fails to return valid JSON
            return ReportOutline(
                title=f"Research Report: {query}",
                executive_summary_plan="Summarize the key findings and answer the query.",
                sections=[
                    SectionPlan(
                        heading="Analysis of Findings", 
                        description="Detailed analysis of the gathered evidence.",
                        key_evidence_ids=[]
                    )
                ],
                conclusion_plan="Synthesize findings and provide a final answer."
            )

    async def _draft_report_content(self, query: str, outline: ReportOutline, context_str: str) -> str:
        """
        Generates the full text of the report based on the outline.
        """
        logger.debug("Drafting full report content...")

        # Construct a text representation of the outline for the prompt
        outline_text = f"Title: {outline.title}\n\n"
        outline_text += f"Executive Summary Plan: {outline.executive_summary_plan}\n\n"
        for section in outline.sections:
            outline_text += f"### Section: {section.heading}\n"
            outline_text += f"Goal: {section.description}\n"
            if section.key_evidence_ids:
                outline_text += f"Key Sources: {', '.join(section.key_evidence_ids)}\n"
            outline_text += "\n"
        outline_text += f"Conclusion Plan: {outline.conclusion_plan}"

        system_prompt = (
            "You are an advanced AI research assistant. Your task is to write a professional, "
            "long-form research report based on the provided outline and context.\n\n"
            "Guidelines:\n"
            "1. **Grounding**: Every claim must be supported by the provided evidence. "
            "Use citation markers like [source_id] or [1] referring to the Source IDs in the context.\n"
            "2. **Synthesis**: Do not just list facts. Synthesize information to answer the query. "
            "If evidence conflicts, explicitly discuss the conflict and weigh the reliability of sources.\n"
            "3. **Structure**: Follow the provided outline strictly. Use Markdown headers (#, ##, ###).\n"
            "4. **Tone**: Objective, analytical, and comprehensive.\n"
            "5. **Completeness**: Ensure the Executive Summary provides a high-level answer, and the Conclusion "
            "offers a final synthesis."
        )

        user_prompt = (
            f"Original Query: {query}\n\n"
            f"Report Outline:\n{outline_text}\n\n"
            f"Available Context & Evidence:\n{context_str}\n\n"
            "Write the full research report in Markdown."
        )

        # We use a standard chat completion here for free-form text generation
        # Assuming LLMClient has a method for this (e.g., get_chat_completion or similar)
        # If strictly using get_structured_output, we would wrap the result in a simple model.
        # Here we assume a direct text generation capability is available or we use a simple wrapper.
        
        class ReportDraft(BaseModel):
            content: str

        try:
            # Using structured output to ensure we get the content field cleanly, 
            # or we could use raw completion if the client supports it.
            # We'll use the structured approach for consistency with the client pattern.
            result = await self.llm.get_structured_output(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_model=ReportDraft
            )
            return result.content
        except Exception as e:
            logger.error(f"Error during report drafting: {e}")
            return "Error: Unable to generate report content due to an internal error."