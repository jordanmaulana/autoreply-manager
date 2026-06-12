import { useEffect, useRef } from "react";
import { Outlet, useNavigate, useRouterState } from "@tanstack/react-router";
import { useAtom } from "jotai";

import { AppShell } from "@/components/layout/app-shell";
import { ApiError } from "@/lib/api";
import { me } from "@/features/auth/api";
import { tokenAtom, userAtom } from "@/features/auth/state";

// "/" is a splash that always redirects; only "/login" is reachable without a token.
const SPLASH_PATHS = new Set(["/", "/login"]);

export function AuthGate() {
  const [token, setToken] = useAtom(tokenAtom);
  const [user, setUser] = useAtom(userAtom);
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const sessionExpiredFiredRef = useRef(false);

  useEffect(() => {
    if (!token || user) return;
    let cancelled = false;
    me()
      .then((u) => {
        if (!cancelled) setUser(u);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) {
          setToken(null);
          setUser(null);
          sessionExpiredFiredRef.current = true;
        }
      });
    return () => {
      cancelled = true;
    };
  }, [token, user, setToken, setUser]);

  useEffect(() => {
    if (!token) {
      if (pathname !== "/login") navigate({ to: "/login" });
      return;
    }
    if (!user) return;
    if (SPLASH_PATHS.has(pathname)) {
      navigate({ to: "/dashboard" });
    }
  }, [token, user, pathname, navigate]);

  if (!token || !user || SPLASH_PATHS.has(pathname)) {
    return <Outlet />;
  }
  return <AppShell />;
}
