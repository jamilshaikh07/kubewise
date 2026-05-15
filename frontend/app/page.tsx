"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  Layers,
  RefreshCw,
  TrendingDown,
  Zap,
} from "lucide-react";
import { api, type ClusterSummary, type NamespaceSummary, type Recommendation, type WorkloadListItem } from "@/lib/api";
import { fmt$$, fmtDate } from "@/lib/utils";
import { MetricCard } from "@/components/MetricCard";
import { FilterBar } from "@/components/FilterBar";
import { WorkloadTable } from "@/components/WorkloadTable";
import { SpendByNamespace } from "@/components/SpendByNamespace";
import { CpuMemChart } from "@/components/CpuMemChart";
import { RecommendationPanel } from "@/components/RecommendationPanel";
import { RiskBadge } from "@/components/RiskBadge";
import { ThemeToggle } from "@/components/ThemeToggle";

function Spinner() {
  return (
    <div className="flex h-64 items-center justify-center">
      <RefreshCw className="h-6 w-6 animate-spin text-slate-400 dark:text-slate-500" />
    </div>
  );
}

function ErrorBanner({ msg }: { msg: string }) {
  return (
    <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-4 py-3 text-sm text-red-700 dark:text-red-400">
      <strong>Error:</strong> {msg}
    </div>
  );
}

