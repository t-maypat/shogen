from __future__ import annotations

import copy
import re
from typing import Any

from app.ai.prompts import (
    CREATIVE_PROMPT_VERSION,
    JOURNEY_PLANNER_VERSION,
    STRATEGY_PROMPT_VERSION,
    build_creative_prompt,
    build_strategy_prompt,
)
from app.ai.provider import FakeModelProvider, ModelProvider, ModelRequest
from app.schemas.brief import CampaignBrief
from app.schemas.creative import (
    CreativeOutput,
    CreativeVariantOut,
    EmailCopy,
    GoogleSearchCopy,
    LinkedInCopy,
)
from app.schemas.journey import JourneyOutput, JourneyStage, JourneyStep
from app.schemas.review import CreativeRevisionOutput, SemanticReviewOutput
from app.schemas.strategy import KPI, Persona, StrategyOutput

JOURNEY_MODEL_NAME = "deterministic-journey-planner"


class CampaignGenerationService:
    def __init__(self, provider: ModelProvider, *, timeout_seconds: float) -> None:
        self.provider = provider
        self.timeout_seconds = timeout_seconds

    def generate_strategy(self, brief: CampaignBrief) -> tuple[StrategyOutput, dict[str, Any]]:
        response = self.provider.generate_structured(
            ModelRequest(
                operation="strategy.generate",
                prompt=build_strategy_prompt(brief),
                prompt_version=STRATEGY_PROMPT_VERSION,
                response_model=StrategyOutput,
                timeout_seconds=self.timeout_seconds,
                metadata={"brief": brief.model_dump(mode="json")},
            )
        )
        return response.output, {
            "schema_version": STRATEGY_PROMPT_VERSION,
            "prompt_version": response.prompt_version,
            "model_name": response.model_name,
            "duration_ms": response.duration_ms,
        }

    def generate_journey(
        self,
        *,
        brief: CampaignBrief,
        strategy: StrategyOutput,
    ) -> tuple[JourneyOutput, dict[str, Any]]:
        journey = JourneyOutput(
            steps=_build_journey_steps(brief=brief, strategy=strategy),
        )
        return journey, {
            "schema_version": JOURNEY_PLANNER_VERSION,
            "prompt_version": JOURNEY_PLANNER_VERSION,
            "model_name": JOURNEY_MODEL_NAME,
            "duration_ms": 0,
        }

    def generate_creative(
        self,
        *,
        brief: CampaignBrief,
        strategy: StrategyOutput,
        journey: JourneyOutput,
    ) -> tuple[CreativeOutput, dict[str, Any]]:
        response = self.provider.generate_structured(
            ModelRequest(
                operation="creative.generate",
                prompt=build_creative_prompt(
                    brief=brief,
                    strategy=strategy,
                    journey=journey,
                ),
                prompt_version=CREATIVE_PROMPT_VERSION,
                response_model=CreativeOutput,
                timeout_seconds=self.timeout_seconds,
                metadata={
                    "brief": brief.model_dump(mode="json"),
                    "strategy": strategy.model_dump(mode="json"),
                    "journey": journey.model_dump(mode="json"),
                },
            )
        )
        return response.output, {
            "schema_version": CREATIVE_PROMPT_VERSION,
            "prompt_version": response.prompt_version,
            "model_name": response.model_name,
            "duration_ms": response.duration_ms,
        }


def build_default_fake_provider() -> FakeModelProvider:
    provider = FakeModelProvider(model_name="fake-shogen-campaign-model")
    provider.register_handler("strategy.generate", _fake_strategy_response)
    provider.register_handler("creative.generate", _fake_creative_response)
    provider.register_handler("semantic.review", _fake_semantic_review_response)
    provider.register_handler("creative.revise", _fake_creative_revision_response)
    return provider


