from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.ai.prompts import WAVE2_PROMPT_VERSION, build_wave2_prompt
from app.ai.provider import ModelProvider, ModelRequest
from app.db.models import Campaign, CreativeVariant, PolicyFinding
from app.schemas.brief import CampaignBrief
from app.schemas.evaluation import EvaluationScores, Wave2AIOutput
from app.services.review import creative_variant_to_payload

EVALUATION_SCHEMA_VERSION = "evaluation.synthetic.v1"
EVALUATION_PROMPT_VERSION = "evaluation.det.v1"
EVALUATION_MODEL_NAME = "deterministic-synthetic-evaluator"
WAVE2_SCHEMA_VERSION = "wave2.proposal.v1"

FACTOR_WEIGHTS = {
    "message_fit": Decimal("0.30"),
    "channel_fit": Decimal("0.25"),
    "cta_clarity": Decimal("0.20"),
    "policy_quality": Decimal("0.15"),
    "journey_consistency": Decimal("0.10"),
}


@dataclass(slots=True, frozen=True)
class EvaluationStageResult:
    payload: dict[str, Any]
    results: list[dict[str, Any]]


@dataclass(slots=True, frozen=True)
class Wave2StageResult:
    proposal: dict[str, Any]
    rationale: dict[str, Any]
    metadata: dict[str, Any]


class SyntheticEvaluationService:
    def evaluate(
        self,
        *,
        campaign: Campaign,
        variants: list[CreativeVariant],
        journey: dict[str, Any],
        policy_findings: list[PolicyFinding],
    ) -> EvaluationStageResult:
        journey_steps = {
            (step["persona_id"], step["channel"]): step
            for step in journey.get("steps", [])
        }
        findings_by_variant = _open_findings_by_variant(policy_findings)

        results = [
            self._score_variant(
                campaign=campaign,
                variant=variant,
                journey_step=journey_steps.get((variant.persona_id, variant.channel)),
                open_findings=findings_by_variant.get(str(variant.id), []),
            )
            for variant in variants
        ]
        average_score = round(
            sum(result["scores"]["weighted_total"] for result in results) / len(results),
            2,
        ) if results else 0
        payload = {
            "evaluation_mode": "synthetic_preflight",
            "directional": True,
            "score_formula": {
                "message_fit": 0.30,
                "channel_fit": 0.25,
                "cta_clarity": 0.20,
                "policy_quality": 0.15,
                "journey_consistency": 0.10,
            },
            "summary": {
                "variant_count": len(results),
                "average_weighted_total": average_score,
                "low_performers": sum(
                    1 for result in results if result["scores"]["weighted_total"] < 40
                ),
                "medium_performers": sum(
                    1
                    for result in results
                    if 40 <= result["scores"]["weighted_total"] < 70
                ),
                "high_performers": sum(
                    1 for result in results if result["scores"]["weighted_total"] >= 70
                ),
            },
            "results": results,
        }
        return EvaluationStageResult(payload=payload, results=results)

    def _score_variant(
        self,
        *,
        campaign: Campaign,
        variant: CreativeVariant,
        journey_step: dict[str, Any] | None,
        open_findings: list[PolicyFinding],
    ) -> dict[str, Any]:
        copy_payload = variant.copy_json.get("copy", {})
        channel_scores = _channel_score_profile(variant.channel)
        scores = EvaluationScores(
            message_fit=channel_scores["message_fit"],
            channel_fit=channel_scores["channel_fit"],
            cta_clarity=_cta_score(copy_payload),
            policy_quality=_policy_quality_score(open_findings),
            journey_consistency=_journey_consistency_score(variant, journey_step),
            weighted_total=0,
        )
        score_payload = scores.model_dump(mode="json")
        score_payload["weighted_total"] = _weighted_total(score_payload)
        rationale = [
            f"{variant.channel} is scored with a directional channel-fit rubric.",
            "Open policy findings are reflected in policy_quality.",
            "Production would replace this rubric with live telemetry and review data.",
        ]
        return {
            "campaign_id": str(campaign.id),
            "variant_id": str(variant.id),
            "client_variant_id": variant.copy_json.get("client_variant_id", str(variant.id)),
            "persona_id": variant.persona_id,
            "channel": variant.channel,
            "journey_stage": variant.journey_stage,
            "primary_kpi": variant.primary_kpi,
            "scores": score_payload,
            "rationale": rationale,
            "production_test_plan": (
                "Validate message fit, channel engagement quality, CTA clarity, and "
                "policy-review outcomes with real platform telemetry before scaling spend."
            ),
        }


