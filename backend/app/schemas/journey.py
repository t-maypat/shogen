from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.schemas.brief import Channel, NonEmptyStr

JourneyStage = Literal["discovery", "consideration", "nurture", "conversion"]


class JourneyStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: NonEmptyStr
    persona_id: Literal["p1", "p2", "p3"]
    channel: Channel
    journey_stage: JourneyStage
    objective: NonEmptyStr
    primary_kpi_id: NonEmptyStr
    allocation_percent: int
    message_angle: NonEmptyStr

    @field_validator("allocation_percent")
    @classmethod
    def ensure_positive_allocation(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("allocation_percent must be greater than zero")
        return value


class JourneyOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    steps: list[JourneyStep]

    @field_validator("steps")
    @classmethod
    def ensure_nine_steps(cls, value: list[JourneyStep]) -> list[JourneyStep]:
        if len(value) != 9:
            raise ValueError("journey must contain exactly nine steps")
        return value

    @model_validator(mode="after")
    def ensure_coverage_and_allocation(self) -> "JourneyOutput":
        pairs = {(step.persona_id, step.channel) for step in self.steps}
        if len(pairs) != 9:
            raise ValueError("journey must contain exactly one step per persona/channel pair")

        allocation_total = sum(step.allocation_percent for step in self.steps)
        if allocation_total != 100:
            raise ValueError("journey allocation_percent must total 100")
        return self