def _fake_strategy_response(request: ModelRequest[Any]) -> StrategyOutput:
    brief = CampaignBrief.model_validate(request.metadata["brief"])
    segments = _audience_segments(brief.audience_summary)
    voice = ", ".join(brief.brand_voice) if brief.brand_voice else "clear and trustworthy"

    personas = [
        Persona(
            id=f"p{index}",
            name=segment["name"],
            summary=segment["summary"],
            needs=segment["needs"],
            objections=segment["objections"],
            preferred_tone=voice,
            decision_trigger=segment["decision_trigger"],
            risk_sensitivity=segment["risk_sensitivity"],
        )
        for index, segment in enumerate(segments, start=1)
    ]
    kpis = [
        KPI(
            id="qualified_signups",
            label="Qualified signups",
            reason="Matches the brief objective and keeps acquisition quality central.",
        ),
        KPI(
            id="onboarding_completion_rate",
            label="Onboarding completion rate",
            reason="Measures whether signups follow through after the first conversion.",
        ),
        KPI(
            id="cost_per_qualified_signup",
            label="Cost per qualified signup",
            reason="Keeps channel efficiency visible without implying real attribution.",
        ),
    ]
    return StrategyOutput(kpis=kpis, personas=personas)


def _fake_creative_response(request: ModelRequest[Any]) -> CreativeOutput:
    brief = CampaignBrief.model_validate(request.metadata["brief"])
    strategy = StrategyOutput.model_validate(request.metadata["strategy"])
    journey = JourneyOutput.model_validate(request.metadata["journey"])
    personas_by_id = {persona.id: persona for persona in strategy.personas}

    variants: list[CreativeVariantOut] = []
    for step in journey.steps:
        persona = personas_by_id[step.persona_id]
        disclosure = _disclosure_for_brief(brief, step.channel)
        claims = _claims_for_brief(brief, step.channel)
        if _should_seed_risky_claim(brief=brief, step=step):
            claims = [*claims, brief.risky_claims[0]]
        variant = CreativeVariantOut(
            client_variant_id=f"{step.persona_id}_{step.channel}",
            persona_id=step.persona_id,
            channel=step.channel,
            journey_stage=step.journey_stage,
            primary_kpi_id=step.primary_kpi_id,
            claims=claims,
            disclosure=disclosure,
            copy=_build_channel_copy(
                brief=brief,
                persona=persona,
                step=step,
                disclosure=disclosure,
            ),
        )
        variants.append(variant)

    return CreativeOutput(variants=variants)


def _fake_semantic_review_response(request: ModelRequest[Any]) -> SemanticReviewOutput:
    brief = CampaignBrief.model_validate(request.metadata["brief"])
    variants = request.metadata["variants"]
    finance_related = "fintech" in brief.product_category.casefold()

    reviews: list[dict[str, Any]] = []
    for variant in variants:
        findings: list[dict[str, Any]] = []
        text_fields = _variant_text_fields(variant)
        for field_name, field_value in text_fields:
            if "guaranteed returns" not in field_value.casefold():
                continue
            findings.append(
                {
                    "finding_type": "unsupported_claim",
                    "severity": "blocking",
                    "evidence": f"{field_name}: {field_value}",
                    "message": (
                        "The copy makes an unsupported investment-performance claim."
                    ),
                    "suggestion": (
                        "Replace guarantee language with risk-aware wording that can "
                        "be substantiated."
                    ),
                }
            )

        disclosure = variant.get("disclosure")
        if finance_related and (
            not isinstance(disclosure, str)
            or "investing involves risk" not in disclosure.casefold()
            or "not guaranteed" not in disclosure.casefold()
        ):
            findings.append(
                {
                    "finding_type": "sensitivity",
                    "severity": "blocking",
                    "evidence": f"disclosure: {disclosure or '<missing>'}",
                    "message": (
                        "Finance messaging needs risk context before approval."
                    ),
                    "suggestion": (
                        "Use a concise disclosure such as 'Investing involves risk. "
                        "Returns are not guaranteed.'"
                    ),
                }
            )

        status = "passed"
        if any(finding["severity"] == "blocking" for finding in findings):
            status = "blocked"
        elif findings:
            status = "warning"
        reviews.append(
            {
                "client_variant_id": variant["client_variant_id"],
                "status": status,
                "findings": findings,
            }
        )

    return SemanticReviewOutput.model_validate({"reviews": reviews})


