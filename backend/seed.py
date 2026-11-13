"""
Seed-скрипт: наполняет БД тестовыми данными из задания.

Данные:
  Склады: Север, Юг
  Товары: SKU-101 Органайзер, SKU-102 Контейнер, SKU-103 Корзина
  Остатки: SKU-101(Север=10, Юг=6), SKU-102(Север=5), SKU-103(Юг=4)
  Пользователь: admin / admin123

Запускается один раз: docker compose exec backend python seed.py
"""
import asyncio

from core.db import async_session_maker, Base, engine
from core.logger import get_logger
from core.security import hash_password
from db.psql.crud.products import create_product, get_product_by_sku
from db.psql.crud.users import create_user, get_user_by_username
from db.psql.crud.warehouses import create_warehouse, get_warehouses
from services.stock_service import StockService

log = get_logger("seed")

PRODUCTS = [
    ("SKU-101", "Органайзер"),
    ("SKU-102", "Контейнер"),
    ("SKU-103", "Корзина"),
]

# (sku, склад_север, склад_юг)
STOCK_DATA = [
    ("SKU-101", 10, 6),
    ("SKU-102", 5, 0),
    ("SKU-103", 0, 4),
]


async def seed():
    log.info("=" * 50)
    log.info("ЗАПУСК SEED — наполнение тестовыми данными")
    log.info("=" * 50)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as db:
        # === Пользователь ===
        existing_user = await get_user_by_username(db, "admin")
        if not existing_user:
            await create_user(db, "admin", hash_password("admin123"))
            log.info("Пользователь admin создан (пароль: admin123)")
        else:
            log.debug("Пользователь admin уже существует")

        # === Склады ===
        warehouses = await get_warehouses(db)
        wh_map = {wh.name: wh for wh in warehouses}

        if "Север" not in wh_map:
            north = await create_warehouse(db, "Север")
            wh_map["Север"] = north
            log.info("Склад 'Север' создан")

        if "Юг" not in wh_map:
            south = await create_warehouse(db, "Юг")
            wh_map["Юг"] = south
            log.info("Склад 'Юг' создан")

        # === Товары ===
        product_map = {}
        for sku, name in PRODUCTS:
            p = await get_product_by_sku(db, sku)
            if not p:
                p = await create_product(db, sku, name)
                log.info(f"Товар {sku} '{name}' создан")
            product_map[sku] = p

        # === Остатки (приход) ===
        svc = StockService(db)
        north_id = wh_map["Север"].id
        south_id = wh_map["Юг"].id

        for sku, qty_north, qty_south in STOCK_DATA:
            product = product_map[sku]
            if qty_north > 0:
                await svc.receive(product.id, north_id, qty_north)
                log.info(f"  Приход {sku}: Север +{qty_north}")
            if qty_south > 0:
                await svc.receive(product.id, south_id, qty_south)
                log.info(f"  Приход {sku}: Юг +{qty_south}")

    log.info("=" * 50)
    log.info("✅ SEED завершён успешно")
    log.info("   Логин: admin | Пароль: admin123")
    log.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
