"""Razorpay orders and confirmation."""

from pydantic import BaseModel

from app.api.schemas.bookings import BookingOut


class PaymentOrderIn(BaseModel):
    booking_id: str
    method: str  # "upi" | "card" | "netbanking"


class PrefillOut(BaseModel):
    name: str | None
    contact: str | None
    email: str | None


class PaymentOrderOut(BaseModel):
    order_id: str  # our local PaymentOrder.id
    razorpay_order_id: str
    razorpay_key_id: str  # PUBLIC key only — never send key_secret or webhook_secret
    amount: int  # paise
    currency: str
    status: str
    prefill: PrefillOut


class PaymentConfirmIn(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str


class PaymentConfirmOut(BaseModel):
    status: str
    booking: BookingOut
