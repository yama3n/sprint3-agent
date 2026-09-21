"use client";

import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  getInquiryDetailQueryKey,
  useInquiryDetail,
  useUpdateCaseField,
  useUpdateItemField,
  type FieldRead,
} from "../api";
import type { ReviewEntry } from "../inspector-lib";
import { InquiryDetailPage } from "./InquiryDetailPage";
import { InspectorPanel, type InspectorState } from "./InspectorPanel";

/**
 * SCR-03 + SCR-04 のホスト。Inspectorは画面遷移ではなく右スライドパネルのため、
 * 詳細画面と同じホストが開閉状態を持つ（03-spec.md SCR-04）。
 */
export function InquiryDetailScreen({ inquiryId }: { inquiryId: number }) {
  const [inspector, setInspector] = useState<InspectorState>({ mode: "closed" });
  const [saveError, setSaveError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const detailQuery = useInquiryDetail(inquiryId);
  const updateCaseField = useUpdateCaseField();
  const updateItemField = useUpdateItemField();

  const detail = detailQuery.data?.status === 200 ? detailQuery.data.data : null;

  const reviewEntries: ReviewEntry<FieldRead>[] = detail
    ? [
        ...detail.case_fields.map((field) => ({ field })),
        ...detail.items.flatMap((item) =>
          item.fields.map((field) => ({ field, itemNo: item.item_no })),
        ),
      ]
    : [];

  const itemIdByItemNo = new Map(detail?.items.map((i) => [i.item_no, i.id]) ?? []);

  const handleConfirm = useCallback(
    async ({
      field,
      itemId,
      value,
      selectedCandidateId,
    }: {
      field: FieldRead;
      itemId?: number;
      value: string;
      selectedCandidateId?: number;
    }) => {
      setSaveError(null);
      try {
        const body = { value, selected_candidate_id: selectedCandidateId ?? null };
        const result =
          itemId === undefined
            ? await updateCaseField.mutateAsync({
                inquiryId,
                fieldId: field.field_id,
                data: body,
              })
            : await updateItemField.mutateAsync({
                inquiryId,
                itemId,
                fieldId: field.field_id,
                data: body,
              });
        if (result.status !== 200) {
          setSaveError("inspector.updateError");
          return false;
        }
        await queryClient.invalidateQueries({
          queryKey: getInquiryDetailQueryKey(inquiryId),
        });
        return true;
      } catch {
        setSaveError("inspector.updateError");
        return false;
      }
    },
    [inquiryId, queryClient, updateCaseField, updateItemField],
  );

  return (
    <>
      <InquiryDetailPage
        inquiryId={inquiryId}
        onOpenField={(field, itemNo) =>
          setInspector({
            mode: "field",
            field,
            itemNo,
            itemId: itemNo === undefined ? undefined : itemIdByItemNo.get(itemNo),
          })
        }
        onOpenOverview={() => setInspector({ mode: "overview" })}
      />
      <InspectorPanel
        state={inspector}
        reviewEntries={reviewEntries}
        onClose={() => setInspector({ mode: "closed" })}
        onBackToOverview={() => setInspector({ mode: "overview" })}
        onSelectEntry={(entry) =>
          setInspector({
            mode: "field",
            field: entry.field,
            itemNo: entry.itemNo,
            itemId:
              entry.itemNo === undefined ? undefined : itemIdByItemNo.get(entry.itemNo),
          })
        }
        onConfirm={handleConfirm}
        isSaving={updateCaseField.isPending || updateItemField.isPending}
        saveError={saveError}
      />
    </>
  );
}
