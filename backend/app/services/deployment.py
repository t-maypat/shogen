from __future__ import annotations

import uuid
from typing import Any

from app.db.models import Approval, Campaign, CreativeVariant

MOCK_DEPLOYMENT_SCHEMA_VERSION = "mock_deployment.v1"
MOCK_DEPLOYMENT_MODEL_NAME = "deterministic-mock-deployment-adapter"
NON_DEPLOYABLE_LABEL = (
    "Platform-shaped mock payload only. No external ad platform or email service "
    "deployment was performed."
)


class MockDeploymentService:
    def build_payload(
        self,
        *,
        campaign: Campaign,
        approval: Approval,
        variants: list[CreativeVariant],
    ) -> dict[str, Any]:
        payloads = [
            self._variant_payload(
                campaign=campaign,
                variant=variant,
            )
            for variant in variants
        ]
        channels = sorted({payload["channel"] for payload in payloads})
        return {
            "deployment_mode": "mock",
            "deployable": False,
            "mock_only": True,
            "non_deployable_label": NON_DEPLOYABLE_LABEL,
            "approval": {
                "approval_id": str(approval.id),
                "approved_by": approval.approved_by,
                "approved_at": approval.created_at.isoformat(),
                "status": approval.status,
            },
            "summary": {
                "payload_count": len(payloads),
                "active_variants": len(variants),
                "channels": channels,
                "platforms": sorted({payload["platform"] for payload in payloads}),
            },
            "payloads": payloads,
        }

    def _variant_payload(
        self,
        *,
        campaign: Campaign,
        variant: CreativeVariant,
    ) -> dict[str, Any]:
        copy_json = variant.copy_json or {}
        copy_payload = copy_json.get("copy", {})
        client_variant_id = copy_json.get("client_variant_id", str(variant.id))
        platform_payload = self._platform_payload(
            campaign=campaign,
            variant=variant,
            copy_payload=copy_payload,
            claims=copy_json.get("claims", []),
            disclosure=copy_json.get("disclosure"),
        )
        platform = self._platform_for_channel(variant.channel)
        return {
            "payload_id": self._payload_id(variant.id),
            "variant_id": str(variant.id),
            "client_variant_id": client_variant_id,
            "persona_id": variant.persona_id,
            "channel": variant.channel,
            "journey_stage": variant.journey_stage,
            "primary_kpi": variant.primary_kpi,
            "platform": platform,
            "deployable": False,
            "mock_only": True,
            "non_deployable_label": NON_DEPLOYABLE_LABEL,
            "payload": platform_payload,
        }

    @staticmethod
    def _platform_payload(
        *,
        campaign: Campaign,
        variant: CreativeVariant,
        copy_payload: dict[str, Any],
        claims: list[str],
        disclosure: str | None,
    ) -> dict[str, Any]:
        common = {
            "campaign_name": campaign.name,
            "persona_id": variant.persona_id,
            "journey_stage": variant.journey_stage,
            "primary_kpi": variant.primary_kpi,
            "claims": claims,
            "disclosure": disclosure,
            "external_submission": "disabled",
        }
        if variant.channel == "google_search":
            return {
                **common,
                "ad_type": "responsive_search_ad",
                "headlines": [
                    {"text": headline}
                    for headline in copy_payload.get("headlines", [])
                ],
                "descriptions": [
                    {"text": description}
                    for description in copy_payload.get("descriptions", [])
                ],
                "path": copy_payload.get("path"),
                "final_url_label": copy_payload.get("final_url_label"),
                "call_to_action": copy_payload.get("cta"),
            }
        if variant.channel == "linkedin_sponsored_post":
            return {
                **common,
                "ad_type": "sponsored_post",
                "intro_text": copy_payload.get("intro_text"),
                "headline": copy_payload.get("headline"),
                "description": copy_payload.get("description"),
                "call_to_action": copy_payload.get("cta"),
                "destination_url": "mock://shogen/non-deployable",
            }
        return {
            **common,
            "message_type": "follow_up_email",
            "subject": copy_payload.get("subject"),
            "preheader": copy_payload.get("preheader"),
            "body_text": copy_payload.get("body"),
            "call_to_action": copy_payload.get("cta"),
            "recipient_source": "synthetic_persona_segment",
        }

    @staticmethod
    def _platform_for_channel(channel: str) -> str:
        if channel == "google_search":
            return "google_ads"
        if channel == "linkedin_sponsored_post":
            return "linkedin_ads"
        return "email_service"

    @staticmethod
    def _payload_id(variant_id: uuid.UUID) -> str:
        return f"mock_{variant_id.hex}"
