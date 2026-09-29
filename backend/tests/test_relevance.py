import pytest
from app.models import IncidentInput, RecalledMemoryItem
from app.relevance import parse_incident_memory, is_matching_service, compute_text_overlap, rank_and_filter_memories

def test_parse_incident_memory_full():
    text = "[12 Aug 2026] INCIDENT: Postgres Pool Saturation | SERVICE: order-service | ROOT CAUSE: HikariCP connection leak | FIX (WORKED): Apply a webhook circuit breaker"
    parsed = parse_incident_memory(text)
    assert parsed["date"] == "12 Aug 2026"
    assert parsed["title"] == "Postgres Pool Saturation"
    assert parsed["service"] == "order-service"
    assert parsed["root_cause"] == "HikariCP connection leak"
    assert parsed["outcome"] == "WORKED"
    assert parsed["fix"] == "Apply a webhook circuit breaker"

def test_parse_incident_memory_failed():
    text = "[04 Sep 2026] INCIDENT: Memory Leak OOM | SERVICE: notification-worker | ROOT CAUSE: Unbounded buffer | FIX (FAILED): Increasing heap memory to 4Gi"
    parsed = parse_incident_memory(text)
    assert parsed["service"] == "notification-worker"
    assert parsed["outcome"] == "FAILED"
    assert parsed["fix"] == "Increasing heap memory to 4Gi"

def test_is_matching_service():
    assert is_matching_service("login-service", "login-service") is True
    assert is_matching_service("login_service", "login-service") is True
    assert is_matching_service("LOGIN-SERVICE", "login-service") is True
    assert is_matching_service("order-service", "login-service") is False
    assert is_matching_service("auth-service", "login-service") is False
    assert is_matching_service(None, "login-service") is False

def test_compute_text_overlap():
    incident = IncidentInput(
        title="Login Service Database Connection Error",
        service="login-service",
        description="Users cannot login",
        symptoms="Database connections exhausted, requests timing out",
        error_logs="Connection is not available, request timed out"
    )
    # High overlap with database connection concepts
    mem1 = "[12 Aug 2026] INCIDENT: DB Connection Timeout | SERVICE: order-service | ROOT CAUSE: leak | FIX (WORKED): restart"
    overlap1 = compute_text_overlap(mem1, incident)
    assert overlap1 > 0.0

    # Zero overlap with completely different issue
    mem2 = "[01 Jan 2026] INCIDENT: TLS cert expired | SERVICE: gateway | ROOT CAUSE: bad cert | FIX (WORKED): renew"
    overlap2 = compute_text_overlap(mem2, incident)
    assert overlap2 == 0.0

def test_rank_and_filter_prioritizes_same_service():
    incident = IncidentInput(
        title="Database Connection Error",
        service="login-service",
        description="Users cannot login",
        symptoms="Database connections exhausted",
        error_logs="Connection is not available"
    )
    
    order_mem = RecalledMemoryItem(
        text="[12 Aug 2026] INCIDENT: Pool Saturation | SERVICE: order-service | ROOT CAUSE: HikariCP leak in OrderPaymentProcessor | FIX (WORKED): circuit breaker",
        score=0.95
    )
    login_mem = RecalledMemoryItem(
        text="[28 Sep 2026] INCIDENT: DB Pool Exhaustion | SERVICE: login-service | ROOT CAUSE: Unclosed session in AuthTokenValidator | FIX (WORKED): Close DB sessions in finally block",
        score=0.85
    )
    unrelated_mem = RecalledMemoryItem(
        text="[05 Jun 2026] INCIDENT: CSS asset 404 | SERVICE: frontend-cdn | ROOT CAUSE: CDN cache invalidation | FIX (WORKED): purge cdn cache",
        score=0.10
    )

    filtered = rank_and_filter_memories([order_mem, login_mem, unrelated_mem], incident)
    
    # First item MUST be the direct login-service match
    assert len(filtered) >= 1
    assert filtered[0].is_same_service is True
    assert filtered[0].service == "login-service"
    assert filtered[0].relevance_grade == "direct_match"
    
    # order-service must be classified as analogy, not direct match
    order_in_results = [m for m in filtered if m.service == "order-service"]
    if order_in_results:
        assert order_in_results[0].is_same_service is False
        assert order_in_results[0].relevance_grade == "analogy"

    # Completely unrelated CDN memory must be filtered out
    assert not any("frontend-cdn" in m.text for m in filtered)
