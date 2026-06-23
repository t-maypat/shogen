from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    desc,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

JSON_VARIANT = JSON().with_variant(JSONB(astext_type=Text()), "postgresql")


class Campaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        Index("campaigns_tenant_created_idx", "tenant_id", desc("created_at")),
        Index("campaigns_status_idx", "status"),
    )

    tenant_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="demo",
        server_default=text("'demo'"),
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    brief_json: Mapped[dict[str, Any]] = mapped_column(JSON_VARIANT, nullable=False)

    workflow_runs: Mapped[list["WorkflowRun"]] = relationship(back_populates="campaign")
    stage_outputs: Mapped[list["StageOutput"]] = relationship(back_populates="campaign")
    creative_variants: Mapped[list["CreativeVariant"]] = relationship(
        back_populates="campaign"
    )
    policy_findings: Mapped[list["PolicyFinding"]] = relationship(
        back_populates="campaign"
    )
    approvals: Mapped[list["Approval"]] = relationship(back_populates="campaign")
    evaluation_results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="campaign"
    )
    wave_proposals: Mapped[list["WaveProposal"]] = relationship(
        back_populates="campaign"
    )
    event_log_entries: Mapped[list["EventLog"]] = relationship(back_populates="campaign")


class WorkflowRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_runs"
    __table_args__ = (
        Index("workflow_runs_campaign_created_idx", "campaign_id", desc("created_at")),
        Index("workflow_runs_status_idx", "status"),
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    current_stage: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    replay_mode: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    error_json: Mapped[dict[str, Any] | None] = mapped_column(JSON_VARIANT, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="workflow_runs")
    stage_outputs: Mapped[list["StageOutput"]] = relationship(back_populates="run")
    creative_variants: Mapped[list["CreativeVariant"]] = relationship(
        back_populates="run"
    )
    policy_findings: Mapped[list["PolicyFinding"]] = relationship(back_populates="run")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="run")
    evaluation_results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="run"
    )
    wave_proposals: Mapped[list["WaveProposal"]] = relationship(back_populates="run")
    event_log_entries: Mapped[list["EventLog"]] = relationship(back_populates="run")


class StageOutput(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "stage_outputs"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "stage_name",
            "schema_version",
            name="stage_outputs_run_stage_schema_key",
        ),
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_runs.id"),
        nullable=False,
    )
    stage_name: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_json: Mapped[dict[str, Any]] = mapped_column(JSON_VARIANT, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="stage_outputs")
    run: Mapped["WorkflowRun"] = relationship(back_populates="stage_outputs")


class CreativeVariant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "creative_variants"
    __table_args__ = (
        Index("creative_campaign_idx", "campaign_id"),
        Index("creative_persona_channel_idx", "campaign_id", "persona_id", "channel"),
        Index("creative_status_idx", "status"),
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_runs.id"),
        nullable=False,
    )
    persona_id: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    journey_stage: Mapped[str] = mapped_column(Text, nullable=False)
    primary_kpi: Mapped[str] = mapped_column(Text, nullable=False)
    revision_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    copy_json: Mapped[dict[str, Any]] = mapped_column(JSON_VARIANT, nullable=False)
    parent_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("creative_variants.id"),
        nullable=True,
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="creative_variants")
    run: Mapped["WorkflowRun"] = relationship(back_populates="creative_variants")
    parent_variant: Mapped[CreativeVariant | None] = relationship(
        remote_side="CreativeVariant.id",
        back_populates="child_variants",
    )
    child_variants: Mapped[list["CreativeVariant"]] = relationship(
        back_populates="parent_variant"
    )
    policy_findings: Mapped[list["PolicyFinding"]] = relationship(
        back_populates="variant"
    )
    evaluation_results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="variant"
    )


class PolicyFinding(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "policy_findings"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_runs.id"),
        nullable=False,
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("creative_variants.id"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    rule_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    finding_type: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON_VARIANT,
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="policy_findings")
    run: Mapped["WorkflowRun"] = relationship(back_populates="policy_findings")
    variant: Mapped["CreativeVariant"] = relationship(back_populates="policy_findings")


class Approval(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "approvals"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_runs.id"),
        nullable=False,
    )
    approved_by: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="approvals")
    run: Mapped["WorkflowRun"] = relationship(back_populates="approvals")


class EvaluationResult(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "evaluation_results"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_runs.id"),
        nullable=False,
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("creative_variants.id"),
        nullable=False,
    )
    persona_id: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    scores_json: Mapped[dict[str, Any]] = mapped_column(JSON_VARIANT, nullable=False)
    total_score: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    campaign: Mapped["Campaign"] = relationship(back_populates="evaluation_results")
    run: Mapped["WorkflowRun"] = relationship(back_populates="evaluation_results")
    variant: Mapped["CreativeVariant"] = relationship(back_populates="evaluation_results")


class WaveProposal(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "wave_proposals"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_runs.id"),
        nullable=False,
    )
    proposal_json: Mapped[dict[str, Any]] = mapped_column(JSON_VARIANT, nullable=False)
    rationale_json: Mapped[dict[str, Any]] = mapped_column(JSON_VARIANT, nullable=False)

    campaign: Mapped["Campaign"] = relationship(back_populates="wave_proposals")
    run: Mapped["WorkflowRun"] = relationship(back_populates="wave_proposals")


class EventLog(CreatedAtMixin, Base):
    __tablename__ = "event_log"
    __table_args__ = (
        Index("event_log_campaign_id_idx", "campaign_id", "id"),
        Index("event_log_run_id_idx", "run_id", "id"),
    )

    id: Mapped[int] = mapped_column(
        Integer().with_variant(BigInteger(), "postgresql"),
        primary_key=True,
        autoincrement=True,
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workflow_runs.id"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    stage: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON_VARIANT, nullable=False)

    campaign: Mapped["Campaign"] = relationship(back_populates="event_log_entries")
    run: Mapped[WorkflowRun | None] = relationship(back_populates="event_log_entries")
