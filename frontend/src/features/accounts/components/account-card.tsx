import { Camera, MessageCircle, AtSign, Trash2 } from "lucide-react";
import { toast } from "react-toastify";

import { useDisconnectAccount, useUpdateAccount } from "@/features/accounts/hooks";
import { useKnowledgeList } from "@/features/knowledge/hooks";
import { cn } from "@/lib/utils";
import type { Platform, SocialAccount } from "@/features/accounts/types";

const PLATFORM_META: Record<Platform, { label: string; icon: typeof Camera }> = {
  instagram: { label: "Instagram", icon: Camera },
  whatsapp: { label: "WhatsApp", icon: MessageCircle },
  threads: { label: "Threads", icon: AtSign },
};

export function AccountCard({ account }: { account: SocialAccount }) {
  const { data: knowledgeList } = useKnowledgeList();
  const update = useUpdateAccount();
  const disconnect = useDisconnectAccount();
  const meta = PLATFORM_META[account.platform];
  const Icon = meta.icon;

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-5 w-5 text-slate-600" />
          <div>
            <div className="text-sm font-semibold text-slate-800">
              {account.username || account.platform_user_id}
            </div>
            <div className="text-xs text-slate-500">{meta.label}</div>
          </div>
        </div>
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-xs font-medium",
            account.status === "connected" && "bg-emerald-100 text-emerald-700",
            account.status === "expired" && "bg-amber-100 text-amber-700",
            account.status === "disconnected" && "bg-slate-100 text-slate-500",
          )}
        >
          {account.status}
        </span>
      </div>

      {account.status === "expired" && (
        <p className="text-xs text-amber-700">
          Token expired — reconnect this account to resume auto-replies.
        </p>
      )}

      <label className="flex flex-col gap-1 text-xs">
        <span className="font-medium text-slate-600">Knowledge</span>
        <select
          value={account.knowledge_id ?? ""}
          onChange={(e) =>
            update.mutate(
              { id: account.id, update: { knowledge_id: e.target.value || null } },
              { onSuccess: () => toast.success("Knowledge updated") },
            )
          }
          className="rounded border border-slate-300 px-2 py-1.5 text-sm focus:border-blue-400 focus:outline-none"
        >
          <option value="">— none (no auto-reply) —</option>
          {(knowledgeList ?? []).map((k) => (
            <option key={k.id} value={k.id}>
              {k.title}
            </option>
          ))}
        </select>
      </label>

      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-xs text-slate-600">
          <input
            type="checkbox"
            checked={account.auto_reply_enabled}
            onChange={(e) =>
              update.mutate({ id: account.id, update: { auto_reply_enabled: e.target.checked } })
            }
            className="h-4 w-4 accent-blue-600"
          />
          Auto-reply enabled
        </label>
        <button
          type="button"
          onClick={() => {
            if (confirm(`Disconnect ${account.username || meta.label}?`)) {
              disconnect.mutate(account.id, {
                onSuccess: () => toast.info("Account disconnected"),
              });
            }
          }}
          className="flex items-center gap-1 rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50"
        >
          <Trash2 className="h-3.5 w-3.5" />
          Disconnect
        </button>
      </div>
    </div>
  );
}
