from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.db import Cluster, Namespace, Recommendation, Workload
from models.schemas import (
    ContainerOut,
    PaginatedWorkloads,
    RecommendationOut,
    WorkloadDetail,
    WorkloadListItem,
)
from storage.database import get_db

router = APIRouter(prefix="/api/v1/workloads", tags=["workloads"])


def _top_rec(recs: list) -> tuple[Optional[str], Optional[str], Optional[str]]:
    if not recs:
        return None, None, None
    risk_order = {"high": 0, "medium": 1, "low": 2}
    top = sorted(recs, key=lambda r: risk_order.get(r.risk, 9))[0]
    return top.flag_type, top.risk, top.confidence


@router.get("", response_model=PaginatedWorkloads)
def list_workloads(
    namespace: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    confidence: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    active_cluster = db.query(Cluster).order_by(Cluster.last_synced_at.desc()).first()
    cluster_id = active_cluster.id if active_cluster else None

    q = db.query(Workload).join(Namespace)
    if cluster_id:
        q = q.filter(Namespace.cluster_id == cluster_id)
    if namespace:
        q = q.filter(Namespace.name == namespace)
    if search:
        q = q.filter(Workload.name.ilike(f"%{search}%"))

    workloads = q.options(joinedload(Workload.recommendations), joinedload(Workload.namespace)).all()

    if risk or confidence:
        filtered = []
        for wl in workloads:
            recs = wl.recommendations
            if risk:
                recs = [r for r in recs if r.risk == risk]
            if confidence:
                recs = [r for r in recs if r.confidence == confidence]
            if recs:
                filtered.append(wl)
        workloads = filtered

    total = len(workloads)
    start = (page - 1) * page_size
    page_workloads = workloads[start: start + page_size]

    items = []
    for wl in page_workloads:
        recs = wl.recommendations
        flag, top_risk, top_conf = _top_rec(recs)
        savings = sum(r.estimated_monthly_savings_usd for r in recs)
        items.append(WorkloadListItem(
            id=wl.id,
            name=wl.name,
            namespace=wl.namespace.name,
            kind=wl.kind,
            replicas=wl.replicas,
            is_high_risk=wl.is_high_risk,
            estimated_monthly_cost_usd=round(wl.estimated_monthly_cost_usd, 2),
            recommendation_count=len(recs),
            top_flag=flag,
            top_risk=top_risk,
            top_confidence=top_conf,
            potential_savings_usd=round(savings, 2),
            is_estimated=True,
        ))

    return PaginatedWorkloads(items=items, total=total, page=page, page_size=page_size)


@router.get("/{workload_id}", response_model=WorkloadDetail)
def get_workload(workload_id: int, db: Session = Depends(get_db)):
    wl = (
        db.query(Workload)
        .options(
            joinedload(Workload.namespace),
            joinedload(Workload.containers),
            joinedload(Workload.recommendations),
        )
        .filter(Workload.id == workload_id)
        .first()
    )
    if not wl:
        raise HTTPException(status_code=404, detail="Workload not found")

    containers = [ContainerOut.model_validate(c) for c in wl.containers]
    recommendations = [
        RecommendationOut(
            id=r.id,
            workload_id=wl.id,
            workload_name=wl.name,
            namespace=wl.namespace.name,
            kind=wl.kind,
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
            created_at=r.created_at,
        )
        for r in wl.recommendations
    ]

    return WorkloadDetail(
        id=wl.id,
        name=wl.name,
        namespace=wl.namespace.name,
        kind=wl.kind,
        replicas=wl.replicas,
        labels=wl.labels,
        annotations=wl.annotations,
        is_high_risk=wl.is_high_risk,
        estimated_monthly_cost_usd=round(wl.estimated_monthly_cost_usd, 2),
        containers=containers,
        recommendations=recommendations,
        is_estimated=True,
    )
