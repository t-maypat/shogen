from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.errors import ApiException
from app.api.routes_campaigns import _session_factory_from_session
from app.db.session import get_db_session
from app.repositories.campaigns import CampaignRepository
from app.schemas.demo import DemoReplayData, DemoReplayEnvelope, DemoReplayRequest
from app.services.replay import ReplayScenarioNotFoundError, ReplayService
from app.services.workflows import WorkflowService, start_campaign_workflow

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post(
    "/replay",
    response_model=DemoReplayEnvelope,
    status_code=status.HTTP_201_CREATED,
)
def start_demo_replay(
    payload: DemoReplayRequest,
    session: Session = Depends(get_db_session),
) -> DemoReplayEnvelope:
    repository = CampaignRepository(session)
    try:
        campaign = ReplayService(repository).create_campaign_for_scenario(
            payload.scenario,
        )
    except ReplayScenarioNotFoundError as exc:
        raise ApiException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPLAY_SCENARIO_NOT_FOUND",
            message=str(exc),
            details={"scenario": exc.scenario},
        ) from exc

    workflow_result = WorkflowService(repository).start_workflow(
        campaign_id=campaign.id,
        mode="replay",
    )
    if workflow_result.started:
        start_campaign_workflow(
            session_factory=_session_factory_from_session(session),
            campaign_id=campaign.id,
            run_id=workflow_result.run.id,
            mode="replay",
        )

    return DemoReplayEnvelope(
        data=DemoReplayData(
            campaign_id=campaign.id,
            run_id=workflow_result.run.id,
            status=workflow_result.run.status,
            replay_mode=workflow_result.run.replay_mode,
        ),
        error=None,
    )
