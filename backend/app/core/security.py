"""JWT issuance/verification, current-user dependencies, demo OTP + guest login helpers."""

import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import RevokedToken, User
from app.db.session import get_db

settings = get_settings()

# Demo OTP convention (see the original design spec "Login"): the mockup hardcodes
# `1234`; the real backend accepts *any* 4-digit string instead of one magic value.
OTP_RE = re.compile(r"^\d{4}$")

_bearer = HTTPBearer(auto_error=False)


def is_valid_otp(otp: str) -> bool:
    return bool(OTP_RE.match(otp))


def normalize_phone(phone: str) -> str:
    """Light normalization: strip everything but digits, keep last 10 (Indian mobile).

    Contract doesn't specify phone validation rules (demo has no real SMS provider).
    Smallest reversible default — see docs/DECISIONS.md.
    """
    digits = re.sub(r"\D", "", phone)
    return digits[-10:] if len(digits) >= 10 else digits


def create_access_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "jti": uuid4().hex, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT, returning its full claim set (sub/jti/exp) or None."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def _is_revoked(db: Session, jti: str | None) -> bool:
    if jti is None:
        return False
    return db.get(RevokedToken, jti) is not None


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(creds.credentials)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if _is_revoked(db, payload.get("jti")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = payload.get("sub")
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if creds is None:
        return None
    payload = decode_access_token(creds.credentials)
    if payload is None:
        return None
    if _is_revoked(db, payload.get("jti")):
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return db.get(User, user_id)


def require_lawyer(user: User = Depends(get_current_user)) -> User:
    if user.role != "lawyer":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Lawyer account required")
    return user
