import { useEffect } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { toast } from "react-toastify";

import { AccountCard } from "@/features/accounts/components/account-card";
import { ConnectButtons } from "@/features/accounts/components/connect-buttons";
import { useAccounts } from "@/features/accounts/hooks";

type AccountsSearch = {
  connected?: string;
  error?: string;
};

export const Route = createFileRoute("/accounts")({
  validateSearch: (search: Record<string, unknown>): AccountsSearch => ({
    connected: typeof search.connected === "string" ? search.connected : undefined,
    error: typeof search.error === "string" ? search.error : undefined,
  }),
  component: AccountsPage,
});

function AccountsPage() {
  const { connected, error } = Route.useSearch();
  const navigate = useNavigate();
  const { data: accounts, isLoading } = useAccounts();

  useEffect(() => {
    if (!connected && !error) return;
    if (connected) toast.success(`${connected} connected`);
    if (error) toast.error(error);
    navigate({ to: "/accounts", search: {}, replace: true });
  }, [connected, error, navigate]);

  return (
    <div>
      <h1 className="text-2xl font-semibold">Accounts</h1>
      <p className="mt-1 text-sm text-slate-600">
        Connect social accounts and link each one to a knowledge base. One account uses one
        knowledge; one knowledge can serve many accounts.
      </p>

      <div className="mt-6">
        <ConnectButtons />
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {isLoading && <p className="text-sm text-slate-500">Loading…</p>}
        {accounts?.length === 0 && (
          <p className="col-span-full rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
            No accounts connected yet.
          </p>
        )}
        {accounts?.map((account) => (
          <AccountCard key={account.id} account={account} />
        ))}
      </div>
    </div>
  );
}
