"use client";

import { ArrowUpDown } from "lucide-react";
import { useState } from "react";
import type { WorkloadListItem } from "@/lib/api";
import { fmt$$, fmtCpu, fmtMem } from "@/lib/utils";
import { ConfidenceBadge, FlagBadge, RiskBadge } from "@/components/RiskBadge";

interface Props {
  workloads: WorkloadListItem[];
  onSelect: (id: number) => void;
}

type SortKey = "name" | "namespace" | "cost" | "savings" | "recs";
type SortDir = "asc" | "desc";

export function WorkloadTable({ workloads, onSelect }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("savings");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir("desc"); }
  }

  const sorted = [...workloads].sort((a, b) => {
    let av: string | number, bv: string | number;
    if (sortKey === "name") { av = a.name; bv = b.name; }
    else if (sortKey === "namespace") { av = a.namespace; bv = b.namespace; }
    else if (sortKey === "cost") { av = a.estimated_monthly_cost_usd; bv = b.estimated_monthly_cost_usd; }
    else if (sortKey === "savings") { av = a.potential_savings_usd; bv = b.potential_savings_usd; }
    else { av = a.recommendation_count; bv = b.recommendation_count; }
    if (av < bv) return sortDir === "asc" ? -1 : 1;
    if (av > bv) return sortDir === "asc" ? 1 : -1;
    return 0;
  });

  function Th({ label, k }: { label: string; k: SortKey }) {
    return (
      <th
        className="px-3 py-2 text-left text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 cursor-pointer select-none hover:text-slate-700 dark:hover:text-slate-200 whitespace-nowrap"
        onClick={() => toggleSort(k)}
      >
        <span className="inline-flex items-center gap-1">
          {label}
          <ArrowUpDown className="h-3 w-3 opacity-50" />
        </span>
      </th>
    );
  }

  if (!sorted.length) {
    return (
      <div className="flex h-32 items-center justify-center text-sm text-slate-400 dark:text-slate-500">
        No workloads match the current filters.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto scrollbar-thin">
      <table className="w-full text-sm">
        <thead className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60">
          <tr>
            <Th label="Workload" k="name" />
            <Th label="Namespace" k="namespace" />
            <th className="px-3 py-2 text-left text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 whitespace-nowrap">Kind</th>
            <th className="px-3 py-2 text-left text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 whitespace-nowrap">Rep.</th>
            <th className="px-3 py-2 text-left text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 whitespace-nowrap">Flag</th>
            <th className="px-3 py-2 text-left text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 whitespace-nowrap">Risk</th>
            <th className="px-3 py-2 text-left text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 whitespace-nowrap">Confidence</th>
            <Th label="Est. Cost/mo" k="cost" />
            <Th label="Savings/mo" k="savings" />
            <Th label="Recs" k="recs" />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
          {sorted.map((wl) => (
            <tr
              key={wl.id}
              onClick={() => onSelect(wl.id)}
              className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
            >
              <td className="px-3 py-2 font-medium text-slate-800 dark:text-slate-200 whitespace-nowrap">
                <span className="hover:text-indigo-600 transition-colors">{wl.name}</span>
                {wl.is_high_risk && (
                  <span className="ml-1.5 text-[9px] font-semibold uppercase text-rose-600">⚠</span>
                )}
              </td>
              <td className="px-3 py-2 text-slate-500 dark:text-slate-400 whitespace-nowrap text-xs">{wl.namespace}</td>
              <td className="px-3 py-2 text-slate-500 dark:text-slate-400 whitespace-nowrap text-xs font-mono">{wl.kind}</td>
              <td className="px-3 py-2 text-slate-500 dark:text-slate-400 text-center text-xs">{wl.replicas}</td>
              <td className="px-3 py-2">
                {wl.top_flag ? <FlagBadge flag={wl.top_flag} /> : <span className="text-slate-300 dark:text-slate-600 text-xs">—</span>}
              </td>
              <td className="px-3 py-2">
                {wl.top_risk ? <RiskBadge level={wl.top_risk} /> : <span className="text-slate-300 dark:text-slate-600 text-xs">—</span>}
              </td>
              <td className="px-3 py-2">
                {wl.top_confidence ? <ConfidenceBadge level={wl.top_confidence} /> : <span className="text-slate-300 dark:text-slate-600 text-xs">—</span>}
              </td>
              <td className="px-3 py-2 text-slate-700 dark:text-slate-300 tabular-nums text-xs whitespace-nowrap">
                {fmt$$(wl.estimated_monthly_cost_usd, 2)}
                <span className="text-slate-400 text-[10px]"> est.</span>
              </td>
              <td className="px-3 py-2 tabular-nums text-xs whitespace-nowrap">
                {wl.potential_savings_usd > 0 ? (
                  <span className="text-green-600 font-medium">{fmt$$(wl.potential_savings_usd, 2)}</span>
                ) : (
                  <span className="text-slate-300 dark:text-slate-600">—</span>
                )}
              </td>
              <td className="px-3 py-2 text-center">
                {wl.recommendation_count > 0 ? (
                  <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 text-[11px] font-semibold">
                    {wl.recommendation_count}
                  </span>
                ) : (
                  <span className="text-slate-300 dark:text-slate-600 text-xs">0</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
