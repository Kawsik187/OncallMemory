import re
import logging
from typing import List, Dict, Optional, Tuple, Literal
from app.models import IncidentInput, RecalledMemoryItem

logger = logging.getLogger(__name__)

STOPWORDS = {
    "the", "is", "are", "and", "a", "an", "to", "in", "of", "for", "with", "on", 
    "at", "by", "from", "service", "error", "occurred", "during", "request", 
    "requests", "after", "while", "which", "about", "other", "their", "there",
    "incident", "symptoms", "logs", "cause", "root", "worked", "failed"
}

def parse_incident_memory(text: str) -> Dict[str, Optional[str]]:
    """
    Parses a standardized incident memory string:
    [DATE] INCIDENT: <title> | SERVICE: <service> | ROOT CAUSE: <cause> | FIX (<outcome>): <fix>
    Returns a dictionary of extracted components.
    """
    date_match = re.search(r"^\[(.*?)\]", text)
    date = date_match.group(1).strip() if date_match else None

    # Service extraction
    svc_match = re.search(r"\|\s*SERVICE:\s*([^|]+)", text, re.IGNORECASE)
    if not svc_match:
        svc_match = re.search(r"\bSERVICE:\s*([^\n|]+)", text, re.IGNORECASE)
    service = svc_match.group(1).strip() if svc_match else None

    # Title extraction
    title_match = re.search(r"INCIDENT:\s*([^|]+)", text, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else None

    # Root Cause extraction
    cause_match = re.search(r"\|\s*ROOT CAUSE:\s*([^|]+)", text, re.IGNORECASE)
    if not cause_match:
        cause_match = re.search(r"\bROOT CAUSE:\s*([^\n|]+)", text, re.IGNORECASE)
    root_cause = cause_match.group(1).strip() if cause_match else None

    # Fix Outcome extraction (WORKED or FAILED)
    outcome_match = re.search(r"FIX\s*\((WORKED|FAILED)\):", text, re.IGNORECASE)
    outcome = outcome_match.group(1).upper() if outcome_match else None

    # Fix description extraction
    fix_match = re.search(r"FIX\s*\([^)]+\):\s*(.+)", text, re.IGNORECASE)
    fix = fix_match.group(1).strip() if fix_match else None

    return {
        "date": date,
        "title": title,
        "service": service,
        "root_cause": root_cause,
        "outcome": outcome,
        "fix": fix
    }

def is_matching_service(mem_service: Optional[str], incident_service: str) -> bool:
    """
    Compares memory service and incident service with normalization.
    """
    if not mem_service or not incident_service:
        return False
    m_clean = mem_service.strip().lower()
    i_clean = incident_service.strip().lower()
    if m_clean == i_clean:
        return True
    
    # Normalize dashes and underscores: "order-service" == "order_service"
    m_norm = re.sub(r"[-_\s]", "", m_clean)
    i_norm = re.sub(r"[-_\s]", "", i_clean)
    return m_norm == i_norm

def compute_text_overlap(text: str, incident: IncidentInput) -> float:
    """
    Computes keyword token overlap between the incident symptoms/error logs and memory text.
    """
    target_text = f"{incident.title} {incident.symptoms} {incident.error_logs} {incident.description}".lower()
    tokens = re.findall(r"\b[a-zA-Z0-9_-]{4,}\b", target_text)
    sig_tokens = set([t for t in tokens if t not in STOPWORDS])
    if not sig_tokens:
        return 0.0

    mem_lower = text.lower()
    matches = sum(1 for t in sig_tokens if t in mem_lower)
    return matches / len(sig_tokens)

def rank_and_filter_memories(
    memories: List[RecalledMemoryItem],
    incident: IncidentInput,
    max_results: int = 5
) -> List[RecalledMemoryItem]:
    """
    Enriches, ranks, and filters memories based on service match, keyword similarity,
    and Hindsight scores.
    
    Categorizes memories into:
    1. Direct Matches: Same service, directly relevant to the target service.
    2. Cross-Service Analogies: Different service, but high symptom/error overlap.
    3. Low/Irrelevant: Filtered out to avoid cluttering LLM context.
    """
    # Deduplicate memories by normalized incident content
    seen_texts = set()
    deduped_memories: List[RecalledMemoryItem] = []
    for m in memories:
        norm = re.sub(r"\(mentioned_at=[^)]+\)", "", m.text).strip()
        if norm not in seen_texts:
            seen_texts.add(norm)
            deduped_memories.append(m)

    direct_matches: List[RecalledMemoryItem] = []
    analogies: List[RecalledMemoryItem] = []

    for m in deduped_memories:
        parsed = parse_incident_memory(m.text)
        service = parsed.get("service")
        outcome = parsed.get("outcome")
        same_service = is_matching_service(service, incident.service)
        overlap = compute_text_overlap(m.text, incident)
        raw_score = m.score if m.score is not None else 0.0

        if same_service:
            # Significant boost for exact service match; WORKED fixes prioritized slightly
            worked_bonus = 0.08 if outcome == "WORKED" else 0.0
            comp_score = 0.60 + (raw_score * 0.20) + (overlap * 0.12) + worked_bonus
            grade: Literal["direct_match", "analogy", "low"] = "direct_match"
            reason = f"Verified historical resolution for service '{incident.service}'"
        elif overlap >= 0.25 and (raw_score >= 0.40 or overlap >= 0.40):
            # Cross-service analogy: similar failure pattern, but DIFFERENT service
            comp_score = min(0.25 + (raw_score * 0.35) + (overlap * 0.40), 0.65)
            grade = "analogy"
            reason = f"Cross-service analogy from '{service or 'external'}' with similar symptoms"
        else:
            comp_score = raw_score * 0.20
            grade = "low"
            reason = "Low relevance or unrelated service"

        # Enrich memory item
        m.score = round(comp_score, 3)
        m.service = service
        m.is_same_service = same_service
        m.outcome = outcome  # type: ignore
        m.relevance_grade = grade
        m.relevance_reason = reason

        if grade == "direct_match":
            direct_matches.append(m)
        elif grade == "analogy":
            analogies.append(m)

    # Sort groups by composite score descending
    direct_matches.sort(key=lambda x: x.score or 0.0, reverse=True)
    analogies.sort(key=lambda x: x.score or 0.0, reverse=True)

    if direct_matches:
        # When direct matches exist for this service, prioritize them!
        result = direct_matches[:4]
        # Include at most 1 top analogy for broad context if room permits
        if len(result) < max_results and analogies:
            result.append(analogies[0])
        logger.info(
            f"Filtered memories for service '{incident.service}': {len(direct_matches)} direct match(es), "
            f"{len(analogies)} analogy(ies). Returning {len(result)} items."
        )
        return result
    else:
        # No direct matches exist for this service!
        # Return at most 2-3 top analogies, clearly tagged
        result = analogies[:3]
        logger.info(
            f"No direct matches found for service '{incident.service}'. "
            f"Returning {len(result)} cross-service analogies."
        )
        return result
