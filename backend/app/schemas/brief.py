from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Channel = Literal["google_search", "linkedin_sponsored_post", "email"]


class CampaignBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_name: NonEmptyStr
    product_category: NonEmptyStr
    objective: NonEmptyStr
    audience_summary: NonEmptyStr
    budget_range: NonEmptyStr | None = None
    duration_days: int | None = Field(default=None, gt=0)
    brand_voice: list[NonEmptyStr] = Field(default_factory=list)
    required_claims: list[NonEmptyStr] = Field(default_factory=list)
    risky_claims: list[NonEmptyStr] = Field(default_factory=list)
    channels: list[Channel] = Field(min_length=1)
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("channels")
    @classmethod
    def ensure_unique_channels(cls, value: list[Channel]) -> list[Channel]:
        if len(set(value)) != len(value):
            raise ValueError("channels must not contain duplicates")
        return value
