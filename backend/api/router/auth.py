"""
Роутер авторизации — login и получение JWT-токена.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.schemas import LoginRequest, TokenResponse
from core.db import get_db
from core.logger import get_logger
from core.security import create_access_token, verify_password
from db.psql.crud.users import get_user_by_username

log = get_logger("auth_router")
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Аутентификация — возвращает JWT-токен."""
    user = await get_user_by_username(db, body.username)
    if not user or not verify_password(body.password, user.hashed_password):
        log.warning(f"Неудачная попытка входа: username={body.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )
    token = create_access_token({"sub": user.username})
    log.info(f"Успешный вход: username={user.username}")
    return TokenResponse(access_token=token)
