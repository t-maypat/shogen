from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.ai.provider import AzureOpenAIModelProvider, ModelProvider, ModelProviderError
from app.core.config import Settings, get_settings
from app.db.models import Campaign, WorkflowRun
from app.policy import DeterministicPolicyEngine
from app.repositories.campaigns import CampaignRepository
from app.schemas.brief import CampaignBrief
from app.schemas.creative import CreativeVariantOut
from app.schemas.journey import JourneyOutput
from app.schemas.strategy import StrategyOutput
from app.services.deployment import (
    MOCK_DEPLOYMENT_MODEL_NAME,
    MOCK_DEPLOYMENT_SCHEMA_VERSION,
    MockDeploymentService,
)
from app.services.campaigns import CampaignNotFoundError
from app.services.events import EventService
from app.services.generation import CampaignGenerationService, build_default_fake_provider
from app.services.review import (
    MAX_CREATIVE_REVISIONS,
    SemanticReviewService,
    creative_variant_to_payload,
)
from app.workflow.graph import build_workflow_graph
from app.workflow.state import WorkflowMode, WorkflowState

logger = logging.getLogger(__name__)

WORKFLOW_STAGE_DELAY_SECONDS = 0.05


@dataclass(slots=True)
class StageExecutionResult:
    payload: dict[str, Any]
    schema_version: str
    prompt_version: str | None = None
    model_name: str | None = None
    duration_ms: int | None = None
    creative_variants: list[CreativeVariantOut] = field(default_factory=list)


class WorkflowAlreadyRunningError(Exception):
    def __init__(self, campaign_id: uuid.UUID, run_id: uuid.UUID) -> None:
        self.campaign_id = campaign_id
        self.run_id = run_id
        super().__init__(f"Campaign {campaign_id} already has a running workflow")


