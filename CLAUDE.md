# Training Sprint 3 - 開発ガイド（memory 駆動ハーネス）

Sprint 3 のテーマは **AIエージェント構築**。Web アプリ（Next.js + FastAPI）はエージェントを
動かすための器であり、主役はエージェント（`backend/app/agent/`・設計の正は `docs/requirements/agent-plan.md`）。
実行はすべて**ローカル環境**（クラウドデプロイなし）。
実装は **memory 駆動の自律ループ（build-loop）** で、クリーンアーキテクチャ＋TDD を守りながら進める。

## ハーネスの憲法（最重要・全エージェント遵守）

1. **`.claude/memory.md` が単一の真実源（進捗・決定・知恵）。** 作業前に必ず読む。
   **更新できるのは orchestrator（build-loop スキル）だけ**（規約: `.claude/rules/memory-protocol.md`）。
2. **実装は build-loop で回す。**
   - 初版: `/build-loop`
   - 継続改善・評価 Fail の修正: `/build-loop --change "<変更要求>"`
3. **クリーンアーキの依存ルール厳守**（内側は外側を知らない）: `.claude/rules/clean-architecture.md`
4. **TDD 必須**: RED（テスト失敗）を確認せず GREEN に進まない: `.claude/rules/tdd-guide.md`
   例外: **エージェントループは単体テストしない**（ツール=決定的関数のみが対象。ループは評価で検証）。
5. **エージェント開発の原則**（`.claude/rules/agent-development.md`）:
   - 設計が正（agent-plan.md に無いものを実装しない）
   - すべての実行をトレース（`backend/traces/{run_id}.jsonl`）に記録
   - ガードレールは hooks で強制（お願いにしない）
   - タイムアウトは2層（無応答 < 内側 < 外側=`jobs.py`）。ハングは外側が必ず回収
   - 起動はジョブ経由（POST 202 + run_id → GET ポーリング。HTTP で完了を同期待ちしない）
6. **レビュー・ゲート**: 実装した本人はレビューしない。**別エージェント（reviewer）**が指摘し、
   **implementer が修正**。指摘ゼロになるまで次スライスに進まない（上限超過は BLOCKED 記録）。
7. **完全自律 & 必ず終端**: 承認を挟まず周回し、詰みは `BLOCKED` にして他スライスへ。
8. **中断復帰**: memory §3 の Status から再開できる。

## 実装ループ（build-loop）

```
/build-loop
  ├─ ① memory.md + 設計書(01〜05, agent-plan.md)を読む → プラン生成（memory §3 バックログ）
  │      スライスは2種類: Web スライス / エージェントスライス（AGENT-XX）
  ├─ ② 次スライス選択（依存が DONE のもの。エージェントのツールが使う API/テーブルの
  │      Web スライスを先に）
  ├─ ③ スライス指示書生成（層→dir→コマンド。agent は agent-slices.md の層順）
  ├─ ④ 層ごとに TDD:  test-designer(RED) → implementer(GREEN)
  │      Web:   DTO → Repository → Service → API →【統合】→ api.ts/hooks → components/page
  │      Agent: tools → definition/ガードレール → jobs経由API →【統合】→ ポーリングUI
  │             → ミニ評価（正常系1本をジョブ実行しトレース×agent-plan.md 突き合わせ）
  ├─ ⑤ reviewer(read-only)で指摘 → implementer が修正（上限3回）
  ├─ ⑥ memory へ記録（決定/指摘/学び/Status=DONE）＋ 品質ゲート＆commit
  └─ ② に戻る（未完スライスが無くなれば 🎉 初版完成 → エージェント評価へ）
```

## 開発フロー全体