class Wave2OptimizationService:
    def __init__(self, provider: ModelProvider, *, timeout_seconds: float) -> None:
        self.provider = provider
        self.timeout_seconds = timeout_seconds

    def optimize(
        self,
        *,
        brief: CampaignBrief,
        variants: list[CreativeVariant],
        journey: dict[str, Any],
        evaluation_results: list[dict[str, Any]],
    ) -> Wave2StageResult:
        evaluation_by_variant_id = {
            result["variant_id"]: result for result in evaluation_results
        }
        wave1_allocations = _wave1_allocations(journey)
        allocation_changes = _allocation_changes(
            variants=variants,
            wave1_allocations=wave1_allocations,
            evaluation_by_variant_id=evaluation_by_variant_id,
        )
        weak_variants = [
            {
                **creative_variant_to_payload(variant),
                "weighted_total": evaluation_by_variant_id[str(variant.id)]["scores"][
                    "weighted_total"
                ],
            }
            for variant in variants
            if evaluation_by_variant_id[str(variant.id)]["scores"]["weighted_total"] < 70
        ]
        response = self.provider.generate_structured(
            ModelRequest(
                operation="wave2.explain",
                prompt=build_wave2_prompt(
                    campaign_brief=brief,
                    evaluation_results=evaluation_results,
                    allocation_changes=allocation_changes,
                    weak_variants=weak_variants,
                ),
                prompt_version=WAVE2_PROMPT_VERSION,
                response_model=Wave2AIOutput,
                timeout_seconds=self.timeout_seconds,
                metadata={
                    "brief": brief.model_dump(mode="json"),
                    "evaluation_results": evaluation_results,
                    "allocation_changes": allocation_changes,
                    "weak_variants": weak_variants,
                },
            )
        )
        proposal = {
            "wave": 2,
            "allocation_changes": allocation_changes,
            "rewrites": [
                rewrite.model_dump(mode="json")
                for rewrite in response.output.rewrites
            ],
            "comparison": {
                "wave1_total_allocation": sum(
                    change["wave1_allocation_percent"]
                    for change in allocation_changes
                ),
                "wave2_total_allocation": sum(
                    change["wave2_allocation_percent"]
                    for change in allocation_changes
                ),
                "changed_allocations": sum(
                    1
                    for change in allocation_changes
                    if change["delta_percent"] != 0
                ),
            },
        }
        rationale = {
            "rationale": response.output.rationale,
            "allocation_summary": response.output.allocation_summary,
            "method": (
                "Deterministic multipliers based on synthetic pre-flight score; AI "
                "explains the changes and rewrites weak creative only."
            ),
            "directional": True,
        }
        return Wave2StageResult(
            proposal=proposal,
            rationale=rationale,
            metadata={
                "schema_version": WAVE2_SCHEMA_VERSION,
                "prompt_version": response.prompt_version,
                "model_name": response.model_name,
                "duration_ms": response.duration_ms,
            },
        )


def _channel_score_profile(channel: str) -> dict[str, int]:
    if channel == "google_search":
        return {"message_fit": 78, "channel_fit": 80}
    if channel == "linkedin_sponsored_post":
        return {"message_fit": 58, "channel_fit": 62}
    return {"message_fit": 84, "channel_fit": 82}


def _cta_score(copy_payload: dict[str, Any]) -> int:
    cta = str(copy_payload.get("cta", "")).strip()
    if not cta:
        return 0
    if any(token in cta.casefold() for token in ("start", "plan", "get")):
        return 86
    if any(token in cta.casefold() for token in ("explore", "learn")):
        return 74
    return 60


def _policy_quality_score(open_findings: list[PolicyFinding]) -> int:
    if any(finding.severity == "blocking" for finding in open_findings):
        return 0
    if any(finding.severity == "high" for finding in open_findings):
        return 30
    if any(finding.severity == "medium" for finding in open_findings):
        return 60
    if open_findings:
        return 80
    return 100


def _journey_consistency_score(
    variant: CreativeVariant,
    journey_step: dict[str, Any] | None,
) -> int:
    if journey_step is None:
        return 30
    expected_kpi = journey_step.get("primary_kpi_id")
    expected_stage = journey_step.get("journey_stage")
    if expected_kpi == variant.primary_kpi and expected_stage == variant.journey_stage:
        return 88
    if expected_kpi == variant.primary_kpi or expected_stage == variant.journey_stage:
        return 60
    return 30


