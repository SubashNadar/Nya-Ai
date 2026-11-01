"""Auth endpoints: demo OTP login, guest login, current-user lookup, logout."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.schemas.auth import (
    GuestIn,
    LogoutOut,
    MeOut,
    OtpRequestIn,
    OtpRequestOut,
    OtpVerifyIn,
    TokenOut,
    UserOut,
)
from app.core.security import (
    _bearer,
    create_access_token,
    decode_access_token,
    get_current_user,
    is_valid_otp,
    normalize_phone,
)
from app.db.models import RevokedToken, User, utcnow
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/otp/request", response_model=OtpRequestOut)
def request_otp(payload: OtpRequestIn) -> OtpRequestOut:
    if not normalize_phone(payload.phone):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid phone number")
    # No real SMS provider (demo convenience, see the original design spec) — nothing
    # to send, just acknowledge so the frontend can show the OTP step.
    return OtpRequestOut(sent=True)


@router.post("/otp/verify", response_model=TokenOut)
def verify_otp(payload: OtpVerifyIn, db: Session = Depends(get_db)) -> TokenOut:
    phone = normalize_phone(payload.phone)
    if not phone:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid phone number")
    if not is_valid_otp(payload.otp):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Enter the 4-digit OTP")
    if payload.role not in ("user", "lawyer"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid role")

    if payload.role == "lawyer":
        # Lawyer OTP login only matches an existing seeded lawyer account by phone —
        # never auto-creates one. See docs/DECISIONS.md "Resolution pass
        # with user, 2026-07-18" (#4).
        user = db.query(User).filter(User.phone == phone, User.role == "lawyer").first()
        if user is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="No lawyer account is registered for this number.",
            )
    else:
        user = db.query(User).filter(User.phone == phone, User.role == "user").first()
        if user is None:
            # No name is ever collected in the phone-login flow (UI reference §1 only asks
            # for a mobile number), so name stays null; the frontend applies the "friend"
            # fallback for that case per the UI reference dashboard greeting rule.
            user = User(role="user", name=None, initials="U", phone=phone)
            db.add(user)
            db.commit()
            db.refresh(user)

    token = create_access_token(user.id)
    return TokenOut(token=token, user=UserOut.model_validate(user))


@router.post("/guest", response_model=TokenOut)
def guest_login(payload: GuestIn, db: Session = Depends(get_db)) -> TokenOut:
    if payload.role not in ("user", "lawyer"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid role")

    if payload.role == "lawyer":
        # Reuse the single canonical demo-lawyer account (seeded, linked to Meera
        # Krishnan) rather than minting a new one each time — the Lawyer Portal header
        # is hardcoded to her identity in the UI reference (§8).
        user = db.query(User).filter(User.role == "lawyer").first()
        if user is None:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, detail="Demo lawyer account not seeded"
            )
    else:
        user = User(role="user", name="Guest", initials="G", phone=None)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(user.id)
    return TokenOut(token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)) -> MeOut:
    return MeOut(user=UserOut.model_validate(user))


@router.post("/logout", response_model=LogoutOut)
def logout(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LogoutOut:
    # `user` dependency guarantees `creds` is present and decodable; re-decode here to
    # get the full claim set (jti/exp) needed to record the revocation.
    assert creds is not None
    payload = decode_access_token(creds.credentials)
    if payload is not None:
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti is not None and exp is not None:
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
            if db.get(RevokedToken, jti) is None:
                db.add(RevokedToken(jti=jti, user_id=user.id, expires_at=expires_at))
            # Prune expired revocations opportunistically so the table stays bounded.
            db.query(RevokedToken).filter(RevokedToken.expires_at < utcnow()).delete()
            db.commit()
    return LogoutOut(ok=True)
