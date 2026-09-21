/** SCR-04 Inspector の決定的ロジック（モード判定・overview集計）。 */

import { REASON_LABEL_KEY, type ReasonType } from "./detail-lib";

export interface InspectorField {
  field_id: string;
  label: string;
  value?: string | null;
  status: "ok" | "review";
  reason_type?: ReasonType | null;
  is_web_supplemented?: boolean;
  candidates?: unknown[];
}

/**
 * 03-spec.md SCR-04:
 * - 確認不要（ok）の項目 → 「根拠確認モード」= 読み取り専用（候補選択UI・編集欄・確定ボタンなし）
 * - 要確認（review）の項目 → 「確認・修正モード」= 候補比較 + 値入力 + 確定ボタン
 */
export type InspectorMode = "evidence" | "review";

export function inspectorModeOf(field: InspectorField): InspectorMode {
  return field.status === "review" ? "review" : "evidence";
}

export function isEditable(field: InspectorField): boolean {
  return inspectorModeOf(field) === "review";
}

export function reasonLabelKeyOf(field: InspectorField): string | null {
  return field.reason_type ? REASON_LABEL_KEY[field.reason_type] : null;
}

export interface ReviewEntry<TField extends InspectorField = InspectorField> {
  field: TField;
  itemNo?: number;
}

export interface ReviewGroup<TField extends InspectorField = InspectorField> {
  reasonKey: string;
  reasonType: ReasonType;
  entries: ReviewEntry<TField>[];
}

/**
 * overviewモード用に、要確認項目を内部理由ごとにグルーピングする
 * （03-spec.md: overviewは理由ごとの一覧。色分けはせず文言で区別する）。
 */
export function groupReviewEntries<TField extends InspectorField>(
  entries: ReviewEntry<TField>[],
): ReviewGroup<TField>[] {
  const groups = new Map<ReasonType, ReviewEntry<TField>[]>();
  for (const entry of entries) {
    if (entry.field.status !== "review") continue;
    const reason = (entry.field.reason_type ?? "missing") as ReasonType;
    groups.set(reason, [...(groups.get(reason) ?? []), entry]);
  }
  return [...groups.entries()].map(([reasonType, groupEntries]) => ({
    reasonType,
    reasonKey: REASON_LABEL_KEY[reasonType],
    entries: groupEntries,
  }));
}
