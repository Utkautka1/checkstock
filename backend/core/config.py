"""
Конфигурация приложения через Pydantic Settings.
Все параметры читаются из переменных окружения / .env файла.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # База данных
    DATABASE_URL: str = "postgresql+asyncpg://checkstock:checkstock@db:5432/checkstock"
    DB_ECHO: bool = False

    # JWT авторизация
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 часа

    # CORS — разрешаем фронтенд на другом порту в dev
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost"]


settings = Settings()
