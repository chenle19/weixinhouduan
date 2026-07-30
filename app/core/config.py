from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Hair Booking API"
    database_url: str = "sqlite:///./data/hair_booking.db"
    secret_key: str = "dev-secret-key"
    access_token_expire_minutes: int = 1440
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    wechat_appid: str = ""
    wechat_secret: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.backend_cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
