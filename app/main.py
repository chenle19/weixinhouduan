from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, bookings, menus, miniapp, users
from app.core.config import settings
from app.db.session import init_db


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"code": "200", "msg": "ok", "data": {"status": "healthy"}}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(miniapp.router, prefix="/miniapp", tags=["miniapp"])
app.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
app.include_router(menus.router, prefix="/api/v1/menus", tags=["menus"])
