from datetime import date
from enum import Enum
from pydantic import BaseModel, field_validator

class MatchStatus(str, Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    UNCLEAR = "unclear"

class ExtractedFields(BaseModel):
    hotel_name: str
    check_in: date | str
    check_out: date | str
    guests: int | str
    total_price: float | str

    @field_validator("hotel_name", mode="before")
    @classmethod
    def validate_hotel_name(cls, v):
        if not isinstance(v, str) or not v.strip():
            return "unclear"
        return v.strip()

    @field_validator("check_in", "check_out", mode="before")
    @classmethod
    def validate_dates(cls, v):
        if v in (None, "", "unclear"):
            return "unclear"
        return v

    @field_validator("guests", mode="before")
    @classmethod
    def validate_guests(cls, v):
        try:
            return int(v)
        except Exception:
            return "unclear"

    @field_validator("total_price", mode="before")
    @classmethod
    def validate_total_price(cls, v):
        try:
            return float(v)
        except Exception:
            return "unclear"

class ScreenshotClassification(str, Enum):
    INITIAL_QUOTE = "initial_quote"
    FINAL_BOOKING = "final_booking"
    UNKNOWN = "unknown"
    
class ScreenshotResult(BaseModel):
    screenshot_id: str
    classification: ScreenshotClassification
    extraction: ExtractedFields

class ComparisonItem(BaseModel):
    field: str  # hotel_name, check_in, check_out, guests, total_price
    initial_value: str
    final_value: str
    status: MatchStatus
    explanation: str
    evidence: list[str]

class StreamEvent(BaseModel):
    type: str  # progress | extraction | comparison | final
    payload: dict[str, object]
