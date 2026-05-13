from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.db import Cluster, Namespace, Recommendation, Workload
from models.schemas import NamespaceSummary
from storage.database import get_db

router = APIRouter(prefix="/api/v1/namespaces", tags=["namespaces"])


@router.get("", response_model=list[NamespaceSummary])
def list_namespaces(db: Session = Depends(get_db)):
    cluster = db.query(Cluster).order_by(Cluster.last_synced_at.desc()).first()
    if not cluster:
        return []

    namespaces = db.query(Namespace).filter_by(cluster_id=cluster.id).all()
    result = []
    for ns in namespaces:
        wl_count = db.query(func.count(Workload.id)).filter_by(namespace_id=ns.id).scalar() or 0
        cost = db.query(func.sum(Workload.estimated_monthly_cost_usd)).filter_by(namespace_id=ns.id).scalar() or 0.0
        rec_count = (
            db.query(func.count(Recommendation.id))
            .join(Workload)
            .filter(Workload.namespace_id == ns.id)
            .scalar()
        ) or 0
        savings = (
            db.query(func.sum(Recommendation.estimated_monthly_savings_usd))
            .join(Workload)
            .filter(Workload.namespace_id == ns.id)
            .scalar()
        ) or 0.0

        result.append(NamespaceSummary(
            id=ns.id,
            name=ns.name,
            is_system=ns.is_system,
            workload_count=wl_count,
            estimated_monthly_cost_usd=round(cost, 2),
            estimated_monthly_savings_usd=round(savings, 2),
            recommendation_count=rec_count,
            is_estimated=True,
        ))
    return result
