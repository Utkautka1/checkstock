"""
Точка входа FastAPI-приложения CheckStock.

Регистрирует роутеры, настраивает CORS и создаёт таблицы при старте.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import auth, movements, shipments, stock, warehouses
from core.config import settings
from core.db import Base, engine
from core.logger import get_logger

log = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Создаём таблицы при старте (в продакшене — Alembic)."""
    log.info("=" * 50)
    log.info("ЗАПУСК CheckStock Backend")
    log.info("=" * 50)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Таблицы БД — OK")
    yield
    log.info("Остановка приложения")


app = FastAPI(
    title="CheckStock API",
    description="Складской учёт: где товар, сколько доступно и что отправлено",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрация роутеров
app.include_router(auth.router, prefix="/api")
app.include_router(warehouses.router, prefix="/api")
app.include_router(stock.router, prefix="/api")
app.include_router(movements.router, prefix="/api")
app.include_router(shipments.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "checkstock"}
