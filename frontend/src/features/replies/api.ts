import { api } from "@/lib/api";
import type { Paginated, ReplyLog } from "@/features/replies/types";

export interface ReplyFilters {
  account?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

export function listReplies(filters: ReplyFilters): Promise<Paginated<ReplyLog>> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== "") params.set(key, String(value));
  }
  return api<Paginated<ReplyLog>>(`/replies/?${params}`);
}