```
Phase 0: セットアップ      r2b-build-sprint3（本テンプレ配置）
Phase 1: Foundation       foundation エージェント（Slice 0-1〜0-7・ループ外）
                          0-7 = /foundation-agent-setup（app/agent/ スケルトン・トレース・
                          タイムアウト2層・ジョブの型・疎通テスト）
Phase 2: 実装ループ        /build-loop（初版完成まで自律周回）
Phase 3: エージェント評価   06-scenario-test.md のエージェント評価シナリオを実行し、
                          トレース（backend/traces/）を agent-plan.md と突き合わせる（下記）
Phase 4: 継続改善          /build-loop --change "..."（評価 Fail の修正もこれで回す）
Phase 5: 開発環境の設定     /r2b-env-sprint3（評価の自動化などを自分の skill として作る）
```

### Phase 3: エージェント評価のやり方

エージェントが**設計どおり**動いているかを検証する。単体テストでは検証できない
「エージェントループの振る舞い」は、シナリオ実行 + トレースで評価する。

1. `docs/requirements/06-scenario-test.md` のエージェント評価シナリオを順に実行し、判定欄に記録
2. 各実行の `backend/traces/{run_id}.jsonl` を開き、agent-plan.md と突き合わせる：
   - 使ったツールがツール一覧の範囲内か
   - ガードレール違反（禁止操作）がないか
   - 完了条件の「判定方法」どおりに終了したか（`*_timeout` / `max_turns` で終わっていないか）
   - フローが IPO 拡張表のスケッチから大きく乖離していないか
3. Fail は原因を 要件(02)・設計(agent-plan.md)・実装 に切り分け、`/build-loop --change` で修正する

> この突き合わせを毎回手でやるのが面倒だと感じたら、それが Env フェーズ
> （`/r2b-env-sprint3`）の出発点。評価ランナーやトレースレビューを**自分の skill として作る**
> レシピが用意されている。

## エージェント / スキル

### スキル
| スキル | 用途 |
|-------|------|
| `/build-loop` | **実装ループ本体（orchestrator）**。初版・継続改善の両方 |
| `/foundation-backend-setup` | Slice 0-1: FastAPI 初期化（ループ外・基盤） |
| `/foundation-postgres-docker` | Slice 0-2: PostgreSQL Docker |
| `/foundation-database-setup` | Slice 0-3: ORM・マイグレーション |
| `/foundation-auth-jwt` | Slice 0-4: JWT 認証 |
| `/foundation-frontend-setup` | Slice 0-5: Next.js 15 + MUI |
| `/foundation-api-integration` | Slice 0-6: OpenAPI 出力・orval 再生成 |
| `/foundation-agent-setup` | Slice 0-7: Claude Agent SDK・`app/agent/` スケルトン・疎通テスト |
| `/git-commit` | 品質チェック後に commit |
| `/r2b-env-sprint3` | 開発環境の設定フェーズ（Env・Build 後） |
| `/design-spec` | 仕様＋モック（`./docs/requirements/mocks/mockup.html`）の作成・更新 |

### エージェント
| エージェント | 役割 | 呼び出し |
|------------|------|---------|
| **foundation** | Foundation Phase（Slice 0-1〜0-7）をガイド（ループ外） | プロンプトで起動 |
| **test-designer** | 🔴 RED: 失敗するテストを層ごとに設計（エージェントのツール含む） | build-loop から Task |
| **implementer** | 🟢 GREEN/REFACTOR ＋ 指摘修正 | build-loop から Task |
| **reviewer** | 🔵 実装範囲を独立レビュー（read-only・指摘のみ。agent-plan.md 突き合わせ含む） | build-loop から Task |

> 旧構成（planner / fullstack-integration / 層別エージェント群 / agent-implementation スキル）は
> build-loop に統合・置換された（エージェントスライスの手順は `.claude/skills/build-loop/agent-slices.md`）。

## 技術スタック