def _fake_creative_revision_response(request: ModelRequest[Any]) -> CreativeRevisionOutput:
    variant = request.metadata["variant"]
    copy_payload = copy.deepcopy(variant["copy"])
    claims = [
        _replace_guarantee_language(claim)
        for claim in variant.get("claims", [])
        if isinstance(claim, str)
    ]

    for field_name, field_value in list(copy_payload.items()):
        if isinstance(field_value, list):
            copy_payload[field_name] = [
                _replace_guarantee_language(item) if isinstance(item, str) else item
                for item in field_value
            ]
        elif isinstance(field_value, str):
            copy_payload[field_name] = _replace_guarantee_language(field_value)

    return CreativeRevisionOutput.model_validate(
        {
            "claims": claims or ["Responsible financial guidance"],
            "disclosure": "Investing involves risk. Returns are not guaranteed.",
            "copy": copy_payload,
        }
    )


def _build_journey_steps(
    *,
    brief: CampaignBrief,
    strategy: StrategyOutput,
) -> list[JourneyStep]:
    allocations = {
        "p1": {"google_search": 13, "linkedin_sponsored_post": 11, "email": 9},
        "p2": {"google_search": 12, "linkedin_sponsored_post": 11, "email": 10},
        "p3": {"google_search": 12, "linkedin_sponsored_post": 11, "email": 11},
    }
    stage_map: dict[str, JourneyStage] = {
        "google_search": "discovery",
        "linkedin_sponsored_post": "consideration",
        "email": "conversion",
    }
    objective_map = {
        "google_search": "Capture high-intent interest with credible search messaging.",
        "linkedin_sponsored_post": "Build trust with responsible proof points and education.",
        "email": "Convert engaged prospects with a clear next step and reassurance.",
    }

    steps: list[JourneyStep] = []
    for index, persona in enumerate(strategy.personas, start=1):
        primary_kpi_id = strategy.kpis[index - 1].id
        for channel in brief.channels:
            steps.append(
                JourneyStep(
                    id=f"step_{persona.id}_{channel}",
                    persona_id=persona.id,
                    channel=channel,
                    journey_stage=stage_map[channel],
                    objective=objective_map[channel],
                    primary_kpi_id=primary_kpi_id,
                    allocation_percent=allocations[persona.id][channel],
                    message_angle=_message_angle(persona.name, channel, brief.objective),
                )
            )
    return steps


def _build_channel_copy(
    *,
    brief: CampaignBrief,
    persona: Persona,
    step: JourneyStep,
    disclosure: str | None,
):
    product_name = brief.product_name
    angle = step.message_angle
    if step.channel == "google_search":
        descriptions = [
            f"{product_name} helps {persona.name.lower()} start with clear saving steps.",
            "Build confident habits with guidance made for first moves in finance.",
        ]
        if _should_seed_risky_claim(brief=brief, step=step):
            descriptions[0] = (
                f"{product_name} helps {persona.name.lower()} pursue guaranteed returns."
            )
        if disclosure:
            descriptions[1] = "Start carefully with transparent guidance and clear risk context."
        return GoogleSearchCopy(
            headlines=[
                f"{product_name} for {persona.name}",
                "Build Smarter Saving Habits",
                "Start Investing With Clarity",
            ],
            descriptions=descriptions,
            path="start-smart",
            final_url_label="Get started",
            cta="Explore plans",
        )

    if step.channel == "linkedin_sponsored_post":
        description = (
            f"{angle} {product_name} keeps the tone practical for {persona.name.lower()}."
        )
        if disclosure:
            description = (
                f"{description} Investing involves risk, so the message stays measured."
            )
        return LinkedInCopy(
            intro_text=(
                f"{persona.name} wants a responsible way to act on financial goals. "
                f"{product_name} offers a guided path without hype."
            ),
            headline=f"A steadier way to start with {product_name}",
            description=description,
            cta="See how it works",
        )

    body = (
        f"{persona.name}, {product_name} is built to help you take the next step with "
        "clear guidance, simple actions, and a pace that feels responsible."
    )
    if disclosure:
        body = f"{body}\n\n{disclosure}"
    return EmailCopy(
        subject=f"{persona.name}, start your next money habit with {product_name}",
        preheader="A clear follow-up path for saving and beginner investing.",
        body=body,
        cta="Start your plan",
    )


