from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str
    grant_type: str | None = None


class WechatLoginRequest(BaseModel):
    code: str | None = None
    nickname: str | None = None
    avatar_url: str | None = None
    avatarUrl: str | None = None
    mobile: str | None = None