| レイヤー | 技術 | 備考 |
|---------|------|------|
| **フロントエンド** | Next.js 15 (App Router) | ローカル起動（`npm run dev`） |
| **バックエンド** | FastAPI + Python 3.12 | ローカル起動（uvicorn）・クリーンアーキ3層 |
| **データベース** | PostgreSQL | ローカル Docker（docker-compose）※下記 |
| **AI エージェント** | Claude Agent SDK（`claude-agent-sdk`） | カスタムツール（in-process MCP）＋ hooks によるガードレール |
| **トレース** | JSONL（`backend/traces/{run_id}.jsonl`） | agent-plan.md の IPO 拡張表と同型。評価・進捗表示に使う |
| **ORM** | SQLAlchemy 2.0（AsyncSession） | 非同期対応 |
| **認証** | JWT（httpOnly Cookie） | Cookie 透過（mutator で自動処理） |
| **API クライアント** | orval + TanStack Query | OpenAPI から自動生成（`shared/api/generated/`） |
| **パッケージ管理（Python）** | uv | 高速・再現可能 |
| **テスト** | pytest + pytest-asyncio / Jest + RTL | ツールは決定的関数として単体テスト |

> **Docker / DB 構成（Sprint 3 の決定事項）**
> - DB は **PostgreSQL**、起動は **docker-compose**（`docker-compose up -d`）。Sprint 1/2 と同一スタック
> - **Sprint 3 で Docker を使うのはこの DB 起動のみ**。アプリのコンテナ化・デプロイには使わない
>   （backend/Dockerfile はローカル再現用の任意成果物）
> - PostgreSQL を継続する理由: エージェントのジョブ（裏で実行状態を書く）と API（読む）の
>   並行アクセスに強い・JSONB がツール入出力/実行ログに合う・将来 pgvector に拡張できる

## ディレクトリ構造

```
training-sprint3/
├── .claude/
│   ├── memory.md                    # ★ハーネスの脳（進捗・決定・知恵。orchestrator のみ編集）
│   ├── settings.json                # 許可リスト（build-loop 自律実行用）
│   ├── skills/                      # build-loop（+agent-slices.md）, foundation-*, git-commit
│   ├── agents/                      # test-designer, implementer, reviewer, foundation
│   └── rules/                       # clean-architecture, design-guidelines, memory-protocol, agent-development, tdd-guide
├── backend/                         # FastAPI
│   ├── app/
│   │   ├── api/v1/                  # endpoints / schemas（Presentation）
│   │   ├── core/                    # 設定・依存注入
│   │   ├── models/                  # ORM（Data Access）
│   │   ├── services/                # ビジネスロジック（エージェント起動もここから）
│   │   ├── repositories/            # Data Access
│   │   ├── agent/                   # ★AI エージェント（Claude Agent SDK）
│   │   │   ├── definition.py        #   システムプロンプト・完了/停止条件（agent-plan.md Part 1 に対応）
│   │   │   ├── tools.py             #   カスタムツール群（agent-plan.md ツール一覧と1対1）
│   │   │   ├── runner.py            #   実行ループ・max_turns・内側タイムアウト
│   │   │   ├── jobs.py              #   実行の型: バックグラウンドジョブ + run_id ポーリング（外側タイムアウト）
│   │   │   └── trace.py             #   トレースレコーダー（JSONL）
│   │   ├── middleware/              # 認証等
│   │   └── main.py
│   ├── scripts/export_openapi.py    # OpenAPI スキーマ出力
│   ├── tests/
│   ├── traces/                      # 実行トレース（{run_id}.jsonl・git管理外）
│   ├── pyproject.toml               # uv 依存管理（claude-agent-sdk 含む）
│   └── .env                         # ANTHROPIC_API_KEY 等
├── frontend/                        # Next.js 15（App Router / FSD）
│   └── src/
│       ├── app/                     # ページ（page.tsx は薄く）
│       ├── features/                # 機能単位（api.ts / hooks.ts / components/ / index.ts）
│       ├── shared/                  # api(generated+mutator) / ui / hooks / lib / theme / i18n
│       └── entities/
├── docs/
│   ├── requirements/                # 設計ドキュメント（01〜06 + agent-plan.md。build-loop の入力）
│   └── env/                         # 開発環境カスタマイズ台帳（Env フェーズ）
├── openapi.json                     # OpenAPI スキーマ（自動生成）
└── docker-compose.yml               # PostgreSQL 開発環境
```

