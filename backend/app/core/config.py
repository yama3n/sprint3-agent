from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定。SSOT: docs/requirements/02-requirement.md 4章, 05-api-ipo.md"""

    APP_NAME: str = "引合書整理エージェント API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = (
        "postgresql+psycopg://inquiry_agent:devpassword@localhost:5433/inquiry_agent_db"
    )

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # 認証: PoC用モック（02-requirement.md Out of Scope・05-api-ipo.md 備考参照）。
    # 本格的なJWT基盤・セッション永続化は行わない。単一ユーザーの簡易照合のみ。
    MOCK_USER_EMAIL: str = "sales@toseki-steel.co.jp"
    MOCK_USER_PASSWORD: str = "password"
    MOCK_AUTH_TOKEN: str = "poc-mock-token"

    # AI Agent
    ANTHROPIC_API_KEY: str = ""

    # アップロードファイルの保存先（04-db.md: ファイル本体はDBに保存しない、storage_pathのみ）
    STORAGE_DIR: str = "storage"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
