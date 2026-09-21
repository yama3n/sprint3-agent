"use client";

import { InquiryDetailPage } from "./InquiryDetailPage";

/**
 * SCR-03 のクライアント側ホスト。Phase 10 で SCR-04 Inspector（右スライドパネル）を
 * ここに重ねる（Inspectorは画面遷移ではなくパネル表示のため、同じホストが状態を持つ）。
 */
export function InquiryDetailScreen({ inquiryId }: { inquiryId: number }) {
  return <InquiryDetailPage inquiryId={inquiryId} />;
}
