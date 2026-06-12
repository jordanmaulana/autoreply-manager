export type KnowledgeStatus = "pending" | "processing" | "ready" | "failed";

export interface Knowledge {
  id: string;
  title: string;
  description: string;
  persona: string;
  status: KnowledgeStatus;
  status_error: string;
  chunk_count: number;
  embedded_on: string | null;
  account_count: number;
  created_on: string;
  updated_on: string;
}

export interface KnowledgeInput {
  title: string;
  description: string;
  persona: string;
}

export interface RetrievedChunk {
  chunk_id: string;
  seq: number;
  score: number;
}

export interface QueryResult {
  reply: string;
  retrieved_chunks: RetrievedChunk[];
}
