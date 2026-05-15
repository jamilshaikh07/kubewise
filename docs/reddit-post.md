# Reddit / X Post Draft — KubeWise

## Reddit Title Options

- **I built a self-hosted Kubernetes right-sizing dashboard for my Talos homelab — KubeWise**
- **KubeWise: read-only Kubernetes cost + resource optimization for homelabs**
- **I wanted Kubecost-lite for bare-metal Kubernetes, so I built KubeWise**

## Reddit Post

Hey r/homelab,

I've been running a small Talos Kubernetes cluster at home and wanted a simple answer to:

> Which workloads are over-requesting resources, missing requests/limits, or quietly wasting capacity?

So I built **KubeWise** — a self-hosted, advisory-only Kubernetes resource optimization dashboard.

It is not trying to be a full cloud billing platform. Think of it more like a lightweight FinOps/SRE assistant for self-hosted Kubernetes: read cluster state, compare requests against usage, estimate waste, and generate safe recommendations.

## What It Does

- Deploys a **read-only agent** with `get/list/watch` permissions
- Collects nodes, namespaces, deployments, statefulsets, pods, resource requests/limits, and usage metrics
- Pulls P95 CPU/memory from Prometheus-compatible backends such as VictoriaMetrics
- Detects missing requests, missing limits, idle workloads, and over-provisioned CPU/memory
- Shows estimated monthly cost and potential savings using a configurable node hourly rate
- Generates advisory YAML and `kubectl set resources` commands
- Never auto-applies changes

## What It Found On My Homelab

Current live run:

```text
Cluster:          talos-homelab
Kubernetes:       v1.34
Nodes:            2
Workloads:        32 across 15 namespaces
Recommendations: 79
Estimated cost:   $21.18/mo
Potential saving: $24.91/mo

Finding breakdown:

missing_requests:        14
missing_limits:          17
idle_workload:           20
over_provisioned_cpu:    14
over_provisioned_memory: 11
high_risk:                3

Confidence breakdown:

high confidence: 75
low confidence:   4

The useful part for me was not the dollar amount itself. Since this is bare metal, cost is an estimate. The useful part was seeing exactly which workloads have no requests/limits, which ones are idle, and which ones are oversized compared to P95 usage.
```

## Cost Model

For bare metal, KubeWise uses a configurable node hourly rate. Workload cost is estimated by splitting node cost across requested CPU and memory:

```
workload_cost =
  cpu_request_fraction * node_monthly_cost * 0.5
+ memory_request_fraction * node_monthly_cost * 0.5
```

This is intentionally approximate. It is meant for prioritization, not billing reconciliation.

Also: missing limits do not count as savings. Limits are treated as reliability/safety findings, not cost reductions.

## Stack

- Backend: FastAPI + SQLAlchemy + SQLite
- Frontend: Next.js + Tailwind + Recharts
- Agent: Python Kubernetes client
- Metrics: metrics-server for current usage, VictoriaMetrics/Prometheus for P95
- Deploy: Helm chart or Docker Compose demo mode

## Deploy It

Helm:

```bash
kubectl create namespace kubewise

helm install kubewise \
  oci://ghcr.io/jamilshaikh07/charts/kubewise \
  --namespace kubewise \
  --set agent.enabled=true \
  --set agent.clusterName=my-cluster
```

If you have VictoriaMetrics/Prometheus:

```bash
helm upgrade kubewise \
  oci://ghcr.io/jamilshaikh07/charts/kubewise \
  --namespace kubewise \
  --set agent.enabled=true \
  --set agent.env.METRICS_URL=http://your-prometheus-or-victoriametrics:8428
```

Port-forward:

```bash
kubectl port-forward -n kubewise svc/kubewise-dashboard 3000:3000
open http://localhost:3000
```

Docker Compose demo mode:

```bash
git clone https://github.com/jamilshaikh07/kubewise
cd kubewise
docker compose up --build
```

## Links

- GitHub: https://github.com/jamilshaikh07/kubewise
- Images: `ghcr.io/jamilshaikh07/kubewise-{api,dashboard,agent}:v1.0.0`

Would love feedback on the recommendation logic and cost model. The goal is a simple, safe, self-hosted Kubernetes right-sizing tool that is useful before you need a full billing platform.

---

## Suggested Subreddits

- **r/homelab** — strongest fit; focus on Talos, bare metal, and self-hosted Kubernetes
- **r/kubernetes** — focus on read-only agent, RBAC, P95 logic, and generated patches
- **r/selfhosted** — focus on no cloud account required
- **r/devops** — focus on advisory right-sizing and FinOps workflow
- **r/opensource** — only after the repo README/screenshots are polished

## Screenshots To Include

1. Dashboard overview with cluster summary and risk breakdown
2. Workload table showing missing requests/limits
3. CPU/memory request vs P95 usage charts
4. Recommendation drawer with YAML and kubectl command

## Comment Talking Points

**Why not Kubecost?**

Kubecost is much more complete for cloud billing and allocation. KubeWise is intentionally smaller: self-hosted, read-only, advisory-first, and useful for homelab/bare-metal clusters where exact cloud billing is not the main problem.

**Can it modify my cluster?**

No. The agent is read-only. The dashboard shows suggested YAML and kubectl commands, but nothing is applied automatically.

**Are the savings exact?**

No. Savings are estimates based on requested CPU/memory and a configurable node hourly rate. This is for prioritization, not invoice-grade accounting.

**Does it need Prometheus?**

No for basic request/limit checks. Yes if you want high-confidence P95-based right-sizing. It works with Prometheus-compatible APIs, including VictoriaMetrics.

---

## X / Twitter Thread

**Tweet 1**

I built KubeWise: a self-hosted, read-only Kubernetes right-sizing dashboard for my Talos homelab.

It finds missing requests/limits, idle workloads, and over-provisioned CPU/memory, then generates advisory YAML + kubectl commands. Nothing is auto-applied.

**Tweet 2**

Current run on my cluster:

- 2 nodes
- 32 workloads
- 15 namespaces
- 79 recommendations
- 75 high-confidence findings using VictoriaMetrics P95 data

The cost numbers are estimates, but the resource findings are immediately useful.

**Tweet 3**

The main thing it surfaced: a lot of homelab workloads either have no resource requests/limits or are oversized compared to P95 usage.

KubeWise treats missing limits as reliability findings, not fake cost savings.

**Tweet 4**

Stack:

- FastAPI + SQLite
- Next.js + Tailwind + Recharts
- Python Kubernetes agent
- Helm deploy
- Prometheus/VictoriaMetrics P95 support

Repo: https://github.com/jamilshaikh07/kubewise

Feedback welcome, especially on the recommendation logic.
