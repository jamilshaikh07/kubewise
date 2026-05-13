# KubeWise — Claude Context

This file gives Claude AI full context about the KubeWise project so it can assist effectively without re-reading all code.

## What is KubeWise?

KubeWise is an **advisory-only** Kubernetes cost and performance optimization platform. It collects read-only cluster state, runs a deterministic recommendation engine, and presents findings in a web dashboard. It **never** writes back to or modifies the cluster.

## Current Deployment State (local dev)

- Backend API: `http://localhost:8001` (Docker)
- Frontend Dashboard: `http://localhost:3002` (Docker)
- Agent: running in Docker, collecting from `talos-homelab` every 60s
- Kubeconfig: `~/.kube/config-homelab` (Talos k8s, bare-metal homelab nodes)

## Repository Layout

```
.
├── backend/                    FastAPI Python backend
│   ├── api/
│   │   ├── cluster.py          GET /api/v1/cluster/summary
│   │   ├── namespaces.py       GET /api/v1/namespaces
│   │   ├── workloads.py        GET /api/v1/workloads, /{id}
│   │   ├── recommendations.py  GET /api/v1/recommendations, /savings, /{id}
│   │   └── ingest.py           POST /api/v1/ingest  ← agent posts here
│   ├── engine/
│   │   ├── analyzer.py         Core recommendation engine (deterministic)
│   │   └── cost.py             Cost estimation formulas
│   ├── models/
│   │   ├── db.py               SQLAlchemy ORM: Cluster, Node, Namespace, Workload, Container, Recommendation
│   │   └── schemas.py          Pydantic request/response schemas
│   ├── storage/
│   │   ├── database.py         SQLAlchemy engine + session + init_db()
│   │   └── seed.py             Demo data seeder (only runs if no cluster exists)
│   ├── tests/
│   │   ├── test_analyzer.py    Unit tests for recommendation engine
│   │   └── test_api.py         API smoke tests with in-memory SQLite
│   ├── pricing.json            Node hourly rates by cloud provider + instance type
│   ├── main.py                 FastAPI app: CORS, routers, startup seed
│   └── Dockerfile
│
├── frontend/                   Next.js 14 + TypeScript + Tailwind CSS
│   ├── app/
│   │   ├── page.tsx            Main dashboard page (all state, filters, charts)
│   │   ├── layout.tsx          Root layout + metadata
│   │   └── globals.css         Tailwind base + CSS vars
│   ├── components/
│   │   ├── MetricCard.tsx      Summary cards (spend, waste, savings, etc.)
│   │   ├── RiskBadge.tsx       Risk/Confidence/Flag badges
│   │   ├── FilterBar.tsx       Namespace/Risk/Confidence/Search filters
│   │   ├── WorkloadTable.tsx   Sortable workload table
│   │   ├── SpendByNamespace.tsx  Bar chart: cost + savings per namespace
│   │   ├── CpuMemChart.tsx     Bar chart: request vs recommended
│   │   ├── RecommendationPanel.tsx  Slide-over detail drawer
│   │   └── PatchViewer.tsx     YAML + kubectl tab panel with copy
│   ├── lib/
│   │   ├── api.ts              Typed fetch client for all 8 API endpoints
│   │   └── utils.ts            Formatters: fmt$$, fmtCpu, fmtMem, fmtDate
│   ├── next.config.js          standalone output, NEXT_PUBLIC_API_URL
│   ├── tailwind.config.ts
│   └── Dockerfile              Multi-stage: deps → builder (npm run build) → runner
│
├── agent/                      Python k8s collector
│   ├── collector.py            Reads nodes, namespaces, workloads, containers via k8s SDK
│   │                           POSTs JSON to POST /api/v1/ingest
│   ├── helm/                   Helm chart for deploying agent INTO a cluster
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   └── templates/          ServiceAccount, ClusterRole, ClusterRoleBinding, Deployment
│   └── Dockerfile
│
├── charts/kubewise/            Helm chart for full stack (backend + frontend)
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│
├── k8s/                        Raw manifests (alternative to Helm)
│   ├── namespace.yaml
│   ├── api-deployment.yaml     Deployment + Service + PVC
│   └── dashboard-deployment.yaml
│
├── docs/
│   ├── architecture.md
│   └── safety-model.md
├── docker-compose.yml          Local dev: api (8001) + dashboard (3002) + agent
├── agent-kubeconfig.yaml       Patched kubeconfig for agent Docker (gitignored)
└── .gitignore
```

## Key Design Decisions

### Active Cluster Resolution
All API endpoints use `db.query(Cluster).order_by(Cluster.last_synced_at.desc()).first()` to pick the most recently ingested cluster. This means real agent data always takes precedence over demo seed data.

### CORS
`CORS_ORIGINS=*` with `allow_credentials=False`. Advisory-only API, no auth needed.

### Cost Model
```
workload_cost_monthly = (
    cpu_request_fraction * node_monthly_cost * 0.5 +
    mem_request_fraction * node_monthly_cost * 0.5
)
```
- Node cost from `pricing.json` by provider+instance_type, fallback `$0.096/hr × 720`
- Bare-metal/Talos: uses fallback rate since no cloud instance type is detected
- All costs labeled `is_estimated: true`

### Recommendation Engine (`engine/analyzer.py`)
Flags detected (in priority order):
1. `over_provisioned_cpu` — P95 usage < 40% of request
2. `over_provisioned_memory` — P95 usage < 50% of request
3. `missing_requests` — no CPU/memory requests set
4. `missing_limits` — no CPU/memory limits set
5. `idle_workload` — zero CPU usage for >24h

Risk assignment:
- `high` — system namespace (kube-system, kube-public, kube-node-lease) OR single replica with no PDB
- `medium` — replicas ≤ 2, or missing limits
- `low` — multiple replicas, has metrics

Confidence:
- `high` — P95 metrics available
- `medium` — partial metrics
- `low` — no metrics (most homelab workloads without metrics-server)

### Why Most Workloads Show LOW Confidence
The Talos homelab cluster doesn't have `metrics-server` installed (or it's not being scraped by the agent). The agent tries to call the metrics API but falls back gracefully. Recommendations are still generated based on the absence of `requests`/`limits` in the pod spec.

### Frontend API Calls
`NEXT_PUBLIC_API_URL` is baked at Next.js build time. In Docker, it's set to `http://localhost:8001` (host port). Inside Docker-to-Docker calls (agent→api), the internal Docker DNS name `kubewise-api:8000` is used.

## Common Tasks

**Rebuild after backend code change:**
```bash
docker compose build kubewise-api && docker compose up -d kubewise-api
```

**View agent logs:**
```bash
docker logs -f kubewise-agent
```

**Check what cluster is active:**
```bash
curl http://localhost:8001/api/v1/cluster/summary | jq .name
```

**Force agent re-poll:**
```bash
docker restart kubewise-agent
```

**Run backend tests:**
```bash
cd backend && python -m pytest tests/ -v
```

**Deploy to k8s (Helm):**
```bash
helm install kubewise ./charts/kubewise -n kubewise --create-namespace \
  --set api.image.tag=0.1.0 \
  --set dashboard.image.tag=0.1.0
kubectl port-forward -n kubewise svc/kubewise-api 8000:8000 &
kubectl port-forward -n kubewise svc/kubewise-dashboard 3000:3000
```
