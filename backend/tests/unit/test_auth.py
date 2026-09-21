from httpx import AsyncClient

from app.core.config import settings


async def test_login_success(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": settings.MOCK_USER_EMAIL, "password": settings.MOCK_USER_PASSWORD},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_token"] == settings.MOCK_AUTH_TOKEN
    assert body["user"]["email"] == settings.MOCK_USER_EMAIL


async def test_login_wrong_password(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": settings.MOCK_USER_EMAIL, "password": "wrong"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "INVALID_CREDENTIALS"


async def test_login_missing_fields(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/login", json={"email": "", "password": ""})
    assert resp.status_code == 400


async def test_logout_requires_token(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 401

    resp2 = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {settings.MOCK_AUTH_TOKEN}"},
    )
    assert resp2.status_code == 204
