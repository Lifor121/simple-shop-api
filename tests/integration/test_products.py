import json

import pytest


async def get_token(ac, email="admin@test.com"):
    """Helper для получения токена"""
    await ac.post("/api/register", json={"email": email, "password": "pass"})
    resp = await ac.post("/api/login", data={"username": email, "password": "pass"})
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_create_and_read_product(ac, redis_mock):
    token = await get_token(ac)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Создание продукта
    product_data = {"name": "Test Laptop", "price": 1500.0}
    response = await ac.post("/api/products", json=product_data, headers=headers)
    assert response.status_code == 201
    created_id = response.json()["id"]

    # 2. Чтение продукта (Должен записаться в кэш)
    await redis_mock.flushall()

    response = await ac.get("/api/products")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # 3. Проверка кэша
    cached_data = await redis_mock.get("products:0:100")
    assert cached_data is not None
    assert json.loads(cached_data)[0]["name"] == "Test Laptop"


@pytest.mark.asyncio
async def test_update_product_invalidates_cache(ac, redis_mock):
    token = await get_token(ac, email="editor@test.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Создаем
    create_resp = await ac.post(
        "/api/products", json={"name": "Old", "price": 10}, headers=headers
    )
    p_id = create_resp.json()["id"]

    # Загружаем в кэш
    await ac.get("/api/products")
    assert await redis_mock.get("products:0:100") is not None

    # Обновляем
    await ac.put(f"/api/products/{p_id}", json={"name": "New"}, headers=headers)

    # Проверяем, что кэш удален (инвалидирован)
    assert await redis_mock.get("products:0:100") is None
