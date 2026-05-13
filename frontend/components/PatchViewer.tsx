"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  yaml: string | null;
  kubectl: string | null;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }
  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 rounded px-2 py-1 text-[11px] font-medium text-slate-500 hover:bg-slate-100 transition-colors"
      title="Copy to clipboard"
    >
      {copied ? (
        <Check className="h-3.5 w-3.5 text-green-500" />
      ) : (
        <Copy className="h-3.5 w-3.5" />
      )}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

export function PatchViewer({ yaml, kubectl }: Props) {
  const [tab, setTab] = useState<"yaml" | "kubectl">("yaml");

  if (!yaml && !kubectl) return null;

  return (
    <div className="rounded-lg border border-slate-200 overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-3 py-1.5">
        <div className="flex gap-1">
          {yaml && (
            <button
              onClick={() => setTab("yaml")}
              className={cn(
                "rounded px-2.5 py-1 text-xs font-medium transition-colors",
                tab === "yaml"
                  ? "bg-white shadow-sm text-slate-800 border border-slate-200"
                  : "text-slate-500 hover:text-slate-700",
              )}
            >
              YAML patch
            </button>
          )}
          {kubectl && (
            <button
              onClick={() => setTab("kubectl")}
              className={cn(
                "rounded px-2.5 py-1 text-xs font-medium transition-colors",
                tab === "kubectl"
                  ? "bg-white shadow-sm text-slate-800 border border-slate-200"
                  : "text-slate-500 hover:text-slate-700",
              )}
            >
              kubectl
            </button>
          )}
        </div>
        <CopyButton text={tab === "yaml" ? yaml ?? "" : kubectl ?? ""} />
      </div>

      <div className="bg-slate-900 p-4 overflow-x-auto scrollbar-thin">
        <pre className="text-xs leading-relaxed text-slate-100 font-mono whitespace-pre">
          {tab === "yaml" ? yaml : kubectl}
        </pre>
      </div>

      <div className="bg-amber-50 border-t border-amber-200 px-3 py-2 text-[11px] text-amber-700">
        <strong>Advisory only</strong> — KubeWise never auto-applies changes. Review this patch carefully before applying manually.
      </div>
    </div>
  );
}
