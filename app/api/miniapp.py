import json
import sqlite3

from fastapi import APIRouter, Depends

from app.api.auth import wechat_login
from app.db.session import get_db
from app.schemas.auth import WechatLoginRequest
from app.schemas.common import ok
from app.schemas.miniapp import MiniappConfigSchema
from app.services.schedule_service import build_booking_schedule, get_miniapp_config, normalize_config


router = APIRouter()


@router.get("/config")
def get_config(db: sqlite3.Connection = Depends(get_db)) -> dict:
    try:
        return ok(get_miniapp_config(db))
    except Exception:
        return ok(normalize_config(None))


@router.put("/config")
def save_config(payload: MiniappConfigSchema, db: sqlite3.Connection = Depends(get_db)) -> dict:
    value = payload.model_dump()
    value["periods"] = value["dailySchedule"]["periods"]
    encoded = json.dumps(value, ensure_ascii=False)
    exists = db.execute("SELECT id FROM miniapp_configs WHERE key = ?", ("default",)).fetchone()
    if exists:
        db.execute("UPDATE miniapp_configs SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?", (encoded, "default"))
    else:
        db.execute("INSERT INTO miniapp_configs (key, value) VALUES (?, ?)", ("default", encoded))
    db.commit()
    return ok(value, "保存成功")


@router.get("/booking-schedule")
def booking_schedule(db: sqlite3.Connection = Depends(get_db)) -> dict:
    try:
        return ok(build_booking_schedule(db))
    except Exception:
        return ok({"startDate": "", "endDate": "", "dates": []})


@router.post("/auth/wechat-login")
def miniapp_wechat_login(payload: WechatLoginRequest, db: sqlite3.Connection = Depends(get_db)) -> dict:
    return wechat_login(payload, db)
