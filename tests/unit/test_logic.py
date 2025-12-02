import pytest
from app.security import hash_password, verify_password
from app.schemas.order import OrderCreate
from pydantic import ValidationError


def test_password_hashing():
    password = "secret_password"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_order_validation():
    # Корректные данные
    order = OrderCreate(product_id=1, quantity=5)
    assert order.quantity == 5

    # Некорректные данные (quantity <= 0)
    with pytest.raises(ValidationError):
        OrderCreate(product_id=1, quantity=0)

    with pytest.raises(ValidationError):
        OrderCreate(product_id=1, quantity=-1)
