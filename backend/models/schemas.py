from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Cluster ──────────────────────────────────────────────────────────────────

class ClusterSummary(BaseModel):
    id: int
    name: str
    provider: Optional[str]
    region: Optional[str]
    node_count: int
    total_cpu_cores: float
    total_memory_gib: float
    kubernetes_version: Optional[str]
    last_synced_at: Optional[datetime]
    workload_count: int
    recommendation_count: int
    estimated_monthly_cost_usd: float
    estimated_monthly_waste_usd: float
    estimated_monthly_savings_usd: float
    is_estimated: bool = True

    model_config = {"from_attributes": True}


# ── Node ─────────────────────────────────────────────────────────────────────

class NodeOut(BaseModel):
    id: int
    name: str
    instance_type: Optional[str]
    cpu_allocatable_m: int
    memory_allocatable_mib: int
    hourly_cost_usd: float

    model_config = {"from_attributes": True}


# ── Namespace ─────────────────────────────────────────────────────────────────

class NamespaceSummary(BaseModel):
    id: int
    name: str
    is_system: bool
    workload_count: int
    estimated_monthly_cost_usd: float
    estimated_monthly_savings_usd: float
    recommendation_count: int
    is_estimated: bool = True

    model_config = {"from_attributes": True}


# ── Container ────────────────────────────────────────────────────────────────

class ContainerOut(BaseModel):
    id: int
    name: str
    cpu_request_m: Optional[int]
    cpu_limit_m: Optional[int]
    memory_request_mib: Optional[int]
    memory_limit_mib: Optional[int]
    cpu_usage_p95_m: Optional[int]
    memory_usage_p95_mib: Optional[int]
    cpu_usage_current_m: Optional[int]
    memory_usage_current_mib: Optional[int]
    has_metrics: bool
    has_historical_metrics: bool

    model_config = {"from_attributes": True}


# ── Workload ─────────────────────────────────────────────────────────────────

class WorkloadListItem(BaseModel):
    id: int
    name: str
    namespace: str
    kind: str
    replicas: int
    is_high_risk: bool
    estimated_monthly_cost_usd: float
    recommendation_count: int
    top_flag: Optional[str]
    top_risk: Optional[str]
    top_confidence: Optional[str]
    potential_savings_usd: float
    is_estimated: bool = True

    model_config = {"from_attributes": True}


class WorkloadDetail(BaseModel):
    id: int
    name: str
    namespace: str
    kind: str
    replicas: int
    labels: Optional[str]
    annotations: Optional[str]
    is_high_risk: bool
    estimated_monthly_cost_usd: float
    containers: list[ContainerOut]
    recommendations: list["RecommendationOut"]
    is_estimated: bool = True

    model_config = {"from_attributes": True}


# ── Recommendation ────────────────────────────────────────────────────────────

class RecommendationOut(BaseModel):
    id: int
    workload_id: int
    workload_name: str
    namespace: str
    kind: str
    container_name: str
    flag_type: str
    confidence: str
    risk: str
    explanation: str

    current_cpu_request_m: Optional[int]
    current_cpu_limit_m: Optional[int]
    current_memory_request_mib: Optional[int]
    current_memory_limit_mib: Optional[int]

    cpu_usage_p95_m: Optional[int] = None
    memory_usage_p95_mib: Optional[int] = None
    cpu_usage_current_m: Optional[int] = None
    memory_usage_current_mib: Optional[int] = None

    recommended_cpu_request_m: Optional[int]
    recommended_cpu_limit_m: Optional[int]
    recommended_memory_request_mib: Optional[int]
    recommended_memory_limit_mib: Optional[int]

    estimated_monthly_savings_usd: float
    is_estimated: bool

    yaml_patch: Optional[str]
    kubectl_command: Optional[str]

    created_at: datetime

    model_config = {"from_attributes": True}


WorkloadDetail.model_rebuild()


# ── Savings ───────────────────────────────────────────────────────────────────

class SavingsEstimate(BaseModel):
    total_estimated_monthly_cost_usd: float
    total_estimated_monthly_waste_usd: float
    total_potential_savings_usd: float
    savings_by_namespace: list[dict]
    is_estimated: bool = True


# ── Ingest ────────────────────────────────────────────────────────────────────

class ContainerIngest(BaseModel):
    name: str
    cpu_request_m: Optional[int] = None
    cpu_limit_m: Optional[int] = None
    memory_request_mib: Optional[int] = None
    memory_limit_mib: Optional[int] = None
    cpu_usage_p95_m: Optional[int] = None
    memory_usage_p95_mib: Optional[int] = None
    cpu_usage_current_m: Optional[int] = None
    memory_usage_current_mib: Optional[int] = None
    has_metrics: bool = False
    has_historical_metrics: bool = False


class WorkloadIngest(BaseModel):
    name: str
    kind: str
    replicas: int = 1
    labels: Optional[str] = None
    annotations: Optional[str] = None
    containers: list[ContainerIngest] = []


class NamespaceIngest(BaseModel):
    name: str
    labels: Optional[str] = None
    is_system: bool = False
    workloads: list[WorkloadIngest] = []


class NodeIngest(BaseModel):
    name: str
    instance_type: Optional[str] = None
    cpu_allocatable_m: int = 0
    memory_allocatable_mib: int = 0
    cpu_capacity_m: int = 0
    memory_capacity_mib: int = 0


class ClusterIngest(BaseModel):
    cluster_name: str
    provider: Optional[str] = None
    region: Optional[str] = None
    kubernetes_version: Optional[str] = None
    nodes: list[NodeIngest] = []
    namespaces: list[NamespaceIngest] = []


class IngestResponse(BaseModel):
    status: str
    cluster_name: str
    namespaces_processed: int
    workloads_processed: int
    recommendations_generated: int


# ── Filters / Pagination ──────────────────────────────────────────────────────

class WorkloadFilters(BaseModel):
    namespace: Optional[str] = None
    risk: Optional[str] = None
    confidence: Optional[str] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class PaginatedWorkloads(BaseModel):
    items: list[WorkloadListItem]
    total: int
    page: int
    page_size: int
