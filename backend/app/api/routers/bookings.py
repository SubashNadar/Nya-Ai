"""Booking endpoints. The rules live in app.services.bookings."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas.bookings import (
    BookingIn,
    BookingOut,
    BookingRespondIn,
    BookingsListOut,
)
from app.core.security import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.services import bookings as svc

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut)
def create_booking(
    payload: BookingIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    return svc.create(db, payload, user)


@router.get("/me", response_model=BookingsListOut)
def my_bookings(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> BookingsListOut:
    return BookingsListOut(bookings=svc.list_for(db, user))


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    return svc.with_lawyer(db, svc.get_owned(db, booking_id, user))


@router.patch("/{booking_id}/respond", response_model=BookingOut)
def respond_booking(
    booking_id: str,
    payload: BookingRespondIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    return svc.respond(db, booking_id, payload.action, user)
