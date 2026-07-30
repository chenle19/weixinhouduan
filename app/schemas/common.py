from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: str = "200"
    msg: str = "ok"
    data: T | None = None


def ok(data=None, msg: str = "ok") -> dict:
    return {"code": "200", "msg": msg, "data": data}


def fail(msg: str, code: str = "400") -> dict:
    return {"code": code, "msg": msg, "data": None}
