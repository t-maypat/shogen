from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.errors import ApiException
from app.db.session import get_db_session
from app.repositories.campaigns import CampaignRepository
from app.schemas.campaigns import (
    CampaignCreateData,
    CampaignCreateEnvelope,
    CampaignCreateRequest,
    CampaignStateEnvelope,
)
from app.services.campaigns import CampaignNotFoundError, CampaignService

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
