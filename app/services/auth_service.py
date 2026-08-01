import sqlite3

from fastapi import Depends, Header, HTTPException

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db


def get_or_create_dev_user(db: sqlite3.Connection) -> sqlite3.Row:
    username = settings.dev_auth_username
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        db.execute(
            """
            INSERT INTO users (username, nickname, hashed_password, role, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, "dev miniapp user", "", "miniapp_user", 1),
        )
        db.commit()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return user


def get_current_user(
    authorization: str | None = Header(default=None),
    db: sqlite3.Connection = Depends(get_db),
) -> sqlite3.Row:
    if not authorization:
        if settings.enable_dev_auth_bypass:
            return get_or_create_dev_user(db)
        raise HTTPException(status_code=401, detail="未登录")

    token = authorization.replace("Bearer ", "").strip()
    username = decode_access_token(token)
    if not username:
        if settings.enable_dev_auth_bypass:
            return get_or_create_dev_user(db)
        raise HTTPException(status_code=401, detail="登录已过期")

    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user or not user["is_active"]:
        raise HTTPException(status_code=401, detail="用户不可用")

    return user
