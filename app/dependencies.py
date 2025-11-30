from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_async_session
from app.models import User
from app.security import decode_access_token
from app.schemas.token import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_session)
):
    token_data = decode_access_token(token)
    user_result = await db.execute(select(User).where(User.email == token_data.email))
    current_user = user_result.scalars().first()

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user


# Пример для админа
# async def get_current_active_admin(current_user: User = Depends(get_current_user)):
#     if not current_user.is_admin: # Предполагается поле is_admin в модели User
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin")
#     return current_user
