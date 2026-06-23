from __future__ import annotations

import re
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Campaign, WorkflowRun
from app.repositories.campaigns import CampaignRepository
from app.services.campaigns import CampaignNotFoundError
from app.services.events import EventService
from app.workflow.graph import build_placeholder_graph
from app.workflow.state import WorkflowMode, WorkflowState

PLACEHOLDER_SCHEMA_VERSION = "placeholder.v1"
PLACEHOLDER_STAGE_DELAY_SECONDS = 0.05


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


class PlaceholderWorkflowRunner:
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

            state: WorkflowState = {
                "campaign_id": campaign_id,
                "run_id": run_id,
                "mode": mode,
                "brief": campaign.brief_json,
            }

            workflow_graph = build_placeholder_graph(
                self._node_handlers(
                    session=session,
                    campaign=campaign,
                    run=run,
                    event_service=event_service,
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
    ) -> dict[str, Any]:
        return {
            "strategy": self._stage_node(
                session=session,
                campaign=campaign,
                run=run,
                event_service=event_service,
                stage_name="strategy",
                build_output=self._build_strategy_output,
            ),
            "journey": self._stage_node(
                session=session,
                campaign=campaign,
                run=run,
                event_service=event_service,
                stage_name="journey",
                build_output=self._build_journey_output,
            ),
            "creative": self._stage_node(
                session=session,
                campaign=campaign,
                run=run,
                event_service=event_service,
                stage_name="creative",
                build_output=self._build_creative_output,
            ),
            "policy": self._stage_node(
                session=session,
                campaign=campaign,
                run=run,
                event_service=event_service,
                stage_name="policy",
                build_output=self._build_policy_output,
            ),
            "approval_required": self._stage_node(
                session=session,
                campaign=campaign,
                run=run,
                event_service=event_service,
                stage_name="approval_required",
                build_output=self._build_approval_output,
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
        build_output: Any,
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

            time.sleep(PLACEHOLDER_STAGE_DELAY_SECONDS)
            output = build_output(state)
            state[stage_name] = output

            repository = CampaignRepository(session)
            repository.create_stage_output(
                campaign_id=campaign.id,
                run_id=run.id,
                stage_name=stage_name,
                schema_version=PLACEHOLDER_SCHEMA_VERSION,
                output_json=output,
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
                display=self._display_summary(stage_name, output),
            )
            session.commit()
            return state

        return node

    def _build_strategy_output(self, state: WorkflowState) -> dict[str, Any]:
        brief = state["brief"]
        personas = _build_personas(brief.get("audience_summary", ""))
        return {
            "schema_version": PLACEHOLDER_SCHEMA_VERSION,
            "placeholder": True,
            "objective": brief.get("objective"),
            "personas": personas,
            "kpis": [
                {
                    "id": "qualified_signups",
                    "label": "Qualified signups",
                    "reason": "Matches the primary campaign objective.",
                },
                {
                    "id": "onboarding_completion_rate",
                    "label": "Onboarding completion rate",
                    "reason": "Tracks signup quality beyond initial conversion.",
                },
                {
                    "id": "cost_per_qualified_signup",
                    "label": "Cost per qualified signup",
                    "reason": "Keeps paid channel efficiency visible for the demo.",
                },
            ],
            "brand_voice": brief.get("brand_voice", []),
        }

    def _build_journey_output(self, state: WorkflowState) -> dict[str, Any]:
        strategy = state["strategy"]
        channels = state["brief"].get("channels", [])
        kpis = strategy["kpis"]
        steps = []
        for persona_index, persona in enumerate(strategy["personas"]):
            for channel in channels:
                steps.append(
                    {
                        "persona_id": persona["id"],
                        "channel": channel,
                        "journey_stage": _channel_stage(channel),
                        "primary_kpi": kpis[persona_index % len(kpis)]["id"],
                        "message_focus": (
                            f"{persona['name']} sees a {channel.replace('_', ' ')}"
                            " touchpoint tailored to the brief objective."
                        ),
                    }
                )

        return {
            "schema_version": PLACEHOLDER_SCHEMA_VERSION,
            "placeholder": True,
            "steps": steps,
        }

    def _build_creative_output(self, state: WorkflowState) -> dict[str, Any]:
        journey = state["journey"]
        variants = [
            {
                "persona_id": step["persona_id"],
                "channel": step["channel"],
                "journey_stage": step["journey_stage"],
                "primary_kpi": step["primary_kpi"],
                "concept": (
                    f"Placeholder creative for {step['persona_id']} on"
                    f" {step['channel']}."
                ),
            }
            for step in journey["steps"]
        ]
        return {
            "schema_version": PLACEHOLDER_SCHEMA_VERSION,
            "placeholder": True,
            "variant_count": len(variants),
            "variants": variants,
        }

    def _build_policy_output(self, state: WorkflowState) -> dict[str, Any]:
        risky_claims = state["brief"].get("risky_claims", [])
        findings = [
            {
                "severity": "warning",
                "message": f"Watch risky claim during later real policy checks: {claim}",
            }
            for claim in risky_claims
        ]
        return {
            "schema_version": PLACEHOLDER_SCHEMA_VERSION,
            "placeholder": True,
            "summary": {
                "blocking_findings": 0,
                "warning_findings": len(findings),
            },
            "findings": findings,
        }

    def _build_approval_output(self, state: WorkflowState) -> dict[str, Any]:
        policy = state["policy"]
        summary = policy["summary"]
        return {
            "schema_version": PLACEHOLDER_SCHEMA_VERSION,
            "placeholder": True,
            "ready_for_approval": summary["blocking_findings"] == 0,
            "blocking_findings": summary["blocking_findings"],
            "warning_findings": summary["warning_findings"],
        }

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
            return {"variants": output["variant_count"]}
        if stage_name == "policy":
            return output["summary"]
        return {
            "readyForApproval": output["ready_for_approval"],
            "warningFindings": output["warning_findings"],
        }


def start_placeholder_workflow(
    *,
    session_factory: sessionmaker[Session],
    campaign_id: uuid.UUID,
    run_id: uuid.UUID,
    mode: WorkflowMode,
) -> None:
    runner = PlaceholderWorkflowRunner(session_factory)
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


def _build_personas(audience_summary: str) -> list[dict[str, str]]:
    raw_segments = [
        segment.strip(" .")
        for segment in re.split(r",| and ", audience_summary)
        if segment.strip(" .")
    ]
    segments = raw_segments[:3]
    while len(segments) < 3:
        segments.append(f"Audience segment {len(segments) + 1}")

    personas = []
    for index, segment in enumerate(segments, start=1):
        personas.append(
            {
                "id": _slugify(f"persona_{index}_{segment}"),
                "name": segment.title(),
                "summary": (
                    f"Placeholder persona synthesized from the brief audience: {segment}."
                ),
            }
        )
    return personas


def _channel_stage(channel: str) -> str:
    if channel == "google_search":
        return "discovery"
    if channel == "linkedin_sponsored_post":
        return "consideration"
    if channel == "email":
        return "conversion"
    return "nurture"


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
