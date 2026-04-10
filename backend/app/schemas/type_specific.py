"""Type-specific data schemas for each content_type returned by link-analyzer."""

from typing import Literal, Optional

from pydantic import BaseModel, HttpUrl


class MenuItem(BaseModel):
    name: str
    price: Optional[int] = None  # 원 단위


class PlaceData(BaseModel):
    address: Optional[str] = None
    hours: Optional[str] = None
    menus: Optional[list[MenuItem]] = None
    price_range: Optional[str] = None
    reservation_required: Optional[bool] = None
    visit_tips: Optional[list[str]] = None
    phone: Optional[str] = None
    website: Optional[str] = None


class EventData(BaseModel):
    start_date: Optional[str] = None   # ISO 8601 date string
    end_date: Optional[str] = None
    time: Optional[str] = None
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    ticket_price: Optional[str] = None
    booking_url: Optional[str] = None
    organizer: Optional[str] = None
    pre_registration_required: Optional[bool] = None


class TipItem(BaseModel):
    step: int
    description: str


class TipsData(BaseModel):
    tip_list: Optional[list[TipItem]] = None
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    materials: Optional[list[str]] = None
    sub_field: Optional[str] = None
    estimated_time: Optional[str] = None
    cautions: Optional[list[str]] = None


class PriceInfo(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None  # e.g. "KRW", "USD"


class ReviewData(BaseModel):
    product_name: Optional[str] = None
    brand: Optional[str] = None
    pros: Optional[list[str]] = None
    cons: Optional[list[str]] = None
    price: Optional[PriceInfo] = None
    rating: Optional[float] = None  # 0.0–5.0
    recommended_for: Optional[list[str]] = None
    purchase_url: Optional[str] = None
