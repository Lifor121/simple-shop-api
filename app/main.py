from fastapi import FastAPI

from app.routers import auth, orders, products

# Описание тегов для группировки в Swagger UI
tags_metadata = [
    {
        "name": "Auth",
        "description": "Регистрация и аутентификация пользователей. Получение JWT токенов.",
    },
    {
        "name": "Products",
        "description": "Управление товарами. Просмотр, создание, обновление и удаление.",
    },
    {
        "name": "Orders",
        "description": "Создание и управление заказами. Обработка статусов и очередей.",
    },
]

app = FastAPI(
    title="Simple Shop API",
    description="""
    Асинхронное API для интернет-магазина.

    Стек технологий:
    * **FastAPI** (Python 3.10+)
    * **PostgreSQL** (Asyncpg + SQLAlchemy 2.0)
    * **Redis** (Кэширование)
    * **RabbitMQ** (Очереди событий: регистрация, заказы)
    """,
    version="0.1.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "Support",
        "email": "support@verycoolsupport.com",
    },
)


@app.get("/")
async def root():
    return {"message": "Welcome to the Simple Shop API!"}


app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(products.router, prefix="/api", tags=["Products"])
app.include_router(orders.router, prefix="/api", tags=["Orders"])
