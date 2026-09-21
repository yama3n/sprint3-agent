"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  Chip,
  Paper,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";
import { Badge } from "@/shared/ui";
import { tokens } from "@/shared/theme/tokens";
import { formatDateTime } from "@/shared/lib/format-date";
import { useInquiryDetail, type FieldRead, type NoteRead } from "../api";
import { FieldValueCell } from "./FieldValueCell";

interface Props {
  inquiryId: number;
  /** 項目クリック時にInspector（SCR-04）を開く。Phase 10で接続する。 */
  onOpenField?: (field: FieldRead, itemNo?: number) => void;
  onOpenOverview?: () => void;
}

function NotesList({ notes }: { notes: NoteRead[] }) {
  const { t } = useTranslation();
  if (notes.length === 0) {
    return (
      <Typography variant="body2" sx={{ color: tokens.colors.text.meta, p: 2 }}>
        {t("detail.notesEmpty")}
      </Typography>
    );
  }
  return (
    <Box sx={{ p: 2, display: "flex", flexDirection: "column", gap: 1.5 }}>
      {notes.map((note) => (
        <Box key={note.id}>
          <Typography variant="body2">{note.content}</Typography>
          {note.source_file ? (
            <Typography variant="caption" sx={{ color: tokens.colors.text.meta }}>
              {note.source_file}
              {note.source_location ? ` ${note.source_location}` : ""}
            </Typography>
          ) : null}
        </Box>
      ))}
    </Box>
  );
}

/** SCR-03 引合詳細（サマリー・確認）。mockup.html #SCR-03 の移植。 */
export function InquiryDetailPage({ inquiryId, onOpenField, onOpenOverview }: Props) {
  const { t } = useTranslation();
  const router = useRouter();
  const query = useInquiryDetail(inquiryId);
  const [noteTab, setNoteTab] = useState(0);

  if (query.isLoading) {
    return (
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Skeleton variant="text" height={36} />
        <Skeleton variant="text" height={36} />
        <Skeleton variant="rectangular" height={180} sx={{ mt: 2 }} />
      </Paper>
    );
  }

  if (query.isError || query.data?.status !== 200) {
    return (
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Typography color="error.main" sx={{ fontWeight: 600, mb: 0.5 }}>
          {t("detail.loadError")}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t("common.error")}
        </Typography>
      </Paper>
    );
  }

  const detail = query.data.data;
  const { inquiry, case_fields, items, case_notes, review_summary } = detail;
  const itemNotes = items.flatMap((item) => item.notes ?? []);
  const isFinal = inquiry.status === "final";

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          mb: 2,
        }}
      >
        <Box>
          <Typography variant="h1" sx={{ fontSize: 22, fontWeight: 700 }}>
            {[inquiry.requester, inquiry.project_name].filter(Boolean).join(" - ") ||
              inquiry.inquiry_code}
          </Typography>
          <Typography variant="caption" sx={{ color: tokens.colors.text.meta }}>
            {t("detail.inquiryCode")}: {inquiry.inquiry_code}　{t("detail.requestedAt")}:{" "}
            {formatDateTime(inquiry.requested_at) || "—"}
          </Typography>
        </Box>
        <Badge variant={isFinal ? "success" : "neutral"} withDot>
          {isFinal ? t("detail.statusFinal") : t("detail.statusConfirming")}
        </Badge>
      </Box>

      <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
        <Chip
          size="small"
          clickable
          onClick={onOpenOverview}
          label={`${t("detail.summaryReview")} ${review_summary.review_count}`}
          sx={{
            bgcolor: tokens.colors.status.review.bg,
            color: tokens.colors.status.review.text,
            border: `1px solid ${tokens.colors.status.review.border}`,
          }}
        />
        <Chip
          size="small"
          label={`${t("detail.summaryWeb")} ${review_summary.web_supplemented_count}`}
          sx={{
            bgcolor: tokens.colors.status.web.bg,
            color: tokens.colors.status.web.text,
            border: `1px solid ${tokens.colors.status.web.border}`,
          }}
        />
      </Box>

      <Typography variant="h2" sx={{ fontSize: 16, fontWeight: 700, mb: 1 }}>
        {t("detail.caseSummary")}
      </Typography>
      <Paper variant="outlined" sx={{ mb: 3 }}>
        <Table size="small">
          <TableBody>
            {case_fields.map((field) => (
              <TableRow
                key={field.field_id}
                hover
                sx={{ cursor: onOpenField ? "pointer" : "default" }}
                onClick={() => onOpenField?.(field)}
              >
                <TableCell sx={{ width: 220, color: tokens.colors.text.secondary }}>
                  {field.label}
                </TableCell>
                <TableCell>
                  <FieldValueCell field={field} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Typography variant="h2" sx={{ fontSize: 16, fontWeight: 700, mb: 1 }}>
        {t("detail.itemList")}
      </Typography>
      <Paper variant="outlined" sx={{ mb: 3, overflowX: "auto" }}>
        {items.length === 0 ? (
          <Typography variant="body2" sx={{ color: tokens.colors.text.meta, p: 2 }}>
            {t("detail.itemsEmpty")}
          </Typography>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t("detail.itemNo")}</TableCell>
                {items[0].fields.map((field) => (
                  <TableCell key={field.field_id}>{field.label}</TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((item) => (
                <TableRow key={item.id} hover>
                  <TableCell>{item.item_no}</TableCell>
                  {item.fields.map((field) => (
                    <TableCell
                      key={field.field_id}
                      onClick={() => onOpenField?.(field, item.item_no)}
                      sx={{ cursor: onOpenField ? "pointer" : "default" }}
                    >
                      <FieldValueCell field={field} />
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>

      <Typography variant="h2" sx={{ fontSize: 16, fontWeight: 700, mb: 1 }}>
        {t("detail.notes")}
      </Typography>
      <Paper variant="outlined" sx={{ mb: 3 }}>
        <Tabs value={noteTab} onChange={(_, v) => setNoteTab(v)}>
          <Tab label={t("detail.notesCase")} />
          <Tab label={t("detail.notesItem")} />
        </Tabs>
        {noteTab === 0 ? <NotesList notes={case_notes} /> : <NotesList notes={itemNotes} />}
      </Paper>

      <Box sx={{ display: "flex", gap: 1 }}>
        <Button
          variant="outlined"
          color="inherit"
          onClick={() => router.push(`/inquiries/${inquiryId}/add-files`)}
        >
          {t("detail.addFiles")}
        </Button>
      </Box>
    </Box>
  );
}
