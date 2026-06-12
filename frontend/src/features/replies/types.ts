import type { Platform } from "@/features/accounts/types";
import type { RetrievedChunk } from "@/features/knowledge/types";

export type ReplyStatus = "received" | "processing" | "sent" | "failed" | "skipped";

export interface ReplyLog {
  id: string;
  account_id: string;
  platform: Platform;
  account_username: string;
  platform_message_id: string;
  sender_id: string;
  sender_name: string;
  inbound_text: string;
  reply_text: string;
  retrieved_chunks: RetrievedChunk[];
  status: ReplyStatus;
  error: string;
  created_on: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
