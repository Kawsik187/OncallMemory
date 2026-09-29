import pytest
from app.models import IncidentInput, IncidentResolution, StructuredRecommendation
from app.agent import agent
from app.hindsight_service import hindsight_service
from app.seed_data import SEED_INCIDENTS, seed_hindsight_bank

@pytest.fixture(scope="module", autouse=True)
def setup_seed_data():
    seed_hindsight_bank()
    import time
    time.sleep(1.5)
    yield

def test_models_formatting():
    resolution = IncidentResolution(
        title="Postgres Pool Saturation",
        service="order-service",
        root_cause="HikariCP connection leak",
        fix="Set leakDetectionThreshold=2000ms",
        outcome="WORKED",
        date="12 Aug 2026"
    )
    content = resolution.to_hindsight_content()
    assert content.startswith("[12 Aug 2026] INCIDENT: Postgres Pool Saturation")
    assert "SERVICE: order-service" in content
    assert "ROOT CAUSE: HikariCP connection leak" in content
    assert "FIX (WORKED): Set leakDetectionThreshold=2000ms" in content

def test_seed_incidents_data_quality():
    assert len(SEED_INCIDENTS) >= 12
    # Verify categories
    services = {s["service"] for s in SEED_INCIDENTS}
    assert "order-service" in services
    assert "notification-worker" in services
    assert "ingress-controller" in services
    assert "search-indexer" in services
    assert "session-cache" in services

    # Verify at least one FAILED attempt is recorded
    outcomes = {s["outcome"] for s in SEED_INCIDENTS}
    assert "FAILED" in outcomes
    assert "WORKED" in outcomes

    # Verify exact format
    for inc in SEED_INCIDENTS:
        assert "INCIDENT:" in inc["content"]
        assert "SERVICE:" in inc["content"]
        assert "ROOT CAUSE:" in inc["content"]
        assert "FIX (WORKED):" in inc["content"] or "FIX (FAILED):" in inc["content"]

def test_hindsight_retain_and_recall_integration():
    test_incident = IncidentResolution(
        title="Pytest Connection Glitch",
        service="pytest-service",
        root_cause="Test connection timeout",
        fix="Set timeout=5s",
        outcome="WORKED",
        date="29 Sep 2026"
    )
    success, msg, content = agent.resolve(test_incident)
    assert success is True
    assert "pytest-service" in content

    # Test recall
    incident_query = IncidentInput(
        title="Pytest Connection Glitch",
        service="pytest-service",
        description="testing recall",
        symptoms="timeouts",
        error_logs="socket timeout"
    )
    payload = agent.analyze(incident_query)
    assert payload.hindsight_available is True
    assert len(payload.recalled_memories) > 0
    # Recommendation should be structured and valid
    assert payload.recommendation.confidence in ["high", "medium", "low"]
    assert len(payload.recommendation.recommended_fix) > 0

def test_before_after_comparison():
    incident = IncidentInput(
        title="Postgres Connection Pool Saturation",
        service="order-service",
        description="Checkout checkout latency spike",
        symptoms="Pool exhausted",
        error_logs="HikariPool-1 connection timeout"
    )
    comparison = agent.compare(incident)
    assert comparison.with_memory is not None
    assert comparison.without_memory is not None
    assert len(comparison.contrast_summary) > 0
    # With memory should be high confidence when historical records exist
    assert comparison.with_memory.confidence == "high"
    # Without memory should start with low or medium confidence
    assert comparison.without_memory.confidence in ["low", "medium"]

def test_graceful_hindsight_fallback():
    # Test service against non-existent port
    from app.hindsight_service import HindsightService
    fake_service = HindsightService(base_url="http://localhost:99999", bank_id="oncall-memory")
    memories, available, status = fake_service.recall("any query")
    assert available is False
    assert memories == []
    assert "Hindsight memory temporarily unavailable" in (status or "")

def test_reflect_integration():
    incident = IncidentInput(
        title="Postgres Connection Pool Saturation",
        service="order-service",
        description="Checkout latency spike",
        symptoms="Pool exhausted",
        error_logs="HikariPool-1 connection timeout"
    )
    reflect_res = agent.reflect(incident)
    assert reflect_res.incident.title == incident.title
    assert reflect_res.reflection is not None
    assert len(reflect_res.reflection.systemic_root_cause) > 0
    assert len(reflect_res.reflection.architectural_fix) > 0
    assert len(reflect_res.reflection.prevention_runbook) > 0