def _audience_segments(audience_summary: str) -> list[dict[str, Any]]:
    raw_segments = [
        segment.strip(" .")
        for segment in re.split(r",| and ", audience_summary)
        if segment.strip(" .")
    ]
    fallback_segments = [
        "Young first-time investors",
        "Risk-conscious professionals",
        "Small-business owners",
    ]
    while len(raw_segments) < 3:
        raw_segments.append(fallback_segments[len(raw_segments)])

    templates = [
        {
            "name": raw_segments[0].title(),
            "summary": "Wants a low-friction first step into disciplined saving and investing.",
            "needs": [
                "Clear onboarding",
                "Beginner-friendly guidance",
                "Confidence before committing money",
            ],
            "objections": [
                "Fear of making the wrong first move",
                "Concern about hidden complexity",
            ],
            "decision_trigger": "A simple plan that feels approachable and transparent.",
            "risk_sensitivity": "high",
        },
        {
            "name": raw_segments[1].title(),
            "summary": "Looks for steady progress and credible financial messaging.",
            "needs": [
                "Trustworthy product framing",
                "Clear benefit explanation",
                "Responsible tone",
            ],
            "objections": [
                "Dislikes hype-driven promises",
                "Needs proof that the workflow is practical",
            ],
            "decision_trigger": "Evidence that the product supports disciplined financial habits.",
            "risk_sensitivity": "medium",
        },
        {
            "name": raw_segments[2].title(),
            "summary": "Balances business demands with a need for efficient financial tools.",
            "needs": [
                "Time-saving setup",
                "A dependable next action",
                "Messaging that respects limited attention",
            ],
            "objections": [
                "Low patience for vague benefits",
                "Needs a practical reason to follow up",
            ],
            "decision_trigger": "A direct explanation of how the product simplifies the next step.",
            "risk_sensitivity": "medium",
        },
    ]
    return templates[:3]


def _claims_for_brief(brief: CampaignBrief, channel: str) -> list[str]:
    claims = list(brief.required_claims[:2])
    if channel == "email" and brief.required_claims:
        claims.append("Clear follow-up guidance")
    return claims


def _disclosure_for_brief(brief: CampaignBrief, channel: str) -> str | None:
    if "fintech" not in brief.product_category.lower():
        return None
    if channel == "google_search":
        return "Investing involves risk. Returns are not guaranteed."
    if channel == "linkedin_sponsored_post":
        return "Investing involves risk. Review product details before acting."
    return "Investing involves risk. Returns are not guaranteed."


def _should_seed_risky_claim(*, brief: CampaignBrief, step: JourneyStep) -> bool:
    return (
        bool(brief.risky_claims)
        and step.persona_id == "p1"
        and step.channel == "google_search"
    )


def _message_angle(persona_name: str, channel: str, objective: str) -> str:
    channel_label = channel.replace("_", " ")
    return (
        f"Connect {persona_name} to {objective.lower()} through a {channel_label} "
        "message that stays clear and responsible."
    )


def _variant_text_fields(variant: dict[str, Any]) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    for index, claim in enumerate(variant.get("claims", [])):
        if isinstance(claim, str):
            fields.append((f"claims[{index}]", claim))
    disclosure = variant.get("disclosure")
    if isinstance(disclosure, str):
        fields.append(("disclosure", disclosure))
    copy_payload = variant.get("copy", {})
    if isinstance(copy_payload, dict):
        for field_name, field_value in copy_payload.items():
            if isinstance(field_value, list):
                for index, item in enumerate(field_value):
                    if isinstance(item, str):
                        fields.append((f"copy.{field_name}[{index}]", item))
            elif isinstance(field_value, str):
                fields.append((f"copy.{field_name}", field_value))
    return fields


def _replace_guarantee_language(value: str) -> str:
    return re.sub(
        "guaranteed returns",
        "responsible long-term progress",
        value,
        flags=re.IGNORECASE,
    )
