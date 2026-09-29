import json
import logging
from typing import Optional, List
from groq import Groq
from app.config import GROQ_API_KEY, LLM_MODEL
from app.models import IncidentInput, RecalledMemoryItem, StructuredRecommendation, ReflectionAnalysis

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Oncall Incident Response Agent: "When production breaks, the agent doesn't start from zero."

Your purpose: Given an ongoing production incident and historical incidents recalled from Hindsight memory bank ("oncall-memory"), reason over past experiences and recommend the optimal fix with calibrated confidence.

CRITICAL REASONING & RELEVANCE RULES:
1. SERVICE INTEGRITY:
   - Check the service of each memory against the current incident's service.
   - If a memory is from a DIFFERENT service (e.g. 'order-service' when current incident is 'login-service'), it is ONLY a conceptual cross-service analogy.
   - NEVER attribute internal components, classes, or bugs from a different service (e.g. "OrderPaymentProcessor", "PaymentGatewayClient", or "order-service") to the current incident's service!
2. CONFIDENCE CALIBRATION:
   - "high": ONLY when there is a confirmed historical resolution for the SAME target service with a verified WORKED or FAILED outcome.
   - "medium": When there are plausible cross-service analogies or general symptom patterns, but NO verified resolution for the target service.
   - "low": When no relevant historical memories exist (cold start).
3. WORKED vs FAILED FIXES:
   - If a same-service memory shows a fix WORKED, recommend that verified solution.
   - If a same-service memory shows a fix FAILED, you MUST issue a prominent warning against repeating that failed remedy.
4. CITATIONS & HISTORICAL EVIDENCE:
   - In "citing", if a same-service memory exists, cite it directly by date, service, and outcome.
   - If NO same-service memory exists, explicitly state: "No historical resolution found for <service>. Starting with cautious exploratory triage."
5. LIKELY ROOT CAUSE:
   - For same-service direct matches: Cite the proven historical root cause.
   - When no same-service memory exists: Formulate a cautious, objective root cause based strictly on the current incident's own symptoms and error logs (e.g. "Database connection exhaustion in login-service; root cause unconfirmed in historical records").

