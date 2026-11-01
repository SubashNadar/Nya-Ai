"""Pydantic request/response models: the API contract, one module per router.

Mirrored by frontend/src/types.ts. Import from the module that owns a model, or from here.
"""

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
from app.api.schemas.bookings import (
    BookingIn,
    BookingOut,
    BookingRespondIn,
    BookingsListOut,
    ConsultBrief,
)
from app.api.schemas.chat import (
    ChatHistoryOut,
    ChatMessageIn,
    ChatMessageOut,
    ChatMessageRecord,
)
from app.api.schemas.dashboard import (
    LawyerDashboardOut,
    RecentQuestion,
    UserDashboardOut,
)
from app.api.schemas.lawyers import LawyerCard, LawyerDetail, LawyersListOut
from app.api.schemas.messages import (
    MessageOut,
    MessageThreadOut,
    MessageThreadsListOut,
    ThreadReplyIn,
    ThreadReplyOut,
)
from app.api.schemas.payments import (
    PaymentConfirmIn,
    PaymentConfirmOut,
    PaymentOrderIn,
    PaymentOrderOut,
    PrefillOut,
)
from app.api.schemas.support import SupportIn, SupportOut

__all__ = [
    "OtpRequestIn",
    "OtpRequestOut",
    "OtpVerifyIn",
    "GuestIn",
    "UserOut",
    "TokenOut",
    "MeOut",
    "LogoutOut",
    "ChatMessageIn",
    "ChatMessageOut",
    "ChatMessageRecord",
    "ChatHistoryOut",
    "LawyerCard",
    "LawyerDetail",
    "LawyersListOut",
    "ConsultBrief",
    "BookingIn",
    "BookingRespondIn",
    "BookingOut",
    "BookingsListOut",
    "PaymentOrderIn",
    "PrefillOut",
    "PaymentOrderOut",
    "PaymentConfirmIn",
    "PaymentConfirmOut",
    "MessageOut",
    "MessageThreadOut",
    "MessageThreadsListOut",
    "ThreadReplyIn",
    "ThreadReplyOut",
    "RecentQuestion",
    "UserDashboardOut",
    "LawyerDashboardOut",
    "SupportIn",
    "SupportOut",
]
