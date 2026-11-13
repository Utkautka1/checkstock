"""
Dependency для получения текущего пользователя из JWT-токена.
Используется в защищённых роутерах через Depends(get_current_user).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from core.logger import get_logger
from core.security import decode_token
from db.psql.crud.users import get_user_by_username

log = get_logger("auth")
bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    """
    Извлекает пользователя из Bearer-токена.
    401 — если токен невалиден или пользователь не найден.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не авторизован",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        log.warning("Невалидный JWT токен")
        raise credentials_exception

    user = await get_user_by_username(db, username)
    if not user:
        raise credentials_exception

    return user
