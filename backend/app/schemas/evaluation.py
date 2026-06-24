from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.brief import NonEmptyStr


class EvaluationScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_fit: int = Field(ge=0, le=100)
    channel_fit: int = Field(ge=0, le=100)
    cta_clarity: int = Field(ge=0, le=100)
    policy_quality: int = Field(ge=0, le=100)
    journey_consistency: int = Field(ge=0, le=100)
    weighted_total: int = Field(ge=0, le=100)


class Wave2Rewrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: NonEmptyStr
    client_variant_id: NonEmptyStr
    rewritten_copy: dict[str, Any]
    rationale: NonEmptyStr


class Wave2AIOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rationale: NonEmptyStr
    allocation_summary: list[NonEmptyStr] = Field(min_length=1)
    rewrites: list[Wave2Rewrite] = Field(default_factory=list)
