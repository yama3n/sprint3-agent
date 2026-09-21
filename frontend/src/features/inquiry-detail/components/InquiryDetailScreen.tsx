"use client";

import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getAuthToken } from "@/shared/lib/auth-store";
import {
  getExportDownloadUrl,
  getInquiryDetailQueryKey,
  useConfirmInquiry,
  useCreateExport,
  useInquiryDetail,
  useUpdateCaseField,
  useUpdateItemField,
  type FieldRead,
} from "../api";
import type { ReviewEntry } from "../inspector-lib";
import { DetailActionBar } from "./DetailActionBar";
import { InquiryDetailPage } from "./InquiryDetailPage";
import { InspectorPanel, type InspectorState } from "./InspectorPanel";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

/** 認証必須のダウンロードURLをBearer付きで取得し、ブラウザに保存させる。 */
async function downloadExportFile(url: string, fileName: string): Promise<void> {
  const token = getAuthToken();
  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!response.ok) throw new Error("download failed");

  const blobUrl = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = blobUrl;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(blobUrl);
}

/**
 * SCR-03 + SCR-04 のホスト。Inspectorは画面遷移ではなく右スライドパネルのため、
 * 詳細画面と同じホストが開閉状態を持つ（03-spec.md SCR-04）。
 */
export function InquiryDetailScreen({ inquiryId }: { inquiryId: number }) {
  const [inspector, setInspector] = useState<InspectorState>({ mode: "closed" });
  const [saveError, setSaveError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  // 確定済みを再編集したら注意表示を出し、再出力でクリアする（mockup: reeditBanner）
  const [editedAfterExport, setEditedAfterExport] = useState(false);
  const queryClient = useQueryClient();
  const detailQuery = useInquiryDetail(inquiryId);
  const updateCaseField = useUpdateCaseField();
  const updateItemField = useUpdateItemField();
  const confirmInquiry = useConfirmInquiry();
  const createExport = useCreateExport();

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
        if (detail?.inquiry.status === "final") {
          setEditedAfterExport(true);
        }
        return true;
      } catch {
        setSaveError("inspector.updateError");
        return false;
      }
    },
    [inquiryId, queryClient, updateCaseField, updateItemField, detail],
  );

  const handleConfirmInquiry = useCallback(async () => {
    setActionError(null);
    try {
      const result = await confirmInquiry.mutateAsync({ inquiryId });
      if (result.status !== 200) {
        setActionError("detail.confirmError");
        return false;
      }
      await queryClient.invalidateQueries({
        queryKey: getInquiryDetailQueryKey(inquiryId),
      });
      return true;
    } catch {
      setActionError("detail.confirmError");
      return false;
    }
  }, [confirmInquiry, inquiryId, queryClient]);

  const handleExport = useCallback(async () => {
    setActionError(null);
    try {
      const result = await createExport.mutateAsync({
        inquiryId,
        data: { format: "excel" },
      });
      if (result.status !== 200) {
        setActionError("detail.exportError");
        return false;
      }
      setEditedAfterExport(false);
      // ダウンロードエンドポイントは認証必須のため、単純な遷移ではなくBearer付きで取得して
      // Blobからダウンロードさせる
      await downloadExportFile(
        `${API_BASE_URL}${getExportDownloadUrl(inquiryId, result.data.export_id)}`,
        result.data.file_name,
      );
      return true;
    } catch {
      setActionError("detail.exportError");
      return false;
    }
  }, [createExport, inquiryId]);

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
        showReeditBanner={detail?.inquiry.status === "final" && editedAfterExport}
        actionBar={
          <DetailActionBar
            inquiryId={inquiryId}
            isFinal={detail?.inquiry.status === "final"}
            onConfirm={handleConfirmInquiry}
            onExport={handleExport}
            isConfirming={confirmInquiry.isPending}
            isExporting={createExport.isPending}
            error={actionError}
          />
        }
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
