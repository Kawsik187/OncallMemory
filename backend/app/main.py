import os
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import BANK_ID, GROQ_API_KEY, LLM_MODEL, HINDSIGHT_URL
from app.models import (
    IncidentInput,
    IncidentResolution,
    IncidentResponsePayload,
    ComparisonResponse,
    ReflectResponsePayload
)
from app.agent import agent
from app.hindsight_service import hindsight_service
from app.seed_data import seed_hindsight_bank, SEED_INCIDENTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("incident_agent")

app = FastAPI(
    title="Incident Response Agent",
    description="When production breaks, the agent doesn't start from zero.",
    version="1.0.0"
)

# Enable CORS for local dev (Vite default port 5173 and others)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    hindsight_ok = hindsight_service.is_available()
    return {
        "status": "online",
        "bank_id": BANK_ID,
        "llm_model": LLM_MODEL,
        "groq_configured": bool(GROQ_API_KEY and len(GROQ_API_KEY.strip()) > 5),
        "hindsight_url": HINDSIGHT_URL,
        "hindsight_connected": hindsight_ok,
        "hindsight_status": "connected" if hindsight_ok else "Hindsight memory temporarily unavailable, continuing without historical context"
    }

@app.post("/api/incidents/analyze", response_model=IncidentResponsePayload)
def analyze_incident(incident: IncidentInput):
    """
    Core Step 1-3: Recalls past memories from Hindsight bank 'oncall-memory'
    and reasons over them with Groq LLM.
    """
    try:
        return agent.analyze(incident)
    except Exception as e:
        logger.error(f"Error in analyze_incident: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/incidents/compare", response_model=ComparisonResponse)
def compare_incident(incident: IncidentInput):
    """
    Shows side-by-side:
    Without Memory vs With Hindsight Memory
    """
    try:
        return agent.compare(incident)
    except Exception as e:
        logger.error(f"Error in compare_incident: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/incidents/resolve")
def resolve_incident(resolution: IncidentResolution):
    """
    Core Step 5-6: Resolves incident and retains the outcome into Hindsight bank 'oncall-memory'.
    """
    try:
        success, message, content = agent.resolve(resolution)
        return {
            "success": success,
            "message": message,
            "retained_content": content,
            "bank_id": BANK_ID
        }
    except Exception as e:
        logger.error(f"Error in resolve_incident: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/incidents/reflect", response_model=ReflectResponsePayload)
def reflect_incident(incident: IncidentInput):
    """
    Core Step 6: Calls Hindsight's native /reflect endpoint to reflect over
    memories, mental models, and failure patterns, generating deep resilience insights.
    """
    try:
        return agent.reflect(incident)
    except Exception as e:
        logger.error(f"Error in reflect_incident: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/seed")
def seed_bank():
    """
    Seeds ~12 realistic past incidents into Hindsight bank 'oncall-memory'.
    """
    try:
        result = seed_hindsight_bank()
        return result
    except Exception as e:
        logger.error(f"Error seeding bank: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/presets")
