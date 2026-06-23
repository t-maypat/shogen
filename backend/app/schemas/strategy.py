from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.brief import NonEmptyStr


class KPI(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: NonEmptyStr
    label: NonEmptyStr
    reason: NonEmptyStr


class Persona(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Literal["p1", "p2", "p3"]
    name: NonEmptyStr
    summary: NonEmptyStr
    needs: list[NonEmptyStr] = Field(min_length=1)
    objections: list[NonEmptyStr] = Field(min_length=1)
    preferred_tone: NonEmptyStr
    decision_trigger: NonEmptyStr
    risk_sensitivity: Literal["low", "medium", "high"]


class StrategyOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kpis: list[KPI]
    personas: list[Persona]

    @field_validator("kpis")
    @classmethod
    def ensure_three_kpis(cls, value: list[KPI]) -> list[KPI]:
        if len(value) != 3:
            raise ValueError("strategy must contain exactly three KPIs")
        return value

    @field_validator("personas")
    @classmethod
    def ensure_three_personas(cls, value: list[Persona]) -> list[Persona]:
        if len(value) != 3:
            raise ValueError("strategy must contain exactly three personas")
        return value

    @model_validator(mode="after")
    def ensure_stable_persona_ids(self) -> "StrategyOutput":
        persona_ids = [persona.id for persona in self.personas]
        if persona_ids != ["p1", "p2", "p3"]:
            raise ValueError("persona ids must be stable and ordered as p1, p2, p3")
        return self
