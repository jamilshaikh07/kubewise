const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${path} → ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface ClusterSummary {
  id: number;
  name: string;
  provider: string | null;
  region: string | null;
  node_count: number;
  total_cpu_cores: number;
  total_memory_gib: number;
  kubernetes_version: string | null;
  last_synced_at: string | null;
  workload_count: number;
  recommendation_count: number;
  estimated_monthly_cost_usd: number;
  estimated_monthly_waste_usd: number;
  estimated_monthly_savings_usd: number;
  is_estimated: boolean;
}

export interface NamespaceSummary {
  id: number;
  name: string;
  is_system: boolean;
  workload_count: number;
  estimated_monthly_cost_usd: number;
  estimated_monthly_savings_usd: number;
  recommendation_count: number;
  is_estimated: boolean;
}

export interface Container {
  id: number;
  name: string;
  cpu_request_m: number | null;
  cpu_limit_m: number | null;
  memory_request_mib: number | null;
  memory_limit_mib: number | null;
  cpu_usage_p95_m: number | null;
  memory_usage_p95_mib: number | null;
  cpu_usage_current_m: number | null;
  memory_usage_current_mib: number | null;
  has_metrics: boolean;
  has_historical_metrics: boolean;
}

export interface WorkloadListItem {
  id: number;
  name: string;
  namespace: string;
  kind: string;
  replicas: number;
  is_high_risk: boolean;
  estimated_monthly_cost_usd: number;
  recommendation_count: number;
  top_flag: string | null;
  top_risk: string | null;
  top_confidence: string | null;
  potential_savings_usd: number;
  is_estimated: boolean;
}

export interface PaginatedWorkloads {
  items: WorkloadListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface Recommendation {
  id: number;
  workload_id: number;
  workload_name: string;
  namespace: string;
  kind: string;
  container_name: string;
  flag_type: string;
  confidence: "high" | "medium" | "low";
  risk: "high" | "medium" | "low";
  explanation: string;
  current_cpu_request_m: number | null;
  current_cpu_limit_m: number | null;
  current_memory_request_mib: number | null;
  current_memory_limit_mib: number | null;
  recommended_cpu_request_m: number | null;
  recommended_cpu_limit_m: number | null;
  recommended_memory_request_mib: number | null;
  recommended_memory_limit_mib: number | null;
  estimated_monthly_savings_usd: number;
  is_estimated: boolean;
  yaml_patch: string | null;
  kubectl_command: string | null;
  created_at: string;
}

export interface WorkloadDetail {
  id: number;
  name: string;
  namespace: string;
  kind: string;
  replicas: number;
  labels: string | null;
  annotations: string | null;
  is_high_risk: boolean;
  estimated_monthly_cost_usd: number;
  containers: Container[];
  recommendations: Recommendation[];
  is_estimated: boolean;
}

export interface SavingsEstimate {
  total_estimated_monthly_cost_usd: number;
  total_estimated_monthly_waste_usd: number;
  total_potential_savings_usd: number;
  savings_by_namespace: {
    namespace: string;
    estimated_monthly_cost_usd: number;
    potential_savings_usd: number;
  }[];
  is_estimated: boolean;
}

// ── API calls ────────────────────────────────────────────────────────────────

export const api = {
  clusterSummary: () => get<ClusterSummary>("/api/v1/cluster/summary"),

  namespaces: () => get<NamespaceSummary[]>("/api/v1/namespaces"),

  workloads: (params?: {
    namespace?: string;
    risk?: string;
    confidence?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.namespace) q.set("namespace", params.namespace);
    if (params?.risk) q.set("risk", params.risk);
    if (params?.confidence) q.set("confidence", params.confidence);
    if (params?.search) q.set("search", params.search);
    if (params?.page) q.set("page", String(params.page));
    if (params?.page_size) q.set("page_size", String(params.page_size));
    const qs = q.toString();
    return get<PaginatedWorkloads>(`/api/v1/workloads${qs ? `?${qs}` : ""}`);
  },

  workloadDetail: (id: number) => get<WorkloadDetail>(`/api/v1/workloads/${id}`),

  recommendations: (params?: {
    namespace?: string;
    risk?: string;
    confidence?: string;
    flag_type?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.namespace) q.set("namespace", params.namespace);
    if (params?.risk) q.set("risk", params.risk);
    if (params?.confidence) q.set("confidence", params.confidence);
    if (params?.flag_type) q.set("flag_type", params.flag_type);
    const qs = q.toString();
    return get<Recommendation[]>(`/api/v1/recommendations${qs ? `?${qs}` : ""}`);
  },

  savings: () => get<SavingsEstimate>("/api/v1/recommendations/savings"),
};
