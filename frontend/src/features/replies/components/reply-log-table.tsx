import { Fragment, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

import { cn } from "@/lib/utils";
import type { ReplyLog, ReplyStatus } from "@/features/replies/types";

const STATUS_STYLES: Record<ReplyStatus, string> = {
  received: "bg-slate-100 text-slate-600",
  processing: "bg-blue-100 text-blue-700",
  sent: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
  skipped: "bg-amber-100 text-amber-700",
};

export function ReplyLogTable({ replies }: { replies: ReplyLog[] }) {
  const [openId, setOpenId] = useState<string | null>(null);

  if (!replies.length) {
    return (
      <p className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        No replies yet. Incoming messages on connected accounts will show up here.
      </p>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs text-slate-500">
          <tr>
            <th className="w-8 px-3 py-2" />
            <th className="px-3 py-2">When</th>
            <th className="px-3 py-2">Account</th>
            <th className="px-3 py-2">From</th>
            <th className="px-3 py-2">Message</th>
            <th className="px-3 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {replies.map((reply) => {
            const open = openId === reply.id;
            return (
              <Fragment key={reply.id}>
                <tr
                  className="cursor-pointer border-t border-slate-100 hover:bg-slate-50"
                  onClick={() => setOpenId(open ? null : reply.id)}
                >
                  <td className="px-3 py-2 text-slate-400">
                    {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  </td>
                  <td className="whitespace-nowrap px-3 py-2 text-xs text-slate-500">
                    {new Date(reply.created_on).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 text-xs">
                    {reply.account_username}
                    <span className="ml-1 text-slate-400">({reply.platform})</span>
                  </td>
                  <td className="px-3 py-2 text-xs">{reply.sender_name || reply.sender_id}</td>
                  <td className="max-w-xs truncate px-3 py-2">{reply.inbound_text}</td>
                  <td className="px-3 py-2">
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-xs font-medium",
                        STATUS_STYLES[reply.status],
                      )}
                    >
                      {reply.status}
                    </span>
                  </td>
                </tr>
                {open && (
                  <tr className="border-t border-slate-100 bg-slate-50/60">
                    <td colSpan={6} className="px-6 py-3">
                      <div className="flex flex-col gap-2 text-xs">
                        <div>
                          <span className="font-semibold text-slate-600">Inbound:</span>{" "}
                          <span className="whitespace-pre-wrap">{reply.inbound_text}</span>
                        </div>
                        {reply.reply_text && (
                          <div>
                            <span className="font-semibold text-slate-600">Reply:</span>{" "}
                            <span className="whitespace-pre-wrap">{reply.reply_text}</span>
                          </div>
                        )}
                        {reply.retrieved_chunks.length > 0 && (
                          <div className="text-slate-500">
                            Chunks:{" "}
                            {reply.retrieved_chunks
                              .map((c) => `#${c.seq} (${c.score})`)
                              .join(", ")}
                          </div>
                        )}
                        {reply.error && <div className="text-red-600">Error: {reply.error}</div>}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
