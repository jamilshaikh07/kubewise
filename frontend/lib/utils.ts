import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function fmt$$(value: number, decimals = 0): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function fmtCpu(m: number | null | undefined): string {
  if (m == null) return "—";
  if (m >= 1000) return `${(m / 1000).toFixed(2)} cores`;
  return `${m}m`;
}

export function fmtMem(mib: number | null | undefined): string {
  if (mib == null) return "—";
  if (mib >= 1024) return `${(mib / 1024).toFixed(1)} GiB`;
  return `${mib} MiB`;
}

export function fmtDate(iso: string | null): string {
  if (!iso) return "Never";
  const utc = iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z";
  return new Date(utc).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  });
}

export const FLAG_LABELS: Record<string, string> = {
  over_provisioned_cpu: "Over-prov. CPU",
  over_provisioned_memory: "Over-prov. Memory",
  missing_requests: "Missing Requests",
  missing_limits: "Missing Limits",
  idle_workload: "Idle",
  high_risk: "High Risk",
};
