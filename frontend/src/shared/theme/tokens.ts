// デザイン値のハードコード禁止。色・余白・タイポはここを経由する。
// 値の真実源は docs/requirements/03-spec.md「3. デザイントークン」（このファイルは転記）。
// 03-spec は黒・グレー基調の無彩色デザインのため、色相2つルールの main はサイドバー/主要
// ボタンの黒系グラデーション（mockup.html .btn = #17181a）を採用し、review/web/success の
// 3色は状態バッジ専用のセマンティックアクセントとして別枠で保持する（本文参照）。
export const tokens = {
  colors: {
    main: {
      100: "#eef0f1", // surface-2（淡い背景・hover）
      300: "#c2c7cc", // border-strong
      500: "#17181a", // 主要アクション（mockup .btn背景）
      700: "#2a2c2f", // hover/active（mockup .btn:hover）
      900: "#0b0c0d", // サイドバーグラデーション最濃部
    },
    background: "#f4f5f6",
    surface: "#ffffff",
    text: {
      primary: "#1b1d1f",
      secondary: "#5c6368",
      meta: "#8b9198",
    },
    error: "#ab3126", // --c-alert（汎用エラー配色。ログインエラー等）
    // 状態表示専用のセマンティックアクセント（03-spec.md 3章）。
    // ボタン等の主要アクションには使わず、要確認/Web補完/確定済みバッジにのみ使用する
    status: {
      review: { text: "#a9781f", bg: "#faf2e2" },
      web: { text: "#2f7a75", bg: "#e7f3f2" },
      success: { text: "#2c7a4d", bg: "#e7f4ec" },
    },
  },
  typography: {
    fontHeading:
      '"Hiragino Kaku Gothic ProN", "Noto Sans JP", "Yu Gothic", sans-serif',
    fontBody: '"Hiragino Kaku Gothic ProN", "Noto Sans JP", "Yu Gothic", sans-serif',
  },
  radius: 10,
  spacing: (n: number) => n * 8,
} as const;
