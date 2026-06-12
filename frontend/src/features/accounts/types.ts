export type Platform = "instagram" | "whatsapp" | "threads";
export type AccountStatus = "connected" | "expired" | "disconnected";

export interface SocialAccount {
  id: string;
  platform: Platform;
  platform_user_id: string;
  username: string;
  status: AccountStatus;
  auto_reply_enabled: boolean;
  knowledge_id: string | null;
  knowledge_title: string;
  token_expires_on: string | null;
  created_on: string;
}

export interface AccountUpdate {
  knowledge_id?: string | null;
  auto_reply_enabled?: boolean;
}

export interface WhatsAppCredentials {
  phone_number_id: string;
  access_token: string;
}
