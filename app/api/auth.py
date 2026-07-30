import json
import sqlite3
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.schemas.auth import LoginRequest, WechatLoginRequest
from app.schemas.common import fail, ok


router = APIRouter()


def code_to_session(code: str) -> tuple[dict | None, str]:
    if not settings.wechat_appid or not settings.wechat_secret:
        return None, "请先在 backend/.env 配置 WECHAT_APPID 和 WECHAT_SECRET"

    params = urlencode({
        "appid": settings.wechat_appid,
        "secret": settings.wechat_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    })
    url = f"https://api.weixin.qq.com/sns/jscode2session?{params}"

    try:
        with urlopen(url, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return None, "微信登录服务连接失败"

    if data.get("errcode"):
        return None, data.get("errmsg") or "微信登录失败"
    if not data.get("openid"):
        return None, "微信登录未返回 openid"

    return data, ""


@router.get("/csrf-token")
def csrf_token() -> dict:
    return ok({"csrf": uuid4().hex})


@router.post("/login")
def login(payload: LoginRequest, db: sqlite3.Connection = Depends(get_db)) -> dict:
    user = db.execute("SELECT * FROM users WHERE username = ?", (payload.username,)).fetchone()
    if not user or not verify_password(payload.password, user["hashed_password"]):
        return fail("用户名或密码错误", "401")

    return ok(create_access_token(user["username"]))


@router.delete("/logout")
def logout() -> dict:
    return ok(True)


@router.post("/wechat-login")
def wechat_login(payload: WechatLoginRequest, db: sqlite3.Connection = Depends(get_db)) -> dict:
    if not payload.code:
        return fail("缺少微信登录 code")

    session, error = code_to_session(payload.code)
    if error:
        return fail(error)

    openid = session["openid"]
    unionid = session.get("unionid", "")
    session_key = session.get("session_key", "")
    username = f"wx_{openid}"
    nickname = payload.nickname or "微信用户"
    avatar = payload.avatar_url or payload.avatarUrl or ""
    mobile = payload.mobile or ""

    user = db.execute(
        "SELECT * FROM users WHERE openid = ? OR username = ?",
        (openid, username),
    ).fetchone()

    if not user:
        db.execute(
            """
            INSERT INTO users (
              username,
              openid,
              unionid,
              session_key,
              nickname,
              avatar,
              mobile,
              hashed_password,
              role,
              is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                openid,
                unionid,
                session_key,
                nickname,
                avatar,
                mobile,
                get_password_hash(uuid4().hex),
                "miniapp_user",
                1,
            ),
        )
    else:
        db.execute(
            """
            UPDATE users
            SET
              username = ?,
              openid = ?,
              unionid = ?,
              session_key = ?,
              nickname = ?,
              avatar = ?,
              mobile = ?
            WHERE id = ?
            """,
            (
                username,
                openid,
                unionid or user["unionid"] or "",
                session_key,
                nickname or user["nickname"] or "微信用户",
                avatar or user["avatar"] or "",
                mobile or user["mobile"] or "",
                user["id"],
            ),
        )

    db.commit()
    user = db.execute("SELECT * FROM users WHERE openid = ?", (openid,)).fetchone()

    return ok({
        "token": create_access_token(user["username"]),
        "user": {
            "nickname": user["nickname"],
            "avatar": user["avatar"],
            "avatarUrl": user["avatar"],
            "mobile": user["mobile"],
        },
    })
