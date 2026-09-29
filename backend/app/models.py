from datetime import datetime, timezone
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

class IncidentInput(BaseModel):
    title: str = Field(..., description="Alert or incident title, e.g. 'Database Connection Pool Exhausted'")
    service: str = Field(..., description="Affected service name, e.g. 'order-service'")
    description: str = Field("", description="Summary description of what is occurring")
    symptoms: str = Field("", description="Observed user-facing symptoms and metric deviations")
    error_logs: str = Field("", description="Raw logs or stack traces from the incident")

    def to_query_text(self) -> str:
        parts = [f"SERVICE: {self.service}", f"INCIDENT: {self.title}"]
        if self.description:
            parts.append(f"DESCRIPTION: {self.description}")
        if self.symptoms:
            parts.append(f"SYMPTOMS: {self.symptoms}")
        if self.error_logs:
            parts.append(f"LOGS: {self.error_logs}")
        return "\n".join(parts)


class IncidentResolution(BaseModel):
    title: str = Field(..., description="Incident alert/title")
    service: str = Field(..., description="Service name")
    root_cause: str = Field(..., description="Identified root cause")
    fix: str = Field(..., description="Fix applied or attempted")
    outcome: Literal["WORKED", "FAILED"] = Field(..., description="Whether this fix WORKED or FAILED")
    date: Optional[str] = Field(None, description="Date of resolution, e.g. '12 Aug 2026' or current date")

    def to_hindsight_content(self) -> str:
        date_str = self.date or datetime.now(timezone.utc).strftime("%d %b %Y")
        # Format: "[DATE] INCIDENT: <alert/title> | SERVICE: <service> | ROOT CAUSE: <cause> | FIX (WORKED or FAILED): <fix description>"
        return f"[{date_str}] INCIDENT: {self.title} | SERVICE: {self.service} | ROOT CAUSE: {self.root_cause} | FIX ({self.outcome}): {self.fix}"


class RecalledMemoryItem(BaseModel):
    id: Optional[str] = None
    text: str
    type: Optional[str] = None
    score: Optional[float] = None
    entities: Optional[list[Any]] = None
    metadata: Optional[dict[str, Any]] = None
    relevance_reason: Optional[str] = None
    service: Optional[str] = None
    is_same_service: bool = False
    outcome: Optional[Literal["WORKED", "FAILED"]] = None
    relevance_grade: Optional[Literal["direct_match", "analogy", "low"]] = None



class StructuredRecommendation(BaseModel):
    likely_root_cause: str = Field(..., description="Probable root cause based on symptoms and historical evidence")
    confidence: Literal["high", "medium", "low"] = Field(..., description="Confidence level in the assessment")
    historical_evidence: list[str] = Field(default_factory=list, description="Historical facts or past incidents recalled")
    recommended_fix: str = Field(..., description="Actionable recommended fix")
    citing: str = Field(..., description="Specific citation of past incidents, e.g. 'same issue on 12 Aug, fix that worked was X'")
    runbook: list[str] = Field(default_factory=list, description="Step-by-step mitigation or verification actions")


class IncidentResponsePayload(BaseModel):
    incident: IncidentInput
    recalled_memories: list[RecalledMemoryItem]
    recommendation: StructuredRecommendation
    hindsight_available: bool
    hindsight_message: Optional[str] = None
    model_used: str


class ComparisonResponse(BaseModel):
    incident: IncidentInput
    with_memory: StructuredRecommendation
    without_memory: StructuredRecommendation
    recalled_memories: list[RecalledMemoryItem]
    hindsight_available: bool
    contrast_summary: str


class ReflectMemoryItem(BaseModel):
    id: Optional[str] = None
    text: str
    type: Optional[str] = None


class ReflectionAnalysis(BaseModel):
    systemic_root_cause: str = Field(..., description="Deep underlying architectural vulnerability")
    pattern_recognition: str = Field(..., description="Historical pattern connecting past failure modes")
    recurrent_risk: str = Field(..., description="Potential cascade or failure if not permanently mitigated")
    architectural_fix: str = Field(..., description="Long-term architectural and resilience fix")
    prevention_runbook: list[str] = Field(default_factory=list, description="Preventative SRE checklist and guardrails")


class ReflectResponsePayload(BaseModel):
    incident: IncidentInput
    hindsight_reflection_text: Optional[str] = None
    based_on_memories: list[ReflectMemoryItem] = Field(default_factory=list)
    reflection: ReflectionAnalysis
    hindsight_available: bool
    hindsight_message: Optional[str] = None
    model_used: str
