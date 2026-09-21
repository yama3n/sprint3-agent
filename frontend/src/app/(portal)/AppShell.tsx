"use client";

import { useState, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Fab,
  IconButton,
  List,
  ListItemButton,
  Tooltip,
  Typography,
} from "@mui/material";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChecklistIcon from "@mui/icons-material/Checklist";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import SettingsIcon from "@mui/icons-material/Settings";
import LogoutIcon from "@mui/icons-material/Logout";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import DescriptionIcon from "@mui/icons-material/Description";
import { tokens } from "@/shared/theme/tokens";
import { useAuthStore } from "@/shared/lib/auth-store";
import { useToastStore } from "@/shared/ui/toast-store";
import { ToastHost } from "@/shared/ui/ToastHost";

interface NavItem {
  key: string;
  label: string;
  icon: ReactNode;
  href?: string;
  disabled?: boolean;
}

export function AppShell({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const router = useRouter();
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);
  const clearSession = useAuthStore((state) => state.clearSession);
  const showToast = useToastStore((state) => state.show);

  const [collapsed, setCollapsed] = useState(false);
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);

  const navItems: NavItem[] = [
    {
      key: "inquiries",
      label: t("shell.navInquiries"),
      icon: <ChecklistIcon fontSize="small" />,
      href: "/inquiries",
    },
    {
      key: "upload",
      label: t("shell.navUpload"),
      icon: <UploadFileIcon fontSize="small" />,
      href: "/inquiries/upload",
    },
    {
      key: "quotation",
      label: t("shell.navQuotation"),
      icon: <ReceiptLongIcon fontSize="small" />,
      disabled: true,
    },
    {
      key: "settings",
      label: t("shell.navSettings"),
      icon: <SettingsIcon fontSize="small" />,
      disabled: true,
    },
  ];

  function isNavActive(item: NavItem): boolean {
    if (!item.href || !pathname) return false;
    if (item.key === "upload") return pathname === "/inquiries/upload";
    if (item.key === "inquiries") {
      return (
        pathname === "/inquiries" ||
        (pathname.startsWith("/inquiries/") && pathname !== "/inquiries/upload")
      );
    }
    return pathname === item.href;
  }

  const breadcrumb =
    navItems.find((item) => isNavActive(item))?.label ??
    t("shell.navInquiries");

  function handleNavClick(item: NavItem) {
    if (item.disabled) {
      showToast(t("shell.comingSoon"));
      return;
    }
    if (item.href) {
      router.push(item.href);
    }
  }

  function handleLogout() {
    setLogoutDialogOpen(false);
    clearSession();
    router.push("/login");
  }

  const sidebarWidth = collapsed
    ? tokens.layout.sidebarWidthCollapsed
    : tokens.layout.sidebarWidth;

  return (
    <Box
      sx={{
        display: "flex",
        minHeight: "100vh",
        bgcolor: "background.default",
      }}
    >
      <Box
        component="aside"
        sx={{
          width: sidebarWidth,
          flexShrink: 0,
          background: tokens.colors.sidebar.gradient,
          color: tokens.colors.sidebar.text,
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          transition: "width 0.15s ease",
        }}
      >
        <Box sx={{ p: "12px 12px 8px" }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              justifyContent: collapsed ? "center" : "flex-start",
              px: collapsed ? 0 : 1,
              py: 1,
            }}
          >
            {!collapsed ? (
              <>
                <DescriptionIcon fontSize="small" />
                <Typography
                  sx={{
                    fontSize: 13,
                    fontWeight: 600,
                    lineHeight: 1.3,
                    letterSpacing: "-0.01em",
                    whiteSpace: "nowrap",
                    flexShrink: 0,
                  }}
                >
                  {t("shell.brandName")}
                </Typography>
              </>
            ) : null}
            <Tooltip title={t("shell.toggleSidebar")}>
              <IconButton
                size="small"
                onClick={() => setCollapsed((prev) => !prev)}
                sx={{ color: tokens.colors.sidebar.textDim }}
              >
                <ChevronLeftIcon
                  fontSize="small"
                  sx={{
                    transform: collapsed ? "rotate(180deg)" : "none",
                    transition: "transform .18s",
                  }}
                />
              </IconButton>
            </Tooltip>
          </Box>

          <List sx={{ mt: 0.5 }} component="nav">
            {navItems.map((item) => {
              const active = isNavActive(item);
              return (
                <Tooltip
                  key={item.key}
                  title={collapsed ? item.label : ""}
                  placement="right"
                >
                  <ListItemButton
                    onClick={() => handleNavClick(item)}
                    selected={active}
                    aria-current={active ? "page" : undefined}
                    sx={{
                      borderRadius: 1,
                      mb: 0.25,
                      color: item.disabled
                        ? tokens.colors.sidebar.textDim
                        : tokens.colors.sidebar.text,
                      justifyContent: collapsed ? "center" : "flex-start",
                      gap: 1.25,
                      "&:hover": {
                        bgcolor: tokens.colors.sidebar.hoverBg,
                        color: tokens.colors.sidebar.textHover,
                      },
                      "&.Mui-selected": {
                        bgcolor: tokens.colors.sidebar.activeBg,
                        color: tokens.colors.sidebar.textStrong,
                        fontWeight: 600,
                      },
                      "&.Mui-selected:hover": {
                        bgcolor: tokens.colors.sidebar.activeBg,
                      },
                    }}
                  >
                    {item.icon}
                    {!collapsed ? (
                      <Typography
                        sx={{ fontSize: 13.5, fontWeight: "inherit" }}
                      >
                        {item.label}
                      </Typography>
                    ) : null}
                  </ListItemButton>
                </Tooltip>
              );
            })}
          </List>
        </Box>

        <Box
          sx={{
            p: "12px 12px 16px",
            borderTop: `1px solid ${tokens.colors.sidebar.border}`,
          }}
        >
          {!collapsed ? (
            <Box
              sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}
            >
              <Box
                sx={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  bgcolor: tokens.colors.sidebar.hoverBg,
                  color: tokens.colors.sidebar.textStrong,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 12,
                  fontWeight: 700,
                  flexShrink: 0,
                }}
              >
                {user?.displayName?.[0] ?? ""}
              </Box>
              <Box sx={{ minWidth: 0 }}>
                <Typography
                  sx={{
                    fontSize: 12.5,
                    color: tokens.colors.sidebar.textStrong,
                    fontWeight: 600,
                  }}
                >
                  {user?.displayName}
                </Typography>
                <Typography
                  sx={{
                    fontSize: 11,
                    color: tokens.colors.sidebar.textDim,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {user?.email}
                </Typography>
              </Box>
            </Box>
          ) : null}
          <Tooltip title={collapsed ? t("shell.logout") : ""} placement="right">
            <ListItemButton
              onClick={() => setLogoutDialogOpen(true)}
              sx={{
                borderRadius: 1,
                border: `1px solid ${tokens.colors.sidebar.border}`,
                color: tokens.colors.sidebar.text,
                justifyContent: collapsed ? "center" : "flex-start",
                gap: 1,
                "&:hover": {
                  bgcolor: tokens.colors.sidebar.hoverBg,
                  color: tokens.colors.sidebar.textStrong,
                },
              }}
            >
              <LogoutIcon fontSize="small" />
              {!collapsed ? (
                <Typography sx={{ fontSize: 13 }}>
                  {t("shell.logout")}
                </Typography>
              ) : null}
            </ListItemButton>
          </Tooltip>
        </Box>
      </Box>

      <Box
        sx={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}
      >
        <Box
          component="header"
          sx={{
            height: tokens.layout.headerHeight,
            display: "flex",
            alignItems: "center",
            px: 3,
            borderBottom: `1px solid ${tokens.colors.border}`,
            bgcolor: tokens.colors.surface,
          }}
        >
          <Typography
            sx={{
              fontSize: 13.5,
              color: tokens.colors.text.secondary,
              fontWeight: 600,
            }}
          >
            {breadcrumb}
          </Typography>
        </Box>
        <Box component="main" sx={{ flex: 1, p: 3 }}>
          {children}
        </Box>
      </Box>

      <Fab
        size="medium"
        aria-label={t("shell.help")}
        onClick={() => showToast(t("shell.comingSoon"))}
        sx={{
          position: "fixed",
          bottom: 22,
          right: 22,
          bgcolor: tokens.colors.main[500],
          color: tokens.colors.onDark,
          "&:hover": { bgcolor: tokens.colors.main[700] },
        }}
      >
        <HelpOutlineIcon />
      </Fab>

      <ToastHost />

      <Dialog
        open={logoutDialogOpen}
        onClose={() => setLogoutDialogOpen(false)}
        PaperProps={{ sx: { minWidth: 460 } }}
      >
        <DialogTitle>{t("shell.logoutConfirmTitle")}</DialogTitle>
        <DialogContent>
          <DialogContentText component="div">
            <Typography
              component="span"
              sx={{ display: "block", whiteSpace: "nowrap" }}
            >
              {t("shell.logoutConfirmBodyLine1")}
            </Typography>
            <Typography
              component="span"
              sx={{ display: "block", whiteSpace: "nowrap" }}
            >
              {t("shell.logoutConfirmBodyLine2")}
            </Typography>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLogoutDialogOpen(false)}>
            {t("shell.cancel")}
          </Button>
          <Button onClick={handleLogout} variant="contained">
            {t("shell.logout")}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
