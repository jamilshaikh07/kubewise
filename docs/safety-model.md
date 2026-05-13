# KubeWise Safety Model

## Core Principle: Advisory Only

KubeWise **never** writes to or modifies your Kubernetes cluster. All recommendations are advisory.

## What the Agent Can and Cannot Do

| Action | Agent |
|---|---|
| List namespaces, nodes, pods, deployments, statefulsets | ✅ |
| Read resource requests and limits | ✅ |
| Read metrics (if metrics-server is present) | ✅ |
| Read secrets, configmaps, or sensitive data | ❌ |
| Create, update, or delete any resource | ❌ |
| Exec into pods | ❌ |
| Access the Kubernetes control plane API beyond list/watch verbs | ❌ |

The agent ClusterRole only grants `get`, `list`, `watch` on a minimal set of resources.

## Risk Classification

Recommendations carry a `risk` label:

| Level | Meaning |
|---|---|
| `high` | Workload is in a system namespace (`kube-system`, `kube-public`, `kube-node-lease`) or is the only replica with no PodDisruptionBudget. Any change could cause service disruption. |
| `medium` | Low replicas (≤ 2), or lack of resource limits. Changes require testing. |
| `low` | Workload has multiple replicas, has metrics, and the change is conservative. Low likelihood of disruption. |

## Confidence Classification

| Level | Meaning |
|---|---|
| `high` | Historical P95 metrics available; recommendation is based on observed data |
| `medium` | Metrics available but limited history, or heuristic-based |
| `low` | No metrics; recommendation is based on absence of requests/limits only |

## UI Safeguards

- A persistent **"Advisory Only"** badge appears in the top navigation bar
- High-risk and system-namespace recommendations show a visible **warning banner** before the patch
- Every patch panel shows the message: *"KubeWise never auto-applies changes. Review this patch carefully before applying manually."*
- All cost values are labelled **(est.)** to indicate they are estimates based on configurable pricing

## How to Apply a Recommendation

1. Review the explanation and resource diff in the recommendation panel
2. Copy the YAML patch or `kubectl` command
3. Test in a non-production environment first
4. Apply manually with `kubectl apply` or your GitOps pipeline
5. Monitor the workload after the change

## Audit Trail

All recommendations are stored in the database with timestamps. No recommendations are deleted when new data is ingested — they are updated. This provides a full audit trail of what was recommended and when.
