import pytest
from app.models import IncidentInput, IncidentResolution
from app.agent import agent
from app.hindsight_service import hindsight_service
from app.seed_data import seed_hindsight_bank

@pytest.fixture(autouse=True)
def setup_bank():
    """Ensure bank is reset to seed data before scenario tests."""
    hindsight_service.clear_bank()
    seed_hindsight_bank()
    yield

def test_scenario_a_and_c_no_matching_memory_and_unrelated_service():
    """
    Test A & Test C:
    Submit Login Service incident when only order-service/other service memories exist.
    Expected:
    1. Unrelated order-service memories are NOT treated as direct evidence (is_same_service == False).
    2. No OrderPaymentProcessor or order-service fix is claimed as verified.
    3. Confidence must NOT be high.
    4. Citing should indicate no historical resolution for login-service.
    """
    incident = IncidentInput(
        title="Login Service — Database Connection Error",
        service="login-service",
        description="Users are unable to log in.",
        symptoms="Database connections are exhausted, and login requests are timing out.",
        error_logs="Connection is not available, request timed out"
    )

    payload = agent.analyze(incident)

    # 1. Memories returned should not be claimed as direct matches
    for mem in payload.recalled_memories:
        assert mem.is_same_service is False, f"Memory {mem.text} was falsely marked as same service"
        assert mem.relevance_grade != "direct_match"

    # 2. Confidence must reflect lack of direct evidence (must NOT be high)
    assert payload.recommendation.confidence in ["medium", "low"], \
        f"Expected medium/low confidence without direct memory, got {payload.recommendation.confidence}"

    # 3. Recommended fix and likely root cause must NOT attribute to OrderPaymentProcessor
    assert "OrderPaymentProcessor" not in payload.recommendation.likely_root_cause, \
        "Falsely attributed order-service root cause to login-service"
    
    # 4. Citations should state no verified precedent for login-service
    assert "login-service" in payload.recommendation.citing.lower() or \
           "no historical resolution" in payload.recommendation.citing.lower() or \
           "no verified" in payload.recommendation.citing.lower()

def test_scenario_b_matching_successful_memory():
    """
    Test B:
    Save a verified login-service resolution with outcome WORKED.
    Submit the same incident again.
    Expected:
    1. Agent retrieves the saved resolution as a direct match (is_same_service == True).
    2. Agent cites it.
    3. Recommends the verified fix.
    4. Confidence is HIGH.
    """
    # 1. Retain verified resolution for login-service
    resolution = IncidentResolution(
        title="Login Service — Database Connection Error",
        service="login-service",
        root_cause="Unclosed DB connection leak in SessionTokenManager during auth token validation",
        fix="Wrap SessionTokenManager in try-finally and ensure session.close() is called",
        outcome="WORKED",
        date="29 Sep 2026"
    )
    success, msg, _ = agent.resolve(resolution)
    assert success is True
    import time
    time.sleep(1.5)

    # 2. Query same incident again
    incident = IncidentInput(
        title="Login Service — Database Connection Error",
        service="login-service",
        description="Users are unable to log in.",
        symptoms="Database connections are exhausted, and login requests are timing out.",
        error_logs="Connection is not available, request timed out"
    )

    payload = agent.analyze(incident)

    # 3. Verify direct match retrieved
    direct_matches = [m for m in payload.recalled_memories if m.is_same_service]
    assert len(direct_matches) >= 1, "Expected at least one direct match for login-service"
    assert direct_matches[0].service == "login-service"
    assert direct_matches[0].relevance_grade == "direct_match"

    # 4. Confidence must be HIGH
    assert payload.recommendation.confidence == "high", \
        f"Expected HIGH confidence with verified same-service memory, got {payload.recommendation.confidence}"

    # 5. Fix should recommend the verified fix
    rec_fix = payload.recommendation.recommended_fix.lower()
    assert "sessiontokenmanager" in rec_fix or "session.close" in rec_fix or "finally" in rec_fix

def test_scenario_d_failed_historical_fix():
    """
    Test D:
    Ensure a relevant failed resolution exists for login-service.
    Submit the same incident again.
    Expected:
    1. Agent warns against the failed fix.
    2. Distinguishes failed fix from successful resolution.
    """
    # 1. Retain a failed resolution for login-service
    failed_resolution = IncidentResolution(
        title="Login Service — Database Connection Error",
        service="login-service",
        root_cause="Database pool saturation under auth bursts",
        fix="Blindly doubling max pool size to 200",
        outcome="FAILED",
        date="28 Sep 2026"
    )
    agent.resolve(failed_resolution)

    # Also retain a successful fix to verify distinction
    worked_resolution = IncidentResolution(
        title="Login Service — Database Connection Error",
        service="login-service",
        root_cause="Unclosed DB connection leak in SessionTokenManager",
        fix="Ensure connection pool cleanup and enforce session.close()",
        outcome="WORKED",
        date="29 Sep 2026"
    )
    agent.resolve(worked_resolution)
    import time
    time.sleep(1.5)

    incident = IncidentInput(
        title="Login Service — Database Connection Error",
        service="login-service",
        description="Users are unable to log in.",
        symptoms="Database connections are exhausted, and login requests are timing out.",
        error_logs="Connection is not available, request timed out"
    )

    payload = agent.analyze(incident)

    # Verify agent mentions or warns against the failed fix
    rec_text = (payload.recommendation.recommended_fix + " " + " ".join(payload.recommendation.runbook)).lower()
    assert "failed" in rec_text or "doubling" in rec_text or "do not" in rec_text or "avoid" in rec_text, \
        "Expected warning against repeating historically failed fix"