## クリーンアーキテクチャ（依存ルール）

```
Presentation（UI/API） → Business Logic（Service / Agent） → Data Access（Repository）
依存は常に「外側 → 内側」。内側は外側を知らない。逆流禁止。
```

- Backend: `api/(endpoints,schemas,middleware)` → `services/`（+ `agent/`） → `repositories/`(+`models/`)
- **Agent の位置づけ**: `app/agent/` は Business Logic。起動は service 層から `jobs.start_agent_job()`。
  ツールが DB に触るときは repository 経由
- Frontend: `app/ + features/*/components` → `hooks.ts/store.ts/entities` → `api.ts`(+`generated/`)
- 詳細・層→dir 対応・reviewer チェックリスト: `.claude/rules/clean-architecture.md`

## 画面モックについて

UI の全体像は仕様（基本設計）の一部として作成する。`/design-spec` を実行すると
全画面をまとめたモック `./docs/requirements/mocks/mockup.html` が生成される（再実行で更新可）。
`open ./docs/requirements/mocks/mockup.html` でブラウザ確認できる。

## Next.js 特有のルール

### Server / Client Component の使い分け

```typescript
// ❌ NG - データフェッチ hooks は Server Component で使えない
// app/(portal)/dashboard/page.tsx（デフォルト: Server Component）
const { data } = useGetApplications(); // エラー

// ✅ OK - Client Component に切り出す
// features/applications/components/ApplicationList.tsx
"use client";
export function ApplicationList() {
  const { data } = useGetApplications(); // OK
}
```

page.tsx は薄く保ち（Server Component のまま feature を組み立てるだけ）、
データフェッチ・状態は `features/*/components/`（`"use client"`）に置く。

## 重要なルール

### Frontend
- orval 生成コード（`shared/api/generated/`）は編集しない
- JSX 内に日本語を直書きしない（`t()` を使う）
- feature 間の直接 import 禁止（`index.ts` 経由）
- デザイン値をハードコードしない（`theme/tokens.ts`。トークンの真実源は `docs/requirements/03-spec.md` 3章）
- UIデザインのガードレール（色相2つルール・脱・標準MUI・3状態設計）: `.claude/rules/design-guidelines.md`
- Client Component には `"use client"` を明示
- 横断コードは `shared/` に集約：共通UI→`shared/ui/`・横断hook→`shared/hooks/`・純粋関数→`shared/lib/`（shared は feature を import しない）
- 共通化は **Rule of Three**（同じUIが3箇所目で `shared/ui/` へ抽出。早すぎる共通化はしない）

### Backend
- uv を使用（pip は使わない）
- 依存ルール厳守（endpoints → services → repositories、逆流禁止）
- テストなしの実装はしない

### AI Agent（詳細は `.claude/rules/agent-development.md`）
- **エージェント実行は `app/agent/` に閉じ込め、起動は service 層から `jobs.start_agent_job()` で**（endpoints から直接呼ばない）
- **HTTP で完了を同期待ちしない**: POST → 202 + run_id → GET /runs/{run_id} ポーリングが実行の型。進捗はトレース末尾を返す
- **すべての実行をトレースに記録する**（記録されない実行は評価できない）
- **完了条件は機械判定可能に**（agent-plan.md の「判定方法」をコードにする）
- **ガードレールは hooks で強制する**（プロンプトのお願いだけに頼らない）
- **タイムアウトは2層**: 内側（エージェントの停止条件）< 外側（`jobs.py` のフェイルセーフ）。
  ハングは外側が必ず回収する

## 困ったときは

- memory の書き方: `.claude/rules/memory-protocol.md`
- クリーンアーキ・reviewer チェックリスト: `.claude/rules/clean-architecture.md`
- UIデザイン: `.claude/rules/design-guidelines.md`
- エージェント開発: `.claude/rules/agent-development.md`
- エージェントスライスの実装手順: `.claude/skills/build-loop/agent-slices.md`
- TDD: `.claude/rules/tdd-guide.md`
