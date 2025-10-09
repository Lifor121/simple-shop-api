from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    price: float = Field(..., gt=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=3, max_length=100)
    price: float | None = Field(None, gt=0)


class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True