You MUST respond strictly with a valid JSON object matching this schema:
{
  "likely_root_cause": "<concise, precise root cause description>",
  "confidence": "high" | "medium" | "low",
  "historical_evidence": ["<bullet point 1 citing past incident/outcome>", "<bullet point 2>"],
  "recommended_fix": "<concrete, actionable mitigation and permanent fix, calling out what WORKED vs FAILED>",
  "citing": "<e.g. same issue on 12 Aug, fix that worked was X, while Y failed>",
  "runbook": [
    "<Step 1 action>",
    "<Step 2 action>",
    "<Step 3 verification>"
  ]
}
"""

class LLMService:
    def __init__(self, api_key: str = GROQ_API_KEY, model: str = LLM_MODEL):
        self.api_key = api_key
        self.model = model
        self._client: Optional[Groq] = None

    def get_client(self) -> Optional[Groq]:
        if not self.api_key:
            return None
        if self._client is None:
            self._client = Groq(api_key=self.api_key)
        return self._client

    def generate_recommendation(
        self,
        incident: IncidentInput,
        memories: List[RecalledMemoryItem],
        include_memories: bool = True
    ) -> StructuredRecommendation:
        """
        Generate structured recommendation using Groq LLM.
        If include_memories is False, runs the baseline "No Memory" reasoning.
        """
        client = self.get_client()

        # Build prompt
        user_prompt = self._build_user_prompt(incident, memories if include_memories else [])

        if client:
            try:
                return self._call_groq(client, user_prompt)
            except Exception as e:
                logger.warning(f"Initial Groq LLM call failed: {e}. Retrying once with strict schema prompt...")
                try:
                    retry_prompt = user_prompt + "\n\nCRITICAL: Return ONLY raw valid JSON. Do not wrap in markdown or backticks."
                    return self._call_groq(client, retry_prompt)
                except Exception as retry_err:
                    logger.error(f"Groq retry also failed: {retry_err}. Falling back gracefully.")
                    return self._fallback_recommendation(incident, memories if include_memories else [], error_detail=str(retry_err))
        else:
            logger.info("GROQ_API_KEY not configured. Generating deterministic expert analysis.")
            return self._fallback_recommendation(incident, memories if include_memories else [])

    def _call_groq(self, client: Groq, user_prompt: str) -> StructuredRecommendation:
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=2048,
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        return StructuredRecommendation.model_validate(parsed)

    def _build_user_prompt(self, incident: IncidentInput, memories: List[RecalledMemoryItem]) -> str:
        prompt = [
            "CURRENT INCIDENT REPORT:",
            f"- Title: {incident.title}",
            f"- Service: {incident.service}",
            f"- Description: {incident.description}",
            f"- Symptoms: {incident.symptoms}",
            f"- Error Logs:\n{incident.error_logs}\n"
        ]

        same_service_memories = [m for m in memories if m.is_same_service or (m.relevance_grade == "direct_match")]
        analogy_memories = [m for m in memories if not (m.is_same_service or (m.relevance_grade == "direct_match"))]

        if same_service_memories:
            prompt.append(f"DIRECT HISTORICAL PRECEDENTS (VERIFIED FOR SERVICE '{incident.service}'):")
            for i, m in enumerate(same_service_memories, 1):
                prompt.append(f"{i}. [Score: {m.score}] {m.text}")
            prompt.append("RULE: Since verified precedents exist for this service, prioritize what WORKED and warn against what FAILED. Confidence may be 'high' if matching.")
        
        if analogy_memories:
            prompt.append("\nCROSS-SERVICE ANALOGIES (FROM OTHER SERVICES - FOR GENERAL PATTERN ONLY):")
            for i, m in enumerate(analogy_memories, 1):
                prompt.append(f"- {m.text}")
            prompt.append(f"CRITICAL RULE: The memories above are from OTHER services (not '{incident.service}'). DO NOT attribute their internal components, classes, or service names (e.g. OrderPaymentProcessor) to '{incident.service}'.")

        if not same_service_memories and not analogy_memories:
            prompt.append(f"NO HISTORICAL MEMORIES AVAILABLE FOR '{incident.service}'. (Cold start - no prior incident records).")
            prompt.append("RULE: Confidence MUST be 'low'. Provide cautious exploratory troubleshooting steps.")
        elif not same_service_memories:
            prompt.append(f"\nCRITICAL INSTRUCTION: There are NO verified historical resolutions for '{incident.service}'. Confidence MUST NOT be 'high' (use 'medium' or 'low'). In 'citing', explicitly state: \"No historical resolution found for {incident.service}.\"")

        return "\n".join(prompt)

    def _fallback_recommendation(
        self,
        incident: IncidentInput,
        memories: List[RecalledMemoryItem],
        error_detail: Optional[str] = None
    ) -> StructuredRecommendation:
        """
        Deterministic, robust fallback when Groq LLM is not configured or during API failure,
        strictly respecting service boundaries and calibrated confidence.
        """
        from app.relevance import parse_incident_memory

        same_service_memories = [m for m in memories if m.is_same_service or (m.relevance_grade == "direct_match")]
        analogy_memories = [m for m in memories if not (m.is_same_service or (m.relevance_grade == "direct_match"))]

        # Check for direct same-service matches
        if same_service_memories:
            worked_fixes = []
            failed_fixes = []
            best_root_cause = None

            for m in same_service_memories:
                parsed = parse_incident_memory(m.text)
                if parsed.get("root_cause") and not best_root_cause:
                    best_root_cause = parsed["root_cause"]
                
                outcome = parsed.get("outcome") or m.outcome
                fix = parsed.get("fix")
                if outcome == "WORKED" and fix:
                    worked_fixes.append(fix)
                elif outcome == "FAILED" and fix:
                    failed_fixes.append(fix)

            if worked_fixes:
                likely_root = best_root_cause or f"Verified recurring issue in {incident.service}"
                warning = f" (Warning: previous attempt '{failed_fixes[0]}' FAILED; do not repeat)" if failed_fixes else ""
                recommended_fix = f"Apply verified fix: {worked_fixes[0]}.{warning}"
                citing = f"Matched verified historical resolution for {incident.service}. Fix that worked: {worked_fixes[0]}"
                confidence = "high"
                evidence = [m.text for m in same_service_memories[:3]]
                runbook = [
                    f"1. Verify symptoms match historical precedent for {incident.service}",
                    f"2. Apply validated fix: {worked_fixes[0]}",
                    f"3. Do NOT attempt failed remedies: {', '.join(failed_fixes) if failed_fixes else 'None recorded'}",
                    "4. Monitor error rates, latency, and pool metrics for stabilization",
                    "5. Confirm resolution and retain outcome in OnCall Memory"
                ]
            else:
                # Same service memory exists, but only FAILED fixes recorded!
                likely_root = best_root_cause or f"Known unresolved failure pattern in {incident.service}"
                failed_desc = failed_fixes[0] if failed_fixes else "previous attempted remedy"
                recommended_fix = f"CRITICAL WARNING: Do NOT attempt '{failed_desc}' as it historically FAILED for {incident.service}. Conduct exploratory diagnostics."
                citing = f"Referenced past incident for {incident.service}: Previous fix '{failed_desc}' FAILED. Alternative remedy required."
                confidence = "medium"
                evidence = [m.text for m in same_service_memories[:3]]
                runbook = [
                    f"1. AVOID repeat of failed action: {failed_desc}",
                    f"2. Inspect active threads and connection states for {incident.service}",
                    "3. Validate upstream/downstream dependency health",
                    "4. Implement cautious isolated mitigation and monitor telemetry"
                ]
        elif analogy_memories:
            # Cross-service analogies exist, but NO direct match for this service!
            confidence = "medium"
            # Formulate root cause from the incident's own symptoms, NEVER from order-service
            if "connection" in incident.title.lower() or "connection" in incident.symptoms.lower():
                likely_root = f"Database connection pool exhaustion or timeout in {incident.service} (Unconfirmed in historical records)"
                rec_fix = f"Audit {incident.service} database connection pool limits, verify DB network latency, and check for unreleased connections or slow queries."
            elif "memory" in incident.title.lower() or "oom" in incident.symptoms.lower():
                likely_root = f"Memory pressure or memory leak in {incident.service} (Unconfirmed in historical records)"
                rec_fix = f"Inspect JVM/heap metrics for {incident.service}, profile active allocations, and consider temporary replica scaling."
            else:
                likely_root = f"Unconfirmed failure mode for {incident.title} in {incident.service}"
                rec_fix = f"Review recent deployment diffs and telemetry for {incident.service}; check downstream service dependencies."

            citing = f"No historical resolution found for service '{incident.service}'. Identified conceptual patterns from related services."
            evidence = [f"[Analogy from {m.service or 'other service'}]: {m.text}" for m in analogy_memories[:2]]
            runbook = [
                f"1. Perform telemetry triage on {incident.service} dashboard",
                f"2. Check error log timestamps against recent releases or load spikes",
                f"3. Verify database / dependency health and connection availability",
                "4. Note: No verified precedent for this service; proceed with cautious exploratory steps",
                "5. Document root cause and verified fix in OnCall Memory upon resolution"
            ]
        else:
            # Cold start - zero memories
            likely_root = f"Unconfirmed failure for {incident.title} in {incident.service} (Cold start - no historical context)"
            confidence = "low"
            recommended_fix = f"Perform initial telemetry triage on {incident.service}, inspect error logs, and check infrastructure metrics."
            citing = f"No historical incident memories found for {incident.service}. Starting from baseline."
            evidence = []
            runbook = [
                f"1. Inspect {incident.service} telemetry dashboard and error spikes",
                "2. Check recent commit / deployment diffs",
                "3. Verify network and dependency health",
                "4. Document root cause upon resolution for future oncall memory"
            ]

        return StructuredRecommendation(
            likely_root_cause=likely_root,
            confidence=confidence,
            historical_evidence=evidence,
            recommended_fix=recommended_fix,
            citing=citing,
            runbook=runbook
        )

    def generate_reflection(
        self,
        incident: IncidentInput,
        memories: List[dict],
        hindsight_text: Optional[str] = None
    ) -> ReflectionAnalysis:
        """
        Synthesizes a deep systemic reflection over the incident and Hindsight's reflect output.
        Identifies systemic vulnerabilities, recurrence risks, and long-term architectural prevention.
        """
        client = self.get_client()

        reflection_system_prompt = """You are the Oncall Incident Response Agent: Reflective Post-Mortem & Resilience Engine.
