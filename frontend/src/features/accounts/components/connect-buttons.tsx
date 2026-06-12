import { useState } from "react";
import { Camera, MessageCircle, AtSign } from "lucide-react";

import { useConnect } from "@/features/accounts/hooks";
import { WhatsAppCredentialsDialog } from "@/features/accounts/components/whatsapp-credentials-dialog";

export function ConnectButtons() {
  const connect = useConnect();
  const [waOpen, setWaOpen] = useState(false);

  const base =
    "flex items-center gap-2 rounded border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50";

  return (
    <div className="flex flex-wrap gap-2">
      <button
        type="button"
        className={base}
        disabled={connect.isPending}
        onClick={() => connect.mutate("instagram")}
      >
        <Camera className="h-4 w-4" /> Connect Instagram
      </button>
      <button
        type="button"
        className={base}
        disabled={connect.isPending}
        onClick={() => connect.mutate("threads")}
      >
        <AtSign className="h-4 w-4" /> Connect Threads
      </button>
      <button type="button" className={base} onClick={() => setWaOpen(true)}>
        <MessageCircle className="h-4 w-4" /> Connect WhatsApp
      </button>
      {waOpen && <WhatsAppCredentialsDialog onClose={() => setWaOpen(false)} />}
    </div>
  );
}
