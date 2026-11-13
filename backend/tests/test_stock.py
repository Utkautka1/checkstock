"""
Тесты складских сценариев CheckStock:
  1. Health check
  2. Структура остатков и инварианты
  3. Нехватка товара (сценарий дефицита)
  4. Перемещение между ФФ и идемпотентность подтверждения
"""
import pytest
from core.security import create_access_token


@pytest.fixture(scope="session")
def auth_headers():
    token = create_access_token({"sub": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio(loop_scope="session")
async def test_health(client):
    res = await client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio(loop_scope="session")
async def test_stock_structure(client, auth_headers):
    res = await client.get("/api/stock", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    for item in data:
        assert item["quantity_physical"] == item["quantity_available"] + item["quantity_reserved"]


@pytest.mark.asyncio(loop_scope="session")
async def test_shortage_handling(client, auth_headers):
    """Сценарий нехватки: заказ больше, чем есть на складе -> 422 с детализацией."""
    res = await client.post(
        "/api/shipments/fbs/reserve",
        json={"product_id": 1, "warehouse_id": 1, "quantity": 9999},
        headers=auth_headers,
    )
    assert res.status_code == 422
    assert "Нехватка" in res.json()["detail"]


@pytest.mark.asyncio(loop_scope="session")
async def test_movement_and_idempotence(client, auth_headers):
    """Сценарий перемещения и идемпотентности подтверждения."""
    res = await client.post(
        "/api/movements",
        json={"product_id": 1, "warehouse_from_id": 1, "warehouse_to_id": 2, "quantity": 1},
        headers=auth_headers,
    )
    assert res.status_code == 201
    m_id = res.json()["id"]

    res_conf1 = await client.post(f"/api/movements/{m_id}/confirm", headers=auth_headers)
    assert res_conf1.status_code == 200
    assert res_conf1.json()["status"] == "completed"

    # Повторное подтверждение идемпотентно
    res_conf2 = await client.post(f"/api/movements/{m_id}/confirm", headers=auth_headers)
    assert res_conf2.status_code == 200
    assert res_conf2.json()["status"] == "completed"
