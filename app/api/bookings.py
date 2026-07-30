import json
import sqlite3
from urllib.parse import unquote

from fastapi import APIRouter, Body, Depends, Header

from app.core.security import decode_access_token
from app.db.session import get_db
from app.schemas.common import fail, ok
from app.services.auth_service import get_current_user
from app.services.schedule_service import slot_is_bookable


router = APIRouter()


def safe_json_list(value) -> list:
    if isinstance(value, list):
        return value
    if not value:
        return []
    try:
        data = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def booking_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "stylistName": row["stylist_name"],
        "serviceName": row["service_name"],
        "bookingDate": row["booking_date"],
        "bookingTime": row["booking_time"],
        "projectId": row["project_id"],
        "customerName": row["customer_name"],
        "gender": row["gender"],
        "peopleCount": row["people_count"],
        "remark": row["remark"],
        "notifyAccepted": bool(row["notify_accepted"]),
        "subscribeTemplateIds": safe_json_list(row["subscribe_template_ids"]),
        "successNotified": bool(row["success_notified"]),
        "reminder15minNotified": bool(row["reminder_15min_notified"]),
        "status": row["status"],
    }


@router.get("/my")
def my_bookings(
    db: sqlite3.Connection = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> dict:
    try:
        if not authorization:
            return ok([])
        username = decode_access_token(authorization.replace("Bearer ", "").strip())
        if not username:
            return ok([])
        current_user = db.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (username,),
        ).fetchone()
        if not current_user:
            return ok([])
        rows = db.execute(
            "SELECT * FROM bookings WHERE user_id = ? ORDER BY id DESC",
            (current_user["id"],),
        ).fetchall()
        data = []
        for row in rows:
            try:
                data.append(booking_to_dict(row))
            except Exception:
                continue
        return ok(data)
    except Exception:
        return ok([])


@router.post("/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    db: sqlite3.Connection = Depends(get_db),
    current_user: sqlite3.Row = Depends(get_current_user),
) -> dict:
    row = db.execute(
        "SELECT * FROM bookings WHERE id = ? AND user_id = ?",
        (booking_id, current_user["id"]),
    ).fetchone()
    if not row:
        return fail("预约不存在")
    if row["status"] != "pending":
        return fail("当前预约不可取消")

    db.execute(
        "UPDATE bookings SET status = ? WHERE id = ? AND user_id = ?",
        ("cancelled", booking_id, current_user["id"]),
    )
    db.commit()
    row = db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    return ok(booking_to_dict(row), "已取消")


@router.post("")
def create_booking(
    payload: dict = Body(default_factory=dict),
    db: sqlite3.Connection = Depends(get_db),
    current_user: sqlite3.Row = Depends(get_current_user),
) -> dict:
    def value(*keys: str, default=""):
        for key in keys:
            item = payload.get(key)
            if item is not None and item != "":
                return item
        return default

    def bool_value(item) -> bool:
        if isinstance(item, bool):
            return item
        if isinstance(item, (int, float)):
            return item == 1
        return str(item).lower() in ("1", "true", "yes", "accept", "accepted")

    booking_date = unquote(str(value("bookingDate", "booking_date")))
    booking_time = unquote(str(value("bookingTime", "booking_time")))
    stylist_name = str(value("stylistName", "stylist_name", default="Benson"))
    service_name = str(value("serviceName", "service_name", default="美发预约"))
    project_id = str(value("projectId", "project_id"))
    customer_name = str(value("customerName", "customer_name"))
    gender = str(value("gender", default="male"))
    remark = str(value("remark"))
    notify_accepted = bool_value(value("notifyAccepted", "notify_accepted", default=False))
    subscribe_template_ids = value("subscribeTemplateIds", "subscribe_template_ids", default=[])
    if not isinstance(subscribe_template_ids, list):
        subscribe_template_ids = []
    try:
        people_count = int(value("peopleCount", "people_count", default=1))
    except (TypeError, ValueError):
        people_count = 1

    if not booking_date or not booking_time:
        return fail("请选择到店时间")

    can_book, message = slot_is_bookable(db, booking_date, booking_time)
    if not can_book:
        return fail(message)

    cursor = db.execute(
        """
        INSERT INTO bookings (
          user_id,
          stylist_name,
          service_name,
          booking_date,
          booking_time,
          project_id,
          customer_name,
          gender,
          people_count,
          remark,
          notify_accepted,
          subscribe_template_ids,
          success_notified,
          reminder_15min_notified,
          status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            current_user["id"],
            stylist_name,
            service_name,
            booking_date,
            booking_time,
            project_id,
            customer_name,
            gender,
            people_count,
            remark,
            1 if notify_accepted else 0,
            json.dumps(subscribe_template_ids, ensure_ascii=False),
            0,
            0,
            "pending",
        ),
    )
    db.commit()
    booking_id = cursor.lastrowid
    return ok({
        "id": booking_id,
        "stylistName": stylist_name,
        "serviceName": service_name,
        "bookingDate": booking_date,
        "bookingTime": booking_time,
        "projectId": project_id,
        "customerName": customer_name,
        "gender": gender,
        "peopleCount": people_count,
        "remark": remark,
        "notifyAccepted": notify_accepted,
        "subscribeTemplateIds": subscribe_template_ids,
        "successNotified": False,
        "reminder15minNotified": False,
        "status": "pending",
    }, "预约成功")
