import type { ReactNode } from "react";
import { AuthGuard } from "@/features/auth";

// サイドバー等のApp Shellは Phase 2 で追加する。ここでは認証ガードのみ。
export default function PortalLayout({ children }: { children: ReactNode }) {
  return <AuthGuard>{children}</AuthGuard>;
}
