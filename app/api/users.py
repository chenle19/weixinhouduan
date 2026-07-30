import sqlite3

from fastapi import APIRouter, Depends

from app.schemas.common import ok
from app.services.auth_service import get_current_user


router = APIRouter()


@router.get("/me")
def me(current_user: sqlite3.Row = Depends(get_current_user)) -> dict:
    role = current_user["role"]
    return ok({
        "nickname": current_user["nickname"] or current_user["username"],
        "avatar": current_user["avatar"],
        "roles": [role],
        "perms": ["*:*:*"] if role == "admin" else [],
    })
