from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from app.database import get_async_session
from app.schemas.order import OrderCreate, OrderStatus, OrderResponse
from app.models import Order, Product, User
from app.dependencies import get_current_active_user
from app.cache import get_redis_client
from redis.asyncio import Redis
import json
from typing import Any, Literal
from datetime import datetime
from app.broker import send_message


router = APIRouter()

CACHE_TTL = 60


@router.get("/orders", response_model=list[OrderResponse])
async def read_orders(
    status: Literal["pending", "completed", "cancelled"] | None = Query(
        None, description="Filter orders by status"
    ),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
    redis: Redis = Depends(get_redis_client),
):
    cache_key = f"orders:{current_user.id}:{status}:{skip}:{limit}"
    cached_orders = await redis.get(cache_key)

    if cached_orders:
        return json.loads(cached_orders)

    query = select(Order).where(Order.user_id == current_user.id)

    if status:
        query = query.where(Order.status == status)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    orders = result.scalars().all()

    order_responses = [OrderResponse.from_orm(o) for o in orders]
    orders_for_cache = [o.model_dump(mode="json") for o in order_responses]
    await redis.set(cache_key, json.dumps(orders_for_cache), ex=CACHE_TTL)

    return order_responses


@router.post(
    "/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED
)
async def create_order(
    order: OrderCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
    redis: Redis = Depends(get_redis_client),
):
    product_result = await db.execute(
        select(Product).where(Product.id == order.product_id)
    )
    product = product_result.scalars().first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    db_order = Order(
        user_id=current_user.id,
        product_id=order.product_id,
        quantity=order.quantity,
        status="pending",
    )
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)

    keys = await redis.keys(f"orders:{current_user.id}:*")
    if keys:
        await redis.delete(*keys)

    # RabbitMQ: Отправка события
    # Приводим статус к строке, если это Enum, чтобы избежать ошибок JSON
    status_value = (
        db_order.status.value if hasattr(db_order.status, "value") else db_order.status
    )

    await send_message(
        event_type="order_created",
        data={
            "id": db_order.id,
            "user_id": db_order.user_id,
            "product_id": db_order.product_id,
            "quantity": db_order.quantity,
            "status": status_value,
        },
    )

    return db_order


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def read_order(
    order_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalars().first()
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or you don't have permission to view it",
        )
    return order


@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    order_status: OrderStatus,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
    redis: Redis = Depends(get_redis_client),
):
    stmt = (
        update(Order)
        .where(Order.id == order_id, Order.user_id == current_user.id)
        .values(status=order_status.status)
    )
    result = await db.execute(stmt)

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or you don't have permission to update it",
        )

    await db.commit()

    keys = await redis.keys(f"orders:{current_user.id}:*")
    if keys:
        await redis.delete(*keys)

    updated_order = await db.get(Order, order_id)

    return updated_order


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
    redis: Redis = Depends(get_redis_client),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalars().first()
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or you don't have permission to delete it",
        )

    await db.delete(order)
    await db.commit()

    keys = await redis.keys(f"orders:{current_user.id}:*")
    if keys:
        await redis.delete(*keys)

    return {"message": "Order deleted successfully"}
