from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.brief import NonEmptyStr
from app.schemas.creative import CreativeCopy

SemanticFindingType = Literal[
    "unsupported_claim",
    "tone",
    "sensitivity",
    "consistency",
]
SemanticSeverity = Literal["blocking", "high", "medium", "low", "info"]
SemanticReviewStatus = Literal["passed", "warning", "blocked"]


class SemanticFindingOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_type: SemanticFindingType
    severity: SemanticSeverity
    evidence: NonEmptyStr
    message: NonEmptyStr
    suggestion: str | None = None


class SemanticVariantReviewOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_variant_id: NonEmptyStr
    status: SemanticReviewStatus
    findings: list[SemanticFindingOut] = Field(default_factory=list)


class SemanticReviewOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviews: list[SemanticVariantReviewOut]


class CreativeRevisionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    claims: list[NonEmptyStr] = Field(default_factory=list)
    disclosure: str | None = None
    copy_payload: CreativeCopy = Field(alias="copy")
