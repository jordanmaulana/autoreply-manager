import { Link, createFileRoute } from "@tanstack/react-router";
import { Plus } from "lucide-react";

import { KnowledgeStatusBadge } from "@/features/knowledge/components/knowledge-status-badge";
import { useKnowledgeList } from "@/features/knowledge/hooks";

export const Route = createFileRoute("/knowledge")({
  component: KnowledgePage,
});

function KnowledgePage() {
  const { data: items, isLoading } = useKnowledgeList();

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Knowledge</h1>
          <p className="mt-1 text-sm text-slate-600">
            Each knowledge base powers auto-replies for the accounts linked to it.
          </p>
        </div>
        <Link
          to="/knowledge/$knowledgeId"
          params={{ knowledgeId: "new" }}
          className="flex items-center gap-1.5 rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" /> New knowledge
        </Link>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {isLoading && <p className="text-sm text-slate-500">Loading…</p>}
        {items?.length === 0 && (
          <p className="col-span-full rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
            No knowledge yet. Create one with your FAQ, prices, policies — anything the
            auto-reply should know.
          </p>
        )}
        {items?.map((k) => (
          <Link
            key={k.id}
            to="/knowledge/$knowledgeId"
            params={{ knowledgeId: k.id }}
            className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-white p-4 hover:border-blue-300"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-800">{k.title}</span>
              <KnowledgeStatusBadge status={k.status} error={k.status_error} />
            </div>
            <p className="line-clamp-2 text-xs text-slate-500">{k.description}</p>
            <div className="mt-auto text-xs text-slate-400">
              {k.chunk_count} chunks · {k.account_count} account(s)
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
