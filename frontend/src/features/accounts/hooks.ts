import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  connectWhatsApp,
  disconnectAccount,
  getConnectUrl,
  listAccounts,
  updateAccount,
} from "@/features/accounts/api";
import type { AccountUpdate, Platform, WhatsAppCredentials } from "@/features/accounts/types";

export function useAccounts() {
  return useQuery({ queryKey: ["accounts"], queryFn: listAccounts });
}

export function useConnect() {
  return useMutation({
    mutationFn: (platform: Platform) => getConnectUrl(platform),
    onSuccess: ({ url }) => {
      window.location.href = url;
    },
  });
}

function useInvalidatingMutation<TArgs, TResult>(fn: (args: TArgs) => Promise<TResult>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["accounts"] }),
  });
}

export function useConnectWhatsApp() {
  return useInvalidatingMutation((creds: WhatsAppCredentials) => connectWhatsApp(creds));
}

export function useUpdateAccount() {
  return useInvalidatingMutation(({ id, update }: { id: string; update: AccountUpdate }) =>
    updateAccount(id, update),
  );
}

export function useDisconnectAccount() {
  return useInvalidatingMutation((id: string) => disconnectAccount(id));
}
