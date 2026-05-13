"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useIsDark } from "@/lib/useIsDark";

interface DataPoint {
  namespace: string;
  estimated_monthly_cost_usd: number;
  potential_savings_usd: number;
}

interface Props {
  data: DataPoint[];
}

const COST_COLOR = "#6366f1";
const SAVINGS_COLOR = "#22c55e";

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 shadow-md text-xs">
      <p className="font-semibold text-slate-700 dark:text-slate-200 mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.fill }}>
          {p.name}: ${p.value.toFixed(2)}/mo
        </p>
      ))}
    </div>
  );
}

export function SpendByNamespace({ data }: Props) {
  const isDark = useIsDark();
  const tickColor = isDark ? "#94a3b8" : "#64748b";
  const gridColor = isDark ? "#334155" : "#f1f5f9";
  const cursorColor = isDark ? "#1e293b" : "#f8fafc";

  if (!data.length) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-slate-400 dark:text-slate-500">
        No namespace data
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 4 }} barCategoryGap="30%">
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
        <XAxis
          dataKey="namespace"
          tick={{ fontSize: 11, fill: tickColor }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={(v) => `$${v}`}
          tick={{ fontSize: 11, fill: tickColor }}
          axisLine={false}
          tickLine={false}
          width={52}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: cursorColor }} />
        <Bar dataKey="estimated_monthly_cost_usd" name="Est. Cost" fill={COST_COLOR} radius={[3, 3, 0, 0]} />
        <Bar dataKey="potential_savings_usd" name="Potential Savings" fill={SAVINGS_COLOR} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
