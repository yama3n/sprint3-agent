"use client";

import { useState, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import { tokens } from "@/shared/theme/tokens";
import "@/shared/i18n";

const theme = createTheme({
  palette: {
    primary: {
      light: tokens.colors.main[300],
      main: tokens.colors.main[500],
      dark: tokens.colors.main[700],
    },
    secondary: { main: tokens.colors.main[700] },
    error: { main: tokens.colors.error },
    background: {
      default: tokens.colors.background,
      paper: tokens.colors.surface,
    },
    text: {
      primary: tokens.colors.text.primary,
      secondary: tokens.colors.text.secondary,
    },
  },
  typography: {
    fontFamily: tokens.typography.fontBody,
    h1: { fontFamily: tokens.typography.fontHeading },
    h2: { fontFamily: tokens.typography.fontHeading },
    h3: { fontFamily: tokens.typography.fontHeading },
  },
  shape: { borderRadius: tokens.radius },
  components: {
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: { root: { textTransform: "none" } },
    },
    MuiCard: { defaultProps: { variant: "outlined" } },
  },
});

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: 1, refetchOnWindowFocus: false },
          mutations: { retry: 1 },
        },
      }),
  );

  return (
    <AppRouterCacheProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          {children}
        </ThemeProvider>
      </QueryClientProvider>
    </AppRouterCacheProvider>
  );
}
