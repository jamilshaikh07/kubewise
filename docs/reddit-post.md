# Reddit Post Draft — r/homelab / r/kubernetes / r/selfhosted

---

## Title options (pick one)

- **"I built an open-source Kubernetes cost & right-sizing dashboard for my homelab Talos cluster — KubeWise"**
- **"Built a self-hosted K8s optimization tool in a weekend: shows you which workloads are wasting resources and generates kubectl patches"**
- **"KubeWise — advisory-only K8s right-sizing dashboard. No cloud account needed, runs on bare-metal"**

---

## Post Body

Hey r/homelab,

I've been running a 2-node Talos cluster at home and noticed I had no visibility into which workloads were actually using what they'd been allocated — most of them had no `resources:` blocks at all.

So I built **KubeWise** — a self-hosted, advisory-only Kubernetes cost and performance optimization dashboard.

### What it does

- Deploys a **read-only agent** (ClusterRole with only `get/list/watch`) into your cluster
- Collects: nodes, namespaces, deployments, statefulsets, pod resource specs
- Runs a **deterministic recommendation engine** — no ML, no AI, no cloud APIs
- Presents findings in a dashboard: cost estimates, waste detection, right-sizing suggestions
- Generates **advisory YAML patches and kubectl commands** — you decide if you apply them
- **Never auto-applies anything** to your cluster

### What I'm seeing on my own homelab

```
Cluster:   talos-homelab (Talos Linux, k8s v1.34)
Nodes:     2 (talos-cp-01 + talos-wk-01)
Workloads: 37 across 30 namespaces
Findings:  39 recommendations

Top flags:
  • 29 workloads with NO resource limits set
  • 10 workloads in system namespaces (HIGH risk to touch)
  • coredns: over-provisioned CPU
```

The biggest takeaway? Almost none of my workloads (ArgoCD, Grafana, Uptime Kuma, Victoria Metrics, Tailscale, etc.) have `resources:` blocks set. That's both a scheduling risk and means the k8s scheduler has no data to work with.

### Cost model

Since it's bare-metal, costs are estimated using a configurable hourly rate per node (`$0.096/hr` default, ~$138/mo for 2 nodes). The cost per workload is:

```
workload_cost = (cpu_request / total_cluster_cpu) × node_cost × 0.5
              + (mem_request / total_cluster_mem) × node_cost × 0.5
```

If a workload has no `resources.requests` set → it shows `$0` because the scheduler doesn't know what it's using. That's exactly the problem — you can't optimize what you can't measure.

### Stack

- **Backend:** FastAPI + SQLAlchemy (SQLite) — no heavy DB required
- **Frontend:** Next.js 14 + Tailwind CSS + Recharts
- **Agent:** Python + kubernetes SDK (read-only)
- **Deploy:** Helm chart or raw k8s manifests
- **Images:** Published to GHCR (`ghcr.io/jamilshaikh07/kubewise-*`)

### Deploy it yourself (5 minutes)

```bash
# Add imagePullSecret if needed (GHCR packages)
kubectl create namespace kubewise
kubectl create secret docker-registry ghcr-pull-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_TOKEN \
  -n kubewise

# Helm install
helm install kubewise \
  oci://ghcr.io/jamilshaikh07/charts/kubewise \
  --namespace kubewise \
  --set "global.imagePullSecrets[0].name=ghcr-pull-secret" \
  --set agent.enabled=true \
  --set agent.clusterName=my-cluster

# Access
kubectl port-forward -n kubewise svc/kubewise-dashboard 3000:3000
# open http://localhost:3000
```

Or just Docker Compose for a quick look with demo data:

```bash
git clone https://github.com/jamilshaikh07/kubewise
cd kubewise
docker compose up
# frontend: http://localhost:3002  |  API docs: http://localhost:8001/docs
```

### What's next

- [ ] Metrics-server integration for real P95 CPU/memory usage (currently confidence is LOW for most workloads without it)
- [ ] Persistent recommendations history (track improvement over time)
- [ ] Grafana dashboard export (Victoria Metrics / Prometheus datasource)
- [ ] Multi-cluster support
- [ ] Slack/webhook alerts for new HIGH risk findings

### Links

- GitHub: https://github.com/jamilshaikh07/kubewise
- Images: `ghcr.io/jamilshaikh07/kubewise-{api,dashboard,agent}:0.1.0`

Happy to answer questions — built this over a few sessions as an MVP. Criticism welcome, especially on the cost model and recommendation logic.

---

## Suggested subreddits

- **r/homelab** — primary, strongest fit (self-hosted k8s angle)
- **r/kubernetes** — technical audience, focus on the RBAC + agent design
- **r/selfhosted** — focus on "no cloud account needed, runs on bare-metal"
- **r/devops** — focus on the FinOps / right-sizing angle
- **r/opensource** — for visibility

## Screenshots to include

1. Dashboard overview (cluster summary + risk breakdown bar)
2. Workload table (showing NO LIMITS flags + cost column)
3. CPU/Memory chart (request vs recommended)
4. Recommendation panel (YAML patch viewer for a specific workload)

## Key talking points for comments

**"Why not just use Kubecost?"**
> Kubecost is great but requires a cloud billing integration or Prometheus stack. KubeWise works with zero external dependencies — just the k8s API. It's intentionally simpler and advisory-only.

**"Confidence is LOW for everything, is it useful?"**
> LOW confidence means no metrics-server data — the tool can still flag missing limits/requests (which is the most common homelab problem) and estimate costs based on what IS set. Add metrics-server and confidence upgrades to HIGH.

**"Why SQLite?"**
> For a homelab tool, SQLite is perfect — no Postgres dependency, runs in a PVC, zero ops overhead. Swap the `DATABASE_URL` env var for Postgres if you want persistence + multi-replica.

**"Is it production safe?"**
> The agent is strictly read-only (ClusterRole with only get/list/watch). It cannot modify anything. All recommendations are advisory — the YAML patches are shown in the UI for you to copy-paste. Nothing is ever auto-applied.