Given an incident and historical memories retrieved by Hindsight's reflect engine, analyze:
1. Systemic root cause: Deep architectural vulnerability rather than surface symptoms.
2. Pattern recognition: How this failure connects to wider historical trends across services.
3. Recurrent risk: What will fail or cascade next if only a temporary patch is applied.
4. Architectural fix: Long-term engineering resilience and systemic design fix.
5. Prevention runbook: Concrete preventative guardrails for platform/SRE teams.

Return strictly a valid JSON object matching this schema:
{
  "systemic_root_cause": "<concise explanation of underlying architectural weakness>",
  "pattern_recognition": "<connection to past incident patterns and memory bank records>",
  "recurrent_risk": "<what will cascade or fail next if unmitigated>",
  "architectural_fix": "<permanent resilience architectural redesign>",
  "prevention_runbook": [
    "<Guardrail 1: monitoring or circuit breaker threshold>",
    "<Guardrail 2: chaos test or automated load test>",
    "<Guardrail 3: schema/resource contract validation>"
  ]
}
"""
        mem_texts = [m.get("text", "") for m in memories[:6]]
        user_prompt = f"""INCIDENT FOR REFLECTION:
- Title: {incident.title}
- Service: {incident.service}
- Description: {incident.description}
- Symptoms: {incident.symptoms}
- Logs: {incident.error_logs}

