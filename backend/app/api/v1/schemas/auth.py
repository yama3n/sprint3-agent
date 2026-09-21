from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class UserInfo(BaseModel):
    email: str
    display_name: str


class LoginResponse(BaseModel):
    session_token: str
    user: UserInfo
