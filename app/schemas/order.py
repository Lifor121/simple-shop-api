from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal, Optional
from app.models import OrderStatus as OrderStatusEnum

class OrderBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderCreate(OrderBase):
    pass


class OrderStatus(BaseModel):
    status: Literal["pending", "completed", "cancelled"]


class OrderResponse(OrderBase):
    id: int
    user_id: int
    status: OrderStatusEnum = "pending"
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
