# 引合書整理エージェント - Backend (FastAPI)

FastAPI + PostgreSQL + Claude Agent SDK によるローカル実行API。

## セットアップ

```bash
uv sync
cp .env.example .env   # ANTHROPIC_API_KEY 等を設定
```

## 開発サーバー起動

```bash
uv run uvicorn app.main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## テスト

```bash
uv run pytest tests/ -v
```

## ディレクトリ構造

- `app/api/`: エンドポイント・スキーマ（Presentation）
- `app/core/`: 設定・DB・依存注入
- `app/services/`: ビジネスロジック
- `app/repositories/` + `app/models/`: Data Access
- `app/agent/`: AIエージェント（Claude Agent SDK。設計の正は `docs/requirements/agent-plan.md`）
- `traces/`: エージェント実行トレース（git管理外）
