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

    def list_active_creative_variants_for_run(
        self,
        run_id: uuid.UUID,
    ) -> list[CreativeVariant]:
        stmt = (
            select(CreativeVariant)
            .where(
                CreativeVariant.run_id == run_id,
                CreativeVariant.status != "revised",
            )
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

    def list_open_blocking_policy_findings_for_run(
        self,
        run_id: uuid.UUID,
        *,
        source: str | None = None,
    ) -> list[PolicyFinding]:
        stmt = select(PolicyFinding).where(
            PolicyFinding.run_id == run_id,
            PolicyFinding.status == "open",
            PolicyFinding.severity == "blocking",
        )
        if source is not None:
            stmt = stmt.where(PolicyFinding.source == source)
        stmt = stmt.order_by(PolicyFinding.created_at.asc(), PolicyFinding.id.asc())
        return list(self.session.scalars(stmt))

    def create_policy_finding(
        self,
        *,
        campaign_id: uuid.UUID,
        run_id: uuid.UUID,
        variant_id: uuid.UUID,
        source: str,
        severity: str,
        status: str,
        finding_type: str,
        evidence: str,
        message: str,
        rule_id: str | None = None,
        suggestion: str | None = None,
        metadata_json: dict | None = None,
    ) -> PolicyFinding:
        finding = PolicyFinding(
            campaign_id=campaign_id,
            run_id=run_id,
            variant_id=variant_id,
            source=source,
            rule_id=rule_id,
            severity=severity,
            status=status,
            finding_type=finding_type,
            evidence=evidence,
            message=message,
            suggestion=suggestion,
            metadata_json=metadata_json,
        )
        self.session.add(finding)
        self.session.flush()
        return finding

    def resolve_open_policy_findings_for_variants(
        self,
        variant_ids: list[uuid.UUID],
        *,
        resolved_at: datetime,
        reason: str,
        resolved_by_variant_id: uuid.UUID | None = None,
    ) -> list[PolicyFinding]:
        if not variant_ids:
            return []

        stmt = select(PolicyFinding).where(
            PolicyFinding.variant_id.in_(variant_ids),
            PolicyFinding.status == "open",
        )
        findings = list(self.session.scalars(stmt))
        for finding in findings:
            finding.status = "resolved"
            finding.resolved_at = resolved_at
            metadata = dict(finding.metadata_json or {})
            metadata["resolution"] = {
                "reason": reason,
                "resolved_by_variant_id": (
                    str(resolved_by_variant_id) if resolved_by_variant_id else None
                ),
            }
            finding.metadata_json = metadata
        self.session.flush()
        return findings

    def update_creative_variant_status(
        self,
        variant: CreativeVariant,
        *,
        status: str,
    ) -> CreativeVariant:
        variant.status = status
        self.session.flush()
        return variant

    def get_latest_approval_for_run(self, run_id: uuid.UUID) -> Approval | None:
        stmt = (
            select(Approval)
            .where(Approval.run_id == run_id)
            .order_by(Approval.created_at.desc(), Approval.id.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def create_approval(
        self,
        *,
        campaign_id: uuid.UUID,
        run_id: uuid.UUID,
        approved_by: str,
        status: str,
        notes: str | None = None,
    ) -> Approval:
        approval = Approval(
            campaign_id=campaign_id,
            run_id=run_id,
            approved_by=approved_by,
            status=status,
            notes=notes,
        )
        self.session.add(approval)
        self.session.flush()
        return approval

    def list_evaluation_results_for_run(self, run_id: uuid.UUID) -> list[EvaluationResult]:
        stmt = (
            select(EvaluationResult)
            .where(EvaluationResult.run_id == run_id)
            .order_by(EvaluationResult.created_at.asc(), EvaluationResult.id.asc())
        )
        return list(self.session.scalars(stmt))

    def create_evaluation_result(
        self,
        *,
        campaign_id: uuid.UUID,
        run_id: uuid.UUID,
        variant_id: uuid.UUID,
        persona_id: str,
        channel: str,
        scores_json: dict,
        total_score: float | int,
    ) -> EvaluationResult:
        result = EvaluationResult(
            campaign_id=campaign_id,
            run_id=run_id,
            variant_id=variant_id,
            persona_id=persona_id,
            channel=channel,
            scores_json=scores_json,
            total_score=total_score,
        )
        self.session.add(result)
        self.session.flush()
        return result

    def get_latest_wave_proposal_for_run(self, run_id: uuid.UUID) -> WaveProposal | None:
        stmt = (
            select(WaveProposal)
            .where(WaveProposal.run_id == run_id)
            .order_by(WaveProposal.created_at.desc(), WaveProposal.id.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def create_wave_proposal(
        self,
        *,
        campaign_id: uuid.UUID,
        run_id: uuid.UUID,
        proposal_json: dict,
        rationale_json: dict,
    ) -> WaveProposal:
        proposal = WaveProposal(
            campaign_id=campaign_id,
            run_id=run_id,
            proposal_json=proposal_json,
            rationale_json=rationale_json,
        )
        self.session.add(proposal)
        self.session.flush()
        return proposal

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
