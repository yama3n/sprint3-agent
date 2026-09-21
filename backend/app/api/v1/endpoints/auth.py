from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.core.config import settings
from app.core.security import get_current_user, verify_mock_credentials

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    if not payload.email or not payload.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="VALIDATION_ERROR")
    if not verify_mock_credentials(payload.email, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS"
        )
    return LoginResponse(
        session_token=settings.MOCK_AUTH_TOKEN,
        user=UserInfo(email=payload.email, display_name="田中 太郎"),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(_current_user: str = Depends(get_current_user)) -> None:
    # PoC用モック: 永続化されたセッションストアを持たないため、サーバー側で無効化する
    # 状態は存在しない（クライアント側でトークンを破棄すれば足りる）
    return None
