"""
CRUD для товаров (справочник).
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.psql.models.models import Product


async def get_products(db: AsyncSession) -> list[Product]:
    """Список всех товаров."""
    result = await db.execute(select(Product).order_by(Product.sku))
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: int) -> Product | None:
    """Товар по ID."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def get_product_by_sku(db: AsyncSession, sku: str) -> Product | None:
    """Товар по артикулу (SKU)."""
    result = await db.execute(select(Product).where(Product.sku == sku))
    return result.scalar_one_or_none()


async def create_product(db: AsyncSession, sku: str, name: str) -> Product:
    """Создаёт товар в справочнике."""
    product = Product(sku=sku, name=name)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product
