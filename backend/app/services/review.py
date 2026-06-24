from __future__ import annotations

from typing import Any

from app.ai.prompts import (
    CREATIVE_REVISION_PROMPT_VERSION,
    SEMANTIC_REVIEW_PROMPT_VERSION,
    build_creative_revision_prompt,
    build_semantic_review_prompt,
)
from app.ai.provider import ModelProvider, ModelRequest
from app.db.models import CreativeVariant
from app.schemas.brief import CampaignBrief
from app.schemas.creative import CreativeVariantOut
from app.schemas.review import CreativeRevisionOutput, SemanticReviewOutput

SEMANTIC_POLICY_SCHEMA_VERSION = "policy.semantic_review.v1"
MAX_CREATIVE_REVISIONS = 2


class SemanticReviewService:
    def __init__(self, provider: ModelProvider, *, timeout_seconds: float) -> None:
        self.provider = provider
        self.timeout_seconds = timeout_seconds

    def review_variants(
        self,
        *,
        brief: CampaignBrief,
        strategy: dict[str, Any],
        journey: dict[str, Any],
        variants: list[CreativeVariant],
    ) -> tuple[SemanticReviewOutput, dict[str, Any]]:
        variant_payloads = [creative_variant_to_payload(variant) for variant in variants]
        response = self.provider.generate_structured(
            ModelRequest(
                operation="semantic.review",
                prompt=build_semantic_review_prompt(
                    brief=brief,
                    strategy=strategy,
                    journey=journey,
                    variants=variant_payloads,
                ),
                prompt_version=SEMANTIC_REVIEW_PROMPT_VERSION,
                response_model=SemanticReviewOutput,
                timeout_seconds=self.timeout_seconds,
                metadata={
                    "brief": brief.model_dump(mode="json"),
                    "strategy": strategy,
                    "journey": journey,
                    "variants": variant_payloads,
                },
            )
        )
        return response.output, {
            "schema_version": SEMANTIC_POLICY_SCHEMA_VERSION,
            "prompt_version": response.prompt_version,
            "model_name": response.model_name,
            "duration_ms": response.duration_ms,
        }

    def revise_variant(
        self,
        *,
        brief: CampaignBrief,
        strategy: dict[str, Any],
        journey: dict[str, Any],
        variant: CreativeVariant,
        findings: list[dict[str, Any]],
        next_revision_number: int,
    ) -> tuple[CreativeVariantOut, dict[str, Any]]:
        variant_payload = creative_variant_to_payload(variant)
        response = self.provider.generate_structured(
            ModelRequest(
                operation="creative.revise",
                prompt=build_creative_revision_prompt(
                    brief=brief,
                    strategy=strategy,
                    journey=journey,
                    variant=variant_payload,
                    findings=findings,
                ),
                prompt_version=CREATIVE_REVISION_PROMPT_VERSION,
                response_model=CreativeRevisionOutput,
                timeout_seconds=self.timeout_seconds,
                metadata={
                    "brief": brief.model_dump(mode="json"),
                    "strategy": strategy,
                    "journey": journey,
                    "variant": variant_payload,
                    "findings": findings,
                    "next_revision_number": next_revision_number,
                },
            )
        )
        revised = CreativeVariantOut(
            client_variant_id=(
                f"{variant_payload['client_variant_id']}_r{next_revision_number}"
            ),
            persona_id=variant.persona_id,
            channel=variant.channel,
            journey_stage=variant.journey_stage,
            primary_kpi_id=variant.primary_kpi,
            claims=response.output.claims,
            disclosure=response.output.disclosure,
            copy=response.output.copy_payload,
        )
        return revised, {
            "schema_version": CREATIVE_REVISION_PROMPT_VERSION,
            "prompt_version": response.prompt_version,
            "model_name": response.model_name,
            "duration_ms": response.duration_ms,
        }


def creative_variant_to_payload(variant: CreativeVariant) -> dict[str, Any]:
    copy_json = variant.copy_json or {}
    return {
        "variant_id": str(variant.id),
        "client_variant_id": copy_json.get("client_variant_id", str(variant.id)),
        "persona_id": variant.persona_id,
        "channel": variant.channel,
        "journey_stage": variant.journey_stage,
        "primary_kpi": variant.primary_kpi,
        "revision_number": variant.revision_number,
        "claims": copy_json.get("claims", []),
        "disclosure": copy_json.get("disclosure"),
        "copy": copy_json.get("copy", {}),
    }
