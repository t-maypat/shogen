from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowEventPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    campaign_id: uuid.UUID = Field(alias="campaignId")
    run_id: uuid.UUID | None = Field(alias="runId", default=None)
    stage: str | None = None
    status: str
    timestamp: datetime
    display: dict[str, Any] | None = None
