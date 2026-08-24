import os
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .models import User

bearer_scheme = HTTPBearer(auto_error=False)
DEV_TOKEN_ISSUER = "recipe-lab-dev-login"


def _unauthorized(detail: str = "Invalid or expired access token") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


@lru_cache(maxsize=4)
def _jwks_client(supabase_url: str) -> PyJWKClient:
    return PyJWKClient(f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json")


def _decode_supabase_token(token: str) -> dict:
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    if not supabase_url:
        raise _unauthorized("Server authentication is not configured")
    try:
        signing_key = _jwks_client(supabase_url).get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience="authenticated",
            issuer=f"{supabase_url}/auth/v1",
        )
    except jwt.PyJWTError as error:
        raise _unauthorized() from error


def _decode_dev_token(token: str) -> dict | None:
    if os.getenv("ENABLE_DEV_LOGIN_BYPASS", "").lower() != "true":
        return None
    secret = os.getenv("DEV_LOGIN_BYPASS_SECRET")
    if not secret:
        return None
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"], issuer=DEV_TOKEN_ISSUER)
    except jwt.PyJWTError:
        return None
    return payload if payload.get("role") == "authenticated" else None


def _user_for_claims(claims: dict, db: Session) -> User:
    subject = claims.get("sub")
    if not isinstance(subject, str):
        raise _unauthorized()
    try:
        supabase_user_id = str(uuid.UUID(subject))
    except ValueError as error:
        raise _unauthorized() from error

    user = db.scalar(select(User).where(User.supabase_user_id == supabase_user_id))
    if user:
        return user

    email = claims.get("email")
    if not isinstance(email, str) or not email:
        email = f"{supabase_user_id}@supabase.local"
    legacy_user = db.scalar(
        select(User).where(User.email == email, User.supabase_user_id.is_(None))
    )
    if legacy_user:
        legacy_user.supabase_user_id = supabase_user_id
        db.commit()
        return legacy_user
    user = User(
        supabase_user_id=supabase_user_id,
        email=email,
        username=f"user-{supabase_user_id[:8]}",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        user = db.scalar(select(User).where(User.supabase_user_id == supabase_user_id))
        if not user:
            raise
    return user


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Sign in required")
    claims = _decode_dev_token(credentials.credentials) or _decode_supabase_token(credentials.credentials)
    return _user_for_claims(claims, db)


def issue_dev_token() -> tuple[str, str]:
    if os.getenv("ENABLE_DEV_LOGIN_BYPASS", "").lower() != "true":
        raise HTTPException(status_code=404, detail="Not found")
    secret = os.getenv("DEV_LOGIN_BYPASS_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="Development login bypass is not configured")
    user_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "recipe-lab-development-user"))
    token = jwt.encode(
        {
            "sub": user_id,
            "role": "authenticated",
            "iss": DEV_TOKEN_ISSUER,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        },
        secret,
        algorithm="HS256",
    )
    return token, user_id
