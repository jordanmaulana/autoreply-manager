import { useEffect, useRef, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";
import { toast } from "react-toastify";

import { ApiError } from "@/lib/api";
import { useEmailAuth, useGoogleSignIn } from "@/features/auth/hooks";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (resp: { credential: string }) => void;
          }) => void;
          renderButton: (el: HTMLElement, opts: Record<string, unknown>) => void;
        };
      };
    };
  }
}

function errorMessage(err: unknown): string {
  if (err instanceof ApiError && err.data && typeof err.data === "object") {
    const values = Object.values(err.data as Record<string, unknown>).flat();
    if (values.length) return values.map(String).join(" ");
  }
  return err instanceof Error ? err.message : "Something went wrong";
}

export function AuthCard() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const emailAuth = useEmailAuth(mode);
  const signIn = useGoogleSignIn();
  const navigate = useNavigate();
  const googleRef = useRef<HTMLDivElement>(null);
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  useEffect(() => {
    if (!clientId || !window.google || !googleRef.current) return;
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: ({ credential }) =>
        signIn.mutate(credential, {
          onSuccess: () => navigate({ to: "/dashboard" }),
          onError: (err) => toast.error(errorMessage(err)),
        }),
    });
    window.google.accounts.id.renderButton(googleRef.current, {
      type: "standard",
      theme: "outline",
      size: "large",
      width: 320,
    });
  }, [clientId, signIn, navigate]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    emailAuth.mutate(
      { email, password },
      {
        onSuccess: () => navigate({ to: "/dashboard" }),
        onError: (err) => setFormError(errorMessage(err)),
      },
    );
  };

  const login = mode === "login";
  return (
    <div className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-xl font-semibold">{login ? "Sign in" : "Create account"}</h1>
      <p className="mt-1 text-sm text-slate-600">
        {login ? "Welcome back." : "Register with your email."}
      </p>
      <form onSubmit={submit} className="mt-6 flex flex-col gap-3">
        <label className="text-sm">
          <span className="text-slate-600">Email</span>
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </label>
        <label className="text-sm">
          <span className="text-slate-600">Password</span>
          <input
            type="password"
            required
            minLength={login ? undefined : 8}
            autoComplete={login ? "current-password" : "new-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </label>
        {formError && <p className="text-sm text-red-600">{formError}</p>}
        <button
          type="submit"
          disabled={emailAuth.isPending}
          className="mt-1 inline-flex items-center justify-center gap-2 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:opacity-60"
        >
          {emailAuth.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          {login ? "Sign in" : "Register"}
        </button>
      </form>
      <button
        type="button"
        onClick={() => {
          setMode(login ? "register" : "login");
          setFormError(null);
        }}
        className="mt-3 text-sm text-blue-600 hover:underline"
      >
        {login ? "No account? Register" : "Have an account? Sign in"}
      </button>
      <div className="mt-5 flex items-center gap-3 text-xs text-slate-400">
        <div className="h-px flex-1 bg-slate-200" />
        or
        <div className="h-px flex-1 bg-slate-200" />
      </div>
      <div ref={googleRef} className="mt-5 flex justify-center" />
      {!clientId && <p className="mt-4 text-xs text-red-600">VITE_GOOGLE_CLIENT_ID not set.</p>}
    </div>
  );
}
