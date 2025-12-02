from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_register_user(ac):
    """Тест регистрации и отправки события в RabbitMQ"""
    user_data = {"email": "test@example.com", "password": "password123"}

    # Мокаем send_message внутри роутера auth
    with patch(
        "app.routers.auth.send_message", new_callable=AsyncMock
    ) as mock_send_message:
        response = await ac.post("/api/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data

        # Проверяем, что сообщение было отправлено в очередь
        mock_send_message.assert_called_once()
        assert mock_send_message.call_args[1]["event_type"] == "user_registered"
        assert mock_send_message.call_args[1]["data"]["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_login_user(ac):
    # Сначала регистрируем
    await ac.post("/api/register", json={"email": "login@test.com", "password": "pass"})

    # Пытаемся залогиниться
    form_data = {"username": "login@test.com", "password": "pass"}
    response = await ac.post("/api/login", data=form_data)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
