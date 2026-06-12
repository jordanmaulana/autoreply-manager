import type { ReactNode } from "react";
import { Link, createFileRoute } from "@tanstack/react-router";

import { useAccounts } from "@/features/accounts/hooks";
import { useKnowledgeList } from "@/features/knowledge/hooks";
import { useReplies } from "@/features/replies/hooks";
import { ReplyLogTable } from "@/features/replies/components/reply-log-table";

export const Route = createFileRoute("/dashboard")({
  component: DashboardPage,
});

function StatCard({
  title,
  to,
  value,
  detail,
  cta,
}: {
  title: string;
  to: string;
  value: string;
  detail?: ReactNode;
  cta?: string;
}) {
  return (
    <Link
      to={to}
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-slate-300"
    >
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-1 text-3xl font-semibold">{value}</p>
      {detail && <div className="mt-2 text-xs text-slate-500">{detail}</div>}
      {cta && <p className="mt-2 text-xs font-medium text-blue-600">{cta} →</p>}
    </Link>
  );
}

function DashboardPage() {
  const accounts = useAccounts();
  const knowledge = useKnowledgeList();
  const replies = useReplies({ limit: 5, offset: 0 });

  const accountList = accounts.data ?? [];
  const expired = accountList.filter((a) => a.status === "expired").length;
  const autoReplying = accountList.filter((a) => a.auto_reply_enabled).length;

  const knowledgeList = knowledge.data ?? [];
  const ready = knowledgeList.filter((k) => k.status === "ready").length;
  const embedding = knowledgeList.filter(
    (k) => k.status === "pending" || k.status === "processing",
  ).length;
  const failed = knowledgeList.filter((k) => k.status === "failed").length;

  return (
    <div>
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="Connected accounts"
          to="/accounts"
          value={accounts.isLoading ? "…" : String(accountList.length)}
          detail={
            accountList.length > 0 ? (
              <>
                {autoReplying} auto-replying
                {expired > 0 && (
                  <span className="ml-2 font-medium text-amber-600">{expired} expired</span>
                )}
              </>
            ) : undefined
          }
          cta={!accounts.isLoading && accountList.length === 0 ? "Connect an account" : undefined}
        />
        <StatCard
          title="Knowledge bases"
          to="/knowledge"
          value={knowledge.isLoading ? "…" : String(knowledgeList.length)}
          detail={
            knowledgeList.length > 0 ? (
              <>
                {ready} ready
                {embedding > 0 && <span className="ml-2 text-blue-600">{embedding} embedding</span>}
                {failed > 0 && (
                  <span className="ml-2 font-medium text-red-600">{failed} failed</span>
                )}
              </>
            ) : undefined
          }
          cta={!knowledge.isLoading && knowledgeList.length === 0 ? "Create knowledge" : undefined}
        />
        <StatCard
          title="Reply logs"
          to="/replies"
          value={replies.isLoading ? "…" : String(replies.data?.count ?? 0)}
          detail="All-time auto-reply log entries"
        />
      </div>
      <div className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Recent replies</h2>
          <Link to="/replies" className="text-sm font-medium text-blue-600 hover:underline">
            View all
          </Link>
        </div>
        <div className="mt-3">
          <ReplyLogTable replies={replies.data?.results ?? []} />
        </div>
      </div>
    </div>
  );
}
