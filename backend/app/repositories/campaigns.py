from __future__ import annotations

import uuid

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

    def create_campaign(self, *, name: str, brief_json: dict, tenant_id: str = "demo") -> Campaign:
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

    def list_stage_outputs_for_run(self, run_id: uuid.UUID) -> list[StageOutput]:
        stmt = (
            select(StageOutput)
            .where(StageOutput.run_id == run_id)
            .order_by(StageOutput.created_at.desc(), StageOutput.id.desc())
        )
        return list(self.session.scalars(stmt))

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

    def list_events_for_campaign(self, campaign_id: uuid.UUID) -> list[EventLog]:
        stmt = (
            select(EventLog)
            .where(EventLog.campaign_id == campaign_id)
            .order_by(EventLog.id.asc())
        )
        return list(self.session.scalars(stmt))
