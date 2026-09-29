import logging
from app.models import (
    IncidentInput,
    IncidentResolution,
    IncidentResponsePayload,
    ComparisonResponse,
    StructuredRecommendation,
    ReflectResponsePayload,
    ReflectMemoryItem
)
from app.hindsight_service import hindsight_service
from app.llm_service import llm_service
from app.config import LLM_MODEL

logger = logging.getLogger(__name__)

class IncidentAgent:
    """
    Oncall Incident Response Agent orchestrator.
    Core loop:
    1. New incident comes in
    2. Recall similar incidents from Hindsight (bank_id="oncall-memory")
    3. Reason over recalled memories using Groq LLM
    4. Provide structured recommendation + historical evidence
    5. Retain incident resolution into Hindsight on closure
    6. Reflect over memories and failure trends to prevent future recurrence
    """

    def analyze(self, incident: IncidentInput) -> IncidentResponsePayload:
        query_text = incident.to_query_text()
        logger.info(f"Agent analyzing incident: '{incident.title}' on service '{incident.service}'")

        # Step 2: Recall from Hindsight with incident context
        memories, is_available, status_msg = hindsight_service.recall(query=query_text, incident=incident)

        # Step 3: Reason with Groq LLM
        recommendation = llm_service.generate_recommendation(
            incident=incident,
            memories=memories,
            include_memories=True
        )

        return IncidentResponsePayload(
            incident=incident,
            recalled_memories=memories,
            recommendation=recommendation,
            hindsight_available=is_available,
            hindsight_message=status_msg,
            model_used=LLM_MODEL
        )

    def compare(self, incident: IncidentInput) -> ComparisonResponse:
        """
        Runs side-by-side comparison:
        - With Hindsight Memory
        - Without Memory (cold start baseline)
        Proves memory value in a single glance.
        """
        query_text = incident.to_query_text()
        memories, is_available, _ = hindsight_service.recall(query=query_text, incident=incident)

        with_memory = llm_service.generate_recommendation(
            incident=incident,
            memories=memories,
            include_memories=True
        )

        without_memory = llm_service.generate_recommendation(
            incident=incident,
            memories=[],
            include_memories=False
        )

        same_service_mems = [m for m in memories if m.is_same_service]
        if same_service_mems:
            mem_summary = f"recalled {len(same_service_mems)} verified precedent(s) for service '{incident.service}'"
        elif memories:
            mem_summary = f"analyzed {len(memories)} cross-service analogies (no direct history for '{incident.service}')"
        else:
            mem_summary = f"noted zero past incidents for '{incident.service}'"

        contrast_summary = (
            f"Without memory, the agent defaulted to generic triage with {without_memory.confidence} confidence. "
            f"With Hindsight memory, it {mem_summary}, calibrated confidence to {with_memory.confidence}, "
            f"and prioritized safe, evidence-backed runbook actions."
        )

        return ComparisonResponse(
            incident=incident,
            with_memory=with_memory,
            without_memory=without_memory,
            recalled_memories=memories,
            hindsight_available=is_available,
            contrast_summary=contrast_summary
        )

    def resolve(self, resolution: IncidentResolution) -> tuple[bool, str, str]:
        """
        Retains the incident resolution experience into Hindsight memory bank 'oncall-memory'.
        Returns (success, message, retained_content).
        """
        content = resolution.to_hindsight_content()
        success, msg = hindsight_service.retain(content=content)
        return success, msg or ("Retained successfully" if success else "Failed to retain"), content

    def reflect(self, incident: IncidentInput) -> ReflectResponsePayload:
        """
        Performs deep systemic reflection across Hindsight memory bank 'oncall-memory'
        using Hindsight's native /reflect endpoint, and synthesizes long-term resilience strategies.
        """
        query_text = incident.to_query_text()
        logger.info(f"Agent reflecting on incident: '{incident.title}' on service '{incident.service}'")

        # Call Hindsight reflect API
        hindsight_text, clean_memories, is_available, status_msg = hindsight_service.reflect(query=query_text)

        # Generate reflection analysis
        reflection = llm_service.generate_reflection(
            incident=incident,
            memories=clean_memories,
            hindsight_text=hindsight_text
        )

        based_on_items = [
            ReflectMemoryItem(
                id=m.get("id"),
                text=m.get("text", ""),
                type=m.get("type", "observation")
            )
            for m in clean_memories
        ]

        return ReflectResponsePayload(
            incident=incident,
            hindsight_reflection_text=hindsight_text,
            based_on_memories=based_on_items,
            reflection=reflection,
            hindsight_available=is_available,
            hindsight_message=status_msg,
            model_used=LLM_MODEL
        )


agent = IncidentAgent()
