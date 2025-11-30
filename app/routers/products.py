from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from app.database import get_async_session
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.models import Product
from app.dependencies import get_current_active_user
from app.cache import get_redis_client
from redis.asyncio import Redis
import json
from typing import Any, Union


router = APIRouter()

CACHE_TTL = 60  # Cache time-to-live in seconds


@router.get("/products", response_model=list[ProductResponse])
async def read_products(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_client),
):
    cache_key = f"products:{skip}:{limit}"
    cached_products = await redis.get(cache_key)

    if cached_products:
        return json.loads(cached_products)

    result = await db.execute(select(Product).offset(skip).limit(limit))
    products = result.scalars().all()

    # Convert SQLAlchemy models to Pydantic models for response and caching
    product_responses = [ProductResponse.from_orm(p) for p in products]

    # Convert Pydantic models to a list of dicts for JSON serialization
    products_for_cache = [p.model_dump() for p in product_responses]
    await redis.set(cache_key, json.dumps(products_for_cache), ex=CACHE_TTL)

    return product_responses


@router.post(
    "/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED
)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_client),
    current_user: Any = Depends(get_current_active_user),
):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    # Invalidate cache
    await redis.delete(f"products:0:100") # A simple invalidation strategy
    return db_product


@router.get("/products/{product_id}", response_model=ProductResponse)
async def read_product(product_id: int, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_client),
    current_user: Any = Depends(get_current_active_user),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    update_data = product_update.model_dump(
        exclude_unset=True
    )
    for key, value in update_data.items():
        setattr(product, key, value)

    await db.commit()
    await db.refresh(product)
    
    # Invalidate cache
    await redis.delete(f"products:0:100")
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_client),
    current_user: Any = Depends(get_current_active_user),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    await db.delete(product)
    await db.commit()
    
    # Invalidate cache
    await redis.delete(f"products:0:100")
    return {"message": "Product deleted successfully"}
