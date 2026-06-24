from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.db.models import EventLog
from app.repositories.campaigns import CampaignRepository
from app.schemas.events import WorkflowEventPayload


class EventService:
    def __init__(self, repository: CampaignRepository) -> None:
        self.repository = repository

    def record_workflow_event(
        self,
        *,
        campaign_id: uuid.UUID,
        run_id: uuid.UUID | None,
        event_type: str,
        status: str,
        stage: str | None = None,
        display: dict[str, Any] | None = None,
    ) -> EventLog:
        payload = WorkflowEventPayload(
            campaignId=campaign_id,
            runId=run_id,
            stage=stage,
            status=status,
            timestamp=datetime.now(timezone.utc),
            display=display,
        )
        return self.repository.create_event(
            campaign_id=campaign_id,
            run_id=run_id,
            event_type=event_type,
            stage=stage,
            payload_json=payload.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            ),
        )

    @staticmethod
    def format_sse(event: EventLog) -> str:
        payload = json.dumps(event.payload_json, separators=(",", ":"))
        return f"id: {event.id}\nevent: {event.event_type}\ndata: {payload}\n\n"
