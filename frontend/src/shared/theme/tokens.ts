// デザイン値のハードコード禁止。色・余白・タイポはここを経由する。
// 値の真実源は docs/requirements/03-spec.md「3. デザイントークン」（色はここからの転記）。
// font/radius/shadow/サイドバー幅は03-specに記載が無いため、実装済みモック
// docs/requirements/mocks/mockup.html の :root 変数から転記する（03-spec不足分の唯一の正）。
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
    surface2: "#eef0f1",
    surface3: "#e4e7e9",
    border: "#dde0e3",
    borderStrong: "#c2c7cc",
    text: {
      primary: "#1b1d1f",
      secondary: "#5c6368",
      meta: "#8b9198",
    },
    error: "#ab3126", // --c-alert（汎用エラー配色。ログインエラー等）
    // 状態表示専用のセマンティックアクセント（03-spec.md 3章）。
    // ボタン等の主要アクションには使わず、要確認/Web補完/確定済みバッジにのみ使用する
    status: {
      review: { text: "#a9781f", bg: "#faf2e2", border: "#ecdab3" },
      web: { text: "#2f7a75", bg: "#e7f3f2", border: "#c3e0dd" },
      success: { text: "#2c7a4d", bg: "#e7f4ec", border: "#c3e4d0" },
    },
    // サイドバー専用（黒〜チャコールのグラデーション上でのみ使う配色）
    sidebar: {
      gradient: "linear-gradient(165deg, #1c1e21 0%, #131417 55%, #0b0c0d 100%)",
      text: "#c7cbcf",
      textHover: "#f1f2f3", // hover時のわずかな強調（textStrongより一段暗い）
      textStrong: "#ffffff", // アクティブ項目・ユーザー名等（暗背景上の強調テキスト）
      textDim: "#797f85",
      activeBg: "rgba(255,255,255,0.09)",
      hoverBg: "rgba(255,255,255,0.05)",
      border: "rgba(255,255,255,0.08)",
      accent: "#e7e9ea",
    },
    // 黒系の塗りボタン（main.500系）・FABの上に乗るテキスト/アイコン色
    onDark: "#ffffff",
  },
  typography: {
    fontHeading:
      '"Hiragino Kaku Gothic ProN", "Noto Sans JP", "Yu Gothic", sans-serif',
    fontBody: '"Hiragino Kaku Gothic ProN", "Noto Sans JP", "Yu Gothic", sans-serif',
  },
  radius: 10,
  radiusSm: 6,
  radiusLg: 14,
  shadow: {
    1: "0 1px 2px rgba(20,22,24,0.06), 0 1px 1px rgba(20,22,24,0.04)",
    2: "0 8px 24px rgba(15,16,18,0.14)",
  },
  layout: {
    sidebarWidth: 224,
    sidebarWidthCollapsed: 64,
    headerHeight: 56,
  },
  spacing: (n: number) => n * 8,
} as const;
