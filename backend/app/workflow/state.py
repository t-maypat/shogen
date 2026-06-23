from __future__ import annotations

import uuid
from typing import Any, Literal, TypedDict


WorkflowMode = Literal["live", "replay"]


class WorkflowState(TypedDict, total=False):
    campaign_id: uuid.UUID
    run_id: uuid.UUID
    mode: WorkflowMode
    brief: dict[str, Any]
    strategy: dict[str, Any]
    journey: dict[str, Any]
    creative: dict[str, Any]
    policy: dict[str, Any]
    approval_required: dict[str, Any]
