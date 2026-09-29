import logging
from typing import List, Dict, Any
from app.hindsight_service import hindsight_service
from app.config import BANK_ID

logger = logging.getLogger(__name__)

# ~12 realistic seed incidents covering:
# 1. Database connection pool exhaustion (with FAILED attempt before WORKED fix)
# 2. OOM kill / memory leak (with FAILED attempt before WORKED fix)
# 3. Bad deployment causing 500 errors
# 4. Expired TLS certificate
# 5. External dependency timeout
# 6. Redis eviction misconfiguration
SEED_INCIDENTS: List[Dict[str, str]] = [
    # Category 1: Database connection pool exhaustion (FAILED attempt)
    {
        "date": "04 May 2026",
        "title": "Postgres Connection Pool Saturation",
        "service": "order-service",
        "root_cause": "Unbounded connection acquisition during checkout traffic burst",
        "outcome": "FAILED",
        "fix": "Restarted order-service pods (connections saturated again within 90 seconds, causing recurring checkout 500s and dropping inflight carts)",
        "content": "[04 May 2026] INCIDENT: Postgres Connection Pool Saturation | SERVICE: order-service | ROOT CAUSE: Unbounded connection acquisition during checkout traffic burst | FIX (FAILED): Restarted order-service pods (connections saturated again within 90 seconds, causing recurring checkout 500s and dropping inflight carts)"
    },
    # Category 1: Database connection pool exhaustion (WORKED fix)
    {
        "date": "04 May 2026",
        "title": "Postgres Connection Pool Saturation",
        "service": "order-service",
        "root_cause": "HikariCP connection leak in OrderPaymentProcessor where uncommitted transactions hung on third-party webhook timeout",
        "outcome": "WORKED",
        "fix": "Wrapped webhook in 2s circuit breaker, configured HikariCP leakDetectionThreshold=2000ms, and scaled max-pool-size to 50 with connectionTimeout=3000ms",
        "content": "[04 May 2026] INCIDENT: Postgres Connection Pool Saturation | SERVICE: order-service | ROOT CAUSE: HikariCP connection leak in OrderPaymentProcessor where uncommitted transactions hung on third-party webhook timeout | FIX (WORKED): Wrapped webhook in 2s circuit breaker, configured HikariCP leakDetectionThreshold=2000ms, and scaled max-pool-size to 50 with connectionTimeout=3000ms"
    },
    # Category 1: DB Pool in another service
    {
        "date": "18 Jun 2026",
        "title": "DB Connection Timeout in Inventory API",
        "service": "inventory-service",
        "root_cause": "Long-running analytics queries hogging primary DB connections on ReadWrite replica pool",
        "outcome": "WORKED",
        "fix": "Routed read-only reporting queries to Read Replica endpoint and set idleTimeout=10000ms in GORM connection pool",
        "content": "[18 Jun 2026] INCIDENT: DB Connection Timeout in Inventory API | SERVICE: inventory-service | ROOT CAUSE: Long-running analytics queries hogging primary DB connections on ReadWrite replica pool | FIX (WORKED): Routed read-only reporting queries to Read Replica endpoint and set idleTimeout=10000ms in GORM connection pool"
    },
    # Category 2: OOM kill / memory leak (FAILED attempt)
    {
        "date": "12 Jan 2026",
        "title": "OOMKilled Container in Event Consumer",
        "service": "notification-worker",
        "root_cause": "Increasing Kubernetes memory limit without fixing application memory retention",
        "outcome": "FAILED",
        "fix": "Increased pod memory limit from 1Gi to 4Gi (delayed OOM kill from 3 hours to 11 hours but still crashed node during batch email blast)",
        "content": "[12 Jan 2026] INCIDENT: OOMKilled Container in Event Consumer | SERVICE: notification-worker | ROOT CAUSE: Increasing Kubernetes memory limit without fixing application memory retention | FIX (FAILED): Increased pod memory limit from 1Gi to 4Gi (delayed OOM kill from 3 hours to 11 hours but still crashed node during batch email blast)"
    },
    # Category 2: OOM kill / memory leak (WORKED fix)
    {
        "date": "13 Jan 2026",
        "title": "OOMKilled Container in Event Consumer",
        "service": "notification-worker",
        "root_cause": "Static unbounded Go slice accumulating un-acknowledged Kafka event payloads in retry channel",
        "outcome": "WORKED",
        "fix": "Implemented bounded ring buffer with 10,000 item capacity, added sync.Pool for byte buffers, and set GOMEMLIMIT=750MiB",
        "content": "[13 Jan 2026] INCIDENT: OOMKilled Container in Event Consumer | SERVICE: notification-worker | ROOT CAUSE: Static unbounded Go slice accumulating un-acknowledged Kafka event payloads in retry channel | FIX (WORKED): Implemented bounded ring buffer with 10,000 item capacity, added sync.Pool for byte buffers, and set GOMEMLIMIT=750MiB"
    },
    # Category 2: JVM Heap OOM Crash
    {
        "date": "22 Mar 2026",
        "title": "JVM Heap OutOfMemoryError in Billing Pipeline",
        "service": "billing-engine",
        "root_cause": "Jackson JSON deserialization loading 80MB multi-tenant invoices entirely into memory on export endpoints",
        "outcome": "WORKED",
        "fix": "Migrated from ObjectMapper tree-model to Streaming API JsonParser and set -XX:+ExitOnOutOfMemoryError with heap dumps enabled",
        "content": "[22 Mar 2026] INCIDENT: JVM Heap OutOfMemoryError in Billing Pipeline | SERVICE: billing-engine | ROOT CAUSE: Jackson JSON deserialization loading 80MB multi-tenant invoices entirely into memory on export endpoints | FIX (WORKED): Migrated from ObjectMapper tree-model to Streaming API JsonParser and set -XX:+ExitOnOutOfMemoryError with heap dumps enabled"
    },
    # Category 3: Bad deployment causing 500 errors
    {
        "date": "08 Feb 2026",
        "title": "HTTP 500 Spike After v2.14.0 Deployment",
        "service": "auth-gateway",
        "root_cause": "Rollout script v2.14.0 introduced missing JWT_SIGNING_SALT environment variable in Helm values",
        "outcome": "WORKED",
        "fix": "Executed instant Helm rollback to v2.13.9, re-added JWT_SIGNING_SALT to Vault secrets injector, and deployed hotfix v2.14.1",
        "content": "[08 Feb 2026] INCIDENT: HTTP 500 Spike After v2.14.0 Deployment | SERVICE: auth-gateway | ROOT CAUSE: Rollout script v2.14.0 introduced missing JWT_SIGNING_SALT environment variable in Helm values | FIX (WORKED): Executed instant Helm rollback to v2.13.9, re-added JWT_SIGNING_SALT to Vault secrets injector, and deployed hotfix v2.14.1"
    },
    # Category 3: Bad schema migration causing 500 errors
    {
        "date": "19 Jul 2026",
        "title": "High 500 Error Rate in Catalog API",
        "service": "product-catalog",
        "root_cause": "Flyway migration script added NOT NULL column 'shipping_tier_id' without DEFAULT value while old pod replicas were still inserting records",
        "outcome": "WORKED",
        "fix": "Applied expand-and-contract pattern: set column DEFAULT value, ran backward-compatible migration, then phased out old application pods",
        "content": "[19 Jul 2026] INCIDENT: High 500 Error Rate in Catalog API | SERVICE: product-catalog | ROOT CAUSE: Flyway migration script added NOT NULL column 'shipping_tier_id' without DEFAULT value while old pod replicas were still inserting records | FIX (WORKED): Applied expand-and-contract pattern: set column DEFAULT value, ran backward-compatible migration, then phased out old application pods"
    },
    # Category 4: Expired TLS certificate
    {
        "date": "14 Mar 2026",
        "title": "SSL/TLS Handshake Failures on Internal Ingress",
        "service": "ingress-controller",
        "root_cause": "cert-manager clusterissuer failed Let's Encrypt DNS-01 ACME challenge due to rotated AWS Route53 IAM credentials",
        "outcome": "WORKED",
        "fix": "Refreshed AWS IAM role for cert-manager service account, reissued internal wildcard cert via kubectl cert-manager renew, and added cert expiration alert at 30 days",
        "content": "[14 Mar 2026] INCIDENT: SSL/TLS Handshake Failures on Internal Ingress | SERVICE: ingress-controller | ROOT CAUSE: cert-manager clusterissuer failed Let's Encrypt DNS-01 ACME challenge due to rotated AWS Route53 IAM credentials | FIX (WORKED): Refreshed AWS IAM role for cert-manager service account, reissued internal wildcard cert via kubectl cert-manager renew, and added cert expiration alert at 30 days"
    },
    # Category 4: mTLS Expired Certificate
    {
        "date": "02 Aug 2026",
        "title": "mTLS Handshake Expired between Microservices",
        "service": "payment-service",
        "root_cause": "Istio sidecar SPIFFE cert expired because istiod leader lease hung during node eviction",
        "outcome": "WORKED",
        "fix": "Restarted istiod deployment pods to trigger immediate certificate authority re-issuance and synced Envoy mTLS secrets",
        "content": "[02 Aug 2026] INCIDENT: mTLS Handshake Expired between Microservices | SERVICE: payment-service | ROOT CAUSE: Istio sidecar SPIFFE cert expired because istiod leader lease hung during node eviction | FIX (WORKED): Restarted istiod deployment pods to trigger immediate certificate authority re-issuance and synced Envoy mTLS secrets"
    },
    # Category 5: External dependency timeout
    {
        "date": "29 May 2026",
        "title": "504 Gateway Timeout Cascade on Search API",
        "service": "search-indexer",
        "root_cause": "External GeoIP provider API experiencing 15s latency, exhausting upstream threadpool",
        "outcome": "WORKED",
        "fix": "Added resilient fallback to local MaxMind GeoLite2 MMDB file and clamped outbound HTTP client timeout to 350ms with resilience4j circuit breaker",
        "content": "[29 May 2026] INCIDENT: 504 Gateway Timeout Cascade on Search API | SERVICE: search-indexer | ROOT CAUSE: External GeoIP provider API experiencing 15s latency, exhausting upstream threadpool | FIX (WORKED): Added resilient fallback to local MaxMind GeoLite2 MMDB file and clamped outbound HTTP client timeout to 350ms with resilience4j circuit breaker"
    },
    # Category 6: Redis eviction misconfiguration
    {
        "date": "11 Jun 2026",
        "title": "Redis Eviction Spike & Cache Miss Storm",
        "service": "session-cache",
        "root_cause": "maxmemory-policy was set to 'noeviction' causing OOM commands on new session writes while 85% of memory held volatile sessions without TTL",
        "outcome": "WORKED",
        "fix": "Changed redis maxmemory-policy to 'volatile-lru', enforced explicit 24h EXPIRE on session tokens in AuthMiddleware, and flushed dead unexpired test keys",
        "content": "[11 Jun 2026] INCIDENT: Redis Eviction Spike & Cache Miss Storm | SERVICE: session-cache | ROOT CAUSE: maxmemory-policy was set to 'noeviction' causing OOM commands on new session writes while 85% of memory held volatile sessions without TTL | FIX (WORKED): Changed redis maxmemory-policy to 'volatile-lru', enforced explicit 24h EXPIRE on session tokens in AuthMiddleware, and flushed dead unexpired test keys"
    }
]

def seed_hindsight_bank() -> Dict[str, Any]:
    """Retains all ~12 realistic seed incidents into Hindsight bank 'oncall-memory'."""
    logger.info(f"Starting seeding into Hindsight bank '{BANK_ID}'...")
    retained_count = 0
    failed_count = 0
    details = []

    for inc in SEED_INCIDENTS:
        success, msg = hindsight_service.retain(inc["content"])
        if success:
            retained_count += 1
            details.append({"title": inc["title"], "status": "RETAINED", "outcome": inc["outcome"]})
        else:
            failed_count += 1
            details.append({"title": inc["title"], "status": "FAILED", "error": msg})

    return {
        "bank_id": BANK_ID,
        "total": len(SEED_INCIDENTS),
        "retained": retained_count,
        "failed": failed_count,
        "details": details
    }

if __name__ == "__main__":
    import json
    result = seed_hindsight_bank()
    print(json.dumps(result, indent=2))
