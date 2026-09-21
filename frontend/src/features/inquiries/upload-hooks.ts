"use client";

import { useCallback, useMemo, useState } from "react";
import { useAddFiles, useAgentStatusQuery, useCreateInquiry } from "./api";
import {
  isTerminalStage,
  partitionFiles,
  STAGE_LABEL_KEY,
  STAGE_PROGRESS,
  type AgentStage,
} from "./upload-lib";

/** 選択ファイルの保持と対応形式チェック（SCR-02 / SCR-05 共通）。 */
export function useFileSelection() {
  const [files, setFiles] = useState<File[]>([]);
  const [rejectedNames, setRejectedNames] = useState<string[]>([]);

  const addFiles = useCallback((incoming: File[]) => {
    const { accepted, rejectedNames: rejected } = partitionFiles(incoming);
    setRejectedNames(rejected);
    if (accepted.length > 0) {
      setFiles((prev) => [...prev, ...accepted]);
    }
  }, []);

  const removeFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const clear = useCallback(() => {
    setFiles([]);
    setRejectedNames([]);
  }, []);

  return { files, rejectedNames, addFiles, removeFile, clear };
}

/**
 * agent-statusのポーリング（05-api-ipo.md: POST 202 → GET でポーリング）。
 * 完了・失敗・強制停止に達したらポーリングを止める。
 */
export function useAgentProgress(inquiryId: number | null) {
  const query = useAgentStatusQuery(inquiryId ?? 0, {
    query: {
      enabled: inquiryId !== null,
      refetchInterval: (query) => {
        const data = query.state.data;
        const stage = data?.status === 200 ? (data.data.stage as AgentStage) : undefined;
        return isTerminalStage(stage) ? false : 2000;
      },
    },
  });

  const stage: AgentStage | undefined =
    query.data?.status === 200 ? (query.data.data.stage as AgentStage) : undefined;

  return useMemo(
    () => ({
      stage,
      progressPercent:
        query.data?.status === 200
          ? query.data.data.progress_percent
          : stage
            ? STAGE_PROGRESS[stage]
            : 0,
      labelKey: stage ? STAGE_LABEL_KEY[stage] : "upload.waiting",
      errorMessage:
        query.data?.status === 200 ? (query.data.data.error_message ?? null) : null,
      isTerminal: isTerminalStage(stage),
      isFailure: stage === "failed" || stage === "stopped",
    }),
    [query.data, stage],
  );
}

/** SCR-02: 新規アップロード（POST /inquiries）。 */
export function useNewUpload() {
  const mutation = useCreateInquiry();
  const [inquiryId, setInquiryId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(
    async (files: File[]) => {
      setError(null);
      try {
        const result = await mutation.mutateAsync({ data: { files } });
        if (result.status === 202) {
          setInquiryId(result.data.inquiry_id);
          return result.data.inquiry_id;
        }
        setError("upload.uploadError");
        return null;
      } catch {
        setError("upload.uploadError");
        return null;
      }
    },
    [mutation],
  );

  return { upload, inquiryId, isUploading: mutation.isPending, error };
}

/** SCR-05: 既存引合への資料追加（POST /inquiries/{id}/files）。 */
export function useAdditionalUpload(inquiryId: number) {
  const mutation = useAddFiles();
  const [started, setStarted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(
    async (files: File[]) => {
      setError(null);
      try {
        const result = await mutation.mutateAsync({ inquiryId, data: { files } });
        if (result.status === 202) {
          setStarted(true);
          return true;
        }
        setError("upload.uploadError");
        return false;
      } catch {
        setError("upload.uploadError");
        return false;
      }
    },
    [mutation, inquiryId],
  );

  return { upload, started, isUploading: mutation.isPending, error };
}
