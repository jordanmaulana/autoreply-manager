import { api } from "@/lib/api";
import type {
  AccountUpdate,
  Platform,
  SocialAccount,
  WhatsAppCredentials,
} from "@/features/accounts/types";

export function listAccounts(): Promise<SocialAccount[]> {
  return api<SocialAccount[]>("/accounts/");
}

export function getConnectUrl(platform: Platform): Promise<{ url: string }> {
  return api<{ url: string }>(`/accounts/${platform}/connect/`);
}

export function connectWhatsApp(creds: WhatsAppCredentials): Promise<SocialAccount> {
  return api<SocialAccount>("/accounts/whatsapp/", {
    method: "POST",
    body: JSON.stringify(creds),
  });
}

export function updateAccount(id: string, update: AccountUpdate): Promise<SocialAccount> {
  return api<SocialAccount>(`/accounts/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(update),
  });
}

export function disconnectAccount(id: string): Promise<void> {
  return api<void>(`/accounts/${id}/`, { method: "DELETE" });
}
