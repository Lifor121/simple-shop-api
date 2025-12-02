import pytest
from unittest.mock import AsyncMock, patch


async def create_user_and_product(ac):
    # Регистрация
    user_data = {"email": "buyer@test.com", "password": "pass"}
    await ac.post("/api/register", json=user_data)
    login_resp = await ac.post(
        "/api/login",
        data={"username": user_data["email"], "password": user_data["password"]},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Продукт
    prod_resp = await ac.post(
        "/api/products", json={"name": "Phone", "price": 500}, headers=headers
    )
    product_id = prod_resp.json()["id"]

    return headers, product_id


@pytest.mark.asyncio
async def test_create_order_with_mq(ac):
    headers, product_id = await create_user_and_product(ac)

    order_data = {"product_id": product_id, "quantity": 2}

    # Мокаем RabbitMQ отправку
    with patch("app.routers.orders.send_message", new_callable=AsyncMock) as mock_send:
        response = await ac.post("/api/orders", json=order_data, headers=headers)

        assert response.status_code == 201
        assert response.json()["status"] == "pending"

        # Проверяем отправку сообщения
        mock_send.assert_called_once()
        assert mock_send.call_args[1]["event_type"] == "order_created"
        assert mock_send.call_args[1]["data"]["product_id"] == product_id


@pytest.mark.asyncio
async def test_get_orders(ac):
    headers, product_id = await create_user_and_product(ac)

    # Создаем заказ
    with patch("app.routers.orders.send_message", new_callable=AsyncMock):
        await ac.post(
            "/api/orders",
            json={"product_id": product_id, "quantity": 1},
            headers=headers,
        )

    # Получаем список
    response = await ac.get("/api/orders", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["product_id"] == product_id
