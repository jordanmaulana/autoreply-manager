import { useState } from "react";

import { useQueryKnowledge } from "@/features/knowledge/hooks";

export function KnowledgeTestPanel({ knowledgeId }: { knowledgeId: string }) {
  const [question, setQuestion] = useState("");
  const query = useQueryKnowledge(knowledgeId);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-slate-800">Test this knowledge</h2>
      <p className="mt-1 text-xs text-slate-500">
        Runs the exact auto-reply pipeline (retrieval + generation) without sending anything.
      </p>
      <form
        className="mt-3 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (question.trim()) query.mutate(question.trim());
        }}
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="flex-1 rounded border border-slate-300 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
          placeholder="Ask like a customer would…"
        />
        <button
          type="submit"
          disabled={query.isPending}
          className="rounded bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50"
        >
          {query.isPending ? "Thinking…" : "Ask"}
        </button>
      </form>
      {query.error && (
        <p className="mt-3 text-sm text-red-600">{(query.error as Error).message}</p>
      )}
      {query.data && (
        <div className="mt-3 flex flex-col gap-2">
          <div className="rounded bg-slate-50 p-3 text-sm whitespace-pre-wrap">
            {query.data.reply}
          </div>
          <div className="text-xs text-slate-500">
            {query.data.retrieved_chunks.length
              ? `Used chunks: ${query.data.retrieved_chunks
                  .map((c) => `#${c.seq} (${c.score})`)
                  .join(", ")}`
              : "No relevant chunks found — answered from the fallback instruction."}
          </div>
        </div>
      )}
    </div>
  );
}
