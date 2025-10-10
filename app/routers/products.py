from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from app.database import get_async_session
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.models import Product
from app.dependencies import get_current_active_user  # Для аутентификации
from typing import Any, Union


router = APIRouter()


@router.get("/products", response_model=list[ProductResponse])
async def read_products(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(select(Product).offset(skip).limit(limit))
    products = result.scalars().all()
    return products


@router.post(
    "/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED
)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: Any = Depends(get_current_active_user),  # Требуется аутентификация
):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
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
    current_user: Any = Depends(get_current_active_user),  # Требуется аутентификация
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    update_data = product_update.model_dump(
        exclude_unset=True
    )  # Игнорируем поля, которые не были предоставлены
    for key, value in update_data.items():
        setattr(product, key, value)

    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: Any = Depends(get_current_active_user),  # Требуется аутентификация
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    await db.delete(product)
    await db.commit()
    return {"message": "Product deleted successfully"}
