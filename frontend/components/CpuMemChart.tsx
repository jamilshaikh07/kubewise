"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useIsDark } from "@/lib/useIsDark";

interface DataPoint {
  name: string;
  request: number;
  usage: number;
}

interface Props {
  data: DataPoint[];
  unit: "CPU (m)" | "Memory (MiB)";
  requestColor?: string;
  usageColor?: string;
}

function CustomTooltip({ active, payload, label, unit }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 shadow-md text-xs">
      <p className="font-semibold text-slate-700 dark:text-slate-200 mb-1 truncate max-w-[160px]">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.fill }}>
          {p.name}: {p.value} {unit}
        </p>
      ))}
    </div>
  );
}

export function CpuMemChart({
  data,
  unit,
  requestColor = "#818cf8",
  usageColor = "#34d399",
}: Props) {
  const isDark = useIsDark();
  const tickColor = isDark ? "#94a3b8" : "#64748b";
  const gridColor = isDark ? "#334155" : "#f1f5f9";
  const cursorColor = isDark ? "#1e293b" : "#f8fafc";

  if (!data.length) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-slate-400 dark:text-slate-500">
        No data
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart
        data={data}
        margin={{ top: 4, right: 4, left: 0, bottom: 24 }}
        barCategoryGap="30%"
      >
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 10, fill: tickColor }}
          axisLine={false}
          tickLine={false}
          angle={-25}
          textAnchor="end"
          interval={0}
        />
        <YAxis
          tick={{ fontSize: 11, fill: tickColor }}
          axisLine={false}
          tickLine={false}
          width={44}
        />
        <Tooltip content={<CustomTooltip unit={unit} />} cursor={{ fill: cursorColor }} />
        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 4 }} />
        <Bar dataKey="request" name="Request" fill={requestColor} radius={[3, 3, 0, 0]} />
        <Bar dataKey="usage" name="P95 Usage" fill={usageColor} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
