import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string;
  sub?: string;
  icon?: LucideIcon;
  trend?: "up" | "down" | "neutral";
  estimated?: boolean;
  highlight?: "green" | "amber" | "red" | "indigo" | "default";
}

const highlightBorder: Record<string, string> = {
  green:   "border-l-4 border-l-green-500",
  amber:   "border-l-4 border-l-amber-500",
  red:     "border-l-4 border-l-red-500",
  indigo:  "border-l-4 border-l-indigo-500",
  default: "border-l-4 border-l-slate-300",
};

export function MetricCard({
  title,
  value,
  sub,
  icon: Icon,
  estimated,
  highlight = "default",
}: Props) {
  return (
    <div
      className={cn(
        "rounded-lg bg-white px-5 py-4 shadow-sm border border-slate-200",
        highlightBorder[highlight],
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            {title}
            {estimated && (
              <span className="ml-1 text-[9px] font-normal normal-case text-slate-400">(est.)</span>
            )}
          </p>
          <p className="mt-1 text-2xl font-semibold tabular-nums text-slate-900 leading-none">
            {value}
          </p>
          {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
        </div>
        {Icon && (
          <div className="shrink-0 rounded-md bg-slate-100 p-2">
            <Icon className="h-4 w-4 text-slate-500" />
          </div>
        )}
      </div>
    </div>
  );
}
