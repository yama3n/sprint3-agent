"use client";

import { useTranslation } from "react-i18next";
import { Box, Typography } from "@mui/material";
import { Badge } from "@/shared/ui";
import { tokens } from "@/shared/theme/tokens";
import { toFieldDisplay, type FieldLike } from "../detail-lib";

/** mockup #SCR-03 の val-cell。確認不要は値のみ、要確認は単一色のバッジ＋理由ヒント。 */
export function FieldValueCell({ field }: { field: FieldLike }) {
  const { t } = useTranslation();
  const display = toFieldDisplay(field);

  if (display.kind === "review") {
    return (
      <Box sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}>
        <Badge variant="review">{t("detail.needsReview")}</Badge>
        {display.candidateCount > 0 ? (
          <Typography variant="caption" sx={{ color: tokens.colors.text.meta }}>
            {t("detail.candidateCount", { count: display.candidateCount })}
          </Typography>
        ) : display.reasonKey ? (
          <Typography variant="caption" sx={{ color: tokens.colors.text.meta }}>
            {t(display.reasonKey)}
          </Typography>
        ) : null}
      </Box>
    );
  }

  if (display.kind === "empty") {
    return <Typography variant="body2" sx={{ color: tokens.colors.text.meta }}>—</Typography>;
  }

  return (
    <Box sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}>
      <Typography variant="body2">{display.value}</Typography>
      {display.isWebSupplemented ? (
        <Badge variant="web">{t("detail.webSupplemented")}</Badge>
      ) : null}
    </Box>
  );
}
