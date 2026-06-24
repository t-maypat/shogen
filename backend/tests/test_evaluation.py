from __future__ import annotations

import uuid

from app.db.models import Campaign, CreativeVariant, PolicyFinding
from app.schemas.brief import CampaignBrief
from app.services.evaluation import SyntheticEvaluationService, Wave2OptimizationService
from app.services.generation import build_default_fake_provider


def test_synthetic_evaluation_uses_weighted_factor_formula() -> None:
    campaign = _campaign()
    variants = [
        _variant(
            persona_id="p1",
            channel="google_search",
            journey_stage="discovery",
            primary_kpi="qualified_signups",
            copy={"cta": "Explore plans"},
        ),
        _variant(
            persona_id="p1",
            channel="linkedin_sponsored_post",
            journey_stage="consideration",
            primary_kpi="qualified_signups",
            copy={"cta": "See how it works"},
        ),
    ]
    warning = PolicyFinding(
        campaign_id=campaign.id,
        run_id=variants[0].run_id,
        variant_id=variants[0].id,
        source="deterministic",
        severity="low",
        status="open",
        finding_type="channel_length",
        evidence="headline",
        message="Shorten the headline.",
    )

    result = SyntheticEvaluationService().evaluate(
        campaign=campaign,
        variants=variants,
        journey=_journey(),
        policy_findings=[warning],
    )

    google_scores = result.results[0]["scores"]
    linkedin_scores = result.results[1]["scores"]
    assert google_scores["policy_quality"] == 80
    assert google_scores["weighted_total"] == 81
    assert linkedin_scores["policy_quality"] == 100
    assert linkedin_scores["weighted_total"] == 69
    assert result.payload["summary"]["medium_performers"] == 1


def test_wave2_optimizer_normalizes_allocations_and_rewrites_weak_variants() -> None:
    campaign = _campaign()
    run_id = uuid.uuid4()
    variants = [
        _variant(
            persona_id="p1",
            channel="google_search",
            journey_stage="discovery",
            primary_kpi="qualified_signups",
            copy={"cta": "Explore plans"},
            run_id=run_id,
        ),
        _variant(
            persona_id="p1",
            channel="linkedin_sponsored_post",
            journey_stage="consideration",
            primary_kpi="qualified_signups",
            copy={
                "intro_text": "A responsible way to act on financial goals.",
                "headline": "A steadier way to start",
                "description": "Guidance without hype.",
                "cta": "See how it works",
            },
            run_id=run_id,
        ),
        _variant(
            persona_id="p1",
            channel="email",
            journey_stage="conversion",
            primary_kpi="qualified_signups",
            copy={"cta": "Start your plan"},
            run_id=run_id,
        ),
    ]
    evaluation = SyntheticEvaluationService().evaluate(
        campaign=campaign,
        variants=variants,
        journey=_journey(),
        policy_findings=[],
    )

    wave2 = Wave2OptimizationService(
        provider=build_default_fake_provider(),
        timeout_seconds=1,
    ).optimize(
        brief=CampaignBrief.model_validate(campaign.brief_json),
        variants=variants,
        journey=_journey(),
        evaluation_results=evaluation.results,
    )

    allocation_changes = wave2.proposal["allocation_changes"]
    assert sum(change["wave2_allocation_percent"] for change in allocation_changes) == 100
    assert any(change["delta_percent"] != 0 for change in allocation_changes)
    assert [
        rewrite["client_variant_id"]
        for rewrite in wave2.proposal["rewrites"]
    ] == ["p1_linkedin_sponsored_post"]
    assert wave2.rationale["directional"] is True


def _campaign() -> Campaign:
    return Campaign(
        id=uuid.uuid4(),
        name="NestWise",
        status="draft",
        brief_json={
            "product_name": "NestWise",
            "product_category": "Fintech savings and starter investing app",
            "objective": "Drive qualified signups",
            "audience_summary": "Young first-time investors",
            "brand_voice": ["clear"],
            "required_claims": ["Easy onboarding"],
            "risky_claims": ["guaranteed returns"],
            "channels": [
                "google_search",
                "linkedin_sponsored_post",
                "email",
            ],
        },
    )


def _journey() -> dict:
    return {
        "steps": [
            {
                "persona_id": "p1",
                "channel": "google_search",
                "journey_stage": "discovery",
                "primary_kpi_id": "qualified_signups",
                "allocation_percent": 34,
            },
            {
                "persona_id": "p1",
                "channel": "linkedin_sponsored_post",
                "journey_stage": "consideration",
                "primary_kpi_id": "qualified_signups",
                "allocation_percent": 33,
            },
            {
                "persona_id": "p1",
                "channel": "email",
                "journey_stage": "conversion",
                "primary_kpi_id": "qualified_signups",
                "allocation_percent": 33,
            },
        ]
    }


def _variant(
    *,
    persona_id: str,
    channel: str,
    journey_stage: str,
    primary_kpi: str,
    copy: dict,
    run_id: uuid.UUID | None = None,
) -> CreativeVariant:
    variant_id = uuid.uuid4()
    return CreativeVariant(
        id=variant_id,
        campaign_id=uuid.uuid4(),
        run_id=run_id or uuid.uuid4(),
        persona_id=persona_id,
        channel=channel,
        journey_stage=journey_stage,
        primary_kpi=primary_kpi,
        status="generated",
        copy_json={
            "client_variant_id": f"{persona_id}_{channel}",
            "claims": ["Easy onboarding"],
            "disclosure": "Investing involves risk. Returns are not guaranteed.",
            "copy": copy,
        },
    )
