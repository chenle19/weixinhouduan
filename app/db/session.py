import json
import sqlite3
from collections.abc import Generator
from pathlib import Path

from app.core.config import settings
from app.core.security import get_password_hash
from app.services.seed import DEFAULT_MINIAPP_CONFIG


def _sqlite_path() -> Path:
    if not settings.database_url.startswith("sqlite:///"):
        return Path("./data/hair_booking.db")
    return Path(settings.database_url.replace("sqlite:///", "", 1))


DB_PATH = _sqlite_path()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              nickname TEXT DEFAULT '',
              hashed_password TEXT DEFAULT '',
              mobile TEXT DEFAULT '',
              avatar TEXT DEFAULT '',
              role TEXT DEFAULT 'user',
              is_active INTEGER DEFAULT 1,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS miniapp_configs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              key TEXT NOT NULL UNIQUE,
              value TEXT NOT NULL,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS bookings (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              stylist_name TEXT NOT NULL,
              service_name TEXT NOT NULL,
              booking_date TEXT NOT NULL,
              booking_time TEXT NOT NULL,
              status TEXT DEFAULT 'pending',
              created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        booking_columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(bookings)").fetchall()
        }
        booking_extra_columns = {
            "project_id": "TEXT DEFAULT ''",
            "customer_name": "TEXT DEFAULT ''",
            "gender": "TEXT DEFAULT 'male'",
            "people_count": "INTEGER DEFAULT 1",
            "remark": "TEXT DEFAULT ''",
            "notify_accepted": "INTEGER DEFAULT 0",
            "subscribe_template_ids": "TEXT DEFAULT '[]'",
            "success_notified": "INTEGER DEFAULT 0",
            "reminder_15min_notified": "INTEGER DEFAULT 0",
        }
        for column, definition in booking_extra_columns.items():
            if column not in booking_columns:
                db.execute(f"ALTER TABLE bookings ADD COLUMN {column} {definition}")

        user_columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(users)").fetchall()
        }
        user_extra_columns = {
            "openid": "TEXT DEFAULT ''",
            "unionid": "TEXT DEFAULT ''",
            "session_key": "TEXT DEFAULT ''",
        }
        for column, definition in user_extra_columns.items():
            if column not in user_columns:
                db.execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")

        admin = db.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
        if not admin:
            db.execute(
                """
                INSERT INTO users (username, nickname, hashed_password, role, is_active)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("admin", "管理员", get_password_hash("123456"), "admin", 1),
            )

        config = db.execute("SELECT id FROM miniapp_configs WHERE key = ?", ("default",)).fetchone()
        if not config:
            db.execute(
                "INSERT INTO miniapp_configs (key, value) VALUES (?, ?)",
                ("default", json.dumps(DEFAULT_MINIAPP_CONFIG, ensure_ascii=False)),
            )

        db.commit()
