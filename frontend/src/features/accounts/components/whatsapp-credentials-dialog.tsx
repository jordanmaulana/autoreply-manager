import { useState } from "react";
import { toast } from "react-toastify";

import { useConnectWhatsApp } from "@/features/accounts/hooks";
import { ApiError } from "@/lib/api";

export function WhatsAppCredentialsDialog({ onClose }: { onClose: () => void }) {
  const [phoneNumberId, setPhoneNumberId] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const connect = useConnectWhatsApp();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-base font-semibold text-slate-800">Connect WhatsApp</h2>
        <p className="mt-1 text-xs text-slate-500">
          From Meta Business Manager: WhatsApp &gt; API Setup. Use the phone number ID and a
          permanent system-user access token.
        </p>
        <form
          className="mt-4 flex flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            connect.mutate(
              { phone_number_id: phoneNumberId.trim(), access_token: accessToken.trim() },
              {
                onSuccess: () => {
                  toast.success("WhatsApp connected");
                  onClose();
                },
                onError: (err) =>
                  toast.error(err instanceof ApiError ? err.message : "Connection failed"),
              },
            );
          }}
        >
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-slate-700">Phone number ID</span>
            <input
              value={phoneNumberId}
              onChange={(e) => setPhoneNumberId(e.target.value)}
              required
              className="rounded border border-slate-300 px-3 py-2 focus:border-blue-400 focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-slate-700">Access token</span>
            <input
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
              required
              type="password"
              className="rounded border border-slate-300 px-3 py-2 focus:border-blue-400 focus:outline-none"
            />
          </label>
          <div className="mt-1 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded px-3 py-2 text-sm text-slate-600 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={connect.isPending}
              className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {connect.isPending ? "Validating…" : "Connect"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