HINDSIGHT REFLECTED MEMORIES & PRECEDENTS:
{chr(10).join(f"- {t}" for t in mem_texts if t)}

HINDSIGHT REFLECTION TEXT:
{hindsight_text or 'Direct memory synthesis active.'}
"""

        if client:
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": reflection_system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=2048,
                )
                content = response.choices[0].message.content or "{}"
                parsed = json.loads(content)
                return ReflectionAnalysis.model_validate(parsed)
            except Exception as e:
                logger.warning(f"Groq reflection failed: {e}. Using deterministic reflection fallback.")
                return self._fallback_reflection(incident, memories)
        else:
            return self._fallback_reflection(incident, memories)

    def _fallback_reflection(self, incident: IncidentInput, memories: List[dict]) -> ReflectionAnalysis:
        service = incident.service
        title = incident.title
        has_mem = len(memories) > 0

        if "connection" in title.lower() or "pool" in title.lower() or "postgres" in title.lower():
            return ReflectionAnalysis(
                systemic_root_cause="Unbounded database connection acquisition without mandatory timeouts or leak detection in client transaction managers.",
                pattern_recognition="Recurrent downstream dependency saturation pattern observed across database tiers during flash sales and traffic surges.",
                recurrent_risk="Unmitigated pool exhaustion will cascade into API gateway thread starvation, triggering HTTP 504 cascades across frontend clients.",
                architectural_fix="Implement strict HikariCP leakDetectionThreshold (2000ms), clamp maximumLifetime, and place all external third-party calls outside DB transaction boundaries.",
                prevention_runbook=[
                    "Configure alerting on DB pool usage > 80% sustained for 30s",
                    "Add automated CI rule banning external HTTP calls inside @Transactional blocks",
                    "Execute chaos monkey connection latency injection test bi-weekly",
                    "Establish automated read-replica fallback for catalog queries"
                ]
            )
        elif "oom" in title.lower() or "memory" in title.lower():
            return ReflectionAnalysis(
                systemic_root_cause="Unbounded in-memory batch accumulation without backpressure or ring-buffer limits during consumer bursts.",
                pattern_recognition="Correlates with past notification-worker OOM incidents where increasing pod memory limits only delayed crash time rather than resolving memory retention.",
                recurrent_risk="Repeated OOMKills cause consumer group rebalances, causing message processing lag to compound exponentially.",
                architectural_fix="Replace unbounded slices with bounded ring buffers (cap=10,000) and sync.Pool memory recycling.",
                prevention_runbook=[
                    "Implement proactive memory watermark alerts at 75% of cgroup limit",
                    "Deploy rate-limiting backpressure on Kafka consumer fetch size",
                    "Run automated soak tests validating flat RSS under 24h sustained load"
                ]
            )
        else:
            return ReflectionAnalysis(
                systemic_root_cause=f"Fragile service boundary resilience on {service} under non-standard latency deviations.",
                pattern_recognition=f"Connects to historical operational telemetry in {service}; recurring failure modes highlight missing isolation boundaries.",
                recurrent_risk="Localized latency degradation risks propagating upstream into user-facing checkout and auth flows.",
                architectural_fix="Introduce circuit breaker wrappers (resilience4j/hystrix) with fail-fast defaults and fallback caches.",
                prevention_runbook=[
                    f"Audit {service} dependencies for strict 2s request timeouts",
                    "Enforce synthetic heartbeat probes validating external integration latency",
                    "Review runbook in Hindsight bank 'oncall-memory' post incident resolution"
                ]
            )


# Singleton LLM service instance
llm_service = LLMService()
