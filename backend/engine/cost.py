import json
import os
from pathlib import Path

_PRICING_PATH = Path(__file__).parent.parent / "pricing.json"

_pricing: dict = {}


def _load() -> dict:
    global _pricing
    if not _pricing:
        with open(_PRICING_PATH) as f:
            _pricing = json.load(f)
    return _pricing


def get_node_hourly_rate(provider: str | None, instance_type: str | None) -> float:
    data = _load()
    default = float(os.getenv("DEFAULT_NODE_HOURLY_RATE", data["default_node_hourly_rate_usd"]))
    if not provider or not instance_type:
        return default
    providers = data.get("providers", {})
    p = providers.get(provider.lower(), {})
    entry = p.get(instance_type)
    if entry:
        return float(entry["hourly_usd"])
    return default


def hours_per_month() -> int:
    return _load().get("hours_per_month", 730)


def monthly_node_cost(provider: str | None, instance_type: str | None) -> float:
    return get_node_hourly_rate(provider, instance_type) * hours_per_month()


def cpu_fraction_cost(
    cpu_request_m: int,
    node_total_cpu_m: int,
    node_monthly_cost: float,
) -> float:
    if node_total_cpu_m <= 0:
        return 0.0
    return (cpu_request_m / node_total_cpu_m) * node_monthly_cost * 0.5


def memory_fraction_cost(
    memory_request_mib: int,
    node_total_memory_mib: int,
    node_monthly_cost: float,
) -> float:
    if node_total_memory_mib <= 0:
        return 0.0
    return (memory_request_mib / node_total_memory_mib) * node_monthly_cost * 0.5


def estimate_workload_monthly_cost(
    cpu_request_m: int | None,
    memory_request_mib: int | None,
    replicas: int,
    node_cpu_m: int = 2000,
    node_memory_mib: int = 8192,
    node_monthly_cost: float | None = None,
) -> float:
    if node_monthly_cost is None:
        node_monthly_cost = monthly_node_cost(None, None)
    cpu_m = (cpu_request_m or 0) * replicas
    mem_mib = (memory_request_mib or 0) * replicas
    cpu_cost = cpu_fraction_cost(cpu_m, node_cpu_m, node_monthly_cost)
    mem_cost = memory_fraction_cost(mem_mib, node_memory_mib, node_monthly_cost)
    return round(cpu_cost + mem_cost, 4)


def estimate_savings(
    current_cpu_m: int | None,
    recommended_cpu_m: int | None,
    current_mem_mib: int | None,
    recommended_mem_mib: int | None,
    replicas: int = 1,
    node_cpu_m: int = 2000,
    node_memory_mib: int = 8192,
    node_monthly_cost: float | None = None,
) -> float:
    current = estimate_workload_monthly_cost(
        current_cpu_m, current_mem_mib, replicas, node_cpu_m, node_memory_mib, node_monthly_cost
    )
    recommended = estimate_workload_monthly_cost(
        recommended_cpu_m, recommended_mem_mib, replicas, node_cpu_m, node_memory_mib, node_monthly_cost
    )
    return max(0.0, round(current - recommended, 4))
