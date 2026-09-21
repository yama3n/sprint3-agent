/** SCR-03/SCR-04 の決定的な表示ロジック（UIから切り離してテストする）。 */

export type ReasonType =
  | "missing"
  | "conflict"
  | "ambiguous"
  | "multiple_candidates"
  | "parse_error";

/**
 * 要確認の内部理由 → Inspector内の日本語ラベルのi18nキー（03-spec.md 4章の対応表）。
 * ユーザー向けステータスは「確認不要／要確認」の2値のみで、理由は色分けしない。
 */
export const REASON_LABEL_KEY: Record<ReasonType, string> = {
  missing: "detail.reasonMissing",
  conflict: "detail.reasonConflict",
  ambiguous: "detail.reasonAmbiguous",
  multiple_candidates: "detail.reasonMultipleCandidates",
  parse_error: "detail.reasonParseError",
};

export interface FieldLike {
  value?: string | null;
  status: "ok" | "review";
  reason_type?: ReasonType | null;
  is_web_supplemented?: boolean;
  candidates?: unknown[];
}

export type FieldDisplay =
  | { kind: "value"; value: string; isWebSupplemented: boolean }
  | { kind: "review"; reasonKey: string | null; candidateCount: number }
  | { kind: "empty" };

/**
 * 1項目のセル表示を決める（mockup #SCR-03 の val-cell）。
 * - 確認不要（ok）: 値を表示しバッジは出さない（Web補完のみ別タグで示す）
 * - 要確認（review）: 要確認バッジ＋理由ヒント（候補件数 / 理由文言）
 */
export function toFieldDisplay(field: FieldLike): FieldDisplay {
  if (field.status === "review") {
    return {
      kind: "review",
      reasonKey: field.reason_type ? REASON_LABEL_KEY[field.reason_type] : null,
      candidateCount: field.candidates?.length ?? 0,
    };
  }
  if (field.value) {
    return {
      kind: "value",
      value: field.value,
      isWebSupplemented: Boolean(field.is_web_supplemented),
    };
  }
  return { kind: "empty" };
}
