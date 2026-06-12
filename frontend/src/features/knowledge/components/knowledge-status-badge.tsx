import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";
import type { KnowledgeStatus } from "@/features/knowledge/types";

const STYLES: Record<KnowledgeStatus, string> = {
  pending: "bg-slate-100 text-slate-600",
  processing: "bg-blue-100 text-blue-700",
  ready: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

export function KnowledgeStatusBadge({
  status,
  error,
}: {
  status: KnowledgeStatus;
  error?: string;
}) {
  return (
    <span
      title={status === "failed" ? error : undefined}
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        STYLES[status],
      )}
    >
      {status === "processing" && <Loader2 className="h-3 w-3 animate-spin" />}
      {status}
    </span>
  );
}
