from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.brief import CampaignBrief, NonEmptyStr


class ApiErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | list[dict[str, Any]]


class CampaignCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyStr
    brief: CampaignBrief


class CampaignCreateData(BaseModel):
    campaign_id: uuid.UUID
    status: str


class CampaignCreateEnvelope(BaseModel):
    data: CampaignCreateData | None
    error: ApiErrorBody | None = None


class CampaignSummary(BaseModel):
    id: uuid.UUID
    tenant_id: str
    name: str
    status: str
    brief: CampaignBrief
    created_at: datetime
    updated_at: datetime


class WorkflowRunSummary(BaseModel):
    id: uuid.UUID
    status: str
    current_stage: str | None
    revision_count: int
    replay_mode: bool
    error: dict[str, Any] | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CreativeVariantSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    run_id: uuid.UUID
    client_variant_id: str
    persona_id: str
    channel: str
    journey_stage: str
    primary_kpi: str
    revision_number: int
    status: str
    claims: list[str]
    disclosure: str | None
    copy_payload: dict[str, Any] = Field(alias="copy")
    parent_variant_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class PolicyFindingSummary(BaseModel):
    id: uuid.UUID
    variant_id: uuid.UUID
    source: str
    rule_id: str | None
    severity: str
    status: str
    finding_type: str
    evidence: str
    message: str
    suggestion: str | None
    metadata: dict[str, Any] | None
    created_at: datetime
    resolved_at: datetime | None


class ApprovalSummary(BaseModel):
    id: uuid.UUID
    approved_by: str
    status: str
    notes: str | None
    created_at: datetime


class EvaluationResultSummary(BaseModel):
    id: uuid.UUID
    variant_id: uuid.UUID
    persona_id: str
    channel: str
    scores: dict[str, Any]
    total_score: Decimal
    created_at: datetime


class WaveProposalSummary(BaseModel):
    id: uuid.UUID
    proposal: dict[str, Any]
    rationale: dict[str, Any]
    created_at: datetime


class EventLogSummary(BaseModel):
    id: int
    run_id: uuid.UUID | None
    event_type: str
    stage: str | None
    payload: dict[str, Any]
    created_at: datetime


class CampaignStateData(BaseModel):
    campaign: CampaignSummary
    latest_run: WorkflowRunSummary | None
    strategy: dict[str, Any] | None
    journey: dict[str, Any] | None
    mock_deployment: dict[str, Any] | None
    creative_variants: list[CreativeVariantSummary]
    policy_findings: list[PolicyFindingSummary]
    approval: ApprovalSummary | None
    evaluation_results: list[EvaluationResultSummary]
    wave_proposal: WaveProposalSummary | None
    events: list[EventLogSummary]


class CampaignStateEnvelope(BaseModel):
    data: CampaignStateData | None
    error: ApiErrorBody | None = None


class CampaignRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["live", "replay"] = "live"


class CampaignRunData(BaseModel):
    run_id: uuid.UUID
    status: str


class CampaignRunEnvelope(BaseModel):
    data: CampaignRunData | None
    error: ApiErrorBody | None = None


class CampaignApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved_by: NonEmptyStr = "demo_marketer"
    notes: str | None = None


class CampaignApprovalData(BaseModel):
    campaign_id: uuid.UUID
    run_id: uuid.UUID
    approval: ApprovalSummary
    mock_deployment: dict[str, Any]
    status: str


class CampaignApprovalEnvelope(BaseModel):
    data: CampaignApprovalData | None
    error: ApiErrorBody | None = None
