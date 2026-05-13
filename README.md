# KubeWise — Kubernetes Cost & Performance Optimization

> See [CLAUDE.md](CLAUDE.md) for full AI context • [SKILLS.md](SKILLS.md) for technical skills map • [docs/architecture.md](docs/architecture.md) for architecture diagram • [docs/safety-model.md](docs/safety-model.md) for safety guarantees

**Advisory-only** Kubernetes right-sizing and cost optimization platform. KubeWise connects read-only to your cluster, detects over-provisioned workloads, estimates cost savings, and generates advisory patches — it never auto-applies changes.

## Quick Start (Docker Compose — Demo Mode)

```bash
# 1. Clone
git clone <this-repo> && cd k8s-performance-optimization

# 2. Start backend + frontend with pre-seeded demo data
docker compose up --build

# 3. Open the dashboard
open http://localhost:3000
```

The backend auto-seeds a realistic demo cluster with 8 namespaces, 20+ workloads, and 30+ recommendations so you can explore the dashboard without a live cluster.

## Running Locally Without Docker

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Copy and optionally edit env
cp .env.example .env

uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Dashboard: http://localhost:3000

### Tests

```bash
cd backend
pytest tests/ -v
```

## How It Works

```
Kubernetes Cluster
      │
      │  (read-only: nodes, namespaces, pods, deployments, resource specs)
      ▼
 kubewise-agent  ──── POST /api/v1/ingest ────►  kubewise-api  ──── SQLite DB
                                                       │
                                          Recommendation Engine:
                                          • Detects missing requests/limits
                                          • Detects over-provisioning (P95 usage)
                                          • Estimates cost (CPU+mem fraction × node rate)
                                          • Assigns risk (high/medium/low)
                                          • Generates advisory YAML + kubectl patches
                                                       │
                                                  REST API
                                                       │
                                                       ▼
                                              kubewise-dashboard
                                          (charts, filters, patch viewer)
```

### Where the numbers come from

| Metric | Source |
|---|---|
| **Workload count** | Every Deployment/StatefulSet the agent lists |
| **Namespaces** | All namespaces in the cluster |
| **Node CPU/memory** | `node.status.allocatable` from k8s API |
| **Container requests/limits** | `container.resources` in pod spec |
| **Est. monthly cost** | `(cpu_request / total_cluster_cpu) × node_hourly_rate × 720h × 0.5` + same for memory |
| **Potential savings** | Difference between current and recommended resource requests |
| **HIGH RISK** | System namespaces (`kube-system`, etc.) or single-replica workloads |
| **LOW confidence** | No metrics-server data; recommendations based on missing `requests`/`limits` only |
| **NO LIMITS flag** | Container has no `resources.limits` set |

**Note on cost accuracy:** Bare-metal clusters (e.g. Talos) use a configurable fallback rate (`$0.096/hr` per node). This is purely indicative — real cost depends on your hardware. Set `DEFAULT_NODE_HOURLY_RATE` to match your actual server cost.

---

## Deploying to Kubernetes (Helm)

### Full stack (API + Dashboard + optional Agent)

```bash
# Build and push images first (or use a local registry)
# For Talos homelab: see "Loading images into Talos" below

helm install kubewise ./charts/kubewise \
  --namespace kubewise \
  --create-namespace \
  --set api.image.tag=0.1.0 \
  --set dashboard.image.tag=0.1.0

# Watch rollout
kubectl rollout status deployment/kubewise-api -n kubewise
kubectl rollout status deployment/kubewise-dashboard -n kubewise
```

### Access via port-forward

```bash
# Terminal 1 — API
kubectl port-forward -n kubewise svc/kubewise-api 8000:8000

# Terminal 2 — Dashboard
kubectl port-forward -n kubewise svc/kubewise-dashboard 3000:3000

# Then open http://localhost:3000
```

### Enable the in-cluster agent

```bash
helm upgrade kubewise ./charts/kubewise \
  --namespace kubewise \
  --set agent.enabled=true \
  --set agent.clusterName=my-cluster \
  --set agent.pollIntervalSeconds=300
```

### Loading images into Talos (no registry)

```bash
# Save images from Docker
docker save kubewise/api:0.1.0 | gzip > kubewise-api.tar.gz
docker save kubewise/dashboard:0.1.0 | gzip > kubewise-dashboard.tar.gz

# Import into each Talos node
talosctl image import kubewise-api.tar.gz --nodes 192.168.60.40,192.168.60.41
talosctl image import kubewise-dashboard.tar.gz --nodes 192.168.60.40,192.168.60.41
```

Then set `imagePullPolicy: Never` in values:
```bash
helm install kubewise ./charts/kubewise \
  --namespace kubewise --create-namespace \
  --set api.image.pullPolicy=Never \
  --set dashboard.image.pullPolicy=Never
```

### Deploy agent only (agent/helm — standalone)

```bash
helm install kubewise-agent ./agent/helm \
  --namespace kubewise \
  --set backendUrl=http://kubewise-api.kubewise.svc.cluster.local:8000 \
  --set clusterName=my-cluster \
  --set pollIntervalSeconds=300
```

## Project Layout

```
.
├── backend/               FastAPI backend (API + recommendation engine)
│   ├── api/               Route handlers
│   ├── engine/            Recommendation logic + cost estimator
│   ├── models/            SQLAlchemy ORM + Pydantic schemas
│   ├── storage/           DB setup + demo seed data
│   ├── tests/             pytest unit + API smoke tests
│   ├── pricing.json       Configurable cloud pricing
│   └── Dockerfile
├── frontend/              Next.js 14 dashboard
│   ├── app/               Next.js App Router pages
│   ├── components/        UI components (charts, table, filters, panels)
│   ├── lib/               API client + utilities
│   └── Dockerfile
├── agent/                 Python Kubernetes collector
│   ├── collector.py
│   ├── helm/              Helm chart (ServiceAccount, ClusterRole, Deployment)
│   └── Dockerfile
├── k8s/                   Raw Kubernetes manifests (namespace, API, dashboard)
├── docs/
│   ├── architecture.md
│   └── safety-model.md
└── docker-compose.yml
```

## Configuration

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./kubewise.db` | SQLAlchemy DB URL |
| `SEED_DEMO_DATA` | `true` | Auto-seed demo cluster on startup |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `DEFAULT_NODE_HOURLY_RATE` | `0.096` | Fallback node hourly cost (USD) |

Edit `backend/pricing.json` to add instance-specific pricing for your cloud provider.

### Agent (environment variables or Helm values)

| Variable | Default | Description |
|---|---|---|
| `BACKEND_URL` | `http://localhost:8000` | Backend API URL |
| `CLUSTER_NAME` | `my-cluster` | Display name for this cluster |
| `POLL_INTERVAL_SECONDS` | `300` | Seconds between collection runs |
| `IN_CLUSTER` | `true` | Use in-cluster kubeconfig |

### Frontend (`frontend/.env.local`)

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |

## Safety

KubeWise is **advisory only**. The agent has read-only RBAC. The dashboard shows patches but never applies them. See [docs/safety-model.md](docs/safety-model.md) for full details.

## Architecture

See [docs/architecture.md](docs/architecture.md) for a full architecture diagram and data flow description.
