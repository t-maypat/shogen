from __future__ import annotations

import asyncio
import uuid

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.errors import ApiException
from app.db.session import get_db_session
from app.repositories.campaigns import CampaignRepository
from app.schemas.campaigns import (
    ApprovalSummary,
    CampaignApprovalData,
    CampaignApprovalEnvelope,
    CampaignApprovalRequest,
    CampaignCreateData,
    CampaignCreateEnvelope,
    CampaignCreateRequest,
    CampaignRunData,
    CampaignRunEnvelope,
    CampaignRunRequest,
    CampaignStateEnvelope,
)
from app.services.campaigns import CampaignNotFoundError, CampaignService
from app.services.events import EventService
from app.services.workflows import (
    WorkflowAlreadyApprovedError,
    WorkflowAlreadyRunningError,
    WorkflowApprovalBlockedError,
    WorkflowApprovalNotReadyError,
    WorkflowService,
    start_campaign_workflow,
)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.post(
    "",
    response_model=CampaignCreateEnvelope,
    status_code=status.HTTP_201_CREATED,
)
def create_campaign(
    payload: CampaignCreateRequest,
    session: Session = Depends(get_db_session),
) -> CampaignCreateEnvelope:
    service = CampaignService(CampaignRepository(session))
    campaign = service.create_campaign(name=payload.name, brief=payload.brief)
    return CampaignCreateEnvelope(
        data=CampaignCreateData(
            campaign_id=campaign.id,
            status=campaign.status,
        ),
        error=None,
    )


@router.get(
    "/{campaign_id}",
    response_model=CampaignStateEnvelope,
)
def get_campaign(
    campaign_id: uuid.UUID,
    session: Session = Depends(get_db_session),
) -> CampaignStateEnvelope:
    service = CampaignService(CampaignRepository(session))
    try:
        state = service.get_campaign_state(campaign_id)
    except CampaignNotFoundError as exc:
        raise ApiException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=str(exc),
            details={"campaign_id": str(exc.campaign_id)},
        ) from exc

    return CampaignStateEnvelope(data=state, error=None)


@router.post(
    "/{campaign_id}/run",
    response_model=CampaignRunEnvelope,
)
def run_campaign(
    campaign_id: uuid.UUID,
    payload: CampaignRunRequest,
    session: Session = Depends(get_db_session),
) -> CampaignRunEnvelope:
    workflow_service = WorkflowService(CampaignRepository(session))
    try:
        run = workflow_service.start_workflow(
            campaign_id=campaign_id,
            mode=payload.mode,
        )
    except CampaignNotFoundError as exc:
        raise ApiException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=str(exc),
            details={"campaign_id": str(exc.campaign_id)},
        ) from exc
    except WorkflowAlreadyRunningError as exc:
        raise ApiException(
            status_code=status.HTTP_409_CONFLICT,
            code="WORKFLOW_ALREADY_RUNNING",
            message=str(exc),
            details={
                "campaign_id": str(exc.campaign_id),
                "run_id": str(exc.run_id),
            },
        ) from exc

    start_campaign_workflow(
        session_factory=_session_factory_from_session(session),
        campaign_id=campaign_id,
        run_id=run.id,
        mode=payload.mode,
    )
    return CampaignRunEnvelope(
        data=CampaignRunData(run_id=run.id, status=run.status),
        error=None,
    )


@router.post(
    "/{campaign_id}/approve",
    response_model=CampaignApprovalEnvelope,
)
def approve_campaign(
    campaign_id: uuid.UUID,
    payload: CampaignApprovalRequest,
    session: Session = Depends(get_db_session),
) -> CampaignApprovalEnvelope:
    workflow_service = WorkflowService(CampaignRepository(session))
    try:
        result = workflow_service.approve_campaign(
            campaign_id=campaign_id,
            approved_by=payload.approved_by,
            notes=payload.notes,
        )
    except CampaignNotFoundError as exc:
        raise ApiException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=str(exc),
            details={"campaign_id": str(exc.campaign_id)},
        ) from exc
    except WorkflowApprovalBlockedError as exc:
        raise ApiException(
            status_code=status.HTTP_409_CONFLICT,
            code="APPROVAL_BLOCKED",
            message=str(exc),
            details={
                "campaign_id": str(exc.campaign_id),
                "run_id": str(exc.run_id),
                "blocking_findings": exc.blocking_findings,
                "deterministic_blocking_findings": (
                    exc.deterministic_blocking_findings
                ),
            },
        ) from exc
    except WorkflowAlreadyApprovedError as exc:
        raise ApiException(
            status_code=status.HTTP_409_CONFLICT,
            code="ALREADY_APPROVED",
            message=str(exc),
            details={
                "campaign_id": str(exc.campaign_id),
                "run_id": str(exc.run_id),
            },
        ) from exc
    except WorkflowApprovalNotReadyError as exc:
        raise ApiException(
            status_code=status.HTTP_409_CONFLICT,
            code="APPROVAL_NOT_READY",
            message=str(exc),
            details={
                "campaign_id": str(exc.campaign_id),
                "run_id": str(exc.run_id) if exc.run_id is not None else None,
                "status": exc.status,
            },
        ) from exc

    return CampaignApprovalEnvelope(
        data=CampaignApprovalData(
            campaign_id=campaign_id,
            run_id=result.run_id,
            approval=ApprovalSummary(
                id=result.approval_id,
                approved_by=result.approved_by,
                status=result.approval_status,
                notes=result.approval_notes,
                created_at=result.approval_created_at,
            ),
            mock_deployment=result.mock_deployment,
            status=result.status,
        ),
        error=None,
    )


@router.get(
    "/{campaign_id}/events",
)
async def stream_campaign_events(
    campaign_id: uuid.UUID,
    request: Request,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    session: Session = Depends(get_db_session),
) -> StreamingResponse:
    repository = CampaignRepository(session)
    if repository.get_campaign(campaign_id) is None:
        raise ApiException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Campaign {campaign_id} not found",
            details={"campaign_id": str(campaign_id)},
        )

    after_id = _parse_last_event_id(last_event_id)
    session_factory = _session_factory_from_session(session)

    async def event_stream() -> AsyncGenerator[str, None]:
        next_after_id = after_id
        while True:
            if await request.is_disconnected():
                break

            with session_factory() as stream_session:
                stream_repository = CampaignRepository(stream_session)
                events = stream_repository.list_events_for_campaign(
                    campaign_id,
                    after_id=next_after_id,
                )

            if events:
                for event in events:
                    next_after_id = event.id
                    yield EventService.format_sse(event)
                continue

            with session_factory() as stream_session:
                latest_run = CampaignRepository(stream_session).get_latest_run(campaign_id)
            if latest_run is None or latest_run.status != "running":
                break

            await asyncio.sleep(0.2)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _session_factory_from_session(session: Session) -> sessionmaker[Session]:
    bind = session.get_bind()
    if not isinstance(bind, Engine):  # pragma: no cover - defensive guard
        raise RuntimeError("Database engine is not available for workflow tasks")
    return sessionmaker(
        bind=bind,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )


def _parse_last_event_id(last_event_id: str | None) -> int | None:
    if last_event_id is None or last_event_id == "":
        return None
    try:
        return int(last_event_id)
    except ValueError as exc:
        raise ApiException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Invalid Last-Event-ID header",
            details={
                "errors": [
                    {
                        "field": "headers.Last-Event-ID",
                        "message": "Value must be an integer",
                        "type": "value_error",
                    }
                ]
            },
        ) from exc
