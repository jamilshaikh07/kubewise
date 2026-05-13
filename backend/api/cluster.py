from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.db import Cluster, Namespace, Recommendation, Workload
from models.schemas import ClusterSummary
from storage.database import get_db

router = APIRouter(prefix="/api/v1/cluster", tags=["cluster"])


@router.get("/summary", response_model=ClusterSummary)
def cluster_summary(db: Session = Depends(get_db)):
    cluster = db.query(Cluster).order_by(Cluster.last_synced_at.desc()).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="No cluster data found. Run seed or ingest first.")

    workload_count = (
        db.query(func.count(Workload.id))
        .join(Namespace)
        .filter(Namespace.cluster_id == cluster.id)
        .scalar()
    ) or 0

    rec_count = (
        db.query(func.count(Recommendation.id))
        .join(Workload)
        .join(Namespace)
        .filter(Namespace.cluster_id == cluster.id)
        .scalar()
    ) or 0

    total_cost = (
        db.query(func.sum(Workload.estimated_monthly_cost_usd))
        .join(Namespace)
        .filter(Namespace.cluster_id == cluster.id)
        .scalar()
    ) or 0.0

    total_savings = (
        db.query(func.sum(Recommendation.estimated_monthly_savings_usd))
        .join(Workload)
        .join(Namespace)
        .filter(Namespace.cluster_id == cluster.id)
        .scalar()
    ) or 0.0

    return ClusterSummary(
        id=cluster.id,
        name=cluster.name,
        provider=cluster.provider,
        region=cluster.region,
        node_count=cluster.node_count,
        total_cpu_cores=cluster.total_cpu_cores,
        total_memory_gib=cluster.total_memory_gib,
        kubernetes_version=cluster.kubernetes_version,
        last_synced_at=cluster.last_synced_at,
        workload_count=workload_count,
        recommendation_count=rec_count,
        estimated_monthly_cost_usd=round(total_cost, 2),
        estimated_monthly_waste_usd=round(total_savings * 0.9, 2),
        estimated_monthly_savings_usd=round(total_savings, 2),
        is_estimated=True,
    )
