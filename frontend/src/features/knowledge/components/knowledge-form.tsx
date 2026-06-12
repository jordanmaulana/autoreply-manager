import { useState } from "react";

import type { KnowledgeInput } from "@/features/knowledge/types";

export function KnowledgeForm({
  initial,
  onSubmit,
  submitting,
  submitLabel,
}: {
  initial?: KnowledgeInput;
  onSubmit: (input: KnowledgeInput) => void;
  submitting: boolean;
  submitLabel: string;
}) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [persona, setPersona] = useState(initial?.persona ?? "");

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ title: title.trim(), description, persona });
      }}
    >
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-slate-700">Title</span>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          maxLength={200}
          className="rounded border border-slate-300 px-3 py-2 focus:border-blue-400 focus:outline-none"
          placeholder="e.g. Store FAQ"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-slate-700">Knowledge text</span>
        <span className="text-xs text-slate-500">
          Everything the auto-reply is allowed to know. Any length works — long texts are
          split into chunks and re-embedded when changed.
        </span>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          rows={14}
          className="rounded border border-slate-300 px-3 py-2 font-mono text-xs focus:border-blue-400 focus:outline-none"
          placeholder="Opening hours, prices, address, policies…"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-slate-700">Persona (optional)</span>
        <textarea
          value={persona}
          onChange={(e) => setPersona(e.target.value)}
          rows={2}
          className="rounded border border-slate-300 px-3 py-2 focus:border-blue-400 focus:outline-none"
          placeholder="Tone instructions, e.g. friendly and brief, greet with 'Kak'"
        />
      </label>
      <button
        type="submit"
        disabled={submitting}
        className="self-start rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? "Saving…" : submitLabel}
      </button>
    </form>
  );
}