def get_presets():
    """
    Returns realistic demo incident presets for quick 1-click testing in the UI,
    including the two-stage learning demo.
    """
    return {
        "presets": [
            {
                "id": "login_service_db_error",
                "incident_number": "#INC-2026-09-29-108",
                "severity": "critical",
                "source": "Datadog / APM",
                "started_ago": "3 minutes ago",
                "assigned_to": "Oncall SRE",
                "affected_resources": ["login-service (EKS)", "users-db (PostgreSQL)", "auth-gateway"],
                "impact": "Users unable to log in. Login requests timing out.",
                "label": "Login Service — Database Connection Error",
                "incident": {
                    "title": "Login Service Database Connection Error",
                    "service": "login-service",
                    "description": "Users are unable to log in.",
                    "symptoms": "Database connections are exhausted, and login requests are timing out.",
                    "error_logs": "Connection is not available, request timed out"
                },
                "expected_recall": "The agent searches its memory for similar incidents. Since this is a new incident, it cautions against false assumptions and suggests checking database connections and connection pool usage.",
                "demo_instruction": "Click 'Analyze with Memory'. The agent searches memory, verifies no prior incident exists for login-service, and suggests cautious exploratory checks on connection pool usage without false order-service claims."
            },
            {
                "id": "payment_500",
                "incident_number": "#INC-2025-05-16-9922",
                "severity": "critical",
                "source": "CloudWatch",
                "started_ago": "18 minutes ago",
                "assigned_to": "Michael Johnson",
                "affected_resources": ["payment-service (EKS)", "checkout-api", "stripe-integration"],
                "impact": "Revenue impact estimated at $450/minute. 23% error rate.",
                "label": "Payment Service HTTP 500 Error Rate Spike",
                "incident": {
                    "title": "Payment Service HTTP 500 Error Rate Spike",
                    "service": "payment-service",
                    "description": "Payment processing service showing 23% error rate (threshold: 5%). Users unable to complete transactions. Revenue impact estimated at $450/minute.",
                    "symptoms": "23% error rate on POST /v1/charges. Webhook timeouts climbing to 8000ms. Inflight checkout requests failing.",
                    "error_logs": "StripePaymentGateway: HTTP 504 Gateway Timeout while awaiting external webhook callback. Transaction rolled back with 500 Internal Server Error."
                },
                "expected_recall": "Should recall wrapping webhook in circuit breaker and increasing timeout from historical payment incident."
            },
            {
                "id": "db_pool_repeat",
                "incident_number": "INC-2025-05-14-047",
                "severity": "critical",
                "source": "Datadog",
                "started_ago": "5 minutes ago",
                "assigned_to": "Michael Johnson",
                "affected_resources": ["users-db (RDS PostgreSQL)", "api-prod-1", "api-prod-2", "payment-service"],
                "impact": "Database connection pool at 100% capacity. Queries experiencing 500ms+ latency.",
                "label": "Database Connection Pool Exhausted",
                "incident": {
                    "title": "Database Connection Pool Exhausted",
                    "service": "order-service",
                    "description": "users-db connection pool at 100% capacity. New connections failing with timeout errors. Database queries experiencing 500ms+ latency.",
                    "symptoms": "Database connection pool utilization at 100%, p99 latency spike to 12s, cart abandonment rate spiked 400%.",
                    "error_logs": "org.springframework.dao.CannotAcquireLockException: HikariPool-1 - Connection is not available, request timed out after 30005ms.\nCaused by: java.sql.SQLTransientConnectionException: Connection pool exhausted."
                },
                "expected_recall": "Should recall that pod restart FAILED on 04 May 2026, and recommend HikariCP leakDetectionThreshold and 2s webhook circuit breaker."
            },
            {
                "id": "oom_repeat",
                "incident_number": "INC-2025-05-12-881",
                "severity": "critical",
                "source": "Prometheus",
                "started_ago": "24 minutes ago",
                "assigned_to": "Sarah Chen",
                "affected_resources": ["notification-worker", "kafka-cluster-1", "worker-pool-b"],
                "impact": "Worker pods in CrashLoopBackOff. Notification delivery delayed.",
                "label": "Worker OOMKilled Leak (Kafka batch consumer)",
                "incident": {
                    "title": "OOMKilled Container in Event Consumer",
                    "service": "notification-worker",
                    "description": "Notification worker pods are repeatedly entering CrashLoopBackOff with Exit Code 137.",
                    "symptoms": "Pod memory climbs monotonically from 200MB to limit over 3 hours then crashes. Kafka consumer group rebalance storm.",
                    "error_logs": "Killed process 1 (notification-worker) total-vm:4231844kB, anon-rss:1048576kB, file-rss:0kB, shmem-rss:0kB\nState: Terminated, Reason: OOMKilled, Exit Code: 137"
                },
                "expected_recall": "Should recall that bumping pod limit to 4Gi FAILED, and recommend bounded ring buffer with 10k capacity + sync.Pool."
            },
            {
                "id": "tls_expired",
                "incident_number": "INC-2025-05-10-619",
                "severity": "warning",
                "source": "Ingress Monitor",
                "started_ago": "42 minutes ago",
                "assigned_to": "Alex Rivera",
                "affected_resources": ["ingress-controller (Nginx)", "api-gateway", "cert-manager"],
                "impact": "Microservices reporting intermittent handshake aborts over internal ingress.",
                "label": "Expired TLS Certificate (Ingress)",
                "incident": {
                    "title": "SSL/TLS Handshake Failures on Internal Ingress",
                    "service": "ingress-controller",
                    "description": "Microservices reporting intermittent handshake aborts when communicating over internal ingress.",
                    "symptoms": "TLS handshake error remote error: tls: bad certificate. 502 Bad Gateway between internal gateways.",
                    "error_logs": "2026/09/29 06:12:01 [error] 42#42: *120412 SSL_do_handshake() failed (SSL: error:0A000086:SSL routines::certificate verify failed) while SSL handshaking"
                },
                "expected_recall": "Should recall cert-manager AWS Route53 IAM credential rotation issue and kubectl cert-manager renew fix."
            },
            {
                "id": "redis_evict",
                "incident_number": "INC-2025-05-08-302",
                "severity": "warning",
                "source": "Datadog",
                "started_ago": "1 hour ago",
                "assigned_to": "Michael Johnson",
                "affected_resources": ["redis-cluster-cache", "session-manager", "auth-service"],
                "impact": "Eviction spike to 10,000 keys/sec. Cache miss rate jumped to 85%.",
                "label": "Redis Eviction Spike & Cache Miss Storm",
                "incident": {
                    "title": "Redis Eviction Spike & Cache Miss Storm",
                    "service": "cache-service",
                    "description": "Redis cluster memory hit maxmemory 98%. Eviction rate spiked 10,000 keys/sec causing downstream database surge.",
                    "symptoms": "Eviction rate spiked, cache miss rate jumped to 85%, backend RDS CPU at 95%.",
                    "error_logs": "OOM command not allowed when used memory > 'maxmemory'. Eviction loop active."
                },
                "expected_recall": "Should recall volatile-lru policy adjustment and session TTL clamps."
            },
            {
                "id": "search_timeout",
                "incident_number": "INC-2025-05-06-118",
                "severity": "warning",
                "source": "CloudWatch",
                "started_ago": "2 hours ago",
                "assigned_to": "DevOps Oncall",
                "affected_resources": ["search-indexer", "catalog-api", "elasticsearch-cluster"],
                "impact": "Search queries timing out under midday search bursts.",
                "label": "504 Gateway Timeout Cascade on Search API",
                "incident": {
                    "title": "504 Gateway Timeout Cascade on Search API",
                    "service": "search-gateway",
                    "description": "Search queries timing out at 30s threshold under midday search bursts.",
                    "symptoms": "HTTP 504 Gateway Timeout spikes, search thread pool queue depth > 500.",
                    "error_logs": "java.util.concurrent.TimeoutException: Search execution timed out after 30000ms"
                },
                "expected_recall": "Should recall query timeout circuit breaker and MaxMind fallback."
            },
            {
                "id": "deploy_rollback",
                "incident_number": "INC-2025-05-04-094",
                "severity": "warning",
                "source": "ArgoCD",
                "started_ago": "3 hours ago",
                "assigned_to": "Michael Johnson",
                "affected_resources": ["order-service", "v2.14.0-deploy", "helm-release"],
                "impact": "Canary rollout of v2.14.0 introduced missing column exception on checkout.",
                "label": "HTTP 500 Spike After v2.14.0 Deployment",
                "incident": {
                    "title": "HTTP 500 Spike After v2.14.0 Deployment",
                    "service": "order-service",
                    "description": "Canary rollout of v2.14.0 introduced missing column exception on checkout table.",
                    "symptoms": "500 error rate 15% on checkout endpoints following canary deploy.",
                    "error_logs": "org.postgresql.util.PSQLException: ERROR: column \"loyalty_discount_cents\" does not exist"
                },
                "expected_recall": "Should recall Helm rollback and Flyway schema migration ordering fix."
            },
            {
                "id": "demo_stage1_new_incident",
                "incident_number": "INC-2025-05-01-002",
                "severity": "info",
                "source": "Elastic APM",
                "started_ago": "Just now",
                "assigned_to": "Unassigned",
                "affected_resources": ["search-indexer", "elasticsearch-node-03"],
                "impact": "Step 1 of Demo: Brand new incident without past memory.",
                "label": "Elasticsearch CircuitBreakingException (Demo Stage 1: Cold Start)",
                "incident": {
                    "title": "Elasticsearch CircuitBreakingException on Query Node",
                    "service": "search-indexer",
                    "description": "Catalog search queries failing with 500 error. Search indexer node heap memory saturated.",
                    "symptoms": "Elasticsearch cluster state Yellow. Search latency up to 8s, parent circuit breaker tripping.",
                    "error_logs": "org.elasticsearch.common.breaker.CircuitBreakingException: [parent] Data too large, data for [<transport_request>] would be [1048576000/1000mb], which is larger than the limit of [996147200/950mb]"
                },
                "demo_instruction": "Stage 1: Analyze this new incident (no past memory for this specific breaker). Resolve it with: Root Cause: 'Unbounded aggregations on unindexed field payload.details', Fix: 'Set indices.breaker.total.use_real_memory: false and clamp terms aggregation max_size=50', Outcome: WORKED. Stage 2: Re-run to see agent recall the newly learned fix!"
            },
            {
                "id": "demo_stage2_similar_incident",
                "incident_number": "INC-2025-05-01-003",
                "severity": "critical",
                "source": "Elastic APM",
                "started_ago": "Moments ago",
                "assigned_to": "Michael Johnson",
                "affected_resources": ["search-indexer", "elasticsearch-node-01"],
                "impact": "Step 2 of Demo: Similar incident proving closed-loop learning.",
                "label": "Parent Circuit Breaker Tripped (Demo Stage 2: Learned Fix)",
                "incident": {
                    "title": "Parent Circuit Breaker Tripped on Search Cluster",
                    "service": "search-indexer",
                    "description": "Search queries crashing again with CircuitBreakingException under moderate load.",
                    "symptoms": "Heap parent circuit breaker triggered on query transport request.",
                    "error_logs": "org.elasticsearch.common.breaker.CircuitBreakingException: [parent] Data too large for [<transport_request>]"
                },
                "demo_instruction": "Shows recall returning the memory retained in Step 1, with agent now citing the resolution from Step 1 with high confidence!"
            }
        ]
    }

# Mount frontend build if it exists
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
