from __future__ import annotations

import uuid

from app.db.models import CreativeVariant
from app.policy.engine import DeterministicPolicyEngine
from app.schemas.brief import CampaignBrief


def test_policy_engine_blocks_banned_phrase() -> None:
    evaluation = DeterministicPolicyEngine().evaluate(
        brief=_brief(),
        strategy=_strategy(),
        journey=_journey(),
        variants=[
            _variant(
                channel="google_search",
                journey_stage="discovery",
                primary_kpi="qualified_signups",
                disclosure="Investing involves risk. Returns are not guaranteed.",
                copy={
                    "headlines": [
                        "NestWise for Savers",
                        "Guaranteed Returns Today",
                        "Start Investing With Clarity",
                    ],
                    "descriptions": [
                        "Build saving habits with a measured plan.",
                        "Transparent steps for careful first moves in finance.",
                    ],
                    "cta": "Explore plans",
                },
            )
        ],
    )

    assert evaluation.summary["blocking_findings"] == 1
    assert evaluation.summary["blocked_variants"] == 1
    assert evaluation.variant_results[0].status == "blocked"
    assert evaluation.findings[0].rule_id == "FIN-CLAIM-001"
    assert "Guaranteed Returns Today" in evaluation.findings[0].evidence


def test_policy_engine_flags_missing_finance_disclosure() -> None:
    evaluation = DeterministicPolicyEngine().evaluate(
        brief=_brief(),
        strategy=_strategy(),
        journey=_journey(channel="linkedin_sponsored_post", journey_stage="consideration"),
        variants=[
            _variant(
                channel="linkedin_sponsored_post",
                journey_stage="consideration",
                primary_kpi="qualified_signups",
                disclosure=None,
                copy={
                    "intro_text": "Build your next money habit with practical guidance.",
                    "headline": "A steadier way to start",
                    "description": "Clear steps for new savers without hype.",
                    "cta": "See how it works",
                },
            )
        ],
    )

    assert evaluation.summary["blocking_findings"] == 1
    assert evaluation.findings[0].rule_id == "FIN-DISC-001"
    assert evaluation.findings[0].evidence == "disclosure: <missing>"


def test_policy_engine_flags_google_length_warning() -> None:
    evaluation = DeterministicPolicyEngine().evaluate(
        brief=_brief(),
        strategy=_strategy(),
        journey=_journey(),
        variants=[
            _variant(
                channel="google_search",
                journey_stage="discovery",
                primary_kpi="qualified_signups",
                disclosure="Investing involves risk. Returns are not guaranteed.",
                copy={
                    "headlines": [
                        "NestWise for Young First-Time Investors",
                        "Build Smarter Saving Habits",
                        "Start Investing With Clarity",
                    ],
                    "descriptions": [
                        "Build saving habits with a measured plan.",
                        "Transparent steps for careful first moves in finance.",
                    ],
                    "cta": "Explore plans",
                },
            )
        ],
    )

    assert evaluation.summary["blocking_findings"] == 0
    assert evaluation.summary["warning_findings"] == 1
    assert evaluation.variant_results[0].status == "warning"
    assert evaluation.findings[0].rule_id == "GOOG-LEN-001"


def test_policy_engine_flags_mapping_mismatch() -> None:
    evaluation = DeterministicPolicyEngine().evaluate(
        brief=_brief(),
        strategy=_strategy(),
        journey=_journey(channel="email", journey_stage="conversion"),
        variants=[
            _variant(
                channel="email",
                journey_stage="discovery",
                primary_kpi="cost_per_qualified_signup",
                disclosure="Investing involves risk. Returns are not guaranteed.",
                copy={
                    "subject": "Start your next money habit",
                    "preheader": "A practical next step for careful savers.",
                    "body": "Clear steps and a steady tone for your first move.",
                    "cta": "Start your plan",
                },
            )
        ],
    )

    assert evaluation.summary["blocking_findings"] == 2
    assert evaluation.variant_results[0].status == "blocked"
    assert {finding.rule_id for finding in evaluation.findings} == {"COMMON-MAP-001"}
    assert {
        finding.metadata["check"] for finding in evaluation.findings if finding.metadata
    } == {"journey_stage", "primary_kpi"}


def _brief() -> CampaignBrief:
    return CampaignBrief.model_validate(
        {
            "product_name": "NestWise",
            "product_category": "Fintech savings and starter investing app",
            "objective": "Drive qualified signups",
            "audience_summary": (
                "Young first-time investors, risk-conscious professionals, "
                "and small-business owners"
            ),
            "brand_voice": ["clear", "trustworthy", "responsible"],
            "required_claims": ["Easy onboarding", "Beginner-friendly saving tools"],
            "risky_claims": ["guaranteed returns"],
            "channels": ["google_search", "linkedin_sponsored_post", "email"],
        }
    )


def _strategy() -> dict:
    return {"personas": [{"id": "p1"}]}


def _journey(
    *,
    channel: str = "google_search",
    journey_stage: str = "discovery",
) -> dict:
    return {
        "steps": [
            {
                "persona_id": "p1",
                "channel": channel,
                "journey_stage": journey_stage,
                "primary_kpi_id": "qualified_signups",
            }
        ]
    }


def _variant(
    *,
    channel: str,
    journey_stage: str,
    primary_kpi: str,
    disclosure: str | None,
    copy: dict,
) -> CreativeVariant:
    return CreativeVariant(
        id=uuid.uuid4(),
        campaign_id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        persona_id="p1",
        channel=channel,
        journey_stage=journey_stage,
        primary_kpi=primary_kpi,
        revision_number=0,
        status="generated",
        copy_json={
            "client_variant_id": f"p1_{channel}",
            "claims": ["Easy onboarding"],
            "disclosure": disclosure,
            "copy": copy,
        },
    )
