"use client";

import { useEffect, useSyncExternalStore, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/shared/lib/auth-store";

/** zustand persistのlocalStorage読み出し完了をSSR安全に購読する（サーバーでは常にfalse）。 */
function useHasHydrated() {
  return useSyncExternalStore(
    (callback) => useAuthStore.persist.onFinishHydration(callback),
    () => useAuthStore.persist.hasHydrated(),
    () => false,
  );
}

/**
 * (portal) 配下の未ログインアクセスを /login へリダイレクトするガード。
 * zustand persist は localStorage 読み出しがマウント後になるため、判定確定までは何も描画しない。
 */
export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const token = useAuthStore((state) => state.token);
  const hydrated = useHasHydrated();

  useEffect(() => {
    if (hydrated && !token) {
      router.replace("/login");
    }
  }, [hydrated, token, router]);

  if (!hydrated || !token) {
    return null;
  }

  return <>{children}</>;
}
