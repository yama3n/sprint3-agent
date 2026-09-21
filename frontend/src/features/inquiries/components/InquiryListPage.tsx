"use client";

import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  Paper,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { Badge } from "@/shared/ui";
import { tokens } from "@/shared/theme/tokens";
import { formatDateTime } from "@/shared/lib/format-date";
import { useInquiryListPage, type InquiryFilter } from "../hooks";

const FILTER_TABS: { key: InquiryFilter; labelKey: string; countKey: "all" | "draft" | "final" }[] = [
  { key: "all", labelKey: "inquiryList.filterAll", countKey: "all" },
  { key: "draft", labelKey: "inquiryList.filterConfirming", countKey: "draft" },
  { key: "final", labelKey: "inquiryList.filterFinal", countKey: "final" },
];

export function InquiryListPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { isLoading, isError, filter, setFilter, counts, visibleItems, emptyState } =
    useInquiryListPage();

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
        <Typography variant="h1" sx={{ fontSize: 22, fontWeight: 700 }}>
          {t("inquiryList.title")}
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => router.push("/inquiries/upload")}
        >
          {t("inquiryList.uploadButton")}
        </Button>
      </Box>

      <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
        {FILTER_TABS.map((tab) => (
          <Button
            key={tab.key}
            variant={filter === tab.key ? "contained" : "outlined"}
            color={filter === tab.key ? "primary" : "inherit"}
            size="small"
            onClick={() => setFilter(tab.key)}
          >
            {t(tab.labelKey)}（{counts[tab.countKey]}）
          </Button>
        ))}
      </Box>

      {isLoading ? (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Skeleton variant="text" width="100%" height={32} />
          <Skeleton variant="text" width="100%" height={32} />
          <Skeleton variant="text" width="100%" height={32} />
        </Paper>
      ) : isError ? (
        <Paper variant="outlined" sx={{ p: 3 }}>
          <Typography color="error.main" sx={{ fontWeight: 600, mb: 0.5 }}>
            {t("inquiryList.loadError")}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t("common.error")}
          </Typography>
        </Paper>
      ) : emptyState.kind === "none" ? (
        <Paper
          variant="outlined"
          sx={{ p: 6, display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}
        >
          <Typography sx={{ color: tokens.colors.text.secondary }}>
            {t("inquiryList.emptyTitleNone")}
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => router.push("/inquiries/upload")}
          >
            {t("inquiryList.emptyCta")}
          </Button>
        </Paper>
      ) : emptyState.kind === "filtered" ? (
        <Paper variant="outlined" sx={{ p: 6, textAlign: "center" }}>
          <Typography sx={{ color: tokens.colors.text.secondary }}>
            {t("inquiryList.emptyTitleFiltered", {
              label: t(
                emptyState.filter === "draft"
                  ? "inquiryList.filterConfirming"
                  : "inquiryList.filterFinal",
              ),
            })}
          </Typography>
        </Paper>
      ) : (
        <Paper variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t("inquiryList.columnRequester")}</TableCell>
                <TableCell>{t("inquiryList.columnProjectName")}</TableCell>
                <TableCell>{t("inquiryList.columnRequestedAt")}</TableCell>
                <TableCell>{t("inquiryList.columnStatus")}</TableCell>
                <TableCell>{t("inquiryList.columnReview")}</TableCell>
                <TableCell>{t("inquiryList.columnUpdatedAt")}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {visibleItems.map((item) => (
                <TableRow
                  key={item.id}
                  hover
                  sx={{ cursor: "pointer" }}
                  onClick={() => router.push(`/inquiries/${item.id}`)}
                >
                  <TableCell>{item.requester}</TableCell>
                  <TableCell>{item.project_name}</TableCell>
                  <TableCell>{formatDateTime(item.requested_at)}</TableCell>
                  <TableCell>
                    {item.status === "final" ? (
                      <Badge variant="success" withDot>
                        {t("inquiryList.statusFinal")}
                      </Badge>
                    ) : (
                      <Badge variant="neutral" withDot>
                        {t("inquiryList.statusConfirming")}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    {item.review_count > 0 ? (
                      <Button
                        size="small"
                        variant="text"
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/inquiries/${item.id}?inspector=overview`);
                        }}
                      >
                        {item.review_count}
                        {t("inquiryList.reviewCountUnit")}
                      </Button>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        0{t("inquiryList.reviewCountUnit")}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>{formatDateTime(item.updated_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </Box>
  );
}
