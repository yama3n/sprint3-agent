"use client";

import { Snackbar } from "@mui/material";
import { useToastStore } from "./toast-store";

/** 完了・準備中通知用のトースト表示先。ルート付近（app shell）に1つだけ配置する。 */
export function ToastHost() {
  const message = useToastStore((state) => state.message);
  const clear = useToastStore((state) => state.clear);

  return (
    <Snackbar
      open={message !== null}
      autoHideDuration={3000}
      onClose={clear}
      message={message}
      anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
    />
  );
}
