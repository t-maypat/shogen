from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.brief import Channel, NonEmptyStr


class GoogleSearchCopy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headlines: list[NonEmptyStr] = Field(min_length=3, max_length=15)
    descriptions: list[NonEmptyStr] = Field(min_length=2, max_length=4)
    path: str | None = None
    final_url_label: str | None = None
    cta: NonEmptyStr


class LinkedInCopy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intro_text: NonEmptyStr
    headline: NonEmptyStr
    description: NonEmptyStr
    cta: NonEmptyStr


class EmailCopy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: NonEmptyStr
    preheader: NonEmptyStr
    body: NonEmptyStr
    cta: NonEmptyStr


CreativeCopy = GoogleSearchCopy | LinkedInCopy | EmailCopy


class CreativeVariantOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    client_variant_id: NonEmptyStr
    persona_id: str
    channel: Channel
    journey_stage: NonEmptyStr
    primary_kpi_id: NonEmptyStr
    claims: list[NonEmptyStr] = Field(default_factory=list)
    disclosure: str | None = None
    copy_payload: CreativeCopy = Field(alias="copy")

    @field_validator("persona_id")
    @classmethod
    def ensure_stable_persona_id(cls, value: str) -> str:
        if value not in {"p1", "p2", "p3"}:
            raise ValueError("persona_id must be one of p1, p2, or p3")
        return value

    @model_validator(mode="after")
    def ensure_copy_matches_channel(self) -> "CreativeVariantOut":
        if self.channel == "google_search" and not isinstance(
            self.copy_payload,
            GoogleSearchCopy,
        ):
            raise ValueError("google_search variants must use GoogleSearchCopy")
        if self.channel == "linkedin_sponsored_post" and not isinstance(
            self.copy_payload,
            LinkedInCopy,
        ):
            raise ValueError("linkedin_sponsored_post variants must use LinkedInCopy")
        if self.channel == "email" and not isinstance(self.copy_payload, EmailCopy):
            raise ValueError("email variants must use EmailCopy")
        return self


class CreativeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variants: list[CreativeVariantOut]

    @field_validator("variants")
    @classmethod
    def ensure_nine_variants(cls, value: list[CreativeVariantOut]) -> list[CreativeVariantOut]:
        if len(value) != 9:
            raise ValueError("creative output must contain exactly nine variants")
        return value

    @model_validator(mode="after")
    def ensure_unique_pairs(self) -> "CreativeOutput":
        pairs = {(variant.persona_id, variant.channel) for variant in self.variants}
        if len(pairs) != 9:
            raise ValueError(
                "creative output must contain exactly one variant per persona/channel pair"
            )
        return self
