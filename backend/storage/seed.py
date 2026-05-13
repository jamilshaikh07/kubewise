"""
Demo seed data — loads a realistic fake cluster so the dashboard works
without a live Kubernetes cluster.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from engine.analyzer import analyze_workload, ContainerMetrics, WorkloadContext
from engine.cost import estimate_workload_monthly_cost, monthly_node_cost
from models.db import Cluster, Container, Namespace, Node, Recommendation, Workload

DEMO_CLUSTER_NAME = "demo-cluster"

_NODES = [
    {"name": "node-1", "instance_type": "m5.xlarge",  "cpu_m": 4000, "mem_mib": 16384, "provider": "aws"},
    {"name": "node-2", "instance_type": "m5.xlarge",  "cpu_m": 4000, "mem_mib": 16384, "provider": "aws"},
    {"name": "node-3", "instance_type": "m5.2xlarge", "cpu_m": 8000, "mem_mib": 32768, "provider": "aws"},
]

_NAMESPACES = [
    {
        "name": "production",
        "is_system": False,
        "workloads": [
            {
                "name": "api-server",
                "kind": "Deployment",
                "replicas": 3,
                "containers": [
                    {
                        "name": "api",
                        "cpu_request_m": 500, "cpu_limit_m": 1000,
                        "memory_request_mib": 512, "memory_limit_mib": 1024,
                        "cpu_usage_p95_m": 85, "memory_usage_p95_mib": 210,
                        "cpu_usage_current_m": 70, "memory_usage_current_mib": 190,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
            {
                "name": "payment-service",
                "kind": "Deployment",
                "replicas": 2,
                "containers": [
                    {
                        "name": "payment",
                        "cpu_request_m": 1000, "cpu_limit_m": 2000,
                        "memory_request_mib": 1024, "memory_limit_mib": 2048,
                        "cpu_usage_p95_m": 220, "memory_usage_p95_mib": 380,
                        "cpu_usage_current_m": 200, "memory_usage_current_mib": 350,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
            {
                "name": "notification-worker",
                "kind": "Deployment",
                "replicas": 1,
                "containers": [
                    {
                        "name": "worker",
                        "cpu_request_m": 500, "cpu_limit_m": 1000,
                        "memory_request_mib": 512, "memory_limit_mib": 1024,
                        "cpu_usage_p95_m": 3, "memory_usage_p95_mib": 45,
                        "cpu_usage_current_m": 2, "memory_usage_current_mib": 40,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
            {
                "name": "frontend",
                "kind": "Deployment",
                "replicas": 2,
                "containers": [
                    {
                        "name": "nginx",
                        "cpu_request_m": 200, "cpu_limit_m": 500,
                        "memory_request_mib": 256, "memory_limit_mib": 512,
                        "cpu_usage_p95_m": 18, "memory_usage_p95_mib": 55,
                        "cpu_usage_current_m": 15, "memory_usage_current_mib": 50,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
            {
                "name": "data-exporter",
                "kind": "Deployment",
                "replicas": 1,
                "containers": [
                    {
                        "name": "exporter",
                        "cpu_request_m": None, "cpu_limit_m": None,
                        "memory_request_mib": None, "memory_limit_mib": None,
                        "cpu_usage_p95_m": 30, "memory_usage_p95_mib": 90,
                        "cpu_usage_current_m": 25, "memory_usage_current_mib": 85,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
            {
                "name": "postgres",
                "kind": "StatefulSet",
                "replicas": 1,
                "containers": [
                    {
                        "name": "postgres",
                        "cpu_request_m": 500, "cpu_limit_m": 1000,
                        "memory_request_mib": 1024, "memory_limit_mib": 2048,
                        "cpu_usage_p95_m": 120, "memory_usage_p95_mib": 820,
                        "cpu_usage_current_m": 110, "memory_usage_current_mib": 800,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
        ],
    },
    {
        "name": "staging",
        "is_system": False,
        "workloads": [
            {
                "name": "api-server",
                "kind": "Deployment",
                "replicas": 1,
                "containers": [
                    {
                        "name": "api",
                        "cpu_request_m": 500, "cpu_limit_m": 1000,
                        "memory_request_mib": 512, "memory_limit_mib": 1024,
                        "cpu_usage_p95_m": 12, "memory_usage_p95_mib": 95,
                        "cpu_usage_current_m": 10, "memory_usage_current_mib": 90,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
            {
                "name": "redis",
                "kind": "StatefulSet",
                "replicas": 1,
                "containers": [
                    {
                        "name": "redis",
                        "cpu_request_m": 250, "cpu_limit_m": None,
                        "memory_request_mib": 512, "memory_limit_mib": None,
                        "cpu_usage_p95_m": 8, "memory_usage_p95_mib": 70,
                        "cpu_usage_current_m": 7, "memory_usage_current_mib": 65,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
            {
                "name": "batch-processor",
                "kind": "Deployment",
                "replicas": 2,
                "containers": [
                    {
                        "name": "processor",
                        "cpu_request_m": 2000, "cpu_limit_m": 4000,
                        "memory_request_mib": 4096, "memory_limit_mib": 8192,
                        "cpu_usage_p95_m": 180, "memory_usage_p95_mib": 310,
                        "cpu_usage_current_m": 150, "memory_usage_current_mib": 280,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
            {
                "name": "ml-inference",
                "kind": "Deployment",
                "replicas": 1,
                "containers": [
                    {
                        "name": "inference",
                        "cpu_request_m": 4000, "cpu_limit_m": 8000,
                        "memory_request_mib": 8192, "memory_limit_mib": 16384,
                        "cpu_usage_p95_m": 600, "memory_usage_p95_mib": 1200,
                        "cpu_usage_current_m": 550, "memory_usage_current_mib": 1100,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
        ],
    },
    {
        "name": "monitoring",
        "is_system": False,
        "workloads": [
            {
                "name": "prometheus",
                "kind": "StatefulSet",
                "replicas": 1,
                "containers": [
                    {
                        "name": "prometheus",
                        "cpu_request_m": 500, "cpu_limit_m": 2000,
                        "memory_request_mib": 2048, "memory_limit_mib": 4096,
                        "cpu_usage_p95_m": 95, "memory_usage_p95_mib": 1600,
                        "cpu_usage_current_m": 85, "memory_usage_current_mib": 1500,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
            {
                "name": "grafana",
                "kind": "Deployment",
                "replicas": 1,
                "containers": [
                    {
                        "name": "grafana",
                        "cpu_request_m": 200, "cpu_limit_m": 500,
                        "memory_request_mib": 256, "memory_limit_mib": 512,
                        "cpu_usage_p95_m": 22, "memory_usage_p95_mib": 185,
                        "cpu_usage_current_m": 20, "memory_usage_current_mib": 180,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
        ],
    },
    {
        "name": "kube-system",
        "is_system": True,
        "workloads": [
            {
                "name": "coredns",
                "kind": "Deployment",
                "replicas": 2,
                "containers": [
                    {
                        "name": "coredns",
                        "cpu_request_m": 100, "cpu_limit_m": None,
                        "memory_request_mib": 70, "memory_limit_mib": 170,
                        "cpu_usage_p95_m": 4, "memory_usage_p95_mib": 22,
                        "cpu_usage_current_m": 3, "memory_usage_current_mib": 20,
                        "has_metrics": True, "has_historical_metrics": True,
                    }
                ],
            },
        ],
    },
]


def seed(db: Session) -> None:
    existing = db.query(Cluster).filter_by(name=DEMO_CLUSTER_NAME).first()
    if existing:
        return

    cluster = Cluster(
        name=DEMO_CLUSTER_NAME,
        provider="aws",
        region="us-east-1",
        kubernetes_version="1.29.3",
        node_count=len(_NODES),
        total_cpu_cores=sum(n["cpu_m"] for n in _NODES) / 1000,
        total_memory_gib=sum(n["mem_mib"] for n in _NODES) / 1024,
        last_synced_at=datetime.now(timezone.utc),
    )
    db.add(cluster)
    db.flush()

    node_monthly = monthly_node_cost("aws", "m5.xlarge")

    for nd in _NODES:
        node_monthly_cost_val = monthly_node_cost("aws", nd["instance_type"])
        db.add(Node(
            cluster_id=cluster.id,
            name=nd["name"],
            instance_type=nd["instance_type"],
            cpu_allocatable_m=nd["cpu_m"] - 100,
            memory_allocatable_mib=nd["mem_mib"] - 512,
            cpu_capacity_m=nd["cpu_m"],
            memory_capacity_mib=nd["mem_mib"],
            hourly_cost_usd=node_monthly_cost_val / 730,
        ))

    avg_node_cpu_m = 5333
    avg_node_mem_mib = 21845

    for ns_data in _NAMESPACES:
        ns = Namespace(
            cluster_id=cluster.id,
            name=ns_data["name"],
            is_system=ns_data["is_system"],
        )
        db.add(ns)
        db.flush()

        for wl_data in ns_data["workloads"]:
            containers_data = wl_data["containers"]

            total_cpu_req = sum(
                (c.get("cpu_request_m") or 0) for c in containers_data
            )
            total_mem_req = sum(
                (c.get("memory_request_mib") or 0) for c in containers_data
            )
            wl_cost = estimate_workload_monthly_cost(
                total_cpu_req, total_mem_req,
                wl_data["replicas"],
                node_cpu_m=avg_node_cpu_m,
                node_memory_mib=avg_node_mem_mib,
                node_monthly_cost=node_monthly,
            )

            wl = Workload(
                namespace_id=ns.id,
                name=wl_data["name"],
                kind=wl_data["kind"],
                replicas=wl_data["replicas"],
                is_high_risk=ns_data["is_system"] or wl_data["kind"] == "StatefulSet",
                estimated_monthly_cost_usd=wl_cost,
            )
            db.add(wl)
            db.flush()

            container_objs: list[Container] = []
            for c_data in containers_data:
                c = Container(
                    workload_id=wl.id,
                    name=c_data["name"],
                    cpu_request_m=c_data.get("cpu_request_m"),
                    cpu_limit_m=c_data.get("cpu_limit_m"),
                    memory_request_mib=c_data.get("memory_request_mib"),
                    memory_limit_mib=c_data.get("memory_limit_mib"),
                    cpu_usage_p95_m=c_data.get("cpu_usage_p95_m"),
                    memory_usage_p95_mib=c_data.get("memory_usage_p95_mib"),
                    cpu_usage_current_m=c_data.get("cpu_usage_current_m"),
                    memory_usage_current_mib=c_data.get("memory_usage_current_mib"),
                    has_metrics=c_data.get("has_metrics", False),
                    has_historical_metrics=c_data.get("has_historical_metrics", False),
                )
                db.add(c)
                container_objs.append(c)

            ctx = WorkloadContext(
                workload_id=wl.id,
                workload_name=wl.name,
                namespace=ns.name,
                kind=wl.kind,
                replicas=wl.replicas,
                is_system_namespace=ns.is_system,
                node_cpu_m=avg_node_cpu_m,
                node_memory_mib=avg_node_mem_mib,
                node_monthly_cost=node_monthly,
                containers=[
                    ContainerMetrics(
                        name=c_data["name"],
                        cpu_request_m=c_data.get("cpu_request_m"),
                        cpu_limit_m=c_data.get("cpu_limit_m"),
                        memory_request_mib=c_data.get("memory_request_mib"),
                        memory_limit_mib=c_data.get("memory_limit_mib"),
                        cpu_usage_p95_m=c_data.get("cpu_usage_p95_m"),
                        memory_usage_p95_mib=c_data.get("memory_usage_p95_mib"),
                        cpu_usage_current_m=c_data.get("cpu_usage_current_m"),
                        memory_usage_current_mib=c_data.get("memory_usage_current_mib"),
                        has_metrics=c_data.get("has_metrics", False),
                        has_historical_metrics=c_data.get("has_historical_metrics", False),
                    )
                    for c_data in containers_data
                ],
            )
            recs = analyze_workload(ctx)
            for r in recs:
                db.add(Recommendation(
                    workload_id=wl.id,
                    container_name=r.container_name,
                    flag_type=r.flag_type,
                    confidence=r.confidence,
                    risk=r.risk,
                    explanation=r.explanation,
                    current_cpu_request_m=r.current_cpu_request_m,
                    current_cpu_limit_m=r.current_cpu_limit_m,
                    current_memory_request_mib=r.current_memory_request_mib,
                    current_memory_limit_mib=r.current_memory_limit_mib,
                    recommended_cpu_request_m=r.recommended_cpu_request_m,
                    recommended_cpu_limit_m=r.recommended_cpu_limit_m,
                    recommended_memory_request_mib=r.recommended_memory_request_mib,
                    recommended_memory_limit_mib=r.recommended_memory_limit_mib,
                    estimated_monthly_savings_usd=r.estimated_monthly_savings_usd,
                    is_estimated=r.is_estimated,
                    yaml_patch=r.yaml_patch,
                    kubectl_command=r.kubectl_command,
                ))

    db.commit()