export default function Dashboard() {
  const [cluster, setCluster] = useState<ClusterSummary | null>(null);
  const [namespaces, setNamespaces] = useState<NamespaceSummary[]>([]);
  const [workloads, setWorkloads] = useState<WorkloadListItem[]>([]);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [nsFilter, setNsFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [confFilter, setConfFilter] = useState("");
  const [search, setSearch] = useState("");

  const [selectedRec, setSelectedRec] = useState<Recommendation | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [c, ns, wl, r] = await Promise.all([
        api.clusterSummary(),
        api.namespaces(),
        api.workloads({ page_size: 200 }),
        api.recommendations(),
      ]);
      setCluster(c);
      setNamespaces(ns);
      setWorkloads(wl.items);
      setRecs(r);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const filteredWorkloads = workloads.filter((w) => {
    if (nsFilter && w.namespace !== nsFilter) return false;
    if (riskFilter && w.top_risk !== riskFilter) return false;
    if (confFilter && w.top_confidence !== confFilter) return false;
    if (search && !w.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const filteredRecs = recs.filter((r) => {
    if (nsFilter && r.namespace !== nsFilter) return false;
    if (riskFilter && r.risk !== riskFilter) return false;
    if (confFilter && r.confidence !== confFilter) return false;
    return true;
  });

  const nsNames = [...new Set(workloads.map((w) => w.namespace))].sort();

  const riskCounts = {
    high:   recs.filter((r) => r.risk === "high").length,
    medium: recs.filter((r) => r.risk === "medium").length,
    low:    recs.filter((r) => r.risk === "low").length,
  };

  const cpuChartData = workloads
    .filter((w) => w.top_flag?.includes("cpu") || w.potential_savings_usd > 0)
    .slice(0, 8)
    .map((w) => {
      const wr = recs.find((r) => r.workload_id === w.id);
      return {
        name: w.name.length > 14 ? w.name.slice(0, 13) + "…" : w.name,
        request: wr?.current_cpu_request_m ?? 0,
        usage: wr?.cpu_usage_p95_m ?? wr?.cpu_usage_current_m ?? 0,
      };
    });

  const memChartData = workloads
    .filter((w) => w.top_flag?.includes("memory") || w.potential_savings_usd > 0)
    .slice(0, 8)
    .map((w) => {
      const wr = recs.find((r) => r.workload_id === w.id && r.current_memory_request_mib);
      return {
        name: w.name.length > 14 ? w.name.slice(0, 13) + "…" : w.name,
        request: wr?.current_memory_request_mib ?? 0,
        usage: wr?.memory_usage_p95_mib ?? wr?.memory_usage_current_mib ?? 0,
      };
    });

  function handleWorkloadSelect(id: number) {
    const topRec = recs.filter((r) => r.workload_id === id)
      .sort((a, b) => {
        const o: Record<string, number> = { high: 0, medium: 1, low: 2 };
        return (o[a.risk] ?? 9) - (o[b.risk] ?? 9);
      })[0];
    if (topRec) setSelectedRec(topRec);
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {selectedRec && (
        <RecommendationPanel rec={selectedRec} onClose={() => setSelectedRec(null)} />
      )}

      {/* Top bar */}
      <header className="border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <Zap className="h-5 w-5 text-indigo-600" />
            <span className="font-bold text-slate-800 dark:text-slate-100 text-base tracking-tight">KubeWise</span>
          </div>
          {cluster && (
            <span className="rounded bg-slate-100 dark:bg-slate-700 px-2 py-0.5 text-xs font-mono text-slate-600 dark:text-slate-300">
              {cluster.name}
            </span>
          )}
          {cluster?.kubernetes_version && (
            <span className="text-xs text-slate-400">k8s {cluster.kubernetes_version}</span>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs text-slate-400">
            Last synced: {fmtDate(cluster?.last_synced_at ?? null)}
          </span>
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-2.5 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <ThemeToggle />
          <span className="rounded bg-amber-50 border border-amber-200 px-2 py-0.5 text-[10px] font-semibold text-amber-700 uppercase tracking-wide">
            Advisory Only
          </span>
        </div>
      </header>

      <main className="px-6 py-5 space-y-6 max-w-screen-2xl mx-auto">
        {error && <ErrorBanner msg={error} />}
        {loading && !cluster ? (
          <Spinner />
        ) : (
          <>
            {/* Metric cards */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
              <MetricCard
                title="Est. Monthly Spend"
                value={fmt$$(cluster?.estimated_monthly_cost_usd ?? 0)}
                sub={`${cluster?.node_count ?? 0} nodes`}
                icon={DollarSign}
                highlight="indigo"
                estimated
              />
              <MetricCard
                title="Estimated Waste"
                value={fmt$$(cluster?.estimated_monthly_waste_usd ?? 0)}
                sub="over-provisioned resources"
                icon={AlertTriangle}
                highlight="amber"
                estimated
              />
              <MetricCard
                title="Potential Savings"
                value={fmt$$(cluster?.estimated_monthly_savings_usd ?? 0)}
                sub="per month"
                icon={TrendingDown}
                highlight="green"
                estimated
              />
              <MetricCard
                title="Workloads Analyzed"
                value={String(cluster?.workload_count ?? 0)}
                sub={`across ${namespaces.length} namespaces`}
                icon={Layers}
              />
              <MetricCard
                title="Recommendations"
                value={String(cluster?.recommendation_count ?? 0)}
                sub="active findings"
                icon={Activity}
                highlight={cluster && cluster.recommendation_count > 0 ? "amber" : "default"}
              />
            </div>

            {/* Risk breakdown */}
            {recs.length > 0 && (
              <div className="rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm px-5 py-3">
                <p className="text-[11px] uppercase tracking-wider font-medium text-slate-400 dark:text-slate-500 mb-2">Risk breakdown</p>
                <div className="flex items-center gap-4 flex-wrap">
                  <div className="flex items-center gap-2">
                    <RiskBadge level="high" label={`${riskCounts.high} High`} size="md" />
                    <RiskBadge level="medium" label={`${riskCounts.medium} Medium`} size="md" />
                    <RiskBadge level="low" label={`${riskCounts.low} Low`} size="md" />
                  </div>
                  <div className="flex-1 min-w-48 h-3 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-700 flex">
                    {riskCounts.high > 0 && (
                      <div
                        className="bg-red-400 h-full"
                        style={{ width: `${(riskCounts.high / recs.length) * 100}%` }}
                      />
                    )}
                    {riskCounts.medium > 0 && (
                      <div
                        className="bg-amber-400 h-full"
                        style={{ width: `${(riskCounts.medium / recs.length) * 100}%` }}
                      />
                    )}
                    {riskCounts.low > 0 && (
                      <div
                        className="bg-green-400 h-full"
                        style={{ width: `${(riskCounts.low / recs.length) * 100}%` }}
                      />
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Charts row */}
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <div className="rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm p-4">
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-1">Spend & Savings by Namespace</p>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 mb-3">Estimated monthly cost vs potential savings</p>
                <SpendByNamespace
                  data={namespaces.map((ns) => ({
                    namespace: ns.name,
                    estimated_monthly_cost_usd: ns.estimated_monthly_cost_usd,
                    potential_savings_usd: ns.estimated_monthly_savings_usd,
                  }))}
                />
              </div>
              <div className="rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm p-4">
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-1">CPU: Request vs Recommended</p>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 mb-3">Millicores — top over-provisioned workloads</p>
                <CpuMemChart data={cpuChartData} unit="CPU (m)" />
              </div>
              <div className="rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm p-4">
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-1">Memory: Request vs Recommended</p>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 mb-3">MiB — top over-provisioned workloads</p>
                <CpuMemChart
                  data={memChartData}
                  unit="Memory (MiB)"
                  requestColor="#818cf8"
                  usageColor="#f472b6"
                />
              </div>
            </div>

            {/* Filters + table */}
            <div className="rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-700 px-4 py-3">
                <div>
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">Workloads</p>
                  <p className="text-xs text-slate-400 dark:text-slate-500">
                    {filteredWorkloads.length} of {workloads.length} shown — click a row to view recommendations
                  </p>
                </div>
                <FilterBar
                  namespaces={nsNames}
                  selectedNamespace={nsFilter}
                  selectedRisk={riskFilter}
                  selectedConfidence={confFilter}
                  search={search}
                  onNamespace={setNsFilter}
                  onRisk={setRiskFilter}
                  onConfidence={setConfFilter}
                  onSearch={setSearch}
                />
              </div>
              <WorkloadTable workloads={filteredWorkloads} onSelect={handleWorkloadSelect} />
              {filteredWorkloads.length === 0 && !loading && (
                <div className="flex flex-col items-center justify-center gap-2 py-12 text-slate-400">
                  <CheckCircle2 className="h-8 w-8 text-slate-200 dark:text-slate-700" />
                  <p className="text-sm">No workloads match the current filters.</p>
                </div>
              )}
            </div>

            {/* Top savings opportunities */}
            {filteredRecs.length > 0 && (
              <div className="rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
                <div className="border-b border-slate-200 dark:border-slate-700 px-4 py-3">
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">Top Saving Opportunities</p>
                  <p className="text-xs text-slate-400 dark:text-slate-500">Highest estimated monthly savings — click to view patch</p>
                </div>
                <div className="divide-y divide-slate-100 dark:divide-slate-700">
                  {[...filteredRecs]
                    .sort((a, b) => b.estimated_monthly_savings_usd - a.estimated_monthly_savings_usd)
                    .slice(0, 8)
                    .map((r) => (
                      <div
                        key={r.id}
                        className="flex items-center justify-between gap-4 px-4 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer transition-colors"
                        onClick={() => setSelectedRec(r)}
                      >
                        <div className="min-w-0">
                          <span className="text-sm font-medium text-slate-700 dark:text-slate-200 truncate">{r.workload_name}</span>
                          <span className="ml-2 text-xs text-slate-400 dark:text-slate-500">{r.namespace} / {r.container_name}</span>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <RiskBadge level={r.risk} />
                          {r.estimated_monthly_savings_usd > 0 && (
                            <span className="text-sm font-semibold text-green-600 tabular-nums">
                              {fmt$$(r.estimated_monthly_savings_usd, 2)}/mo
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
