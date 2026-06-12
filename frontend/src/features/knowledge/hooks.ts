import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createKnowledge,
  deleteKnowledge,
  getKnowledge,
  listKnowledge,
  queryKnowledge,
  rebuildKnowledge,
  updateKnowledge,
} from "@/features/knowledge/api";
import type { Knowledge, KnowledgeInput } from "@/features/knowledge/types";

const EMBEDDING_IN_FLIGHT = new Set(["pending", "processing"]);

function pollWhileEmbedding(data: Knowledge | Knowledge[] | undefined): number | false {
  const items = Array.isArray(data) ? data : data ? [data] : [];
  return items.some((k) => EMBEDDING_IN_FLIGHT.has(k.status)) ? 3000 : false;
}

export function useKnowledgeList() {
  return useQuery({
    queryKey: ["knowledge"],
    queryFn: listKnowledge,
    refetchInterval: (query) => pollWhileEmbedding(query.state.data),
  });
}

export function useKnowledge(id: string) {
  return useQuery({
    queryKey: ["knowledge", id],
    queryFn: () => getKnowledge(id),
    refetchInterval: (query) => pollWhileEmbedding(query.state.data),
  });
}

function useInvalidatingMutation<TArgs, TResult>(fn: (args: TArgs) => Promise<TResult>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["knowledge"] }),
  });
}

export function useCreateKnowledge() {
  return useInvalidatingMutation((input: KnowledgeInput) => createKnowledge(input));
}

export function useUpdateKnowledge(id: string) {
  return useInvalidatingMutation((input: KnowledgeInput) => updateKnowledge(id, input));
}

export function useDeleteKnowledge() {
  return useInvalidatingMutation((id: string) => deleteKnowledge(id));
}

export function useRebuildKnowledge(id: string) {
  return useInvalidatingMutation(() => rebuildKnowledge(id));
}

export function useQueryKnowledge(id: string) {
  return useMutation({ mutationFn: (question: string) => queryKnowledge(id, question) });
}
