"use client";

import { useMemo, useState } from "react";
import { useListInquiries, type InquiryListItem } from "./api";

export type InquiryFilter = "all" | "draft" | "final";

export type InquiryEmptyState =
  | { kind: "none" }
  | { kind: "filtered"; filter: Exclude<InquiryFilter, "all"> }
  | { kind: "list" };

/**
 * SCR-01の状態を一括管理する。mockup.html の applyFilter/updateInquiryEmptyState と同じく、
 * 一覧は1回取得しフィルタはクライアント側で適用する（タブ切替のたびに再フェッチしない）。
 */
export function useInquiryListPage() {
  const query = useListInquiries();
  const [filter, setFilter] = useState<InquiryFilter>("all");

  const items: InquiryListItem[] = useMemo(
    () => (query.data?.status === 200 ? query.data.data.items : []),
    [query.data],
  );

  const counts = useMemo(
    () => ({
      all: items.length,
      draft: items.filter((i) => i.status === "draft").length,
      final: items.filter((i) => i.status === "final").length,
    }),
    [items],
  );

  const visibleItems = useMemo(
    () => (filter === "all" ? items : items.filter((i) => i.status === filter)),
    [items, filter],
  );

  const emptyState: InquiryEmptyState =
    items.length === 0
      ? { kind: "none" }
      : visibleItems.length === 0
        ? { kind: "filtered", filter: filter as Exclude<InquiryFilter, "all"> }
        : { kind: "list" };

  return {
    isLoading: query.isLoading,
    isError: query.isError || (query.data && query.data.status !== 200),
    filter,
    setFilter,
    counts,
    visibleItems,
    emptyState,
  };
}
