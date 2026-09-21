"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { Button } from "@mui/material";
import { useAgentProgress, useFileSelection, useNewUpload } from "../upload-hooks";
import { UploadForm } from "./UploadForm";

/** SCR-02 書類アップロード（FUNC-01 新規アップロード）。 */
export function NewUploadPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { files, rejectedNames, addFiles, removeFile } = useFileSelection();
  const { upload, inquiryId, isUploading, error } = useNewUpload();
  const progress = useAgentProgress(inquiryId);

  // 完了したら引合詳細（SCR-03）へ遷移する（mockup: 完了後にSCR-03を表示）
  useEffect(() => {
    if (inquiryId !== null && progress.stage === "completed") {
      const timer = setTimeout(() => router.push(`/inquiries/${inquiryId}`), 800);
      return () => clearTimeout(timer);
    }
  }, [inquiryId, progress.stage, router]);

  return (
    <UploadForm
      title={t("upload.title")}
      subtitle={t("upload.subtitle")}
      submitLabel={t("upload.startUpload")}
      files={files}
      rejectedNames={rejectedNames}
      onAddFiles={addFiles}
      onRemoveFile={removeFile}
      onSubmit={() => void upload(files)}
      isSubmitting={isUploading}
      errorMessage={error}
      progress={
        inquiryId === null
          ? null
          : {
              percent: progress.progressPercent,
              label: t(progress.labelKey),
              isFailure: progress.isFailure,
              errorMessage: progress.errorMessage,
            }
      }
      footer={
        inquiryId !== null && progress.isTerminal ? (
          <Button
            sx={{ mt: 2 }}
            variant="outlined"
            color="inherit"
            onClick={() => router.push(`/inquiries/${inquiryId}`)}
          >
            {t("upload.goToDetail")}
          </Button>
        ) : null
      }
    />
  );
}
