from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    node_count: Mapped[int] = mapped_column(Integer, default=0)
    total_cpu_cores: Mapped[float] = mapped_column(Float, default=0.0)
    total_memory_gib: Mapped[float] = mapped_column(Float, default=0.0)
    kubernetes_version: Mapped[Optional[str]] = mapped_column(String(50))
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    namespaces: Mapped[list["Namespace"]] = relationship(
        "Namespace", back_populates="cluster", cascade="all, delete-orphan"
    )
    nodes: Mapped[list["Node"]] = relationship(
        "Node", back_populates="cluster", cascade="all, delete-orphan"
    )


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    instance_type: Mapped[Optional[str]] = mapped_column(String(100))
    cpu_allocatable_m: Mapped[int] = mapped_column(Integer, default=0)
    memory_allocatable_mib: Mapped[int] = mapped_column(Integer, default=0)
    cpu_capacity_m: Mapped[int] = mapped_column(Integer, default=0)
    memory_capacity_mib: Mapped[int] = mapped_column(Integer, default=0)
    hourly_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="nodes")


class Namespace(Base):
    __tablename__ = "namespaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    labels: Mapped[Optional[str]] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="namespaces")
    workloads: Mapped[list["Workload"]] = relationship(
        "Workload", back_populates="namespace", cascade="all, delete-orphan"
    )


class Workload(Base):
    __tablename__ = "workloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    namespace_id: Mapped[int] = mapped_column(ForeignKey("namespaces.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    replicas: Mapped[int] = mapped_column(Integer, default=1)
    labels: Mapped[Optional[str]] = mapped_column(Text)
    annotations: Mapped[Optional[str]] = mapped_column(Text)
    is_high_risk: Mapped[bool] = mapped_column(Boolean, default=False)
    estimated_monthly_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    namespace: Mapped["Namespace"] = relationship("Namespace", back_populates="workloads")
    containers: Mapped[list["Container"]] = relationship(
        "Container", back_populates="workload", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="workload", cascade="all, delete-orphan"
    )


class Container(Base):
    __tablename__ = "containers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workload_id: Mapped[int] = mapped_column(ForeignKey("workloads.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    cpu_request_m: Mapped[Optional[int]] = mapped_column(Integer)
    cpu_limit_m: Mapped[Optional[int]] = mapped_column(Integer)
    memory_request_mib: Mapped[Optional[int]] = mapped_column(Integer)
    memory_limit_mib: Mapped[Optional[int]] = mapped_column(Integer)

    cpu_usage_p95_m: Mapped[Optional[int]] = mapped_column(Integer)
    memory_usage_p95_mib: Mapped[Optional[int]] = mapped_column(Integer)
    cpu_usage_current_m: Mapped[Optional[int]] = mapped_column(Integer)
    memory_usage_current_mib: Mapped[Optional[int]] = mapped_column(Integer)

    has_metrics: Mapped[bool] = mapped_column(Boolean, default=False)
    has_historical_metrics: Mapped[bool] = mapped_column(Boolean, default=False)

    workload: Mapped["Workload"] = relationship("Workload", back_populates="containers")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workload_id: Mapped[int] = mapped_column(ForeignKey("workloads.id"), nullable=False)
    container_name: Mapped[str] = mapped_column(String(255), nullable=False)

    flag_type: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    risk: Mapped[str] = mapped_column(String(20), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    current_cpu_request_m: Mapped[Optional[int]] = mapped_column(Integer)
    current_cpu_limit_m: Mapped[Optional[int]] = mapped_column(Integer)
    current_memory_request_mib: Mapped[Optional[int]] = mapped_column(Integer)
    current_memory_limit_mib: Mapped[Optional[int]] = mapped_column(Integer)

    recommended_cpu_request_m: Mapped[Optional[int]] = mapped_column(Integer)
    recommended_cpu_limit_m: Mapped[Optional[int]] = mapped_column(Integer)
    recommended_memory_request_mib: Mapped[Optional[int]] = mapped_column(Integer)
    recommended_memory_limit_mib: Mapped[Optional[int]] = mapped_column(Integer)

    estimated_monthly_savings_usd: Mapped[float] = mapped_column(Float, default=0.0)
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=True)

    yaml_patch: Mapped[Optional[str]] = mapped_column(Text)
    kubectl_command: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    workload: Mapped["Workload"] = relationship("Workload", back_populates="recommendations")
