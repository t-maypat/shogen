from __future__ import annotations

import json

from app.schemas.brief import CampaignBrief
from app.schemas.journey import JourneyOutput
from app.schemas.strategy import StrategyOutput

STRATEGY_PROMPT_VERSION = "strategy.v1"
CREATIVE_PROMPT_VERSION = "creative.v1"
JOURNEY_PLANNER_VERSION = "journey.det.v1"


def build_strategy_prompt(brief: CampaignBrief) -> str:
    brief_json = json.dumps(brief.model_dump(mode="json"), indent=2)
    return (
        "You are Shogen's strategy planner.\n"
        "Return exactly three KPIs and exactly three aggregate personas for the campaign.\n"
        "Keep the output grounded in the brief, avoid PII, and use responsible fintech language.\n"
        "Each persona must include needs, objections, preferred tone, decision trigger, and "
        "risk sensitivity.\n"
        "Persona ids must be p1, p2, and p3 in order.\n\n"
        f"Campaign brief:\n{brief_json}"
    )


def build_creative_prompt(
    *,
    brief: CampaignBrief,
    strategy: StrategyOutput,
    journey: JourneyOutput,
) -> str:
    brief_json = json.dumps(brief.model_dump(mode="json"), indent=2)
    strategy_json = json.dumps(strategy.model_dump(mode="json"), indent=2)
    journey_json = json.dumps(journey.model_dump(mode="json"), indent=2)
    return (
        "You are Shogen's creative generator.\n"
        "Return exactly nine creative variants: one for every persona/channel pair.\n"
        "Respect the campaign brief, journey stage, and KPI mapping.\n"
        "Keep the voice clear, trustworthy, and responsible for a fintech audience.\n"
        "Include claims used in each variant and add a disclosure when responsible finance "
        "messaging needs one.\n"
        "Channel requirements:\n"
        "- google_search: headlines, descriptions, optional path/final_url_label, cta\n"
        "- linkedin_sponsored_post: intro_text, headline, description, cta\n"
        "- email: subject, preheader, body, cta\n\n"
        f"Campaign brief:\n{brief_json}\n\n"
        f"Strategy:\n{strategy_json}\n\n"
        f"Journey:\n{journey_json}"
    )
