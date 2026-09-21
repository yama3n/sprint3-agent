import type { ReactNode } from "react";
import { AuthGuard } from "@/features/auth";
import { AppShell } from "./AppShell";

export default function PortalLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
