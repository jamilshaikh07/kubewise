# KubeWise — Skills & Concepts Demonstrated

This document maps the project's implementation to the engineering skills it exercises.

---

## 1. Kubernetes (Advanced)

| Skill | Where |
|---|---|
| RBAC — ClusterRole with least-privilege read-only access | `agent/helm/templates/clusterrole.yaml` |
| ServiceAccount + ClusterRoleBinding | `agent/helm/templates/` |
| Kubernetes Python SDK (listing nodes, pods, deployments, resource specs) | `agent/collector.py` |
| Talos Linux bare-metal k8s administration | Local cluster at 192.168.60.40/41 |
| Helm chart authoring (Chart.yaml, values.yaml, templated manifests) | `agent/helm/`, `charts/kubewise/` |
| Resource requests/limits analysis | `backend/engine/analyzer.py` |
| Pod topology and namespace classification | `backend/engine/analyzer.py` |
| kubectl patch generation (strategic merge, JSON) | `backend/engine/analyzer.py` |
| YAML patch generation for right-sizing | `backend/engine/analyzer.py` |

---

## 2. Python / Backend Engineering

| Skill | Where |
|---|---|
| FastAPI — routers, dependency injection, Pydantic validation | `backend/api/`, `backend/main.py` |
| SQLAlchemy ORM — models, relationships, sessions, migrations | `backend/models/db.py`, `backend/storage/database.py` |
| Pydantic v2 — schemas, `model_validate`, nested models | `backend/models/schemas.py` |
| Deterministic algorithm design (no ML, no LLM) | `backend/engine/analyzer.py` |
| Cost modeling — fractional resource attribution, pricing lookup | `backend/engine/cost.py` |
| Database seeding — idempotent demo data | `backend/storage/seed.py` |
| Pytest — unit tests + API smoke tests + in-memory SQLite fixtures | `backend/tests/` |
| CORS middleware configuration | `backend/main.py` |
| Environment-driven configuration (`.env`, `os.getenv`) | `backend/main.py`, `backend/storage/database.py` |
| Multi-cluster data isolation (query by most recent `last_synced_at`) | `backend/api/cluster.py`, etc. |

---

## 3. TypeScript / Frontend Engineering

| Skill | Where |
|---|---|
| Next.js 14 App Router with `"use client"` components | `frontend/app/page.tsx` |
| TypeScript strict typing — interfaces, generics, `unknown` narrowing | `frontend/lib/api.ts`, all components |
| React hooks — `useState`, `useEffect`, `useCallback` | `frontend/app/page.tsx` |
| Recharts — `BarChart`, `ResponsiveContainer`, custom tooltips | `frontend/components/SpendByNamespace.tsx`, `CpuMemChart.tsx` |
| Tailwind CSS — utility-first, responsive, custom config | All components, `tailwind.config.ts` |
| Component composition — reusable typed props interfaces | All `components/*.tsx` |
| Async data fetching with error/loading states | `frontend/app/page.tsx` |
| Clipboard API (`navigator.clipboard.writeText`) | `frontend/components/PatchViewer.tsx` |
| Next.js standalone output for minimal Docker image | `frontend/next.config.js` |
| Environment variable injection at build time vs runtime | `frontend/Dockerfile`, `next.config.js` |

---

## 4. Docker & Container Engineering

| Skill | Where |
|---|---|
| Multi-stage Dockerfile (deps → builder → runner) | `frontend/Dockerfile`, `backend/Dockerfile` |
| Docker Compose with health checks and service dependencies | `docker-compose.yml` |
| Container networking — internal DNS (`kubewise-api:8000`) vs host ports | `docker-compose.yml` |
| Non-root system users in containers | Both Dockerfiles |
| Build args vs runtime environment variables | `frontend/Dockerfile`, `docker-compose.yml` |
| Volume mounts — persistent data + kubeconfig injection | `docker-compose.yml` |
| Kubeconfig patching for Docker networking (localhost → node IP) | `agent-kubeconfig.yaml` |
| Image layering and cache optimization | Both Dockerfiles |

---

## 5. FinOps / SRE Domain Knowledge

| Skill | Where |
|---|---|
| Kubernetes resource right-sizing methodology | `backend/engine/analyzer.py` |
| P95 usage-based CPU/memory recommendations | `backend/engine/analyzer.py` |
| Cost attribution by namespace and workload | `backend/engine/cost.py` |
| Cloud pricing models (per-vCPU, per-GiB fractional attribution) | `backend/pricing.json`, `backend/engine/cost.py` |
| Waste identification — over-provisioning, idle workloads | `backend/engine/analyzer.py` |
| Risk classification for production workloads | `backend/engine/analyzer.py` |
| Advisory-only safety model (no auto-apply) | `docs/safety-model.md`, UI banners |
| System namespace protection | `backend/engine/analyzer.py` |

---

## 6. Software Architecture

| Skill | Where |
|---|---|
| Clean separation of concerns (collector / engine / API / UI) | Full project structure |
| Pluggable data ingestion (any agent can POST to `/ingest`) | `backend/api/ingest.py` |
| Idempotent upsert pattern | `backend/api/ingest.py` |
| Pagination and filtering on list endpoints | `backend/api/workloads.py`, `frontend/app/page.tsx` |
| Advisory-only design (display patches, never apply) | Full stack |
| Local-first dev with Docker Compose → production Helm chart | `docker-compose.yml`, `charts/kubewise/` |

---

## 7. Developer Experience

| Skill | Where |
|---|---|
| Auto-seeding demo data on startup | `backend/storage/seed.py`, `backend/main.py` |
| OpenAPI docs auto-generated at `/docs` | FastAPI |
| `.env.example` files for both services | `backend/.env.example`, `frontend/.env.example` |
| `.gitignore` for credentials and build artifacts | `.gitignore` |
| Structured logging in the agent | `agent/collector.py` |
