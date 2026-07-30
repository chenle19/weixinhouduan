import json
import sqlite3
from copy import deepcopy
from datetime import date, datetime, timedelta

from app.services.seed import DEFAULT_MINIAPP_CONFIG


REST_PERIOD_MAP = {
    "morning": "上午",
    "afternoon": "下午",
    "evening": "晚上",
}


def _normalize_slot(slot) -> dict:
    if isinstance(slot, str):
        return {"time": slot, "status": "available", "capacity": 1}
    status = slot.get("status", "available")
    if status in ("已约", "booked"):
        status = "available"
    if status in ("休假", "rest"):
        status = "rest"
    return {
        "time": slot.get("time", ""),
        "status": status,
        "capacity": max(int(slot.get("capacity") or 1), 1),
    }


def normalize_config(saved: dict | None) -> dict:
    config = deepcopy(DEFAULT_MINIAPP_CONFIG)
    if not saved:
        return config

    for key, value in saved.items():
        if value not in (None, ""):
            config[key] = value

    daily_schedule = saved.get("dailySchedule") or {}
    source_periods = daily_schedule.get("periods") or saved.get("periods") or config["periods"]
    normalized_periods = [
        {
            **period,
            "slots": [_normalize_slot(slot) for slot in period.get("slots", []) if _normalize_slot(slot)["time"]],
        }
        for period in source_periods
    ]

    config["dailySchedule"] = {
        "enabled": bool(daily_schedule.get("enabled", True)),
        "periods": normalized_periods,
    }
    config["periods"] = normalized_periods
    config["restDays"] = saved.get("restDays") or []
    config["banners"] = [
        {**item, "bgColor": item.get("bgColor") or item.get("bg") or item.get("posterBg") or "#d7c1ff"}
        for item in config.get("banners", [])
    ]
    config["categories"] = [
        {**item, "bgColor": item.get("bgColor") or item.get("bg") or "#c46ce7"}
        for item in config.get("categories", [])
    ]
    config["recommends"] = [
        {**item, "bgColor": item.get("bgColor") or item.get("bg") or "#f8d7df"}
        for item in config.get("recommends", [])
    ]
    config["stylist"] = {
        **DEFAULT_MINIAPP_CONFIG.get("stylist", {}),
        **(config.get("stylist") or {}),
    }
    return config


def get_miniapp_config(db: sqlite3.Connection) -> dict:
    row = db.execute("SELECT value FROM miniapp_configs WHERE key = ?", ("default",)).fetchone()
    saved = json.loads(row["value"]) if row else None
    return normalize_config(saved)


def _booking_counts(db: sqlite3.Connection, start: date, end: date) -> dict[tuple[str, str], int]:
    rows = db.execute(
        """
        SELECT booking_date, booking_time, COUNT(*) AS total
        FROM bookings
        WHERE booking_date >= ? AND booking_date <= ? AND status IN ('pending', 'confirmed')
        GROUP BY booking_date, booking_time
        """,
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    return {(row["booking_date"], row["booking_time"]): int(row["total"]) for row in rows}


def _rest_period_titles(rest_days: list[dict], day: date) -> set[str]:
    titles: set[str] = set()
    day_key = day.isoformat()
    for rule in rest_days:
        if rule.get("date") != day_key:
            continue
        rest_type = rule.get("restType", "all")
        if rest_type == "all":
            return {"上午", "下午", "晚上"}
        mapped = REST_PERIOD_MAP.get(rest_type)
        if mapped:
            titles.add(mapped)
    return titles


def build_booking_schedule(db: sqlite3.Connection, days: int = 92) -> dict:
    config = get_miniapp_config(db)
    today = date.today()
    end = today + timedelta(days=days - 1)
    counts = _booking_counts(db, today, end)
    dates = []

    for offset in range(days):
        current_day = today + timedelta(days=offset)
        date_key = current_day.isoformat()
        rest_titles = _rest_period_titles(config.get("restDays", []), current_day)
        periods = []

        for period in config["dailySchedule"]["periods"]:
            title = period["title"]
            slots = []
            for slot in period.get("slots", []):
                capacity = max(int(slot.get("capacity") or 1), 1)
                booked_count = counts.get((date_key, slot["time"]), 0)
                status = slot.get("status", "available")
                if title in rest_titles or status == "rest":
                    status = "rest"
                elif booked_count >= capacity:
                    status = "booked"
                else:
                    status = "available"

                slots.append({
                    "time": slot["time"],
                    "status": status,
                    "capacity": capacity,
                    "bookedCount": booked_count,
                })
            periods.append({"title": title, "slots": slots})

        dates.append({"date": date_key, "periods": periods})

    return {"startDate": today.isoformat(), "endDate": end.isoformat(), "dates": dates}


def slot_is_bookable(db: sqlite3.Connection, booking_date: str, booking_time: str) -> tuple[bool, str]:
    try:
        target_day = datetime.strptime(booking_date, "%Y-%m-%d").date()
    except ValueError:
        return False, "预约日期格式错误"

    today = date.today()
    if target_day < today or target_day > today + timedelta(days=91):
        return False, "只能预约未来 3 个月内的时间"

    schedule = build_booking_schedule(db, 92)
    day = next((item for item in schedule["dates"] if item["date"] == booking_date), None)
    if not day:
        return False, "预约日期不可用"

    for period in day["periods"]:
        for slot in period["slots"]:
            if slot["time"] == booking_time:
                if slot["status"] == "available":
                    return True, "ok"
                if slot["status"] == "rest":
                    return False, "该时间为休息时间"
                return False, "该时间已约满"

    return False, "预约时间不存在"
