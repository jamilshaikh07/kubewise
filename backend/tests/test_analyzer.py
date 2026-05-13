"""
Unit tests for the KubeWise recommendation engine.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from engine.analyzer import (
    CPU_FLOOR_M,
    CPU_SCALE,
    FLAG_HIGH_RISK,
    FLAG_IDLE,
    FLAG_MISSING_LIMITS,
    FLAG_MISSING_REQUESTS,
    FLAG_OVER_CPU,
    FLAG_OVER_MEM,
    MEM_FLOOR_MIB,
    MEM_SCALE,
    ContainerMetrics,
    WorkloadContext,
    analyze_workload,
    _recommended_cpu,
    _recommended_mem,
    _confidence,
    _risk,
)


def make_ctx(
    name="test-wl",
    namespace="default",
    kind="Deployment",
    replicas=1,
    is_system=False,
    containers=None,
) -> WorkloadContext:
    return WorkloadContext(
        workload_id=1,
        workload_name=name,
        namespace=namespace,
        kind=kind,
        replicas=replicas,
        is_system_namespace=is_system,
        containers=containers or [],
    )


def make_container(
    name="app",
    cpu_req=500,
    cpu_lim=1000,
    mem_req=512,
    mem_lim=1024,
    cpu_p95=80,
    mem_p95=200,
    cpu_cur=70,
    mem_cur=180,
    has_metrics=True,
    has_historical=True,
) -> ContainerMetrics:
    return ContainerMetrics(
        name=name,
        cpu_request_m=cpu_req,
        cpu_limit_m=cpu_lim,
        memory_request_mib=mem_req,
        memory_limit_mib=mem_lim,
        cpu_usage_p95_m=cpu_p95,
        memory_usage_p95_mib=mem_p95,
        cpu_usage_current_m=cpu_cur,
        memory_usage_current_mib=mem_cur,
        has_metrics=has_metrics,
        has_historical_metrics=has_historical,
    )


# ── Formula unit tests ────────────────────────────────────────────────────────

def test_recommended_cpu_above_floor():
    assert _recommended_cpu(100) == max(int(100 * CPU_SCALE), CPU_FLOOR_M)


def test_recommended_cpu_floor_enforced():
    assert _recommended_cpu(0) == CPU_FLOOR_M


def test_recommended_mem_above_floor():
    assert _recommended_mem(100) == max(int(100 * MEM_SCALE), MEM_FLOOR_MIB)


def test_recommended_mem_floor_enforced():
    assert _recommended_mem(0) == MEM_FLOOR_MIB


# ── Confidence tests ──────────────────────────────────────────────────────────

def test_confidence_high_with_historical():
    c = make_container(has_historical=True, cpu_p95=50)
    assert _confidence(c) == "high"


def test_confidence_medium_current_only():
    c = make_container(has_historical=False, has_metrics=True, cpu_p95=None, cpu_cur=50)
    assert _confidence(c) == "medium"


def test_confidence_low_no_metrics():
    c = make_container(has_historical=False, has_metrics=False, cpu_p95=None, cpu_cur=None)
    assert _confidence(c) == "low"


# ── Risk tests ────────────────────────────────────────────────────────────────

def test_risk_high_system_namespace():
    ctx = make_ctx(namespace="kube-system", is_system=True)
    assert _risk(ctx) == "high"


def test_risk_high_statefulset_single_replica():
    ctx = make_ctx(kind="StatefulSet", replicas=1)
    assert _risk(ctx) == "high"


def test_risk_medium_statefulset_multi():
    ctx = make_ctx(kind="StatefulSet", replicas=3)
    assert _risk(ctx) == "medium"


def test_risk_medium_many_replicas():
    ctx = make_ctx(kind="Deployment", replicas=5)
    assert _risk(ctx) == "medium"


def test_risk_low_normal():
    ctx = make_ctx(kind="Deployment", replicas=2)
    assert _risk(ctx) == "low"


# ── Flag: over_provisioned_cpu ────────────────────────────────────────────────

def test_over_provisioned_cpu_detected():
    c = make_container(cpu_req=1000, cpu_p95=50, has_historical=True)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    flags = [r.flag_type for r in recs]
    assert FLAG_OVER_CPU in flags


def test_over_provisioned_cpu_recommendation_value():
    c = make_container(cpu_req=1000, cpu_p95=100, has_historical=True)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    over_recs = [r for r in recs if r.flag_type == FLAG_OVER_CPU]
    assert over_recs, "Expected over_provisioned_cpu flag"
    assert over_recs[0].recommended_cpu_request_m == _recommended_cpu(100)


def test_cpu_not_flagged_when_usage_close_to_request():
    c = make_container(cpu_req=200, cpu_p95=160)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    flags = [r.flag_type for r in recs]
    assert FLAG_OVER_CPU not in flags


# ── Flag: over_provisioned_memory ─────────────────────────────────────────────

def test_over_provisioned_memory_detected():
    c = make_container(mem_req=2048, mem_p95=100, has_historical=True)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    flags = [r.flag_type for r in recs]
    assert FLAG_OVER_MEM in flags


def test_over_provisioned_memory_recommendation_value():
    c = make_container(mem_req=2048, mem_p95=200, has_historical=True)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    over_recs = [r for r in recs if r.flag_type == FLAG_OVER_MEM]
    assert over_recs
    assert over_recs[0].recommended_memory_request_mib == _recommended_mem(200)


# ── Flag: missing_requests ────────────────────────────────────────────────────

def test_missing_requests_no_cpu():
    c = make_container(cpu_req=None, mem_req=512)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    flags = [r.flag_type for r in recs]
    assert FLAG_MISSING_REQUESTS in flags


def test_missing_requests_no_memory():
    c = make_container(cpu_req=500, mem_req=None)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    flags = [r.flag_type for r in recs]
    assert FLAG_MISSING_REQUESTS in flags


# ── Flag: missing_limits ──────────────────────────────────────────────────────

def test_missing_limits_no_cpu_limit():
    c = make_container(cpu_lim=None)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    flags = [r.flag_type for r in recs]
    assert FLAG_MISSING_LIMITS in flags


def test_missing_limits_no_mem_limit():
    c = make_container(mem_lim=None)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    flags = [r.flag_type for r in recs]
    assert FLAG_MISSING_LIMITS in flags


# ── Flag: idle ────────────────────────────────────────────────────────────────

def test_idle_workload_detected():
    c = make_container(cpu_req=500, mem_req=512, cpu_p95=2, mem_p95=30)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    flags = [r.flag_type for r in recs]
    assert FLAG_IDLE in flags


def test_non_idle_not_flagged():
    c = make_container(cpu_p95=100, mem_p95=200)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    flags = [r.flag_type for r in recs]
    assert FLAG_IDLE not in flags


# ── Flag: high_risk (system namespace) ───────────────────────────────────────

def test_high_risk_system_namespace_flagged():
    c = make_container()
    ctx = make_ctx(namespace="kube-system", is_system=True, containers=[c])
    recs = analyze_workload(ctx)
    flags = [r.flag_type for r in recs]
    assert FLAG_HIGH_RISK in flags


# ── Patch generation ──────────────────────────────────────────────────────────

def test_yaml_patch_present():
    c = make_container(cpu_req=1000, cpu_p95=50)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    over_recs = [r for r in recs if r.flag_type == FLAG_OVER_CPU]
    assert over_recs
    assert "advisory" in over_recs[0].yaml_patch.lower()
    assert "kubewise" in over_recs[0].yaml_patch.lower()


def test_kubectl_command_present():
    c = make_container(cpu_req=1000, cpu_p95=50)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    over_recs = [r for r in recs if r.flag_type == FLAG_OVER_CPU]
    assert over_recs
    assert "kubectl set resources" in over_recs[0].kubectl_command


# ── Savings estimation ────────────────────────────────────────────────────────

def test_savings_positive_for_over_provisioned():
    c = make_container(cpu_req=2000, mem_req=4096, cpu_p95=100, mem_p95=200)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    savings = sum(r.estimated_monthly_savings_usd for r in recs)
    assert savings > 0


def test_savings_zero_when_not_over_provisioned():
    c = make_container(cpu_req=200, cpu_p95=160, mem_req=256, mem_p95=220)
    ctx = make_ctx(containers=[c])
    recs = [r for r in analyze_workload(ctx) if r.flag_type in (FLAG_OVER_CPU, FLAG_OVER_MEM)]
    savings = sum(r.estimated_monthly_savings_usd for r in recs)
    assert savings == 0


# ── Explanation text ──────────────────────────────────────────────────────────

def test_explanation_is_non_empty():
    c = make_container(cpu_req=1000, cpu_p95=50)
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    for r in recs:
        assert len(r.explanation) > 20


def test_is_estimated_always_true():
    c = make_container()
    ctx = make_ctx(containers=[c])
    recs = analyze_workload(ctx)
    for r in recs:
        assert r.is_estimated is True
