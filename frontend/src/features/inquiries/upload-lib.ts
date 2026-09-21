/** アップロード画面（SCR-02 / SCR-05）の決定的ロジック。UIから切り離してテストする。 */

export const SUPPORTED_EXTENSIONS = ["xlsx", "pdf", "eml"] as const;

export type AgentStage =
  | "uploading"
  | "extracting"
  | "structuring"
  | "reviewing"
  | "completed"
  | "failed"
  | "stopped";

/** stage → 進捗バーの％（agent-plan.md §2 stage表の目安に対応）。 */
export const STAGE_PROGRESS: Record<AgentStage, number> = {
  uploading: 10,
  extracting: 40,
  structuring: 65,
  reviewing: 85,
  completed: 100,
  failed: 100,
  stopped: 100,
};

/** stage → i18nキー（mockup.html startUploadDemo のラベル遷移に対応）。 */
export const STAGE_LABEL_KEY: Record<AgentStage, string> = {
  uploading: "upload.stageUploading",
  extracting: "upload.stageExtracting",
  structuring: "upload.stageStructuring",
  reviewing: "upload.stageReviewing",
  completed: "upload.stageCompleted",
  failed: "upload.stageFailed",
  stopped: "upload.stageStopped",
};

export function extensionOf(fileName: string): string {
  return fileName.includes(".") ? fileName.split(".").pop()!.toLowerCase() : "";
}

export function isSupportedFile(fileName: string): boolean {
  return (SUPPORTED_EXTENSIONS as readonly string[]).includes(extensionOf(fileName));
}

export interface FileSelection {
  accepted: File[];
  rejectedNames: string[];
}

/** 選択されたファイルを対応形式／非対応形式に振り分ける（FUNC-01: 非対応はアップロード時点で拒否）。 */
export function partitionFiles(files: File[]): FileSelection {
  const accepted: File[] = [];
  const rejectedNames: string[] = [];
  for (const file of files) {
    if (isSupportedFile(file.name)) {
      accepted.push(file);
    } else {
      rejectedNames.push(file.name);
    }
  }
  return { accepted, rejectedNames };
}

/** 進捗表示が完了しているか（completed / failed / stopped はポーリング停止条件）。 */
export function isTerminalStage(stage: AgentStage | undefined): boolean {
  return stage === "completed" || stage === "failed" || stage === "stopped";
}
