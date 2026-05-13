"""
Agent data ingestion endpoint.
Accepts cluster state from the KubeWise collector agent,
upserts it into the database, and runs the recommendation engine.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from engine.analyzer import ContainerMetrics, WorkloadContext, analyze_workload
from engine.cost import estimate_workload_monthly_cost, monthly_node_cost
from models.db import Cluster, Container, Namespace, Node, Recommendation, Workload
from models.schemas import ClusterIngest, IngestResponse
from storage.database import get_db

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


@router.post("", response_model=IngestResponse)
def ingest_cluster(payload: ClusterIngest, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter_by(name=payload.cluster_name).first()
    if cluster:
        db.query(Node).filter_by(cluster_id=cluster.id).delete()
        for ns in db.query(Namespace).filter_by(cluster_id=cluster.id).all():
            for wl in db.query(Workload).filter_by(namespace_id=ns.id).all():
                db.query(Recommendation).filter_by(workload_id=wl.id).delete()
                db.query(Container).filter_by(workload_id=wl.id).delete()
                db.delete(wl)
            db.delete(ns)
    else:
        cluster = Cluster(name=payload.cluster_name)
        db.add(cluster)

    cluster.provider = payload.provider
    cluster.region = payload.region
    cluster.kubernetes_version = payload.kubernetes_version
    cluster.node_count = len(payload.nodes)
    cluster.last_synced_at = datetime.now(timezone.utc)
    db.flush()

    total_cpu_m = 0
    total_mem_mib = 0
    provider_str = (payload.provider or "").lower()

    for nd in payload.nodes:
        node_cost = monthly_node_cost(provider_str, nd.instance_type)
        db.add(Node(
            cluster_id=cluster.id,
            name=nd.name,
            instance_type=nd.instance_type,
            cpu_allocatable_m=nd.cpu_allocatable_m,
            memory_allocatable_mib=nd.memory_allocatable_mib,
            cpu_capacity_m=nd.cpu_capacity_m,
            memory_capacity_mib=nd.memory_capacity_mib,
            hourly_cost_usd=node_cost / 730,
        ))
        total_cpu_m += nd.cpu_capacity_m
        total_mem_mib += nd.memory_capacity_mib

    cluster.total_cpu_cores = total_cpu_m / 1000
    cluster.total_memory_gib = total_mem_mib / 1024

    avg_node_cpu_m = max(total_cpu_m // max(len(payload.nodes), 1), 2000)
    avg_node_mem_mib = max(total_mem_mib // max(len(payload.nodes), 1), 8192)
    node_monthly = monthly_node_cost(provider_str, None)

    ns_count = 0
    wl_count = 0
    rec_count = 0

    for ns_data in payload.namespaces:
        ns = Namespace(
            cluster_id=cluster.id,
            name=ns_data.name,
            labels=ns_data.labels,
            is_system=ns_data.is_system,
        )
        db.add(ns)
        db.flush()
        ns_count += 1

        for wl_data in ns_data.workloads:
            total_cpu = sum((c.cpu_request_m or 0) for c in wl_data.containers)
            total_mem = sum((c.memory_request_mib or 0) for c in wl_data.containers)
            wl_cost = estimate_workload_monthly_cost(
                total_cpu, total_mem, wl_data.replicas,
                node_cpu_m=avg_node_cpu_m,
                node_memory_mib=avg_node_mem_mib,
                node_monthly_cost=node_monthly,
            )
            wl = Workload(
                namespace_id=ns.id,
                name=wl_data.name,
                kind=wl_data.kind,
                replicas=wl_data.replicas,
                labels=wl_data.labels,
                annotations=wl_data.annotations,
                is_high_risk=ns_data.is_system or wl_data.kind == "StatefulSet",
                estimated_monthly_cost_usd=wl_cost,
            )
            db.add(wl)
            db.flush()
            wl_count += 1

            container_metrics = []
            for c_data in wl_data.containers:
                db.add(Container(
                    workload_id=wl.id,
                    name=c_data.name,
                    cpu_request_m=c_data.cpu_request_m,
                    cpu_limit_m=c_data.cpu_limit_m,
                    memory_request_mib=c_data.memory_request_mib,
                    memory_limit_mib=c_data.memory_limit_mib,
                    cpu_usage_p95_m=c_data.cpu_usage_p95_m,
                    memory_usage_p95_mib=c_data.memory_usage_p95_mib,
                    cpu_usage_current_m=c_data.cpu_usage_current_m,
                    memory_usage_current_mib=c_data.memory_usage_current_mib,
                    has_metrics=c_data.has_metrics,
                    has_historical_metrics=c_data.has_historical_metrics,
                ))
                container_metrics.append(ContainerMetrics(
                    name=c_data.name,
                    cpu_request_m=c_data.cpu_request_m,
                    cpu_limit_m=c_data.cpu_limit_m,
                    memory_request_mib=c_data.memory_request_mib,
                    memory_limit_mib=c_data.memory_limit_mib,
                    cpu_usage_p95_m=c_data.cpu_usage_p95_m,
                    memory_usage_p95_mib=c_data.memory_usage_p95_mib,
                    cpu_usage_current_m=c_data.cpu_usage_current_m,
                    memory_usage_current_mib=c_data.memory_usage_current_mib,
                    has_metrics=c_data.has_metrics,
                    has_historical_metrics=c_data.has_historical_metrics,
                ))

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
                containers=container_metrics,
            )
            for r in analyze_workload(ctx):
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
                rec_count += 1

    db.commit()

    return IngestResponse(
        status="ok",
        cluster_name=payload.cluster_name,
        namespaces_processed=ns_count,
        workloads_processed=wl_count,
        recommendations_generated=rec_count,
    )
