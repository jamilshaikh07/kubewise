"use client";

import { AlertTriangle, X } from "lucide-react";
import type { Recommendation } from "@/lib/api";
import { fmt$$, fmtCpu, fmtMem } from "@/lib/utils";
import { ConfidenceBadge, FlagBadge, RiskBadge } from "@/components/RiskBadge";
import { PatchViewer } from "@/components/PatchViewer";

interface Props {
  rec: Recommendation | null;
  onClose: () => void;
}

function Row({ label, current, recommended }: { label: string; current: string; recommended: string }) {
  return (
    <tr className="border-b border-slate-100 dark:border-slate-700">
      <td className="py-1.5 pr-4 text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">{label}</td>
      <td className="py-1.5 pr-4 text-xs font-mono text-slate-700 dark:text-slate-300">{current}</td>
      <td className="py-1.5 text-xs font-mono text-indigo-600 font-medium">{recommended}</td>
    </tr>
  );
}

export function RecommendationPanel({ rec, onClose }: Props) {
  if (!rec) return null;

  const isHighRisk = rec.risk === "high";
  const isSystem = ["kube-system", "kube-public", "kube-node-lease"].includes(rec.namespace);

  return (
    <div className="fixed inset-0 z-40 flex justify-end" onClick={onClose}>
      <div
        className="relative h-full w-full max-w-xl overflow-y-auto bg-white dark:bg-slate-900 shadow-2xl border-l border-slate-200 dark:border-slate-700 scrollbar-thin"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-5 py-3">
          <div>
            <p className="text-xs text-slate-400 dark:text-slate-500 font-medium uppercase tracking-wider">Recommendation</p>
            <h2 className="text-base font-semibold text-slate-800 dark:text-slate-100 leading-tight mt-0.5 truncate">
              {rec.workload_name}
              <span className="text-slate-400 font-normal"> / {rec.container_name}</span>
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-slate-400 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-600 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {(isHighRisk || isSystem) && (
            <div className="flex gap-2 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 px-3 py-2.5 text-xs text-amber-800 dark:text-amber-300">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-amber-500" />
              <span>
                {isSystem
                  ? `This workload is in the '${rec.namespace}' namespace (system/critical). Review very carefully before applying any changes manually.`
                  : "This workload is flagged high-risk. Do not apply changes without thorough review."}
              </span>
            </div>
          )}

          <div className="flex flex-wrap gap-2 items-center">
            <FlagBadge flag={rec.flag_type} />
            <RiskBadge level={rec.risk} label={`${rec.risk} risk`} size="md" />
            <ConfidenceBadge level={rec.confidence} size="md" />
            <span className="text-xs text-slate-400 dark:text-slate-500 ml-auto">
              {rec.namespace} · {rec.kind}
            </span>
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-3.5">
            <p className="text-[11px] uppercase tracking-wider font-medium text-slate-400 dark:text-slate-500 mb-1">Explanation</p>
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{rec.explanation}</p>
          </div>

          <div>
            <p className="text-[11px] uppercase tracking-wider font-medium text-slate-400 dark:text-slate-500 mb-2">Resource changes</p>
            <table className="w-full">
              <thead>
                <tr>
                  <th className="pb-1 text-left text-[11px] text-slate-400 dark:text-slate-500 font-medium w-32">Field</th>
                  <th className="pb-1 text-left text-[11px] text-slate-400 dark:text-slate-500 font-medium">Current</th>
                  <th className="pb-1 text-left text-[11px] text-indigo-500 font-medium">Recommended</th>
                </tr>
              </thead>
              <tbody>
                <Row
                  label="CPU request"
                  current={fmtCpu(rec.current_cpu_request_m)}
                  recommended={fmtCpu(rec.recommended_cpu_request_m)}
                />
                <Row
                  label="CPU limit"
                  current={fmtCpu(rec.current_cpu_limit_m)}
                  recommended={fmtCpu(rec.recommended_cpu_limit_m)}
                />
                <Row
                  label="Mem request"
                  current={fmtMem(rec.current_memory_request_mib)}
                  recommended={fmtMem(rec.recommended_memory_request_mib)}
                />
                <Row
                  label="Mem limit"
                  current={fmtMem(rec.current_memory_limit_mib)}
                  recommended={fmtMem(rec.recommended_memory_limit_mib)}
                />
              </tbody>
            </table>
          </div>

          <div className="rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 px-4 py-3 flex items-center justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-wider font-medium text-green-600 dark:text-green-400">Estimated savings</p>
              <p className="text-xl font-bold text-green-700 dark:text-green-400 tabular-nums">
                {fmt$$(rec.estimated_monthly_savings_usd, 2)}
                <span className="text-sm font-normal text-green-500">/mo</span>
              </p>
            </div>
            {rec.is_estimated && (
              <span className="text-[10px] text-green-500 border border-green-200 dark:border-green-800 rounded px-1.5 py-0.5">estimated</span>
            )}
          </div>

          <div>
            <p className="text-[11px] uppercase tracking-wider font-medium text-slate-400 dark:text-slate-500 mb-2">Suggested patch</p>
            <PatchViewer yaml={rec.yaml_patch} kubectl={rec.kubectl_command} />
          </div>
        </div>
      </div>
    </div>
  );
}
