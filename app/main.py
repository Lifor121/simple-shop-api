from fastapi import FastAPI
from app.routers import auth
# from app.routers import products # Будут добавлены позже
# from app.routers import orders # Будут добавлены позже

app = FastAPI(
    title="Simple Shop API",
    description="A simple e-commerce API built with FastAPI, PostgreSQL, Redis, and RabbitMQ.",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "Welcome to the Simple Shop API!"}


app.include_router(auth.router, prefix="/api", tags=["Auth"])
# app.include_router(products.router, prefix="/api", tags=["Products"])
# app.include_router(orders.router, prefix="/api", tags=["Orders"])
