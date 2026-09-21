"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { Badge } from "@/shared/ui";
import { tokens } from "@/shared/theme/tokens";
import { formatDateTime } from "@/shared/lib/format-date";
import type { CandidateRead, FieldRead } from "../api";
import {
  groupReviewEntries,
  inspectorModeOf,
  reasonLabelKeyOf,
  type ReviewEntry,
} from "../inspector-lib";

export type InspectorState =
  | { mode: "closed" }
  | { mode: "overview" }
  | { mode: "field"; field: FieldRead; itemNo?: number; itemId?: number };

interface Props {
  state: InspectorState;
  reviewEntries: ReviewEntry<FieldRead>[];
  onClose: () => void;
  onBackToOverview: () => void;
  onSelectEntry: (entry: ReviewEntry<FieldRead>) => void;
  onConfirm: (params: {
    field: FieldRead;
    itemId?: number;
    value: string;
    selectedCandidateId?: number;
  }) => Promise<boolean>;
  isSaving: boolean;
  saveError: string | null;
}

function SourceLine({ candidate }: { candidate: CandidateRead }) {
  const { t } = useTranslation();
  if (candidate.source_type === "web") {
    return (
      <Box>
        <Typography variant="caption" sx={{ color: tokens.colors.text.meta, display: "block" }}>
          {t("inspector.sourceWeb")}: {candidate.web_source_name} ({candidate.web_url})
        </Typography>
        {candidate.web_referenced_at ? (
          <Typography variant="caption" sx={{ color: tokens.colors.text.meta }}>
            {t("inspector.referencedAt")}: {formatDateTime(candidate.web_referenced_at)}
          </Typography>
        ) : null}
      </Box>
    );
  }
  return (
    <Typography variant="caption" sx={{ color: tokens.colors.text.meta, display: "block" }}>
      {t("inspector.source")}: {candidate.source_file}
      {candidate.source_location ? ` ${candidate.source_location}` : ""}
    </Typography>
  );
}

function CandidateCard({
  candidate,
  isEditable,
  isActive,
  onUse,
}: {
  candidate: CandidateRead;
  isEditable: boolean;
  isActive: boolean;
  onUse: () => void;
}) {
  const { t } = useTranslation();
  return (
    <Paper
      variant="outlined"
      sx={{
        p: 1.5,
        mb: 1,
        borderColor: isActive ? tokens.colors.main[500] : tokens.colors.border,
      }}
    >
      <Box sx={{ display: "flex", justifyContent: "space-between", gap: 1 }}>
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {candidate.value}
        </Typography>
        {candidate.source_type === "web" ? (
          <Badge variant="web">{t("detail.webSupplemented")}</Badge>
        ) : null}
      </Box>
      {candidate.quoted_text ? (
        <Typography variant="caption" sx={{ display: "block", mt: 0.5 }}>
          {candidate.quoted_text}
        </Typography>
      ) : null}
      <SourceLine candidate={candidate} />
      {candidate.is_explicit_correction && candidate.superseded_value ? (
        <Typography variant="caption" sx={{ color: tokens.colors.status.review.text }}>
          {t("inspector.correctedFrom", { value: candidate.superseded_value })}
        </Typography>
      ) : null}
      {isEditable ? (
        <Button size="small" sx={{ mt: 1 }} onClick={onUse} disabled={isActive}>
          {isActive ? t("inspector.selected") : t("inspector.useCandidate")}
        </Button>
      ) : null}
    </Paper>
  );
}


