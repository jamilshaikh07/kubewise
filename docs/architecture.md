# KubeWise Architecture

## Overview

KubeWise is a three-tier advisory platform. No component ever writes back to Kubernetes.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Your Kubernetes Cluster                     │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  kubewise-agent  (read-only ServiceAccount)                │     │
│  │  - Lists: namespaces, nodes, deployments, statefulsets,    │     │
│  │    pods, containers, resource requests/limits              │     │
│  │  - Optionally reads metrics-server for live CPU/mem        │     │
│  │  - POSTs JSON payload to Backend API  ──────────────────────────►│
│  └────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                    │  POST /api/v1/ingest
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         KubeWise Backend (FastAPI)                  │
│                                                                     │
│  ┌────────────┐   ┌─────────────────────────────────────────────┐   │
│  │  SQLite /  │   │  Recommendation Engine (engine/analyzer.py) │   │
│  │  Postgres  │◄──│  - Deterministic right-sizing formulas      │   │
│  │  database  │   │  - CPU: max(P95 × 1.5, 10m floor)          │   │
│  └────────────┘   │  - Mem: max(P95 × 1.3, 32Mi floor)         │   │
│                   │  - Flags: over-prov, missing req/lim, idle  │   │
│                   │  - Confidence: high / medium / low          │   │
│                   │  - Risk: high / medium / low                │   │
│                   │  - Generates advisory YAML + kubectl patch  │   │
│                   └─────────────────────────────────────────────┘   │
│                                                                     │
│  REST API endpoints:                                                │
│  GET  /api/v1/cluster/summary                                       │
│  GET  /api/v1/namespaces                                            │
│  GET  /api/v1/workloads  (filterable, paginated)                    │
│  GET  /api/v1/workloads/{id}                                        │
│  GET  /api/v1/recommendations  (filterable)                         │
│  GET  /api/v1/recommendations/{id}                                  │
│  GET  /api/v1/recommendations/savings                               │
│  POST /api/v1/ingest                                                │
└─────────────────────────────────────────────────────────────────────┘
                                    │  fetch
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    KubeWise Dashboard (Next.js)                     │
│                                                                     │
│  - Metric cards: spend, waste, savings, workloads, recs             │
│  - Risk breakdown bar                                               │
│  - Spend & savings by namespace (bar chart)                         │
│  - CPU / Memory request vs P95 usage (grouped bar charts)           │
│  - Filterable workload table (namespace, risk, confidence, search)  │
│  - Recommendation slide-over: explanation, resource diff, patch     │
│  - Advisory warning banners for high-risk / system namespaces       │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Agent** collects cluster state every N seconds (default 300s)
2. **Backend** ingests payload, upserts workloads/containers, runs recommendation engine
3. **Dashboard** polls the REST API; all data is displayed read-only
4. **User** copies advisory patches and applies them manually — nothing is auto-applied

## Cost Model

- Cost is attributed per workload based on the fraction of node resources requested
- Formula: `workload_cost = (cpu_req / node_cpu) × node_monthly_cost × 0.5 + (mem_req / node_mem) × node_monthly_cost × 0.5`
- Node hourly prices are looked up from `backend/pricing.json` by provider + instance type
- All cost values are labeled `is_estimated: true` in the API and UI

## Tech Stack

| Component | Technology |
|---|---|
| Agent | Python 3.12, kubernetes SDK |
| Backend | FastAPI, SQLAlchemy, SQLite (dev) |
| Frontend | Next.js 14, React 18, TypeScript |
| Charts | Recharts |
| Styling | Tailwind CSS |
| Container | Docker (multi-stage) |
| K8s deploy | Helm chart (agent), raw manifests (backend + frontend) |
