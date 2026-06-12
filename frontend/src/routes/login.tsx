import { createFileRoute } from "@tanstack/react-router";

import { AuthCard } from "@/features/auth/components/auth-card";

export const Route = createFileRoute("/login")({
  component: () => (
    <div className="flex min-h-screen items-center justify-center px-4">
      <AuthCard />
    </div>
  ),
});
