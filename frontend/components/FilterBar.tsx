"use client";

import { cn } from "@/lib/utils";

interface Props {
  namespaces: string[];
  selectedNamespace: string;
  selectedRisk: string;
  selectedConfidence: string;
  search: string;
  onNamespace: (v: string) => void;
  onRisk: (v: string) => void;
  onConfidence: (v: string) => void;
  onSearch: (v: string) => void;
}

const selectCls =
  "rounded border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400";

export function FilterBar({
  namespaces,
  selectedNamespace,
  selectedRisk,
  selectedConfidence,
  search,
  onNamespace,
  onRisk,
  onConfidence,
  onSearch,
}: Props) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <input
        type="search"
        placeholder="Search workloads…"
        value={search}
        onChange={(e) => onSearch(e.target.value)}
        className={cn(selectCls, "w-44")}
      />

      <select
        value={selectedNamespace}
        onChange={(e) => onNamespace(e.target.value)}
        className={selectCls}
      >
        <option value="">All namespaces</option>
        {namespaces.map((ns) => (
          <option key={ns} value={ns}>
            {ns}
          </option>
        ))}
      </select>

      <select
        value={selectedRisk}
        onChange={(e) => onRisk(e.target.value)}
        className={selectCls}
      >
        <option value="">All risk levels</option>
        <option value="high">High risk</option>
        <option value="medium">Medium risk</option>
        <option value="low">Low risk</option>
      </select>

      <select
        value={selectedConfidence}
        onChange={(e) => onConfidence(e.target.value)}
        className={selectCls}
      >
        <option value="">All confidence</option>
        <option value="high">High confidence</option>
        <option value="medium">Medium confidence</option>
        <option value="low">Low confidence</option>
      </select>
    </div>
  );
}
