from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.campaigns import ApiErrorBody


class DemoReplayRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: Literal["fintech"] = "fintech"


class DemoReplayData(BaseModel):
    campaign_id: uuid.UUID
    run_id: uuid.UUID
    status: str
    replay_mode: bool


class DemoReplayEnvelope(BaseModel):
    data: DemoReplayData | None
    error: ApiErrorBody | None = None
