"use client";

import { useRef, useState, type DragEvent, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  Chip,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  Paper,
  Typography,
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import { tokens } from "@/shared/theme/tokens";

interface UploadFormProps {
  title: string;
  subtitle: string;
  submitLabel: string;
  files: File[];
  rejectedNames: string[];
  onAddFiles: (files: File[]) => void;
  onRemoveFile: (index: number) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
  /** アップロード後の進捗表示（未開始ならnull） */
  progress: {
    percent: number;
    label: string;
    isFailure: boolean;
    errorMessage: string | null;
  } | null;
  errorMessage?: string | null;
  /** 対象引合の表示など、フォーム上部に差し込む要素（SCR-05用） */
  header?: ReactNode;
  footer?: ReactNode;
}

/** mockup.html #SCR-02 のアップロードUI。SCR-02（新規）とSCR-05（追加）で共用する。 */
export function UploadForm({
  title,
  subtitle,
  submitLabel,
  files,
  rejectedNames,
  onAddFiles,
  onRemoveFile,
  onSubmit,
  isSubmitting,
  progress,
  errorMessage,
  header,
  footer,
}: UploadFormProps) {
  const { t } = useTranslation();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragOver(false);
    onAddFiles(Array.from(event.dataTransfer.files));
  }

  return (
    <Box sx={{ maxWidth: 760 }}>
      <Typography variant="h1" sx={{ fontSize: 22, fontWeight: 700, mb: 0.5 }}>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {subtitle}
      </Typography>

      {header}

      <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
        <Chip size="small" variant="outlined" label={t("upload.chipExcel")} />
        <Chip size="small" variant="outlined" label={t("upload.chipPdf")} />
        <Chip size="small" variant="outlined" label={t("upload.chipEml")} />
      </Box>

      <Paper
        variant="outlined"
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        sx={{
          p: 5,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 1,
          borderStyle: isDragOver ? "solid" : "dashed",
          borderColor: isDragOver ? tokens.colors.main[500] : tokens.colors.borderStrong,
          bgcolor: isDragOver ? tokens.colors.surface2 : tokens.colors.surface,
        }}
      >
        <CloudUploadIcon sx={{ color: tokens.colors.text.primary }} />
        <Typography sx={{ fontWeight: 600 }}>{t("upload.dropzoneMain")}</Typography>
        <Typography variant="body2" color="text.secondary">
          {t("upload.dropzoneOr")}
        </Typography>
        <Button variant="outlined" color="inherit" onClick={() => inputRef.current?.click()}>
          {t("upload.selectFiles")}
        </Button>
        <input
          ref={inputRef}
          type="file"
          multiple
          hidden
          aria-label={t("upload.selectFiles")}
          onChange={(event) => {
            onAddFiles(Array.from(event.target.files ?? []));
            event.target.value = "";
          }}
        />
      </Paper>

      {rejectedNames.map((name) => (
        <Alert key={name} severity="warning" sx={{ mt: 2 }}>
          {t("upload.unsupportedFile", { name })}
        </Alert>
      ))}

      {errorMessage ? (
        <Alert severity="error" sx={{ mt: 2 }}>
          {t(errorMessage)}
        </Alert>
      ) : null}

      {files.length > 0 ? (
        <List dense sx={{ mt: 2 }}>
          {files.map((file, index) => (
            <ListItem
              key={`${file.name}-${index}`}
              divider
              secondaryAction={
                <IconButton
                  edge="end"
                  aria-label={`${file.name} ${t("upload.remove")}`}
                  onClick={() => onRemoveFile(index)}
                  disabled={isSubmitting}
                >
                  <DeleteOutlineIcon fontSize="small" />
                </IconButton>
              }
            >
              <Typography variant="body2">{file.name}</Typography>
            </ListItem>
          ))}
        </List>
      ) : null}

      <Box sx={{ display: "flex", alignItems: "center", gap: 3, mt: 3 }}>
        <Button
          variant="contained"
          onClick={onSubmit}
          disabled={files.length === 0 || isSubmitting || progress !== null}
        >
          {submitLabel}
        </Button>

        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              {progress ? progress.label : t("upload.waiting")}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {progress ? progress.percent : 0}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={progress ? progress.percent : 0}
            color={progress?.isFailure ? "error" : "primary"}
          />
        </Box>
      </Box>

      {progress?.isFailure ? (
        <Alert severity="error" sx={{ mt: 2 }}>
          {progress.errorMessage ?? progress.label}
        </Alert>
      ) : null}

      {footer}
    </Box>
  );
}
