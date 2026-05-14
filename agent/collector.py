#!/usr/bin/env python3
"""
KubeWise Collector Agent
Read-only Kubernetes cluster data collector.

Collects cluster state and POSTs it to the KubeWise backend.
Never mutates any Kubernetes resource.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional

import httpx
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [kubewise-agent] %(levelname)s %(message)s",
)
log = logging.getLogger("kubewise")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
CLUSTER_NAME = os.getenv("CLUSTER_NAME", "my-cluster")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
PROVIDER = os.getenv("CLOUD_PROVIDER", None)
REGION = os.getenv("CLOUD_REGION", None)
IN_CLUSTER = os.getenv("IN_CLUSTER", "true").lower() == "true"
METRICS_URL = os.getenv("METRICS_URL", "")  # e.g. http://vmsingle-...:8428

SYSTEM_NAMESPACES = {"kube-system", "kube-public", "kube-node-lease"}

_excluded_env = os.getenv("EXCLUDED_NAMESPACES", "")
EXCLUDED_NAMESPACES: set[str] = (
    SYSTEM_NAMESPACES | {ns.strip() for ns in _excluded_env.split(",") if ns.strip()}
    if _excluded_env
    else SYSTEM_NAMESPACES
)


def load_kube_config() -> None:
    if IN_CLUSTER:
        config.load_incluster_config()
        log.info("Loaded in-cluster kubeconfig")
    else:
        config.load_kube_config()
        log.info("Loaded local kubeconfig")


def parse_cpu(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    if value.endswith("m"):
        return int(value[:-1])
    try:
        return int(float(value) * 1000)
    except (ValueError, TypeError):
        return None


def parse_memory(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    units = {"Ki": 1 / 1024, "Mi": 1, "Gi": 1024, "Ti": 1024 * 1024, "K": 1 / 1024, "M": 1, "G": 1024}
    for suffix, factor in units.items():
        if value.endswith(suffix):
            try:
                return int(float(value[: -len(suffix)]) * factor)
            except ValueError:
                return None
    try:
        return int(value) // (1024 * 1024)
    except ValueError:
        return None


def collect_nodes(core_v1: client.CoreV1Api) -> list[dict]:
    nodes = []
    try:
        for node in core_v1.list_node().items:
            name = node.metadata.name
            labels = node.metadata.labels or {}
            instance_type = (
                labels.get("node.kubernetes.io/instance-type")
                or labels.get("beta.kubernetes.io/instance-type")
            )
            cap = node.status.capacity or {}
            alloc = node.status.allocatable or {}
            nodes.append({
                "name": name,
                "instance_type": instance_type,
                "cpu_capacity_m": parse_cpu(cap.get("cpu")) or 0,
                "memory_capacity_mib": parse_memory(cap.get("memory")) or 0,
                "cpu_allocatable_m": parse_cpu(alloc.get("cpu")) or 0,
                "memory_allocatable_mib": parse_memory(alloc.get("memory")) or 0,
            })
    except ApiException as e:
        log.warning("Failed to list nodes: %s", e)
    return nodes


def try_prometheus_p95(metrics_url: str) -> dict[str, dict]:
    """Query VictoriaMetrics/Prometheus for P95 CPU and memory over 24 h.
    Returns {namespace/pod/container: {cpu_p95_m, mem_p95_mib}}.
    """
    if not metrics_url:
        return {}
    results: dict[str, dict] = {}
    base = metrics_url.rstrip("/")
    queries = {
        "cpu_p95_m": (
            'quantile_over_time(0.95, rate('
            'container_cpu_usage_seconds_total{container!="",container!="POD"}'
            '[5m])[24h:5m]) * 1000'
        ),
        "mem_p95_mib": (
            'quantile_over_time(0.95, '
            'container_memory_working_set_bytes{container!="",container!="POD"}'
            '[24h:5m]) / 1048576'
        ),
    }
    try:
        with httpx.Client(timeout=30) as client_http:
            for field, query in queries.items():
                resp = client_http.get(f"{base}/api/v1/query", params={"query": query})
                resp.raise_for_status()
                for item in resp.json().get("data", {}).get("result", []):
                    m = item.get("metric", {})
                    ns, pod, container = m.get("namespace", ""), m.get("pod", ""), m.get("container", "")
                    if not (ns and pod and container):
                        continue
                    key = f"{ns}/{pod}/{container}"
                    val = item.get("value", [None, None])[1]
                    if val is not None:
                        results.setdefault(key, {})[field] = int(float(val))
    except Exception as e:
        log.warning("P95 query failed (%s): %s", base, e)
    log.info("P95 metrics fetched for %d containers", len(results))
    return results


def try_metrics_server(custom_api: client.CustomObjectsApi) -> dict[str, dict]:
    metrics: dict[str, dict] = {}
    try:
        result = custom_api.list_cluster_custom_object(
            group="metrics.k8s.io", version="v1beta1", plural="pods"
        )
        for pod in result.get("items", []):
            pod_name = pod["metadata"]["name"]
            ns = pod["metadata"]["namespace"]
            for c in pod.get("containers", []):
                key = f"{ns}/{pod_name}/{c['name']}"
                metrics[key] = {
                    "cpu_m": parse_cpu(c["usage"].get("cpu")),
                    "mem_mib": parse_memory(c["usage"].get("memory")),
                }
    except ApiException:
        log.info("metrics-server not available — skipping live metrics")
    return metrics


def collect_namespace(
    ns_name: str,
    apps_v1: client.AppsV1Api,
    core_v1: client.CoreV1Api,
    live_metrics: dict[str, dict],
    p95_metrics: dict[str, dict],
) -> dict:
    workloads = []

    for deploy in apps_v1.list_namespaced_deployment(ns_name).items:
        workloads.append(
            _extract_workload(deploy, "Deployment", ns_name, core_v1, live_metrics, p95_metrics)
        )

    for ss in apps_v1.list_namespaced_stateful_set(ns_name).items:
        workloads.append(
            _extract_workload(ss, "StatefulSet", ns_name, core_v1, live_metrics, p95_metrics)
        )

    return {
        "name": ns_name,
        "is_system": ns_name in SYSTEM_NAMESPACES,
        "workloads": workloads,
    }


def _extract_workload(
    resource,
    kind: str,
    ns_name: str,
    core_v1: client.CoreV1Api,
    live_metrics: dict[str, dict],
    p95_metrics: dict[str, dict],
) -> dict:
    spec = resource.spec
    replicas = getattr(spec, "replicas", 1) or 1
    template_spec = spec.template.spec
    pod_selector = (spec.selector.match_labels or {}) if spec.selector else {}

    containers = []
    for c in template_spec.containers:
        cpu_req = cpu_lim = mem_req = mem_lim = None
        if c.resources:
            req = c.resources.requests or {}
            lim = c.resources.limits or {}
            cpu_req = parse_cpu(req.get("cpu"))
            mem_req = parse_memory(req.get("memory"))
            cpu_lim = parse_cpu(lim.get("cpu"))
            mem_lim = parse_memory(lim.get("memory"))

        cpu_cur = mem_cur = None
        has_metrics = False
        cpu_p95 = mem_p95 = None
        has_historical = False
        for pod in _get_pods(core_v1, ns_name, pod_selector):
            key = f"{ns_name}/{pod}/{c.name}"
            m = live_metrics.get(key)
            if m:
                cpu_cur = m.get("cpu_m")
                mem_cur = m.get("mem_mib")
                has_metrics = True
            p = p95_metrics.get(key)
            if p:
                cpu_p95 = p.get("cpu_p95_m")
                mem_p95 = p.get("mem_p95_mib")
                has_historical = cpu_p95 is not None or mem_p95 is not None
            if has_metrics or has_historical:
                break

        containers.append({
            "name": c.name,
            "cpu_request_m": cpu_req,
            "cpu_limit_m": cpu_lim,
            "memory_request_mib": mem_req,
            "memory_limit_mib": mem_lim,
            "cpu_usage_current_m": cpu_cur,
            "memory_usage_current_mib": mem_cur,
            "cpu_usage_p95_m": cpu_p95,
            "memory_usage_p95_mib": mem_p95,
            "has_metrics": has_metrics,
            "has_historical_metrics": has_historical,
        })

    return {
        "name": resource.metadata.name,
        "kind": kind,
        "replicas": replicas,
        "labels": json.dumps(resource.metadata.labels or {}),
        "annotations": json.dumps(resource.metadata.annotations or {}),
        "containers": containers,
    }


def _get_pods(core_v1: client.CoreV1Api, namespace: str, selector: dict) -> list[str]:
    try:
        label_sel = ",".join(f"{k}={v}" for k, v in selector.items())
        pods = core_v1.list_namespaced_pod(namespace, label_selector=label_sel).items
        return [p.metadata.name for p in pods if p.status.phase == "Running"]
    except ApiException:
        return []


def collect() -> dict:
    core_v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    custom_api = client.CustomObjectsApi()
    version_api = client.VersionApi()

    k8s_version = None
    try:
        v = version_api.get_code()
        k8s_version = f"{v.major}.{v.minor}"
    except ApiException:
        pass

    nodes = collect_nodes(core_v1)
    live_metrics = try_metrics_server(custom_api)
    p95_metrics = try_prometheus_p95(METRICS_URL)

    ns_list = [ns.metadata.name for ns in core_v1.list_namespace().items]
    namespaces = []
    for ns_name in ns_list:
        if ns_name in EXCLUDED_NAMESPACES:
            log.debug("Skipping excluded namespace %s", ns_name)
            continue
        try:
            ns_data = collect_namespace(ns_name, apps_v1, core_v1, live_metrics, p95_metrics)
            namespaces.append(ns_data)
        except ApiException as e:
            log.warning("Skipping namespace %s: %s", ns_name, e)

    return {
        "cluster_name": CLUSTER_NAME,
        "provider": PROVIDER,
        "region": REGION,
        "kubernetes_version": k8s_version,
        "nodes": nodes,
        "namespaces": namespaces,
    }


def post_to_backend(payload: dict) -> None:
    url = f"{BACKEND_URL}/api/v1/ingest"
    with httpx.Client(timeout=60) as http:
        resp = http.post(url, json=payload)
        resp.raise_for_status()
        result = resp.json()
        log.info(
            "Ingested: %d namespaces, %d workloads, %d recommendations generated",
            result["namespaces_processed"],
            result["workloads_processed"],
            result["recommendations_generated"],
        )


def main() -> None:
    load_kube_config()
    log.info("KubeWise collector starting. cluster=%s backend=%s interval=%ds",
             CLUSTER_NAME, BACKEND_URL, POLL_INTERVAL)
    while True:
        try:
            log.info("Collecting cluster state...")
            payload = collect()
            log.info("Collected %d namespaces, %d nodes",
                     len(payload["namespaces"]), len(payload["nodes"]))
            post_to_backend(payload)
        except Exception as e:
            log.error("Collection cycle failed: %s", e)
        log.info("Sleeping %ds until next collection", POLL_INTERVAL)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