/** 1項目分の詳細（根拠確認モード / 確認・修正モード）。項目切替時はkeyで再マウントされる。 */
function FieldDetail({
  field,
  itemId,
  onConfirm,
  isSaving,
  saveError,
}: {
  field: FieldRead;
  itemId?: number;
  onConfirm: Props["onConfirm"];
  isSaving: boolean;
  saveError: string | null;
}) {
  const { t } = useTranslation();
  const editable = inspectorModeOf(field) === "review";
  const [draftValue, setDraftValue] = useState(field.value ?? "");
  const [selectedCandidateId, setSelectedCandidateId] = useState<number | undefined>(
    field.candidates?.find((c) => c.is_selected)?.id,
  );
  const [justConfirmed, setJustConfirmed] = useState(false);
  const reasonKey = reasonLabelKeyOf(field);

  return (
    <Box>
      <Typography
        variant="caption"
        sx={{
          color: editable ? tokens.colors.status.review.text : tokens.colors.text.meta,
          fontWeight: 700,
        }}
      >
        {editable ? t("inspector.eyebrowReview") : t("inspector.eyebrowEvidence")}
      </Typography>
      {editable && reasonKey ? (
        <Typography variant="body2" sx={{ mb: 1 }}>
          {t(reasonKey)}
        </Typography>
      ) : null}

      <Divider sx={{ my: 1.5 }} />

      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        {t("inspector.candidates")}
      </Typography>
      {(field.candidates ?? []).length === 0 ? (
        <Typography variant="body2" sx={{ color: tokens.colors.text.meta, mb: 2 }}>
          {t("inspector.noCandidates")}
        </Typography>
      ) : (
        (field.candidates ?? []).map((candidate) => (
          <CandidateCard
            key={candidate.id}
            candidate={candidate}
            isEditable={editable}
            isActive={selectedCandidateId === candidate.id}
            onUse={() => {
              setSelectedCandidateId(candidate.id);
              setDraftValue(candidate.value);
            }}
          />
        ))
      )}

      {editable ? (
        <Box sx={{ mt: 2 }}>
          <TextField
            label={t("inspector.confirmedValue")}
            value={draftValue}
            onChange={(e) => {
              setDraftValue(e.target.value);
              setSelectedCandidateId(undefined);
            }}
            fullWidth
            size="small"
          />
          {draftValue === "" ? (
            <Alert severity="warning" sx={{ mt: 1 }}>
              {t("inspector.emptyConfirmWarning")}
            </Alert>
          ) : null}
          {saveError ? (
            <Alert severity="error" sx={{ mt: 1 }}>
              {t(saveError)}
            </Alert>
          ) : null}
          {justConfirmed ? (
            <Alert severity="success" sx={{ mt: 1 }}>
              {t("inspector.confirmed")}
            </Alert>
          ) : null}
          <Button
            variant="contained"
            sx={{ mt: 1.5 }}
            disabled={isSaving}
            onClick={async () => {
              const ok = await onConfirm({
                field,
                itemId,
                value: draftValue,
                selectedCandidateId,
              });
              setJustConfirmed(ok);
            }}
          >
            {t("inspector.confirmButton")}
          </Button>
        </Box>
      ) : null}
    </Box>
  );
}

/** SCR-04 根拠確認Inspector（右スライド式サイドパネル、暗転オーバーレイなし）。 */
export function InspectorPanel({
  state,
  reviewEntries,
  onClose,
  onBackToOverview,
  onSelectEntry,
  onConfirm,
  isSaving,
  saveError,
}: Props) {
  const { t } = useTranslation();
  const field = state.mode === "field" ? state.field : null;

  return (
    <Drawer
      anchor="right"
      open={state.mode !== "closed"}
      onClose={onClose}
      hideBackdrop
      variant="persistent"
      PaperProps={{
        sx: {
          width: "min(34vw, 620px)",
          minWidth: 380,
          borderLeft: `1px solid ${tokens.colors.border}`,
          p: 2,
        },
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
        {state.mode === "field" ? (
          <IconButton size="small" aria-label={t("inspector.back")} onClick={onBackToOverview}>
            <ArrowBackIcon fontSize="small" />
          </IconButton>
        ) : null}
        <Typography sx={{ flex: 1, fontWeight: 700 }}>
          {state.mode === "overview"
            ? t("inspector.overviewTitle")
            : (field?.label ?? "")}
        </Typography>
        <IconButton size="small" aria-label={t("inspector.close")} onClick={onClose}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>

      {state.mode === "overview" ? (
        <Box>
          {reviewEntries.length === 0 ? (
            <Typography variant="body2" sx={{ color: tokens.colors.text.meta }}>
              {t("inspector.overviewEmpty")}
            </Typography>
          ) : (
            groupReviewEntries(reviewEntries).map((group) => (
              <Box key={group.reasonType} sx={{ mb: 2 }}>
                <Typography
                  variant="caption"
                  sx={{ color: tokens.colors.status.review.text, fontWeight: 700 }}
                >
                  {t(group.reasonKey)}
                </Typography>
                {group.entries.map((entry) => (
                  <Button
                    key={`${entry.field.field_id}-${entry.itemNo ?? "case"}`}
                    fullWidth
                    color="inherit"
                    sx={{ justifyContent: "flex-start" }}
                    onClick={() => onSelectEntry(entry)}
                  >
                    {entry.itemNo
                      ? `${t("inspector.itemLabel", { itemNo: entry.itemNo })} / ${entry.field.label}`
                      : entry.field.label}
                  </Button>
                ))}
              </Box>
            ))
          )}
        </Box>
      ) : null}

      {state.mode === "field" && field ? (
        <FieldDetail
          // field_idをkeyにすることで、項目を切り替えたときに入力状態が自然に初期化される
          // （useEffect + setStateでの同期を避ける）
          key={`${field.field_id}-${state.itemNo ?? "case"}`}
          field={field}
          itemId={state.itemId}
          onConfirm={onConfirm}
          isSaving={isSaving}
          saveError={saveError}
        />
      ) : null}
    </Drawer>
  );
}
