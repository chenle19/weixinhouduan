from typing import Literal

from pydantic import BaseModel, Field


class MiniappBanner(BaseModel):
    id: int
    type: Literal["image", "video"] = "image"
    title: str
    subtitle: str = ""
    mediaUrl: str = ""
    bgColor: str = "#d7c1ff"
    enabled: bool = True


class MiniappCategory(BaseModel):
    id: int
    label: str
    icon: str = ""
    bgColor: str = "#c46ce7"
    enabled: bool = True


class MiniappRecommend(BaseModel):
    id: int
    imageUrl: str = ""
    title: str
    tag: str = ""
    label: str = ""
    action: str = ""
    price: float = 0
    buttonText: str = "预约"
    bgColor: str = "#f8d7df"
    enabled: bool = True


class MiniappStylist(BaseModel):
    title: str = "服务人员"
    name: str = "Benson"
    role: str = "你的专属发型师"
    avatarBg: str = "#dbe7ff"


class MiniappTimeSlot(BaseModel):
    time: str
    status: Literal["available", "rest"] = "available"
    capacity: int = 1


class MiniappTimePeriod(BaseModel):
    title: Literal["上午", "下午", "晚上"]
    slots: list[MiniappTimeSlot]


class MiniappDailySchedule(BaseModel):
    enabled: bool = True
    periods: list[MiniappTimePeriod]


class MiniappRestDayRule(BaseModel):
    id: int
    date: str
    restType: Literal["all", "morning", "afternoon", "evening"] = "all"
    remark: str = ""


class MiniappHolidayConfig(BaseModel):
    festivalDays: list[str] = Field(default_factory=list)
    extraWorkdays: list[str] = Field(default_factory=list)
    randomSeed: str = "hair-booking"


class MiniappConfigSchema(BaseModel):
    brand: str = "Benson"
    shopName: str = "A hair salon(白土坝店)"
    supportText: str = "抖音勇猛乐哥提供软件技术支持 当前版本0.01"
    contactPhone: str = ""
    banners: list[MiniappBanner]
    categories: list[MiniappCategory]
    recommends: list[MiniappRecommend]
    stylist: MiniappStylist = Field(default_factory=MiniappStylist)
    dailySchedule: MiniappDailySchedule
    restDays: list[MiniappRestDayRule] = Field(default_factory=list)
    periods: list[MiniappTimePeriod] = Field(default_factory=list)
    holidayConfig: MiniappHolidayConfig = Field(default_factory=MiniappHolidayConfig)
