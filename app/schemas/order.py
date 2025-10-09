from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


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
    status: Literal["pending", "completed", "cancelled"] = "pending"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
