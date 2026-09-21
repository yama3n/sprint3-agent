"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import { useLoginApiV1AuthLoginPost } from "@/shared/api/generated/auth";
import { useAuthStore } from "@/shared/lib/auth-store";

interface LoginErrorBody {
  detail?: string;
}

export function LoginForm() {
  const { t } = useTranslation();
  const router = useRouter();
  const setSession = useAuthStore((state) => state.setSession);
  const loginMutation = useLoginApiV1AuthLoginPost();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const isSubmitting = loginMutation.isPending;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!email || !password) {
      setError(t("auth.validationError"));
      return;
    }

    setError(null);

    try {
      const result = await loginMutation.mutateAsync({ data: { email, password } });

      if (result.status === 200) {
        setSession(result.data.session_token, {
          email: result.data.user.email,
          displayName: result.data.user.display_name,
        });
        router.push("/inquiries");
        return;
      }

      const body = result.data as unknown as LoginErrorBody;
      setError(
        body?.detail === "INVALID_CREDENTIALS"
          ? t("auth.invalidCredentials")
          : t("auth.validationError"),
      );
    } catch {
      setError(t("auth.genericError"));
    }
  }

  return (
    <Box
      component="main"
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "background.default",
        px: 2,
      }}
    >
      <Paper
        variant="outlined"
        sx={{ width: "100%", maxWidth: 400, p: 4 }}
      >
        <Typography variant="h1" sx={{ fontSize: 22, fontWeight: 700, mb: 0.5 }}>
          {t("auth.appName")}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {t("auth.loginSubtitle")}
        </Typography>

        {error ? (
          <Alert severity="error" role="alert" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : null}

        <Box
          component="form"
          onSubmit={handleSubmit}
          noValidate
          sx={{ display: "flex", flexDirection: "column", gap: 2 }}
        >
          <TextField
            label={t("auth.emailLabel")}
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            fullWidth
            autoComplete="username"
          />
          <TextField
            label={t("auth.passwordLabel")}
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            fullWidth
            autoComplete="current-password"
          />
          <Button type="submit" variant="contained" disabled={isSubmitting} fullWidth>
            {isSubmitting ? t("auth.loggingIn") : t("auth.loginButton")}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
