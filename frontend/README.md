# 引合書整理エージェント - Frontend (Next.js 15)

## セットアップ

```bash
npm install
cp .env.local.example .env.local
```

## 開発コマンド

- `npm run dev` - 開発サーバー起動（http://localhost:3000）
- `npm run build` - 本番ビルド
- `npm run typecheck` - 型チェック
- `npm run lint` - ESLint
- `npm run test` - Jest
- `npm run orval` - OpenAPIスキーマからAPIクライアント再生成

## 構造

- `src/app/`: ページ（App Router。page.tsx は薄く保つ）
- `src/features/`: 機能単位（api.ts / hooks.ts / components/ / index.ts）
- `src/shared/`: 横断コード（api(generated+mutator) / ui / hooks / lib / theme / i18n）
- `src/entities/`: ドメインエンティティ

## ルール

- `shared/api/generated/` は編集しない（orval生成）
- JSX内に日本語を直書きしない（`t()`を使う）
- デザイン値は `shared/theme/tokens.ts` 経由のみ（真実源: `docs/requirements/03-spec.md` 3章）
- feature間の直接importは禁止（`index.ts`経由）
