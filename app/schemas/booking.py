from pydantic import BaseModel
from typing import Any


class BookingCreate(BaseModel):
    stylistName: str = "Benson"
    serviceName: str = "美发护理体验套餐"
    bookingDate: str
    bookingTime: str
    projectId: Any = ""
    customerName: str = ""
    gender: str = "male"
    peopleCount: int = 1
    remark: str = ""


class BookingOut(BaseModel):
    id: int
    stylistName: str
    serviceName: str
    bookingDate: str
    bookingTime: str
    projectId: str = ""
    customerName: str = ""
    gender: str = "male"
    peopleCount: int = 1
    remark: str = ""
    status: str
