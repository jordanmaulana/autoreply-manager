import { useQuery } from "@tanstack/react-query";

import { listReplies, type ReplyFilters } from "@/features/replies/api";

export function useReplies(filters: ReplyFilters) {
  return useQuery({
    queryKey: ["replies", filters],
    queryFn: () => listReplies(filters),
  });
}
