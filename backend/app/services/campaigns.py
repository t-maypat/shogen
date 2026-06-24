from __future__ import annotations

import uuid

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
from app.repositories.campaigns import CampaignRepository
from app.schemas.brief import CampaignBrief
from app.schemas.campaigns import (
    ApprovalSummary,
    CampaignStateData,
    CampaignSummary,
    CreativeVariantSummary,
    EvaluationResultSummary,
    EventLogSummary,
    PolicyFindingSummary,
    WaveProposalSummary,
    WorkflowRunSummary,
)


class CampaignNotFoundError(Exception):
    def __init__(self, campaign_id: uuid.UUID) -> None:
        self.campaign_id = campaign_id
        super().__init__(f"Campaign {campaign_id} not found")


class CampaignService:
    def __init__(self, repository: CampaignRepository) -> None:
        self.repository = repository

    def create_campaign(self, *, name: str, brief: CampaignBrief) -> Campaign:
        campaign = self.repository.create_campaign(
            name=name,
            brief_json=brief.model_dump(mode="json"),
        )
        self.repository.session.commit()
        self.repository.session.refresh(campaign)
        return campaign

    def get_campaign_state(self, campaign_id: uuid.UUID) -> CampaignStateData:
        campaign = self.repository.get_campaign(campaign_id)
        if campaign is None:
            raise CampaignNotFoundError(campaign_id)

        latest_run = self.repository.get_latest_run(campaign_id)
        stage_outputs: list[StageOutput] = []
        creative_variants: list[CreativeVariant] = []
        policy_findings: list[PolicyFinding] = []
        approval: Approval | None = None
        evaluation_results: list[EvaluationResult] = []
        wave_proposal: WaveProposal | None = None

        if latest_run is not None:
            stage_outputs = self.repository.list_stage_outputs_for_run(latest_run.id)
            creative_variants = self.repository.list_creative_variants_for_run(latest_run.id)
            policy_findings = self.repository.list_policy_findings_for_run(latest_run.id)
            approval = self.repository.get_latest_approval_for_run(latest_run.id)
            evaluation_results = self.repository.list_evaluation_results_for_run(latest_run.id)
            wave_proposal = self.repository.get_latest_wave_proposal_for_run(latest_run.id)

        stage_payloads = self._stage_payload_map(stage_outputs)
        events = self.repository.list_events_for_campaign(campaign_id)

        return CampaignStateData(
            campaign=self._serialize_campaign(campaign),
            latest_run=self._serialize_run(latest_run),
            strategy=stage_payloads.get("strategy"),
            journey=stage_payloads.get("journey"),
            creative_variants=[
                self._serialize_creative_variant(variant) for variant in creative_variants
            ],
            policy_findings=[
                self._serialize_policy_finding(finding) for finding in policy_findings
            ],
            approval=self._serialize_approval(approval),
            evaluation_results=[
                self._serialize_evaluation_result(result)
                for result in evaluation_results
            ],
            wave_proposal=self._serialize_wave_proposal(wave_proposal),
            events=[self._serialize_event(event) for event in events],
        )

    @staticmethod
    def _stage_payload_map(stage_outputs: list[StageOutput]) -> dict[str, dict]:
        payloads: dict[str, dict] = {}
        for stage_output in stage_outputs:
            payloads.setdefault(stage_output.stage_name, stage_output.output_json)
        return payloads

    @staticmethod
    def _serialize_campaign(campaign: Campaign) -> CampaignSummary:
        return CampaignSummary(
            id=campaign.id,
            tenant_id=campaign.tenant_id,
            name=campaign.name,
            status=campaign.status,
            brief=CampaignBrief.model_validate(campaign.brief_json),
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )

    @staticmethod
    def _serialize_run(run: WorkflowRun | None) -> WorkflowRunSummary | None:
        if run is None:
            return None
        return WorkflowRunSummary(
            id=run.id,
            status=run.status,
            current_stage=run.current_stage,
            revision_count=run.revision_count,
            replay_mode=run.replay_mode,
            error=run.error_json,
            started_at=run.started_at,
            completed_at=run.completed_at,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @staticmethod
    def _serialize_creative_variant(
        variant: CreativeVariant,
    ) -> CreativeVariantSummary:
        return CreativeVariantSummary(
            id=variant.id,
            run_id=variant.run_id,
            client_variant_id=variant.copy_json.get("client_variant_id", str(variant.id)),
            persona_id=variant.persona_id,
            channel=variant.channel,
            journey_stage=variant.journey_stage,
            primary_kpi=variant.primary_kpi,
            revision_number=variant.revision_number,
            status=variant.status,
            claims=variant.copy_json.get("claims", []),
            disclosure=variant.copy_json.get("disclosure"),
            copy_payload=variant.copy_json.get("copy", {}),
            parent_variant_id=variant.parent_variant_id,
            created_at=variant.created_at,
            updated_at=variant.updated_at,
        )

    @staticmethod
    def _serialize_policy_finding(
        finding: PolicyFinding,
    ) -> PolicyFindingSummary:
        return PolicyFindingSummary(
            id=finding.id,
            variant_id=finding.variant_id,
            source=finding.source,
            rule_id=finding.rule_id,
            severity=finding.severity,
            status=finding.status,
            finding_type=finding.finding_type,
            evidence=finding.evidence,
            message=finding.message,
            suggestion=finding.suggestion,
            metadata=finding.metadata_json,
            created_at=finding.created_at,
            resolved_at=finding.resolved_at,
        )

    @staticmethod
    def _serialize_approval(approval: Approval | None) -> ApprovalSummary | None:
        if approval is None:
            return None
        return ApprovalSummary(
            id=approval.id,
            approved_by=approval.approved_by,
            status=approval.status,
            notes=approval.notes,
            created_at=approval.created_at,
        )

    @staticmethod
    def _serialize_evaluation_result(
        result: EvaluationResult,
    ) -> EvaluationResultSummary:
        return EvaluationResultSummary(
            id=result.id,
            variant_id=result.variant_id,
            persona_id=result.persona_id,
            channel=result.channel,
            scores=result.scores_json,
            total_score=result.total_score,
            created_at=result.created_at,
        )

    @staticmethod
    def _serialize_wave_proposal(
        proposal: WaveProposal | None,
    ) -> WaveProposalSummary | None:
        if proposal is None:
            return None
        return WaveProposalSummary(
            id=proposal.id,
            proposal=proposal.proposal_json,
            rationale=proposal.rationale_json,
            created_at=proposal.created_at,
        )

    @staticmethod
    def _serialize_event(event: EventLog) -> EventLogSummary:
        return EventLogSummary(
            id=event.id,
            run_id=event.run_id,
            event_type=event.event_type,
            stage=event.stage,
            payload=event.payload_json,
            created_at=event.created_at,
        )
