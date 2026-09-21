"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { Button, Typography } from "@mui/material";
import { tokens } from "@/shared/theme/tokens";
import { useInquiryDetail } from "@/features/inquiry-detail";
import { useAdditionalUpload, useAgentProgress, useFileSelection } from "../upload-hooks";
import { UploadForm } from "./UploadForm";

/** SCR-05 資料追加アップロード（FUNC-01 追加アップロード）。SCR-02とUploadFormを共用する。 */
export function AddFilesPage({ inquiryId }: { inquiryId: number }) {
  const { t } = useTranslation();
  const router = useRouter();
  const { files, rejectedNames, addFiles, removeFile } = useFileSelection();
  const { upload, started, isUploading, error } = useAdditionalUpload(inquiryId);
  const progress = useAgentProgress(started ? inquiryId : null);
  const detailQuery = useInquiryDetail(inquiryId);

  const inquiry = detailQuery.data?.status === 200 ? detailQuery.data.data.inquiry : null;
  const targetLabel = inquiry
    ? `${[inquiry.requester, inquiry.project_name].filter(Boolean).join(" - ")}（${inquiry.inquiry_code}）`
    : "";

  // 追加解析が完了したら引合詳細（SCR-03）へ戻る
  useEffect(() => {
    if (started && progress.stage === "completed") {
      const timer = setTimeout(() => router.push(`/inquiries/${inquiryId}`), 800);
      return () => clearTimeout(timer);
    }
  }, [started, progress.stage, router, inquiryId]);

  return (
    <UploadForm
      title={t("upload.addTitle")}
      subtitle={t("upload.addSubtitle")}
      submitLabel={t("upload.startAdd")}
      files={files}
      rejectedNames={rejectedNames}
      onAddFiles={addFiles}
      onRemoveFile={removeFile}
      onSubmit={() => void upload(files)}
      isSubmitting={isUploading}
      errorMessage={error}
      header={
        targetLabel ? (
          <Typography variant="body2" sx={{ mb: 2, color: tokens.colors.text.secondary }}>
            {t("upload.targetInquiry")}: <strong>{targetLabel}</strong>
          </Typography>
        ) : null
      }
      progress={
        !started
          ? null
          : {
              percent: progress.progressPercent,
              label: t(progress.labelKey),
              isFailure: progress.isFailure,
              errorMessage: progress.errorMessage,
            }
      }
      footer={
        <Button
          sx={{ mt: 2 }}
          variant="text"
          color="inherit"
          onClick={() => router.push(`/inquiries/${inquiryId}`)}
        >
          {t("upload.goToDetail")}
        </Button>
      }
    />
  );
}
