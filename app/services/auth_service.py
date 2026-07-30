import sqlite3

from fastapi import Depends, Header, HTTPException

from app.core.security import decode_access_token
from app.db.session import get_db


def get_current_user(
    authorization: str | None = Header(default=None),
    db: sqlite3.Connection = Depends(get_db),
) -> sqlite3.Row:
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录")

    token = authorization.replace("Bearer ", "").strip()
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="登录已过期")

    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user or not user["is_active"]:
        raise HTTPException(status_code=401, detail="用户不可用")

    return user
