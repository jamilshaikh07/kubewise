import { cn } from "@/lib/utils";

interface Props {
  level: "high" | "medium" | "low" | string;
  label?: string;
  size?: "sm" | "md";
}

const styles: Record<string, string> = {
  high:   "bg-red-50 text-red-700 ring-1 ring-red-200",
  medium: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  low:    "bg-green-50 text-green-700 ring-1 ring-green-200",
};

export function RiskBadge({ level, label, size = "sm" }: Props) {
  const base = styles[level] ?? "bg-slate-100 text-slate-600 ring-1 ring-slate-200";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded font-medium uppercase tracking-wide",
        size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-1 text-xs",
        base,
      )}
    >
      {label ?? level}
    </span>
  );
}

export function ConfidenceBadge({ level, size = "sm" }: { level: string; size?: "sm" | "md" }) {
  const styles: Record<string, string> = {
    high:   "bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200",
    medium: "bg-sky-50 text-sky-700 ring-1 ring-sky-200",
    low:    "bg-slate-100 text-slate-600 ring-1 ring-slate-200",
  };
  const base = styles[level] ?? styles.low;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded font-medium uppercase tracking-wide",
        size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-1 text-xs",
        base,
      )}
    >
      {level}
    </span>
  );
}

export function FlagBadge({ flag }: { flag: string }) {
  const map: Record<string, string> = {
    over_provisioned_cpu:    "bg-orange-50 text-orange-700 ring-1 ring-orange-200",
    over_provisioned_memory: "bg-orange-50 text-orange-700 ring-1 ring-orange-200",
    missing_requests:        "bg-red-50 text-red-700 ring-1 ring-red-200",
    missing_limits:          "bg-red-50 text-red-700 ring-1 ring-red-200",
    idle_workload:           "bg-slate-100 text-slate-500 ring-1 ring-slate-200",
    high_risk:               "bg-rose-50 text-rose-700 ring-1 ring-rose-200",
  };
  const labels: Record<string, string> = {
    over_provisioned_cpu:    "Over-prov CPU",
    over_provisioned_memory: "Over-prov Mem",
    missing_requests:        "No Requests",
    missing_limits:          "No Limits",
    idle_workload:           "Idle",
    high_risk:               "High Risk",
  };
  const base = map[flag] ?? "bg-slate-100 text-slate-600 ring-1 ring-slate-200";
  return (
    <span className={cn("inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide", base)}>
      {labels[flag] ?? flag}
    </span>
  );
}
