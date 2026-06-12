import { api } from "@/lib/api";
import type { Knowledge, KnowledgeInput, QueryResult } from "@/features/knowledge/types";

export function listKnowledge(): Promise<Knowledge[]> {
  return api<Knowledge[]>("/knowledge/");
}

export function getKnowledge(id: string): Promise<Knowledge> {
  return api<Knowledge>(`/knowledge/${id}/`);
}

export function createKnowledge(input: KnowledgeInput): Promise<Knowledge> {
  return api<Knowledge>("/knowledge/", { method: "POST", body: JSON.stringify(input) });
}

export function updateKnowledge(id: string, input: KnowledgeInput): Promise<Knowledge> {
  return api<Knowledge>(`/knowledge/${id}/`, { method: "PUT", body: JSON.stringify(input) });
}

export function deleteKnowledge(id: string): Promise<void> {
  return api<void>(`/knowledge/${id}/`, { method: "DELETE" });
}

export function rebuildKnowledge(id: string): Promise<Knowledge> {
  return api<Knowledge>(`/knowledge/${id}/rebuild/`, { method: "POST" });
}

export function queryKnowledge(id: string, question: string): Promise<QueryResult> {
  return api<QueryResult>(`/knowledge/${id}/query/`, {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}