def _weighted_total(scores: dict[str, Any]) -> int:
    weighted = sum(
        Decimal(str(scores[factor])) * weight
        for factor, weight in FACTOR_WEIGHTS.items()
    )
    return int(weighted.quantize(Decimal("1")))


def _open_findings_by_variant(
    policy_findings: list[PolicyFinding],
) -> dict[str, list[PolicyFinding]]:
    findings_by_variant: dict[str, list[PolicyFinding]] = {}
    for finding in policy_findings:
        if finding.status != "open":
            continue
        findings_by_variant.setdefault(str(finding.variant_id), []).append(finding)
    return findings_by_variant


def _wave1_allocations(journey: dict[str, Any]) -> dict[tuple[str, str], int]:
    return {
        (step["persona_id"], step["channel"]): int(step["allocation_percent"])
        for step in journey.get("steps", [])
    }


def _allocation_changes(
    *,
    variants: list[CreativeVariant],
    wave1_allocations: dict[tuple[str, str], int],
    evaluation_by_variant_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    weighted_rows: list[dict[str, Any]] = []
    for variant in variants:
        evaluation = evaluation_by_variant_id[str(variant.id)]
        scores = evaluation["scores"]
        total_score = scores["weighted_total"]
        multiplier, reason_codes, recommendation = _allocation_rule(scores)
        wave1_allocation = wave1_allocations.get((variant.persona_id, variant.channel), 1)
        weighted_rows.append(
            {
                "variant": variant,
                "evaluation": evaluation,
                "wave1_allocation_percent": wave1_allocation,
                "weighted_allocation": wave1_allocation * multiplier,
                "score": total_score,
                "policy_quality": scores["policy_quality"],
                "multiplier": multiplier,
                "reason_codes": reason_codes,
                "recommendation": recommendation,
                "requires_rewrite": total_score < 70,
            }
        )

    normalized_allocations = _normalize_to_100(
        [row["weighted_allocation"] for row in weighted_rows]
    )
    changes: list[dict[str, Any]] = []
    for row, wave2_allocation in zip(weighted_rows, normalized_allocations):
        variant = row["variant"]
        changes.append(
            {
                "variant_id": str(variant.id),
                "client_variant_id": variant.copy_json.get(
                    "client_variant_id",
                    str(variant.id),
                ),
                "persona_id": variant.persona_id,
                "channel": variant.channel,
                "wave1_allocation_percent": row["wave1_allocation_percent"],
                "wave2_allocation_percent": wave2_allocation,
                "delta_percent": wave2_allocation - row["wave1_allocation_percent"],
                "synthetic_preflight_score": row["score"],
                "policy_quality": row["policy_quality"],
                "multiplier": row["multiplier"],
                "reason_codes": row["reason_codes"],
                "requires_rewrite": row["requires_rewrite"],
                "recommendation": row["recommendation"],
            }
        )
    return changes


def _allocation_rule(scores: dict[str, Any]) -> tuple[float, list[str], str]:
    total_score = scores["weighted_total"]
    if total_score < 40:
        multiplier = 0.35
        reason_codes = ["score_below_40", "rewrite_required"]
        recommendation = "pause_or_strongly_reduce"
    elif total_score < 70:
        multiplier = 0.85
        reason_codes = ["score_40_to_69", "rewrite_required"]
        recommendation = "slightly_reduce_and_rewrite"
    else:
        multiplier = 1.20
        reason_codes = ["score_70_or_above", "scale_directionally"]
        recommendation = "increase_relative_allocation"

    if scores["policy_quality"] < 60:
        multiplier = min(multiplier, 0.50)
        reason_codes.append("policy_quality_below_60")
    return multiplier, reason_codes, recommendation


def _normalize_to_100(values: list[float]) -> list[int]:
    if not values:
        return []
    total = sum(values)
    if total <= 0:
        base = [100 // len(values) for _ in values]
        for index in range(100 - sum(base)):
            base[index] += 1
        return base

    raw = [(value / total) * 100 for value in values]
    floors = [int(value) for value in raw]
    remainder = 100 - sum(floors)
    ranked_remainders = sorted(
        enumerate(raw),
        key=lambda item: item[1] - floors[item[0]],
        reverse=True,
    )
    normalized = list(floors)
    for index, _ in ranked_remainders[:remainder]:
        normalized[index] += 1
    return normalized
