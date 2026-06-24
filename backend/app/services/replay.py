from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.db.models import Campaign
from app.repositories.campaigns import CampaignRepository

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "demo"
GOLDEN_REPLAY_FIXTURES = {
    "fintech": FIXTURES_DIR / "golden_replay_fintech.json",
}


class ReplayScenarioNotFoundError(Exception):
    def __init__(self, scenario: str) -> None:
        self.scenario = scenario
        super().__init__(f"Replay scenario {scenario!r} was not found")


@dataclass(slots=True, frozen=True)
class GoldenReplayScenario:
    scenario: str
    name: str
    brief: dict
    description: str | None = None


class ReplayService:
    def __init__(self, repository: CampaignRepository) -> None:
        self.repository = repository

    def create_campaign_for_scenario(self, scenario: str) -> Campaign:
        replay_scenario = load_golden_replay_scenario(scenario)
        return self.repository.create_campaign(
            name=replay_scenario.name,
            brief_json=replay_scenario.brief,
        )


def load_golden_replay_scenario(scenario: str) -> GoldenReplayScenario:
    fixture_path = GOLDEN_REPLAY_FIXTURES.get(scenario)
    if fixture_path is None or not fixture_path.exists():
        raise ReplayScenarioNotFoundError(scenario)

    with fixture_path.open("r", encoding="utf-8") as fixture_file:
        payload = json.load(fixture_file)

    return GoldenReplayScenario(
        scenario=payload["scenario"],
        name=payload["name"],
        description=payload.get("description"),
        brief=payload["brief"],
    )
