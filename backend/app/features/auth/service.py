import uuid
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token, encode_token, verify_password
from app.features.users.models import User
from app.features.users.service import get_user_by_email

redis_client = aioredis.from_url(settings.REDIS_URL)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    if not user:
        raise ValueError("Invalid email or password")
    if not user.is_active:
        raise ValueError("Email not verified")
    if user.deleted_at is not None:
        raise ValueError("Invalid email or password")
    if not verify_password(password, user.hashed_password):
        raise ValueError("Invalid email or password")
    return user


def create_access_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return encode_token(payload)


def create_refresh_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return encode_token(payload)


async def blacklist_token(token: str) -> None:
    payload = decode_token(token)
    if not payload:
        return
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        ttl = exp - int(datetime.now(timezone.utc).timestamp())
        if ttl > 0:
            await redis_client.set(f"blacklist:{jti}", "1", ex=ttl)


async def is_token_blacklisted(token: str) -> bool:
    payload = decode_token(token)
    if not payload:
        return True
    jti = payload.get("jti")
    if not jti:
        return False
    return await redis_client.exists(f"blacklist:{jti}") > 0
