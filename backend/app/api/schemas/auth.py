"""Sign-in and the current user."""

from pydantic import BaseModel, ConfigDict


class OtpRequestIn(BaseModel):
    phone: str


class OtpRequestOut(BaseModel):
    sent: bool = True


class OtpVerifyIn(BaseModel):
    phone: str
    otp: str
    role: str = "user"  # "user" | "lawyer"


class GuestIn(BaseModel):
    role: str  # "user" | "lawyer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    name: str | None
    initials: str
    phone: str | None


class TokenOut(BaseModel):
    token: str
    user: UserOut


class MeOut(BaseModel):
    user: UserOut


class LogoutOut(BaseModel):
    ok: bool = True
