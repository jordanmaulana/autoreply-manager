import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, RefreshCw, Trash2 } from "lucide-react";
import { toast } from "react-toastify";

import { KnowledgeForm } from "@/features/knowledge/components/knowledge-form";
import { KnowledgeStatusBadge } from "@/features/knowledge/components/knowledge-status-badge";
import { KnowledgeTestPanel } from "@/features/knowledge/components/knowledge-test-panel";
import {
  useCreateKnowledge,
  useDeleteKnowledge,
  useKnowledge,
  useRebuildKnowledge,
  useUpdateKnowledge,
} from "@/features/knowledge/hooks";
import { ApiError } from "@/lib/api";

export const Route = createFileRoute("/knowledge_/$knowledgeId")({
  component: KnowledgeDetailPage,
});

function KnowledgeDetailPage() {
  const { knowledgeId } = Route.useParams();
  const isNew = knowledgeId === "new";
  return isNew ? <CreatePage /> : <EditPage knowledgeId={knowledgeId} />;
}

function CreatePage() {
  const navigate = useNavigate();
  const create = useCreateKnowledge();

  return (
    <div className="mx-auto max-w-3xl">
      <BackLink />
      <h1 className="mt-2 text-2xl font-semibold">New knowledge</h1>
      <div className="mt-6 rounded-lg border border-slate-200 bg-white p-5">
        <KnowledgeForm
          submitting={create.isPending}
          submitLabel="Create & embed"
          onSubmit={(input) =>
            create.mutate(input, {
              onSuccess: (k) => {
                toast.success("Knowledge created — embedding started");
                navigate({ to: "/knowledge/$knowledgeId", params: { knowledgeId: k.id } });
              },
              onError: (err) =>
                toast.error(err instanceof ApiError ? err.message : "Create failed"),
            })
          }
        />
      </div>
    </div>
  );
}

function EditPage({ knowledgeId }: { knowledgeId: string }) {
  const navigate = useNavigate();
  const { data: knowledge, isLoading } = useKnowledge(knowledgeId);
  const update = useUpdateKnowledge(knowledgeId);
  const rebuild = useRebuildKnowledge(knowledgeId);
  const remove = useDeleteKnowledge();

  if (isLoading || !knowledge) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }

  return (
    <div className="mx-auto max-w-3xl">
      <BackLink />
      <div className="mt-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">{knowledge.title}</h1>
          <KnowledgeStatusBadge status={knowledge.status} error={knowledge.status_error} />
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() =>
              rebuild.mutate(undefined, {
                onSuccess: () => toast.info("Rebuild started"),
                onError: (err) =>
                  toast.error(err instanceof ApiError ? err.message : "Rebuild failed"),
              })
            }
            className="flex items-center gap-1.5 rounded border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Rebuild
          </button>
          <button
            type="button"
            onClick={() => {
              if (confirm("Delete this knowledge? Linked accounts stop auto-replying.")) {
                remove.mutate(knowledgeId, {
                  onSuccess: () => {
                    toast.info("Knowledge deleted");
                    navigate({ to: "/knowledge" });
                  },
                });
              }
            }}
            className="flex items-center gap-1.5 rounded border border-red-200 bg-white px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
          >
            <Trash2 className="h-3.5 w-3.5" /> Delete
          </button>
        </div>
      </div>

      {knowledge.status === "failed" && (
        <p className="mt-3 rounded border border-red-200 bg-red-50 p-3 text-xs text-red-700">
          Embedding failed: {knowledge.status_error}
        </p>
      )}
      <p className="mt-2 text-xs text-slate-500">
        {knowledge.chunk_count} chunks
        {knowledge.embedded_on &&
          ` · embedded ${new Date(knowledge.embedded_on).toLocaleString()}`}
        {" · "}
        {knowledge.account_count} linked account(s)
      </p>

      <div className="mt-6 flex flex-col gap-6">
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <p className="mb-4 text-xs text-slate-500">
            Saving a changed text re-chunks and re-embeds the knowledge.
          </p>
          <KnowledgeForm
            key={knowledge.updated_on}
            initial={{
              title: knowledge.title,
              description: knowledge.description,
              persona: knowledge.persona,
            }}
            submitting={update.isPending}
            submitLabel="Save"
            onSubmit={(input) =>
              update.mutate(input, {
                onSuccess: () => toast.success("Saved"),
                onError: (err) =>
                  toast.error(err instanceof ApiError ? err.message : "Save failed"),
              })
            }
          />
        </div>
        {knowledge.status === "ready" && <KnowledgeTestPanel knowledgeId={knowledgeId} />}
      </div>
    </div>
  );
}

function BackLink() {
  return (
    <Link
      to="/knowledge"
      className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700"
    >
      <ArrowLeft className="h-3.5 w-3.5" /> All knowledge
    </Link>
  );
}
