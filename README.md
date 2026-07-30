# Hair Booking Backend

FastAPI 后端，服务于 `vue3-admin` 后台和 `hair-miniapp` 小程序。

## 数据库选择

- 本地开发默认：SQLite，文件在 `backend/data/hair_booking.db`
- 生产优先：PostgreSQL，设置 `DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname`

当前代码为了方便本机直接跑，使用 Python 自带 `sqlite3`，不依赖 SQLAlchemy。PostgreSQL 更适合正式预约业务，因为它的事务、并发、约束、JSON 配置和时间查询能力更稳。后续切 PostgreSQL 时建议引入 SQLAlchemy + Alembic。

## 运行

```bash
cd G:\uni\backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

默认后台账号：

```text
admin / 123456
```

## 已实现接口

- `GET /health`
- `GET /auth/csrf-token`
- `POST /auth/login`
- `DELETE /auth/logout`
- `GET /users/me`
- `GET /miniapp/config`
- `PUT /miniapp/config`
- `POST /miniapp/auth/wechat-login`
- `GET /bookings/my`
- `POST /bookings`
