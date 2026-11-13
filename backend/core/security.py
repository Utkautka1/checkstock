"""
Утилиты JWT-авторизации: хэширование паролей, создание и проверка токенов.
Использует bcrypt напрямую для полной совместимости с Python 3.12.
"""
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import JWTError, jwt

from core.config import settings


def hash_password(password: str) -> str:
    """Хэширует пароль через bcrypt напрямую."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Проверяет соответствие пароля хэшу."""
    plain_bytes = plain.encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")
    try:
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    """
    Создаёт JWT-токен с временем жизни из настроек.
    В payload добавляется 'exp' — время истечения.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["exp"] = expire
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Декодирует JWT. Бросает JWTError если токен невалиден или истёк.
    Вызывающая сторона обязана обработать исключение.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
