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
from app.services.campaigns import CampaignNotFoundError
from app.services.events import EventService
from app.services.generation import CampaignGenerationService, build_default_fake_provider
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
        campaign: Campaign,
        run: WorkflowRun,
    ) -> StageExecutionResult:
        brief = CampaignBrief.model_validate(state["brief"])
        variants = repository.list_creative_variants_for_run(run.id)
        evaluation = DeterministicPolicyEngine().evaluate(
            brief=brief,
            strategy=state.get("strategy"),
            journey=state.get("journey"),
            variants=variants,
        )

        results_by_variant_id = {
            result.variant_id: result for result in evaluation.variant_results
        }
        for variant in variants:
            variant_result = results_by_variant_id[variant.id]
            repository.update_creative_variant_status(
                variant,
                status=variant_result.status,
            )

        for finding in evaluation.findings:
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

        if evaluation.summary["blocking_findings"] > 0:
            event_service.record_workflow_event(
                campaign_id=campaign.id,
                run_id=run.id,
                event_type="policy.failed",
                stage="policy",
                status="blocked",
                display={
                    "blocking_findings": evaluation.summary["blocking_findings"],
                    "blocked_variants": evaluation.summary["blocked_variants"],
                },
            )

        return StageExecutionResult(
            payload=evaluation.to_stage_payload(),
            schema_version="policy.det.v1",
        )

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
