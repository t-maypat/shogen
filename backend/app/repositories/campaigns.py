from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Approval,
    Campaign,
    CreativeVariant,
    EvaluationResult,
    EventLog,
    PolicyFinding,
    StageOutput,
    WaveProposal,
    WorkflowRun,
)


class CampaignRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_campaign(
        self,
        *,
        name: str,
        brief_json: dict,
        tenant_id: str = "demo",
    ) -> Campaign:
        campaign = Campaign(
            name=name,
            status="draft",
            tenant_id=tenant_id,
            brief_json=brief_json,
        )
        self.session.add(campaign)
        self.session.flush()
        return campaign

    def get_campaign(self, campaign_id: uuid.UUID) -> Campaign | None:
        return self.session.get(Campaign, campaign_id)

    def get_latest_run(self, campaign_id: uuid.UUID) -> WorkflowRun | None:
        stmt = (
            select(WorkflowRun)
            .where(WorkflowRun.campaign_id == campaign_id)
            .order_by(WorkflowRun.created_at.desc(), WorkflowRun.id.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def create_workflow_run(
        self,
        *,
        campaign_id: uuid.UUID,
        status: str,
        replay_mode: bool,
        started_at: datetime | None = None,
    ) -> WorkflowRun:
        run = WorkflowRun(
            campaign_id=campaign_id,
            status=status,
            replay_mode=replay_mode,
            started_at=started_at,
        )
        self.session.add(run)
        self.session.flush()
        return run

    def get_workflow_run(self, run_id: uuid.UUID) -> WorkflowRun | None:
        return self.session.get(WorkflowRun, run_id)

    def list_stage_outputs_for_run(self, run_id: uuid.UUID) -> list[StageOutput]:
        stmt = (
            select(StageOutput)
            .where(StageOutput.run_id == run_id)
            .order_by(StageOutput.created_at.desc(), StageOutput.id.desc())
        )
        return list(self.session.scalars(stmt))

    def create_stage_output(
        self,
        *,
        campaign_id: uuid.UUID,
        run_id: uuid.UUID,
        stage_name: str,
        schema_version: str,
        output_json: dict,
        prompt_version: str | None = None,
        model_name: str | None = None,
        duration_ms: int | None = None,
    ) -> StageOutput:
        stage_output = StageOutput(
            campaign_id=campaign_id,
            run_id=run_id,
            stage_name=stage_name,
            schema_version=schema_version,
            prompt_version=prompt_version,
            model_name=model_name,
            output_json=output_json,
            duration_ms=duration_ms,
        )
        self.session.add(stage_output)
        self.session.flush()
        return stage_output

    def create_creative_variant(
        self,
        *,
        campaign_id: uuid.UUID,
        run_id: uuid.UUID,
        persona_id: str,
        channel: str,
        journey_stage: str,
        primary_kpi: str,
        status: str,
        copy_json: dict,
        revision_number: int = 0,
        parent_variant_id: uuid.UUID | None = None,
    ) -> CreativeVariant:
        variant = CreativeVariant(
            campaign_id=campaign_id,
            run_id=run_id,
            persona_id=persona_id,
            channel=channel,
            journey_stage=journey_stage,
            primary_kpi=primary_kpi,
            revision_number=revision_number,
            status=status,
            copy_json=copy_json,
            parent_variant_id=parent_variant_id,
        )
        self.session.add(variant)
        self.session.flush()
        return variant

    def list_creative_variants_for_run(self, run_id: uuid.UUID) -> list[CreativeVariant]:
        stmt = (
            select(CreativeVariant)
            .where(CreativeVariant.run_id == run_id)
            .order_by(CreativeVariant.created_at.asc(), CreativeVariant.id.asc())
        )
        return list(self.session.scalars(stmt))

    def list_policy_findings_for_run(self, run_id: uuid.UUID) -> list[PolicyFinding]:
        stmt = (
            select(PolicyFinding)
            .where(PolicyFinding.run_id == run_id)
            .order_by(PolicyFinding.created_at.asc(), PolicyFinding.id.asc())
        )
        return list(self.session.scalars(stmt))

    def get_latest_approval_for_run(self, run_id: uuid.UUID) -> Approval | None:
        stmt = (
            select(Approval)
            .where(Approval.run_id == run_id)
            .order_by(Approval.created_at.desc(), Approval.id.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def list_evaluation_results_for_run(self, run_id: uuid.UUID) -> list[EvaluationResult]:
        stmt = (
            select(EvaluationResult)
            .where(EvaluationResult.run_id == run_id)
            .order_by(EvaluationResult.created_at.asc(), EvaluationResult.id.asc())
        )
        return list(self.session.scalars(stmt))

    def get_latest_wave_proposal_for_run(self, run_id: uuid.UUID) -> WaveProposal | None:
        stmt = (
            select(WaveProposal)
            .where(WaveProposal.run_id == run_id)
            .order_by(WaveProposal.created_at.desc(), WaveProposal.id.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def create_event(
        self,
        *,
        campaign_id: uuid.UUID,
        event_type: str,
        payload_json: dict,
        run_id: uuid.UUID | None = None,
        stage: str | None = None,
    ) -> EventLog:
        event = EventLog(
            campaign_id=campaign_id,
            run_id=run_id,
            event_type=event_type,
            stage=stage,
            payload_json=payload_json,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def list_events_for_campaign(
        self,
        campaign_id: uuid.UUID,
        *,
        after_id: int | None = None,
    ) -> list[EventLog]:
        stmt = select(EventLog).where(EventLog.campaign_id == campaign_id)
        if after_id is not None:
            stmt = stmt.where(EventLog.id > after_id)
        stmt = stmt.order_by(EventLog.id.asc())
        return list(self.session.scalars(stmt))
