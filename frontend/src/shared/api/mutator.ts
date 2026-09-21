/**
 * Orval Custom Mutator (Fetch API版)
 *
 * 認証: PoCモック認証（Bearerトークン、レスポンスbodyで受け取りクライアント側stateに保持）。
 * 02-requirement.md（認証・セッション管理・SSO・マルチユーザーはOut of Scope）・
 * 05-api-ipo.md（PoCモック認証がSSOT。本格的なセッション永続化は行わない）に準拠する。
 * httpOnly Cookie・自動リフレッシュ・本格的なJWT基盤は実装しない（Scope 1では不要）。
 *
 * 注意: Client Component からのみ呼ばれる前提（window を使うため）。
 *
 * @see https://orval.dev/reference/configuration/output#mutator
 */
import { getAuthToken, useAuthStore } from "@/shared/lib/auth-store";

// Next.js: ブラウザに公開する環境変数は NEXT_PUBLIC_ プレフィックス（.env.local で設定）
const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function redirectToLogin(): void {
  useAuthStore.getState().clearSession();
  if (typeof window !== "undefined" && window.location.pathname !== "/login") {
    // Client Component外（fetchの中）から呼ばれるためNextのrouter/redirect()は使えない。
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- 上記理由によりhref遷移が唯一の手段
    window.location.href = "/login";
  }
}

/**
 * カスタムインスタンス（orval用）
 *
 * - 保持しているトークンを `Authorization: Bearer` ヘッダに付与
 * - トークン保持中に401 Unauthorizedを受けた場合（セッション失効）はセッションを破棄し
 *   ログインページへリダイレクトする（リフレッシュトークン機構は持たないため再試行はしない）。
 * - トークンを保持していない状態での401（例: ログイン画面での認証情報誤り）はリダイレクトせず
 *   呼び出し元にそのまま返す（ログイン失敗はログイン画面自身がエラー表示として扱う）。
 *
 * @template T - レスポンス型
 * @param url - リクエストURL
 * @param options - Fetch APIのRequestInit
 * @returns Promiseでラップされたレスポンス
 */
export const customInstance = async <T>(
  url: string,
  options?: RequestInit,
): Promise<T> => {
  const headers = new Headers(options?.headers);

  if (
    !headers.has("Content-Type") &&
    options?.body &&
    typeof options.body === "string"
  ) {
    headers.set("Content-Type", "application/json");
  }

  const token = getAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${baseURL}${url}`, { ...options, headers });

  if (response.status === 401 && token) {
    redirectToLogin();
    throw new Error("Authentication failed");
  }

  // 204 No Content（ログアウト等）や空ボディでも落ちないようにする
  const rawBody = [204, 205, 304].includes(response.status)
    ? null
    : await response.text();
  const data = rawBody ? JSON.parse(rawBody) : undefined;

  return {
    data,
    status: response.status,
    headers: response.headers,
  } as T;
};

/**
 * エラー型（orval用）
 *
 * API呼び出しで発生するエラーの型定義。
 * TanStack Queryのerror型として使用される。
 */
export type ErrorType<E> = E & { message?: string };

/**
 * Body型（orval用）
 *
 * リクエストボディの型定義。
 */
export type BodyType<B> = B;
