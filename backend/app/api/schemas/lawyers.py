"""Advocate listings and profiles."""

from pydantic import BaseModel, ConfigDict


class LawyerCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    initials: str
    avatar_color: str
    spec: str
    category: str
    exp: int
    langs: list[str]
    rating: float
    reviews: int
    next_slot: str


class LawyerDetail(LawyerCard):
    bio: str
    bar_council_id: str
    price: int
    price_struck: int


class LawyersListOut(BaseModel):
    lawyers: list[LawyerCard]
