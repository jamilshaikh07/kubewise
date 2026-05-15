from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from models.db import Cluster, Container, Namespace, Recommendation, Workload
from models.schemas import RecommendationOut, SavingsEstimate
from storage.database import get_db

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


def _rec_out(r: Recommendation, wl: Workload, ns_name: str) -> RecommendationOut:
    ctr = next((c for c in wl.containers if c.name == r.container_name), None)
    return RecommendationOut(
        id=r.id,
        workload_id=wl.id,
        workload_name=wl.name,
        namespace=ns_name,
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
        cpu_usage_p95_m=ctr.cpu_usage_p95_m if ctr else None,
        memory_usage_p95_mib=ctr.memory_usage_p95_mib if ctr else None,
        cpu_usage_current_m=ctr.cpu_usage_current_m if ctr else None,
        memory_usage_current_mib=ctr.memory_usage_current_mib if ctr else None,
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


@router.get("", response_model=list[RecommendationOut])
def list_recommendations(
    namespace: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    confidence: Optional[str] = Query(None),
    flag_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    active_cluster = db.query(Cluster).order_by(Cluster.last_synced_at.desc()).first()
    cluster_id = active_cluster.id if active_cluster else None

    q = (
        db.query(Recommendation)
        .join(Workload)
        .join(Namespace)
        .options(
            joinedload(Recommendation.workload).joinedload(Workload.namespace),
            joinedload(Recommendation.workload).joinedload(Workload.containers),
        )
    )
    if cluster_id:
        q = q.filter(Namespace.cluster_id == cluster_id)
    if namespace:
        q = q.filter(Namespace.name == namespace)
    if risk:
        q = q.filter(Recommendation.risk == risk)
    if confidence:
        q = q.filter(Recommendation.confidence == confidence)
    if flag_type:
        q = q.filter(Recommendation.flag_type == flag_type)

    recs = q.all()
    return [_rec_out(r, r.workload, r.workload.namespace.name) for r in recs]


@router.get("/savings", response_model=SavingsEstimate)
def savings_estimate(db: Session = Depends(get_db)):
    from sqlalchemy import func

    active_cluster = db.query(Cluster).order_by(Cluster.last_synced_at.desc()).first()
    cluster_id = active_cluster.id if active_cluster else None

    cost_q = db.query(func.sum(Workload.estimated_monthly_cost_usd)).join(Namespace)
    sav_q = db.query(func.sum(Recommendation.estimated_monthly_savings_usd)).join(Workload).join(Namespace)
    if cluster_id:
        cost_q = cost_q.filter(Namespace.cluster_id == cluster_id)
        sav_q = sav_q.filter(Namespace.cluster_id == cluster_id)
    total_cost = cost_q.scalar() or 0.0
    total_savings = sav_q.scalar() or 0.0

    ns_sav_q = (
        db.query(Namespace.name, func.sum(Recommendation.estimated_monthly_savings_usd))
        .join(Workload, Workload.namespace_id == Namespace.id)
        .join(Recommendation, Recommendation.workload_id == Workload.id)
        .group_by(Namespace.name)
    )
    ns_cost_q = (
        db.query(Namespace.name, func.sum(Workload.estimated_monthly_cost_usd))
        .join(Workload, Workload.namespace_id == Namespace.id)
        .group_by(Namespace.name)
    )
    if cluster_id:
        ns_sav_q = ns_sav_q.filter(Namespace.cluster_id == cluster_id)
        ns_cost_q = ns_cost_q.filter(Namespace.cluster_id == cluster_id)
    ns_savings = ns_sav_q.all()
    ns_cost = ns_cost_q.all()
    cost_map = {name: val for name, val in ns_cost}

    savings_by_ns = [
        {
            "namespace": name,
            "estimated_monthly_cost_usd": round(cost_map.get(name, 0.0), 2),
            "potential_savings_usd": round(val or 0.0, 2),
        }
        for name, val in ns_savings
    ]

    return SavingsEstimate(
        total_estimated_monthly_cost_usd=round(total_cost, 2),
        total_estimated_monthly_waste_usd=round(total_savings * 0.9, 2),
        total_potential_savings_usd=round(total_savings, 2),
        savings_by_namespace=savings_by_ns,
        is_estimated=True,
    )


@router.get("/{rec_id}", response_model=RecommendationOut)
def get_recommendation(rec_id: int, db: Session = Depends(get_db)):
    r = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.workload).joinedload(Workload.namespace))
        .filter(Recommendation.id == rec_id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return _rec_out(r, r.workload, r.workload.namespace.name)
