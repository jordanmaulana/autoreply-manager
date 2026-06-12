import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";

import { useAccounts } from "@/features/accounts/hooks";
import { ReplyLogTable } from "@/features/replies/components/reply-log-table";
import { useReplies } from "@/features/replies/hooks";

const PAGE_SIZE = 50;

export const Route = createFileRoute("/replies")({
  component: RepliesPage,
});

function RepliesPage() {
  const [account, setAccount] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const { data: accounts } = useAccounts();
  const { data, isLoading } = useReplies({ account, status, limit: PAGE_SIZE, offset });

  const select =
    "rounded border border-slate-300 bg-white px-2 py-1.5 text-sm focus:border-blue-400 focus:outline-none";

  return (
    <div>
      <h1 className="text-2xl font-semibold">Replies</h1>
      <p className="mt-1 text-sm text-slate-600">Every inbound message and what happened to it.</p>

      <div className="mt-6 flex gap-2">
        <select
          value={account}
          onChange={(e) => {
            setAccount(e.target.value);
            setOffset(0);
          }}
          className={select}
        >
          <option value="">All accounts</option>
          {(accounts ?? []).map((a) => (
            <option key={a.id} value={a.id}>
              {a.platform}: {a.username || a.platform_user_id}
            </option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setOffset(0);
          }}
          className={select}
        >
          <option value="">All statuses</option>
          {["sent", "failed", "skipped", "processing", "received"].map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-4">
        {isLoading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : (
          <ReplyLogTable replies={data?.results ?? []} />
        )}
      </div>

      {data && data.count > PAGE_SIZE && (
        <div className="mt-4 flex items-center gap-3 text-sm">
          <button
            type="button"
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            className="rounded border border-slate-300 bg-white px-3 py-1.5 disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-slate-500">
            {offset + 1}–{Math.min(offset + PAGE_SIZE, data.count)} of {data.count}
          </span>
          <button
            type="button"
            disabled={offset + PAGE_SIZE >= data.count}
            onClick={() => setOffset(offset + PAGE_SIZE)}
            className="rounded border border-slate-300 bg-white px-3 py-1.5 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
