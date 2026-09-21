// PoCモック認証のセッション保持（zustand + localStorage）。
// 02-requirement.md（認証・セッション管理はOut of Scope）・05-api-ipo.md（PoCモック認証がSSOT）に
// 準拠し、サーバー側セッション永続化・リフレッシュトークンは実装しない。
// ここで保持するのはクライアント側の「今のトークンを覚えておく」だけの薄い状態。
import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AuthUser {
  email: string;
  displayName: string;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  setSession: (token: string, user: AuthUser) => void;
  clearSession: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setSession: (token, user) => set({ token, user }),
      clearSession: () => set({ token: null, user: null }),
    }),
    { name: "auth-storage" },
  ),
);

export function getAuthToken(): string | null {
  return useAuthStore.getState().token;
}
