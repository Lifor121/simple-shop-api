import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.cache import get_redis_client
from app.database import Base, get_async_session
from app.main import app
from app.models import Order, Product, User

# Используем in-memory SQLite для тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

#  Фикстуры инфраструктуры


@pytest.fixture(scope="session")
def event_loop():
    """Создает экземпляр цикла обработки событий по умолчанию для каждого тестового примера"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def init_db():
    """Создает и очищает таблицы перед каждым тестом"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session(init_db) -> AsyncGenerator[AsyncSession, None]:
    """Предоставляет сессию БД"""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def redis_mock():
    """Mock для Redis"""
    server = fakeredis.FakeServer()
    redis = fakeredis.aioredis.FakeRedis(
        server=server, encoding="utf-8", decode_responses=True
    )
    yield redis
    await redis.flushall()


# Mock для RabbitMQ
@pytest.fixture(autouse=True)
async def mock_rabbitmq():
    """
    Автоматически подменяет aio_pika во всех тестах.
    Предотвращает реальные попытки подключения к RabbitMQ.
    """
    with patch("app.broker.aio_pika") as mock_pika:
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()

        mock_pika.connect_robust = AsyncMock(return_value=mock_connection)

        mock_connection.__aenter__.return_value = mock_connection
        mock_connection.__aexit__.return_value = None

        mock_connection.channel.return_value = mock_channel

        yield mock_pika


# Подмена зависимостей)
@pytest.fixture(scope="function")
async def ac(db_session, redis_mock) -> AsyncGenerator[AsyncClient, None]:
    """Асинхронный HTTP клиент с переопределенными зависимостями"""

    async def override_get_async_session():
        yield db_session

    async def override_get_redis_client():
        yield redis_mock

    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[get_redis_client] = override_get_redis_client

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
