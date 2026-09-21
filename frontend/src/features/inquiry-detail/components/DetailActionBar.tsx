"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControlLabel,
  Radio,
  RadioGroup,
} from "@mui/material";

interface Props {
  inquiryId: number;
  isFinal: boolean;
  onConfirm: () => Promise<boolean>;
  onExport: () => Promise<boolean>;
  isConfirming: boolean;
  isExporting: boolean;
  error: string | null;
}

/**
 * SCR-03 下部のアクションバー（mockup: 資料を追加 / 出力する / 確定する）。
 * 「出力する」は確定済みのときのみ表示する。出力形式はScope 1ではExcelのみ選択可能で、
 * Word/PDFは選択不可の状態で表示する（Scope 2）。
 */
export function DetailActionBar({
  inquiryId,
  isFinal,
  onConfirm,
  onExport,
  isConfirming,
  isExporting,
  error,
}: Props) {
  const { t } = useTranslation();
  const router = useRouter();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [exported, setExported] = useState(false);

  return (
    <Box sx={{ mt: 3 }}>
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {t(error)}
        </Alert>
      ) : null}
      {exported ? (
        <Alert severity="success" sx={{ mb: 2 }}>
          {t("detail.exportDone")}
        </Alert>
      ) : null}

      <Box sx={{ display: "flex", gap: 1 }}>
        <Button
          variant="outlined"
          color="inherit"
          onClick={() => router.push(`/inquiries/${inquiryId}/add-files`)}
        >
          {t("detail.addFiles")}
        </Button>

        {isFinal ? (
          <Button variant="contained" onClick={() => setExportOpen(true)}>
            {t("detail.export")}
          </Button>
        ) : (
          <Button variant="contained" onClick={() => setConfirmOpen(true)}>
            {t("detail.confirm")}
          </Button>
        )}
      </Box>

      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)}>
        <DialogTitle>{t("detail.confirmModalTitle")}</DialogTitle>
        <DialogContent>
          <DialogContentText>{t("detail.confirmModalBody")}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmOpen(false)}>
            {t("detail.confirmModalCancel")}
          </Button>
          <Button
            variant="contained"
            disabled={isConfirming}
            onClick={async () => {
              const ok = await onConfirm();
              if (ok) setConfirmOpen(false);
            }}
          >
            {t("detail.confirmModalOk")}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={exportOpen} onClose={() => setExportOpen(false)}>
        <DialogTitle>{t("detail.exportModalTitle")}</DialogTitle>
        <DialogContent>
          <RadioGroup defaultValue="excel">
            <FormControlLabel
              value="excel"
              control={<Radio />}
              label={t("detail.exportModalExcel")}
            />
            <FormControlLabel
              value="word"
              disabled
              control={<Radio />}
              label={t("detail.exportModalWord")}
            />
            <FormControlLabel
              value="pdf"
              disabled
              control={<Radio />}
              label={t("detail.exportModalPdf")}
            />
          </RadioGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportOpen(false)}>
            {t("detail.confirmModalCancel")}
          </Button>
          <Button
            variant="contained"
            disabled={isExporting}
            onClick={async () => {
              const ok = await onExport();
              setExported(ok);
              if (ok) setExportOpen(false);
            }}
          >
            {t("detail.exportModalStart")}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