class WorkflowApprovalNotReadyError(Exception):
    def __init__(
        self,
        campaign_id: uuid.UUID,
        *,
        reason: str,
        run_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> None:
        self.campaign_id = campaign_id
        self.run_id = run_id
        self.status = status
        self.reason = reason
        super().__init__(reason)


class WorkflowApprovalBlockedError(Exception):
    def __init__(
        self,
        campaign_id: uuid.UUID,
        run_id: uuid.UUID,
        *,
        blocking_findings: int,
        deterministic_blocking_findings: int,
    ) -> None:
        self.campaign_id = campaign_id
        self.run_id = run_id
        self.blocking_findings = blocking_findings
        self.deterministic_blocking_findings = deterministic_blocking_findings
        super().__init__(
            "Campaign cannot be approved while blocking policy findings remain"
        )


class WorkflowAlreadyApprovedError(Exception):
    def __init__(self, campaign_id: uuid.UUID, run_id: uuid.UUID) -> None:
        self.campaign_id = campaign_id
        self.run_id = run_id
        super().__init__(f"Campaign {campaign_id} has already been approved")


@dataclass(slots=True)
class WorkflowApprovalResult:
    approval_id: uuid.UUID
    approval_status: str
    approved_by: str
    approval_notes: str | None
    approval_created_at: datetime
    run_id: uuid.UUID
    status: str
    mock_deployment: dict[str, Any]


class WorkflowService:
    def __init__(self, repository: CampaignRepository) -> None:
        self.repository = repository
        self.event_service = EventService(repository)

    def start_workflow(
        self,
        *,
        campaign_id: uuid.UUID,
        mode: WorkflowMode,
    ) -> WorkflowRun:
        campaign = self.repository.get_campaign(campaign_id)
        if campaign is None:
            raise CampaignNotFoundError(campaign_id)

        latest_run = self.repository.get_latest_run(campaign_id)
        if latest_run is not None and latest_run.status == "running":
            raise WorkflowAlreadyRunningError(campaign_id, latest_run.id)

        campaign.status = "running"
        run = self.repository.create_workflow_run(
            campaign_id=campaign_id,
            status="running",
            replay_mode=mode == "replay",
            started_at=datetime.now(timezone.utc),
        )
        self.event_service.record_workflow_event(
            campaign_id=campaign_id,
            run_id=run.id,
            event_type="workflow.started",
            stage=None,
            status="running",
            display={"mode": mode},
        )
        self.repository.session.commit()
        self.repository.session.refresh(run)
        return run

    def approve_campaign(
        self,
        *,
        campaign_id: uuid.UUID,
        approved_by: str,
        notes: str | None,
    ) -> WorkflowApprovalResult:
        campaign = self.repository.get_campaign(campaign_id)
        if campaign is None:
            raise CampaignNotFoundError(campaign_id)

        run = self.repository.get_latest_run(campaign_id)
        if run is None:
            raise WorkflowApprovalNotReadyError(
                campaign_id,
                reason="Campaign has no workflow run to approve",
            )
        if run.status != "approval_required":
            raise WorkflowApprovalNotReadyError(
                campaign_id,
                run_id=run.id,
                status=run.status,
                reason=(
                    "Campaign must be waiting at approval_required before approval"
                ),
            )
        if self.repository.get_latest_approval_for_run(run.id) is not None:
            raise WorkflowAlreadyApprovedError(campaign_id, run.id)

        open_blocking_findings = (
            self.repository.list_open_blocking_policy_findings_for_run(run.id)
        )
        deterministic_blocking_findings = (
            self.repository.list_open_blocking_policy_findings_for_run(
                run.id,
                source="deterministic",
            )
        )
        if open_blocking_findings:
            raise WorkflowApprovalBlockedError(
                campaign_id,
                run.id,
                blocking_findings=len(open_blocking_findings),
                deterministic_blocking_findings=len(deterministic_blocking_findings),
            )

        active_variants = self.repository.list_active_creative_variants_for_run(run.id)
        if not active_variants:
            raise WorkflowApprovalNotReadyError(
                campaign_id,
                run_id=run.id,
                status=run.status,
                reason="Campaign has no active creative variants to approve",
            )

        approval = self.repository.create_approval(
            campaign_id=campaign.id,
            run_id=run.id,
            approved_by=approved_by,
            status="approved",
            notes=notes,
        )
        self.repository.session.refresh(approval)
        self.event_service.record_workflow_event(
            campaign_id=campaign.id,
            run_id=run.id,
            event_type="approval.recorded",
            stage="approval",
            status="approved",
            display={
                "approved_by": approval.approved_by,
                "notes": bool(approval.notes),
            },
        )

        campaign.status = "running"
        run.status = "running"
        run.current_stage = "mock_deployment"
        run.completed_at = None
        self.event_service.record_workflow_event(
            campaign_id=campaign.id,
            run_id=run.id,
            event_type="stage.started",
            stage="mock_deployment",
            status="running",
        )

        deployment_payload = MockDeploymentService().build_payload(
            campaign=campaign,
            approval=approval,
            variants=active_variants,
        )
        self.repository.create_stage_output(
            campaign_id=campaign.id,
            run_id=run.id,
            stage_name="mock_deployment",
            schema_version=MOCK_DEPLOYMENT_SCHEMA_VERSION,
            prompt_version="mock_deployment.det.v1",
            model_name=MOCK_DEPLOYMENT_MODEL_NAME,
            duration_ms=0,
            output_json=deployment_payload,
        )

        campaign.status = "mock_deployed"
        run.status = "mock_deployed"
        run.current_stage = "mock_deployment"
        run.completed_at = datetime.now(timezone.utc)
        self.event_service.record_workflow_event(
            campaign_id=campaign.id,
            run_id=run.id,
            event_type="stage.completed",
            stage="mock_deployment",
            status="mock_deployed",
            display=deployment_payload["summary"],
        )
        self.repository.session.commit()
        self.repository.session.refresh(run)
        self.repository.session.refresh(approval)

        return WorkflowApprovalResult(
            approval_id=approval.id,
            approval_status=approval.status,
            approved_by=approval.approved_by,
            approval_notes=approval.notes,
            approval_created_at=approval.created_at,
            run_id=run.id,
            status=run.status,
            mock_deployment=deployment_payload,
        )


class CampaignWorkflowRunner:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def run(
        self,
        *,
        campaign_id: uuid.UUID,
        run_id: uuid.UUID,
        mode: WorkflowMode,
    ) -> None:
        with self.session_factory() as session:
            repository = CampaignRepository(session)
            event_service = EventService(repository)

            campaign = repository.get_campaign(campaign_id)
            run = repository.get_workflow_run(run_id)
            if campaign is None or run is None:
                return

            settings = get_settings()
            generation_service = CampaignGenerationService(
                provider=_build_model_provider(settings),
                timeout_seconds=settings.model_timeout_seconds,
            )
            review_service = SemanticReviewService(
                provider=generation_service.provider,
                timeout_seconds=settings.model_timeout_seconds,
            )
            state: WorkflowState = {
                "campaign_id": campaign_id,
                "run_id": run_id,
                "mode": mode,
                "brief": campaign.brief_json,
            }

            workflow_graph = build_workflow_graph(
                self._node_handlers(
                    session=session,
                    campaign=campaign,
                    run=run,
                    event_service=event_service,
                    generation_service=generation_service,
                    review_service=review_service,
                )
            )

            try:
                workflow_graph.invoke(state)
            except Exception as exc:  # pragma: no cover - exercised via failure paths
                run.status = "failed"
                run.completed_at = datetime.now(timezone.utc)
                run.error_json = {"message": str(exc)}
                campaign.status = "failed"
                event_service.record_workflow_event(
                    campaign_id=campaign.id,
                    run_id=run.id,
                    event_type="workflow.failed",
                    stage=run.current_stage,
                    status="failed",
                    display={"message": str(exc)},
                )
                session.commit()
                raise

    def _node_handlers(
        self,
        *,
        session: Session,
        campaign: Campaign,
        run: WorkflowRun,
        event_service: EventService,
        generation_service: CampaignGenerationService,
        review_service: SemanticReviewService,
    ) -> dict[str, Any]:
        return {
            "strategy": self._stage_node(
                session=session,
                campaign=campaign,
                run=run,
                event_service=event_service,
                stage_name="strategy",
                execute_stage=lambda state: self._execute_strategy_stage(
                    state=state,
                    generation_service=generation_service,
                ),
            ),
            "journey": self._stage_node(
                session=session,
                campaign=campaign,
                run=run,
                event_service=event_service,
                stage_name="journey",
                execute_stage=lambda state: self._execute_journey_stage(
                    state=state,
                    generation_service=generation_service,
                ),
            ),
            "creative": self._stage_node(
                session=session,
                campaign=campaign,
                run=run,
                event_service=event_service,
                stage_name="creative",
                execute_stage=lambda state: self._execute_creative_stage(
                    state=state,
                    generation_service=generation_service,
                ),
            ),
            "policy": self._stage_node(
                session=session,
                campaign=campaign,
                run=run,
                event_service=event_service,
                stage_name="policy",
                execute_stage=lambda state: self._execute_policy_stage(
                    state=state,
                    repository=CampaignRepository(session),
                    event_service=event_service,
                    review_service=review_service,
                    campaign=campaign,
                    run=run,
                ),
            ),
            "approval_required": self._stage_node(
                session=session,
                campaign=campaign,
                run=run,
                event_service=event_service,
                stage_name="approval_required",
                execute_stage=self._execute_approval_stage,
                terminal_status="approval_required",
            ),
        }

    def _stage_node(
        self,
        *,
        session: Session,
        campaign: Campaign,
        run: WorkflowRun,
        event_service: EventService,
        stage_name: str,
        execute_stage: Any,
        terminal_status: str | None = None,
    ) -> Any:
        def node(state: WorkflowState) -> WorkflowState:
            run.current_stage = stage_name
            event_service.record_workflow_event(
                campaign_id=campaign.id,
                run_id=run.id,
                event_type="stage.started",
                stage=stage_name,
                status="running",
            )
            session.commit()

            time.sleep(WORKFLOW_STAGE_DELAY_SECONDS)
            stage_result = execute_stage(state)
            state[stage_name] = stage_result.payload

            repository = CampaignRepository(session)
            repository.create_stage_output(
                campaign_id=campaign.id,
                run_id=run.id,
                stage_name=stage_name,
                schema_version=stage_result.schema_version,
                prompt_version=stage_result.prompt_version,
                model_name=stage_result.model_name,
                duration_ms=stage_result.duration_ms,
                output_json=stage_result.payload,
            )
            for variant in stage_result.creative_variants:
                repository.create_creative_variant(
                    campaign_id=campaign.id,
                    run_id=run.id,
                    persona_id=variant.persona_id,
                    channel=variant.channel,
                    journey_stage=variant.journey_stage,
                    primary_kpi=variant.primary_kpi_id,
                    status="generated",
                    copy_json={
                        "client_variant_id": variant.client_variant_id,
                        "claims": variant.claims,
                        "disclosure": variant.disclosure,
                        "copy": variant.copy_payload.model_dump(mode="json"),
                    },
                )

            next_status = terminal_status or "completed"
            if terminal_status is not None:
                campaign.status = terminal_status
                run.status = terminal_status
                run.completed_at = datetime.now(timezone.utc)

            event_service.record_workflow_event(
                campaign_id=campaign.id,
                run_id=run.id,
                event_type="stage.completed",
                stage=stage_name,
                status=next_status,
                display=self._display_summary(stage_name, stage_result.payload),
            )
            session.commit()
            return state

        return node

    def _execute_strategy_stage(
        self,
        *,
        state: WorkflowState,
        generation_service: CampaignGenerationService,
    ) -> StageExecutionResult:
        brief = CampaignBrief.model_validate(state["brief"])
        strategy, metadata = generation_service.generate_strategy(brief)
        return StageExecutionResult(
            payload=strategy.model_dump(mode="json"),
            schema_version=metadata["schema_version"],
            prompt_version=metadata["prompt_version"],
            model_name=metadata["model_name"],
            duration_ms=metadata["duration_ms"],
        )

    def _execute_journey_stage(
        self,
        *,
        state: WorkflowState,
        generation_service: CampaignGenerationService,
    ) -> StageExecutionResult:
        brief = CampaignBrief.model_validate(state["brief"])
        strategy = state["strategy"]
        journey, metadata = generation_service.generate_journey(
            brief=brief,
            strategy=_strategy_from_payload(strategy),
        )
        return StageExecutionResult(
            payload=journey.model_dump(mode="json"),
            schema_version=metadata["schema_version"],
            prompt_version=metadata["prompt_version"],
            model_name=metadata["model_name"],
            duration_ms=metadata["duration_ms"],
        )

    def _execute_creative_stage(
        self,
        *,
        state: WorkflowState,
        generation_service: CampaignGenerationService,
    ) -> StageExecutionResult:
        brief = CampaignBrief.model_validate(state["brief"])
        strategy = _strategy_from_payload(state["strategy"])
        journey = _journey_from_payload(state["journey"])
        creative, metadata = generation_service.generate_creative(
            brief=brief,
            strategy=strategy,
            journey=journey,
        )
        return StageExecutionResult(
            payload=creative.model_dump(mode="json", by_alias=True),
            schema_version=metadata["schema_version"],
            prompt_version=metadata["prompt_version"],
            model_name=metadata["model_name"],
            duration_ms=metadata["duration_ms"],
            creative_variants=creative.variants,
        )

    def _execute_policy_stage(
        self,
        *,
        state: WorkflowState,
        repository: CampaignRepository,
        event_service: EventService,
        review_service: SemanticReviewService,
        campaign: Campaign,
        run: WorkflowRun,
    ) -> StageExecutionResult:
        brief = CampaignBrief.model_validate(state["brief"])
        strategy = state.get("strategy") or {}
        journey = state.get("journey") or {}
        policy_engine = DeterministicPolicyEngine()
        passes: list[dict[str, Any]] = []
        revisions: list[dict[str, Any]] = []
        final_payload: dict[str, Any] | None = None
        final_metadata: dict[str, Any] = {}

        while True:
            active_variants = repository.list_active_creative_variants_for_run(run.id)
            if passes:
                repository.resolve_open_policy_findings_for_variants(
                    [variant.id for variant in active_variants],
                    resolved_at=datetime.now(timezone.utc),
                    reason="policy_rerun",
                )

            deterministic_evaluation = policy_engine.evaluate(
                brief=brief,
                strategy=strategy,
                journey=journey,
                variants=active_variants,
            )
            deterministic_findings = [
                finding.to_payload() for finding in deterministic_evaluation.findings
            ]
            for finding in deterministic_evaluation.findings:
                repository.create_policy_finding(
                    campaign_id=campaign.id,
                    run_id=run.id,
                    variant_id=finding.variant_id,
                    source=finding.source,
                    rule_id=finding.rule_id,
                    severity=finding.severity,
                    status="open",
                    finding_type=finding.finding_type,
                    evidence=finding.evidence,
                    message=finding.message,
                    suggestion=finding.suggestion,
                    metadata_json=finding.metadata,
                )

            semantic_review, semantic_metadata = review_service.review_variants(
                brief=brief,
                strategy=strategy,
                journey=journey,
                variants=active_variants,
            )
            final_metadata = semantic_metadata
            semantic_findings = self._persist_semantic_findings(
                repository=repository,
                campaign=campaign,
                run=run,
                variants=active_variants,
                semantic_review=semantic_review.model_dump(mode="json"),
            )

            combined_payload = self._combined_policy_payload(
                variants=active_variants,
                deterministic_payload=deterministic_evaluation.to_stage_payload(),
                deterministic_findings=deterministic_findings,
                semantic_payload=semantic_review.model_dump(mode="json"),
                semantic_findings=semantic_findings,
                revisions=revisions,
                revision_count=run.revision_count,
            )

            statuses_by_variant_id = {
                variant_status["variant_id"]: variant_status["status"]
                for variant_status in combined_payload["variant_statuses"]
            }
            for variant in active_variants:
                repository.update_creative_variant_status(
                    variant,
                    status=statuses_by_variant_id[str(variant.id)],
                )

            passes.append(
                {
                    "revision_count": run.revision_count,
                    "summary": combined_payload["summary"],
                }
            )
            blocking_findings_by_variant = self._blocking_findings_by_variant(
                [*deterministic_findings, *semantic_findings]
            )
            if (
                not blocking_findings_by_variant
                or run.revision_count >= MAX_CREATIVE_REVISIONS
            ):
                final_payload = {**combined_payload, "passes": passes}
                break

            next_revision_count = run.revision_count + 1
            created_revisions = []
            for variant in active_variants:
                findings_for_variant = blocking_findings_by_variant.get(variant.id)
                if not findings_for_variant:
                    continue
                if variant.revision_number >= MAX_CREATIVE_REVISIONS:
                    continue

                revised_variant, revision_metadata = review_service.revise_variant(
                    brief=brief,
                    strategy=strategy,
                    journey=journey,
                    variant=variant,
                    findings=findings_for_variant,
                    next_revision_number=variant.revision_number + 1,
                )
                child_variant = repository.create_creative_variant(
                    campaign_id=campaign.id,
                    run_id=run.id,
                    persona_id=revised_variant.persona_id,
                    channel=revised_variant.channel,
                    journey_stage=revised_variant.journey_stage,
                    primary_kpi=revised_variant.primary_kpi_id,
                    revision_number=variant.revision_number + 1,
                    status="generated",
                    parent_variant_id=variant.id,
                    copy_json={
                        "client_variant_id": revised_variant.client_variant_id,
                        "claims": revised_variant.claims,
                        "disclosure": revised_variant.disclosure,
                        "copy": revised_variant.copy_payload.model_dump(mode="json"),
                    },
                )
                repository.update_creative_variant_status(variant, status="revised")
                repository.resolve_open_policy_findings_for_variants(
                    [variant.id],
                    resolved_at=datetime.now(timezone.utc),
                    reason="revised",
                    resolved_by_variant_id=child_variant.id,
                )
                revision_payload = {
                    "parent_variant_id": str(variant.id),
                    "child_variant_id": str(child_variant.id),
                    "client_variant_id": revised_variant.client_variant_id,
                    "revision_number": child_variant.revision_number,
                    "findings_addressed": findings_for_variant,
                    "prompt_version": revision_metadata["prompt_version"],
                    "model_name": revision_metadata["model_name"],
                }
                revisions.append(revision_payload)
                created_revisions.append(revision_payload)

            if not created_revisions:
                final_payload = {**combined_payload, "passes": passes}
                break

            run.revision_count = next_revision_count
            event_service.record_workflow_event(
                campaign_id=campaign.id,
                run_id=run.id,
                event_type="policy.revision_created",
                stage="policy",
                status="running",
                display={
                    "revision_count": run.revision_count,
                    "revised_variants": len(created_revisions),
                },
            )

        if final_payload is None:  # pragma: no cover - defensive guard
            raise RuntimeError("Policy review did not produce a final payload")

        if final_payload["summary"]["blocking_findings"] > 0:
            event_service.record_workflow_event(
                campaign_id=campaign.id,
                run_id=run.id,
                event_type="policy.failed",
                stage="policy",
                status="blocked",
                display={
                    "blocking_findings": final_payload["summary"]["blocking_findings"],
                    "blocked_variants": final_payload["summary"]["blocked_variants"],
                },
            )

        return StageExecutionResult(
            payload=final_payload,
            schema_version="policy.review.v1",
            prompt_version=final_metadata.get("prompt_version"),
            model_name=final_metadata.get("model_name"),
            duration_ms=final_metadata.get("duration_ms"),
        )

    @staticmethod
    def _persist_semantic_findings(
        *,
        repository: CampaignRepository,
        campaign: Campaign,
        run: WorkflowRun,
        variants: list[Any],
        semantic_review: dict[str, Any],
    ) -> list[dict[str, Any]]:
        variants_by_client_id = {
            creative_variant_to_payload(variant)["client_variant_id"]: variant
            for variant in variants
        }
        persisted_findings: list[dict[str, Any]] = []

        for review in semantic_review["reviews"]:
            variant = variants_by_client_id.get(review["client_variant_id"])
            if variant is None:
                continue
            client_variant_id = creative_variant_to_payload(variant)["client_variant_id"]
            for finding in review["findings"]:
                metadata = {
                    "variant_id": str(variant.id),
                    "client_variant_id": client_variant_id,
                    "channel": variant.channel,
                    "review_status": review["status"],
                    "revision_number": variant.revision_number,
                }
                repository.create_policy_finding(
                    campaign_id=campaign.id,
                    run_id=run.id,
                    variant_id=variant.id,
                    source="semantic",
                    rule_id=None,
                    severity=finding["severity"],
                    status="open",
                    finding_type=finding["finding_type"],
                    evidence=finding["evidence"],
                    message=finding["message"],
                    suggestion=finding.get("suggestion"),
                    metadata_json=metadata,
                )
                persisted_findings.append(
                    {
                        "variant_id": str(variant.id),
                        "client_variant_id": client_variant_id,
                        "source": "semantic",
                        "rule_id": None,
                        "severity": finding["severity"],
                        "finding_type": finding["finding_type"],
                        "evidence": finding["evidence"],
                        "message": finding["message"],
                        "suggestion": finding.get("suggestion"),
                        "metadata": metadata,
                    }
                )

        return persisted_findings

    @staticmethod
    def _combined_policy_payload(
        *,
        variants: list[Any],
        deterministic_payload: dict[str, Any],
        deterministic_findings: list[dict[str, Any]],
        semantic_payload: dict[str, Any],
        semantic_findings: list[dict[str, Any]],
        revisions: list[dict[str, Any]],
        revision_count: int,
    ) -> dict[str, Any]:
        findings = [*deterministic_findings, *semantic_findings]
        findings_by_variant_id: dict[str, list[dict[str, Any]]] = {
            str(variant.id): [] for variant in variants
        }
        for finding in findings:
            findings_by_variant_id.setdefault(finding["variant_id"], []).append(finding)

        deterministic_status_by_variant_id = {
            status["variant_id"]: status
            for status in deterministic_payload["variant_statuses"]
        }
        variant_statuses: list[dict[str, Any]] = []
        for variant in variants:
            variant_id = str(variant.id)
            variant_findings = findings_by_variant_id[variant_id]
            blocking_findings = sum(
                1 for finding in variant_findings if finding["severity"] == "blocking"
            )
            warning_findings = len(variant_findings) - blocking_findings
            status = "passed"
            if blocking_findings:
                status = "blocked"
            elif warning_findings:
                status = "warning"
            variant_statuses.append(
                {
                    "variant_id": variant_id,
                    "client_variant_id": creative_variant_to_payload(variant)[
                        "client_variant_id"
                    ],
                    "status": status,
                    "deterministic_status": deterministic_status_by_variant_id.get(
                        variant_id,
                        {},
                    ).get("status"),
                    "blocking_findings": blocking_findings,
                    "warning_findings": warning_findings,
                    "finding_count": len(variant_findings),
                    "revision_number": variant.revision_number,
                    "parent_variant_id": (
                        str(variant.parent_variant_id)
                        if variant.parent_variant_id is not None
                        else None
                    ),
                }
            )

        blocked_variants = sum(
            1 for variant_status in variant_statuses if variant_status["status"] == "blocked"
        )
        warning_variants = sum(
            1 for variant_status in variant_statuses if variant_status["status"] == "warning"
        )
        passed_variants = sum(
            1 for variant_status in variant_statuses if variant_status["status"] == "passed"
        )
        blocking_findings = sum(
            1 for finding in findings if finding["severity"] == "blocking"
        )
        summary = {
            "total_variants": len(variant_statuses),
            "passed_variants": passed_variants,
            "warning_variants": warning_variants,
            "blocked_variants": blocked_variants,
            "blocking_findings": blocking_findings,
            "warning_findings": len(findings) - blocking_findings,
            "total_findings": len(findings),
            "ready_for_approval": blocking_findings == 0,
            "revision_count": revision_count,
            "max_revisions": MAX_CREATIVE_REVISIONS,
            "revised_variants": len(revisions),
        }
        return {
            "summary": summary,
            "variant_statuses": variant_statuses,
            "findings": findings,
            "deterministic": deterministic_payload,
            "semantic": semantic_payload,
            "revisions": list(revisions),
        }

    @staticmethod
    def _blocking_findings_by_variant(
        findings: list[dict[str, Any]],
    ) -> dict[uuid.UUID, list[dict[str, Any]]]:
        blocking_findings: dict[uuid.UUID, list[dict[str, Any]]] = {}
        for finding in findings:
            if finding["severity"] != "blocking":
                continue
            variant_id = uuid.UUID(finding["variant_id"])
            blocking_findings.setdefault(variant_id, []).append(finding)
        return blocking_findings

    def _execute_approval_stage(self, state: WorkflowState) -> StageExecutionResult:
        policy = state["policy"]
        summary = policy["summary"]
        return StageExecutionResult(
            payload={
                "ready_for_approval": summary["blocking_findings"] == 0,
                "blocking_findings": summary["blocking_findings"],
                "warning_findings": summary["warning_findings"],
            },
            schema_version="approval.placeholder.v1",
        )

    @staticmethod
    def _display_summary(stage_name: str, output: dict[str, Any]) -> dict[str, Any]:
        if stage_name == "strategy":
            return {
                "personas": len(output["personas"]),
                "kpis": len(output["kpis"]),
            }
        if stage_name == "journey":
            return {
                "steps": len(output["steps"]),
                "channels": len({step["channel"] for step in output["steps"]}),
            }
        if stage_name == "creative":
            return {"variants": len(output["variants"])}
        if stage_name == "policy":
            return output["summary"]
        return {
            "readyForApproval": output["ready_for_approval"],
            "warningFindings": output["warning_findings"],
        }


def start_campaign_workflow(
    *,
    session_factory: sessionmaker[Session],
    campaign_id: uuid.UUID,
    run_id: uuid.UUID,
    mode: WorkflowMode,
) -> None:
    runner = CampaignWorkflowRunner(session_factory)
    thread = threading.Thread(
        target=runner.run,
        kwargs={
            "campaign_id": campaign_id,
            "run_id": run_id,
            "mode": mode,
        },
        daemon=True,
        name=f"workflow-{run_id}",
    )
    thread.start()


def _build_model_provider(settings: Settings) -> ModelProvider:
    if settings.model_provider == "fake":
        logger.info("Using fake structured model provider for workflow generation")
        return build_default_fake_provider()

    missing_fields = [
        field_name
        for field_name, value in (
            ("azure_openai_endpoint", settings.azure_openai_endpoint),
            ("azure_openai_api_key", settings.azure_openai_api_key),
            ("azure_openai_deployment", settings.azure_openai_deployment),
        )
        if not value
    ]
    if missing_fields:
        raise ModelProviderError(
            "Azure OpenAI provider is selected but required settings are missing: "
            + ", ".join(missing_fields)
        )

    return AzureOpenAIModelProvider(
        endpoint=settings.azure_openai_endpoint or "",
        api_key=settings.azure_openai_api_key or "",
        api_version=settings.azure_openai_api_version,
        deployment=settings.azure_openai_deployment or "",
        default_timeout_seconds=settings.model_timeout_seconds,
    )


def _strategy_from_payload(strategy_payload: dict[str, Any]) -> StrategyOutput:
    return StrategyOutput.model_validate(strategy_payload)


def _journey_from_payload(journey_payload: dict[str, Any]) -> JourneyOutput:
    return JourneyOutput.model_validate(journey_payload)
