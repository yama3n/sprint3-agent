"""PoC用モック認証。

02-requirement.md（Out of Scope: ID/パスワード認証・セッション管理・ロール管理はMVP対象外）
および 05-api-ipo.md（/auth/login・/auth/logout の備考: 本格的なセッション永続化は行わない）
がSSOT。本格的なJWT発行・検証・リフレッシュトークン・DBセッションストアは実装しない。
単一ユーザー（settings.MOCK_USER_EMAIL）の平文照合と、固定トークンの発行のみを行う。
"""

from fastapi import Header, HTTPException, status

from app.core.config import settings


def verify_mock_credentials(email: str, password: str) -> bool:
    return email == settings.MOCK_USER_EMAIL and password == settings.MOCK_USER_PASSWORD


async def get_current_user(authorization: str | None = Header(default=None)) -> str:
    """Authorization: Bearer <MOCK_AUTH_TOKEN> のみを確認する簡易チェック。

    永続化されたセッション・失効管理は行わない（PoC用モック）。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    token = authorization.removeprefix("Bearer ")
    if token != settings.MOCK_AUTH_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    return settings.MOCK_USER_EMAIL
