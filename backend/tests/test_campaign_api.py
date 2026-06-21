from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import create_engine_for_url, get_db_session
from app.main import create_app


@pytest.fixture
def client(tmp_path) -> Generator[TestClient, None, None]:
    database_path = tmp_path / "campaign-api.db"
    engine = create_engine_for_url(f"sqlite+pysqlite:///{database_path}")
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )

    app = create_app()

    def override_db_session() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def valid_campaign_payload() -> dict:
    return {
        "name": "NestWise June Campaign",
        "brief": {
            "product_name": "NestWise",
            "product_category": "Fintech savings and starter investing app",
            "objective": "Drive qualified signups",
            "audience_summary": (
                "Young first-time investors, risk-conscious professionals, "
                "and small-business owners"
            ),
            "budget_range": "$25k demo budget",
            "duration_days": 30,
            "brand_voice": ["clear", "trustworthy", "responsible"],
            "required_claims": [
                "Easy onboarding",
                "Beginner-friendly saving tools",
            ],
            "risky_claims": ["guaranteed returns"],
            "channels": [
                "google_search",
                "linkedin_sponsored_post",
                "email",
            ],
            "notes": "Demo scenario should intentionally test policy-readiness.",
        },
    }


def test_create_campaign_returns_draft_envelope(
    client: TestClient,
    valid_campaign_payload: dict,
) -> None:
    response = client.post("/api/campaigns", json=valid_campaign_payload)

    assert response.status_code == 201
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["status"] == "draft"
    assert uuid.UUID(payload["data"]["campaign_id"])


def test_get_campaign_returns_full_campaign_state(
    client: TestClient,
    valid_campaign_payload: dict,
) -> None:
    create_response = client.post("/api/campaigns", json=valid_campaign_payload)
    campaign_id = create_response.json()["data"]["campaign_id"]

    response = client.get(f"/api/campaigns/{campaign_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["campaign"]["id"] == campaign_id
    assert payload["data"]["campaign"]["name"] == valid_campaign_payload["name"]
    assert payload["data"]["campaign"]["brief"] == valid_campaign_payload["brief"]
    assert payload["data"]["campaign"]["status"] == "draft"
    assert payload["data"]["latest_run"] is None
    assert payload["data"]["strategy"] is None
    assert payload["data"]["journey"] is None
    assert payload["data"]["creative_variants"] == []
    assert payload["data"]["policy_findings"] == []
    assert payload["data"]["approval"] is None
    assert payload["data"]["evaluation_results"] == []
    assert payload["data"]["wave_proposal"] is None
    assert payload["data"]["events"] == []


def test_create_campaign_with_invalid_brief_returns_validation_error(
    client: TestClient,
    valid_campaign_payload: dict,
) -> None:
    invalid_payload = {
        **valid_campaign_payload,
        "brief": {
            key: value
            for key, value in valid_campaign_payload["brief"].items()
            if key != "product_name"
        },
    }

    response = client.post("/api/campaigns", json=invalid_payload)

    assert response.status_code == 422
    payload = response.json()
    assert payload["data"] is None
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert "brief.product_name" in payload["error"]["message"]
    assert {
        "field": "brief.product_name",
        "message": "Field required",
        "type": "missing",
    } in payload["error"]["details"]["errors"]


def test_get_campaign_returns_not_found_error(client: TestClient) -> None:
    response = client.get(f"/api/campaigns/{uuid.uuid4()}")

    assert response.status_code == 404
    payload = response.json()
    assert payload["data"] is None
    assert payload["error"]["code"] == "NOT_FOUND"
