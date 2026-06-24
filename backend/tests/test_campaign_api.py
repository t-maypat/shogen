from __future__ import annotations

import json
import time
import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import StageOutput
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
def client_with_session_factory(
    tmp_path,
) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    database_path = tmp_path / "campaign-run-api.db"
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
        yield test_client, session_factory

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


def test_run_campaign_persists_generated_workflow_outputs(
    client_with_session_factory: tuple[TestClient, sessionmaker[Session]],
    valid_campaign_payload: dict,
) -> None:
    client, session_factory = client_with_session_factory

    create_response = client.post("/api/campaigns", json=valid_campaign_payload)
    campaign_id = create_response.json()["data"]["campaign_id"]

    run_response = client.post(
        f"/api/campaigns/{campaign_id}/run",
        json={"mode": "live"},
    )

    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["error"] is None
    run_id = run_payload["data"]["run_id"]
    assert run_payload["data"]["status"] == "running"
    assert uuid.UUID(run_id)

    campaign_state = _wait_for_campaign_status(
        client,
        campaign_id,
        expected_status="approval_required",
    )

    assert campaign_state["latest_run"]["status"] == "approval_required"
    assert campaign_state["latest_run"]["current_stage"] == "approval_required"
    assert [persona["id"] for persona in campaign_state["strategy"]["personas"]] == [
        "p1",
        "p2",
        "p3",
    ]
    assert len(campaign_state["strategy"]["personas"]) == 3
    assert len(campaign_state["strategy"]["kpis"]) == 3
    assert len(campaign_state["journey"]["steps"]) == 9
    assert (
        sum(step["allocation_percent"] for step in campaign_state["journey"]["steps"]) == 100
    )
    assert len(campaign_state["creative_variants"]) == 13
    active_variants = [
        variant
        for variant in campaign_state["creative_variants"]
        if variant["status"] != "revised"
    ]
    revised_variants = [
        variant
        for variant in campaign_state["creative_variants"]
        if variant["status"] == "revised"
    ]
    assert len(active_variants) == 9
    assert len(revised_variants) == 4
    assert {
        (variant["persona_id"], variant["channel"])
        for variant in active_variants
    } == {
        ("p1", "google_search"),
        ("p1", "linkedin_sponsored_post"),
        ("p1", "email"),
        ("p2", "google_search"),
        ("p2", "linkedin_sponsored_post"),
        ("p2", "email"),
        ("p3", "google_search"),
        ("p3", "linkedin_sponsored_post"),
        ("p3", "email"),
    }
    assert all(
        variant["claims"] for variant in active_variants
    )
    assert all(
        variant["copy"] for variant in active_variants
    )
    assert all(
        variant["revision_number"] <= 2
        for variant in campaign_state["creative_variants"]
    )
    assert all(
        variant["parent_variant_id"] is not None
        for variant in active_variants
        if variant["revision_number"] > 0
    )
    assert not any(variant["status"] == "blocked" for variant in active_variants)
    assert any(variant["status"] == "passed" for variant in active_variants)
    assert any(
        finding["source"] == "semantic"
        for finding in campaign_state["policy_findings"]
    )
    assert any(
        finding["rule_id"] == "FIN-CLAIM-001"
        for finding in campaign_state["policy_findings"]
    )
    assert not any(
        finding["severity"] == "blocking" and finding["status"] == "open"
        for finding in campaign_state["policy_findings"]
    )
    assert len(campaign_state["events"]) >= 12
    assert campaign_state["events"][0]["event_type"] == "workflow.started"
    assert any(
        event["event_type"] == "policy.revision_created"
        for event in campaign_state["events"]
    )
    assert campaign_state["events"][-1]["stage"] == "approval_required"
    assert campaign_state["events"][-1]["payload"]["status"] == "approval_required"

    with session_factory() as session:
        stage_outputs = (
            session.query(StageOutput)
            .where(StageOutput.run_id == uuid.UUID(run_id))
            .order_by(StageOutput.created_at.asc(), StageOutput.id.asc())
            .all()
        )

    stage_outputs_by_name = {
        stage_output.stage_name: stage_output for stage_output in stage_outputs
    }
    assert set(stage_outputs_by_name) == {
        "strategy",
        "journey",
        "creative",
        "policy",
        "approval_required",
    }
    assert stage_outputs_by_name["strategy"].prompt_version == "strategy.v1"
    assert stage_outputs_by_name["strategy"].model_name == "fake-shogen-campaign-model"
    assert stage_outputs_by_name["journey"].prompt_version == "journey.det.v1"
    assert stage_outputs_by_name["journey"].model_name == "deterministic-journey-planner"
    assert stage_outputs_by_name["creative"].prompt_version == "creative.v1"
    assert stage_outputs_by_name["creative"].model_name == "fake-shogen-campaign-model"
    assert stage_outputs_by_name["policy"].schema_version == "policy.review.v1"
    assert stage_outputs_by_name["policy"].prompt_version == "semantic_review.v1"
    assert stage_outputs_by_name["policy"].output_json["summary"]["blocking_findings"] == 0
    assert stage_outputs_by_name["policy"].output_json["summary"]["revision_count"] == 1
    assert stage_outputs_by_name["policy"].output_json["summary"]["ready_for_approval"] is True
    assert stage_outputs_by_name["approval_required"].output_json["ready_for_approval"] is True


def test_campaign_events_endpoint_streams_sse_payloads(
    client: TestClient,
    valid_campaign_payload: dict,
) -> None:
    create_response = client.post("/api/campaigns", json=valid_campaign_payload)
    campaign_id = create_response.json()["data"]["campaign_id"]

    run_response = client.post(
        f"/api/campaigns/{campaign_id}/run",
        json={"mode": "replay"},
    )
    run_id = run_response.json()["data"]["run_id"]

    with client.stream("GET", f"/api/campaigns/{campaign_id}/events") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

        lines: list[str] = []
        for line in response.iter_lines():
            if not line:
                if lines:
                    break
                continue
            lines.append(line)

    assert lines[0].startswith("id: ")
    assert lines[1] == "event: workflow.started"
    assert lines[2].startswith("data: ")

    payload = json.loads(lines[2].removeprefix("data: "))
    assert payload["campaignId"] == campaign_id
    assert payload["runId"] == run_id
    assert payload["status"] == "running"

    with client.stream(
        "GET",
        f"/api/campaigns/{campaign_id}/events",
        headers={"Last-Event-ID": lines[0].removeprefix("id: ")},
    ) as response:
        resumed_lines: list[str] = []
        for line in response.iter_lines():
            if not line:
                if resumed_lines:
                    break
                continue
            resumed_lines.append(line)

    assert resumed_lines[0] != lines[0]
    assert resumed_lines[1].startswith("event: stage.")


def _wait_for_campaign_status(
    client: TestClient,
    campaign_id: str,
    *,
    expected_status: str,
    timeout_seconds: float = 3.0,
) -> dict:
    deadline = time.monotonic() + timeout_seconds
    latest_payload: dict | None = None

    while time.monotonic() < deadline:
        response = client.get(f"/api/campaigns/{campaign_id}")
        assert response.status_code == 200
        latest_payload = response.json()["data"]
        latest_run = latest_payload["latest_run"]
        if latest_run and latest_run["status"] == expected_status:
            return latest_payload
        time.sleep(0.05)

    raise AssertionError(f"Campaign {campaign_id} did not reach {expected_status}")
