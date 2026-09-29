# System Documentation & Reference Manual
**Oncall Incident Response Agent**

---

## 1. System Summary

The **Oncall Incident Response Agent** is an AI co-pilot designed to eliminate repetitive oncall troubleshooting in distributed systems. It combines long-term agent memory via **Hindsight** and fast LLM synthesis via **Groq** (`openai/gpt-oss-120b`).

---

## 2. Component Architecture

```text
+-----------------------------------------------------------------+
|                       Client Layer                              |
|   React 19 + TypeScript + Vite + Tailwind CSS v4 Dashboard      |
|   (Served statically on port 8000 by FastAPI)                   |
+--------------------------------+--------------------------------+
                                 | HTTP / REST
+--------------------------------v--------------------------------+
|                   Application Server Layer                      |
|   FastAPI + Uvicorn ASGI Server (Port 8000)                     |
|                                                                 |
|   * /api/health             - System connectivity & bank state  |
|   * /api/presets            - Demo incidents with 1-click test  |
|   * /api/incidents/analyze  - Recalls past fixes & generates advice
|   * /api/incidents/compare  - Contrast view (With vs Without)   |
|   * /api/incidents/resolve  - Retains verified fix into memory  |
|   * /api/incidents/reflect  - Deep systemic reflection & resilience
|   * /api/seed               - Populates ~12 realistic incidents |
+------------------+------------------------------+---------------+
                   |                              |
                   | HTTP (Port 8888)             | HTTPS
+------------------v--------------+ +-------------v---------------+
|    Hindsight Agent Memory       | |        Groq Cloud API       |
|    Container: `hindsight`       | |   Model: openai/gpt-oss-120b|
|    Bank: `oncall-memory`        | |   Strict Pydantic JSON      |
|    Engine: TEMPR Multi-Strategy | |   Ultra-low latency LLM     |
|    Storage: Embedded pg0        | +-----------------------------+
|    Volume: `hindsight-data`     |
+---------------------------------+
```

---

## 3. Database Architecture (Zero-DB Design)

* **No External Database Required**: No Postgres, MySQL, MongoDB, or Redis instances need to be installed on the host.
* **Embedded Memory Persistence**: Hindsight runs an internal, zero-configuration database (`pg0` with `pgvector`) inside its container.
* **Volume Persistence**: Stored under `/home/hindsight/.pg0` mapped to named Docker volume `hindsight-data`.
* **Zero ORM Overhead**: The backend code interacts with Hindsight via standard HTTP endpoints with zero database connection pooling issues.

---

## 4. Docker Deployment Cheatsheet

### Start Stack
```powershell
docker compose up --build -d
```

### Stop Stack
```powershell
docker compose down
```

### Stream Live Logs
```powershell
docker compose logs -f
```

### Check Container Status & Health
```powershell
docker compose ps
```

---

## 5. Endpoints & Schemas

### Incident Input (`POST /api/incidents/analyze`)
```json
{
  "title": "Postgres Connection Pool Saturation",
  "service": "order-service",
  "description": "API latency jumped to 14,000ms during flash sale.",
  "symptoms": "Pool saturation at 100%, checkout 500 errors.",
  "error_logs": "CannotAcquireLockException: Connection pool exhausted."
}
```

### Incident Resolution (`POST /api/incidents/resolve`)
```json
{
  "incident_title": "Postgres Connection Pool Saturation",
  "service": "order-service",
  "root_cause": "HikariCP connection leak in OrderPaymentProcessor",
  "fix_description": "Added 2s circuit breaker and configured leakDetectionThreshold=2000ms",
  "outcome": "WORKED"
}
```

---

## 6. Verification Checklist

- [x] Containers running in detached mode: `hindsight` and `incident-response-agent`
- [x] Healthcheck passing: `GET /api/health` returns status `online` and `hindsight_connected: true`
- [x] Persistent volume active: `hindsight-data`
- [x] Production web dashboard accessible at: `http://localhost:8000`
- [x] Automated test suite passing: 5/5 tests passing with `pytest`
