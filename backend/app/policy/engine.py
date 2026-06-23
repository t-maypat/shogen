from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import CreativeVariant
from app.schemas.brief import CampaignBrief

PolicySeverity = Literal["blocking", "high", "medium", "low", "info"]
VariantPolicyStatus = Literal["passed", "warning", "blocked"]

SUPPORTED_CHANNELS = {
    "google_search",
    "linkedin_sponsored_post",
    "email",
}
FINANCE_CATEGORY_KEYWORDS = (
    "fintech",
    "invest",
    "investment",
    "saving",
    "savings",
    "finance",
    "financial",
    "wealth",
    "retirement",
)
POLICY_SCHEMA_VERSION = "policy.det.v1"
RULES_FILE_PATH = Path(__file__).with_name("rules.json")


class PolicyRule(BaseModel):
    model_config = ConfigDict(extra="allow")

    rule_id: str
    version: str
    name: str
    channel: str
    severity: PolicySeverity
    type: Literal[
        "banned_phrase",
        "finance_disclosure",
        "required_fields",
        "channel_length",
        "mapping_check",
    ]
    message: str
    suggestion: str | None = None
    pattern: str | None = None
    fields: list[str] = Field(default_factory=list)
    max_length: int | None = None
    required_terms: list[str] = Field(default_factory=list)


@dataclass(slots=True)
class PolicyFindingRecord:
    variant_id: uuid.UUID
    client_variant_id: str
    source: str
    rule_id: str | None
    severity: PolicySeverity
    finding_type: str
    evidence: str
    message: str
    suggestion: str | None
    metadata: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "variant_id": str(self.variant_id),
            "client_variant_id": self.client_variant_id,
            "source": self.source,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "finding_type": self.finding_type,
            "evidence": self.evidence,
            "message": self.message,
            "suggestion": self.suggestion,
        }
        if self.metadata is not None:
            payload["metadata"] = self.metadata
        return payload


@dataclass(slots=True)
class VariantPolicyResult:
    variant_id: uuid.UUID
    client_variant_id: str
    status: VariantPolicyStatus
    findings: list[PolicyFindingRecord]

    def to_payload(self) -> dict[str, Any]:
        blocking_findings = sum(
            1 for finding in self.findings if finding.severity == "blocking"
        )
        warning_findings = len(self.findings) - blocking_findings
        return {
            "variant_id": str(self.variant_id),
            "client_variant_id": self.client_variant_id,
            "status": self.status,
            "blocking_findings": blocking_findings,
            "warning_findings": warning_findings,
            "finding_count": len(self.findings),
        }


@dataclass(slots=True)
class PolicyEvaluation:
    summary: dict[str, Any]
    variant_results: list[VariantPolicyResult]
    findings: list[PolicyFindingRecord]

    def to_stage_payload(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "variant_statuses": [
                variant_result.to_payload()
                for variant_result in self.variant_results
            ],
            "findings": [finding.to_payload() for finding in self.findings],
        }


class DeterministicPolicyEngine:
    def __init__(self) -> None:
        self.rules = load_policy_rules()

    def evaluate(
        self,
        *,
        brief: CampaignBrief,
        strategy: dict[str, Any] | None,
        journey: dict[str, Any] | None,
        variants: list[CreativeVariant],
    ) -> PolicyEvaluation:
        strategy_persona_ids = {
            persona.get("id")
            for persona in (strategy or {}).get("personas", [])
            if isinstance(persona, dict) and persona.get("id")
        }
        journey_steps = {
            (step.get("persona_id"), step.get("channel")): step
            for step in (journey or {}).get("steps", [])
            if isinstance(step, dict)
        }
        finance_related = _is_finance_related(brief)

        all_findings: list[PolicyFindingRecord] = []
        variant_results: list[VariantPolicyResult] = []

        for variant in variants:
            context = _variant_context(variant)
            findings: list[PolicyFindingRecord] = []

            for rule in self.rules:
                if rule.channel not in {"all", context.channel}:
                    continue
                if rule.type == "banned_phrase":
                    findings.extend(self._banned_phrase_findings(rule, context))
                elif rule.type == "finance_disclosure":
                    if finance_related:
                        finding = self._finance_disclosure_finding(rule, context)
                        if finding is not None:
                            findings.append(finding)
                elif rule.type == "required_fields":
                    findings.extend(self._required_field_findings(rule, context))
                elif rule.type == "channel_length":
                    findings.extend(self._channel_length_findings(rule, context))
                elif rule.type == "mapping_check":
                    findings.extend(
                        self._mapping_findings(
                            rule,
                            context,
                            strategy_persona_ids=strategy_persona_ids,
                            journey_steps=journey_steps,
                        )
                    )

            status: VariantPolicyStatus = "passed"
            if any(finding.severity == "blocking" for finding in findings):
                status = "blocked"
            elif findings:
                status = "warning"

            variant_result = VariantPolicyResult(
                variant_id=variant.id,
                client_variant_id=context.client_variant_id,
                status=status,
                findings=findings,
            )
            variant_results.append(variant_result)
            all_findings.extend(findings)

        blocking_findings = sum(
            1 for finding in all_findings if finding.severity == "blocking"
        )
        blocked_variants = sum(
            1 for variant_result in variant_results if variant_result.status == "blocked"
        )
        warning_variants = sum(
            1 for variant_result in variant_results if variant_result.status == "warning"
        )
        passed_variants = sum(
            1 for variant_result in variant_results if variant_result.status == "passed"
        )

        summary = {
            "total_variants": len(variant_results),
            "passed_variants": passed_variants,
            "warning_variants": warning_variants,
            "blocked_variants": blocked_variants,
            "blocking_findings": blocking_findings,
            "warning_findings": len(all_findings) - blocking_findings,
            "total_findings": len(all_findings),
            "ready_for_approval": blocking_findings == 0,
        }
        return PolicyEvaluation(
            summary=summary,
            variant_results=variant_results,
            findings=all_findings,
        )

    def _banned_phrase_findings(
        self,
        rule: PolicyRule,
        context: "_VariantContext",
    ) -> list[PolicyFindingRecord]:
        if not rule.pattern:
            return []

        findings: list[PolicyFindingRecord] = []
        pattern = rule.pattern.casefold()
        for field_name, field_value in context.iter_text_fields():
            if pattern not in field_value.casefold():
                continue
            findings.append(
                self._finding(
                    rule,
                    context,
                    evidence=f"{field_name}: {field_value}",
                    metadata={
                        "field": field_name,
                        "channel": context.channel,
                        "matched_text": rule.pattern,
                    },
                )
            )
        return findings

    def _finance_disclosure_finding(
        self,
        rule: PolicyRule,
        context: "_VariantContext",
    ) -> PolicyFindingRecord | None:
        disclosure = (context.disclosure or "").strip()
        if not disclosure:
            return self._finding(
                rule,
                context,
                evidence="disclosure: <missing>",
                metadata={"channel": context.channel, "field": "disclosure"},
            )

        disclosure_casefold = disclosure.casefold()
        if rule.required_terms and not all(
            required_term.casefold() in disclosure_casefold
            for required_term in rule.required_terms
        ):
            return self._finding(
                rule,
                context,
                evidence=f"disclosure: {disclosure}",
                metadata={
                    "channel": context.channel,
                    "field": "disclosure",
                    "required_terms": rule.required_terms,
                },
            )
        return None

    def _required_field_findings(
        self,
        rule: PolicyRule,
        context: "_VariantContext",
    ) -> list[PolicyFindingRecord]:
        findings: list[PolicyFindingRecord] = []
        for field_name in rule.fields:
            field_value = context.lookup(field_name)
            if _has_value(field_value):
                continue
            findings.append(
                self._finding(
                    rule,
                    context,
                    evidence=f"{field_name}: <missing>",
                    metadata={"channel": context.channel, "field": field_name},
                )
            )
        return findings

    def _channel_length_findings(
        self,
        rule: PolicyRule,
        context: "_VariantContext",
    ) -> list[PolicyFindingRecord]:
        if rule.max_length is None:
            return []

        findings: list[PolicyFindingRecord] = []
        for field_name in rule.fields:
            field_value = context.lookup(field_name)
            if isinstance(field_value, list):
                for index, item in enumerate(field_value):
                    if not isinstance(item, str) or len(item) <= rule.max_length:
                        continue
                    findings.append(
                        self._finding(
                            rule,
                            context,
                            evidence=f"{field_name}[{index}]: {item}",
                            metadata={
                                "channel": context.channel,
                                "field": field_name,
                                "index": index,
                                "observed_length": len(item),
                                "max_length": rule.max_length,
                            },
                        )
                    )
            elif isinstance(field_value, str) and len(field_value) > rule.max_length:
                findings.append(
                    self._finding(
                        rule,
                        context,
                        evidence=f"{field_name}: {field_value}",
                        metadata={
                            "channel": context.channel,
                            "field": field_name,
                            "observed_length": len(field_value),
                            "max_length": rule.max_length,
                        },
                    )
                )
        return findings

    def _mapping_findings(
        self,
        rule: PolicyRule,
        context: "_VariantContext",
        *,
        strategy_persona_ids: set[str],
        journey_steps: dict[tuple[str | None, str | None], dict[str, Any]],
    ) -> list[PolicyFindingRecord]:
        findings: list[PolicyFindingRecord] = []

        if context.channel not in SUPPORTED_CHANNELS:
            findings.append(
                self._finding(
                    rule,
                    context,
                    evidence=f"channel: {context.channel or '<missing>'}",
                    metadata={"channel": context.channel, "check": "supported_channel"},
                )
            )
            return findings

        if not context.persona_id or context.persona_id not in strategy_persona_ids:
            findings.append(
                self._finding(
                    rule,
                    context,
                    evidence=f"persona_id: {context.persona_id or '<missing>'}",
                    metadata={"channel": context.channel, "check": "persona_id"},
                )
            )

        journey_step = journey_steps.get((context.persona_id, context.channel))
        if journey_step is None:
            findings.append(
                self._finding(
                    rule,
                    context,
                    evidence=(
                        "journey step: "
                        f"({context.persona_id or '<missing>'}, {context.channel or '<missing>'})"
                    ),
                    metadata={"channel": context.channel, "check": "journey_step"},
                )
            )
            return findings

        expected_stage = journey_step.get("journey_stage")
        if context.journey_stage != expected_stage:
            findings.append(
                self._finding(
                    rule,
                    context,
                    evidence=(
                        f"journey_stage: {context.journey_stage or '<missing>'} "
                        f"(expected {expected_stage or '<missing>'})"
                    ),
                    metadata={"channel": context.channel, "check": "journey_stage"},
                )
            )

        expected_kpi = journey_step.get("primary_kpi_id")
        if context.primary_kpi != expected_kpi:
            findings.append(
                self._finding(
                    rule,
                    context,
                    evidence=(
                        f"primary_kpi: {context.primary_kpi or '<missing>'} "
                        f"(expected {expected_kpi or '<missing>'})"
                    ),
                    metadata={"channel": context.channel, "check": "primary_kpi"},
                )
            )

        return findings

    def _finding(
        self,
        rule: PolicyRule,
        context: "_VariantContext",
        *,
        evidence: str,
        metadata: dict[str, Any] | None = None,
    ) -> PolicyFindingRecord:
        finding_metadata = {
            "variant_id": str(context.variant_id),
            "client_variant_id": context.client_variant_id,
            **(metadata or {}),
        }
        return PolicyFindingRecord(
            variant_id=context.variant_id,
            client_variant_id=context.client_variant_id,
            source="deterministic",
            rule_id=rule.rule_id,
            severity=rule.severity,
            finding_type=rule.type,
            evidence=evidence,
            message=rule.message,
            suggestion=rule.suggestion,
            metadata=finding_metadata,
        )


@dataclass(slots=True)
class _VariantContext:
    variant_id: uuid.UUID
    client_variant_id: str
    persona_id: str
    channel: str
    journey_stage: str
    primary_kpi: str
    claims: list[str]
    disclosure: str | None
    copy: dict[str, Any]

    def iter_text_fields(self) -> list[tuple[str, str]]:
        text_fields: list[tuple[str, str]] = []
        for index, claim in enumerate(self.claims):
            text_fields.append((f"claims[{index}]", claim))
        if self.disclosure:
            text_fields.append(("disclosure", self.disclosure))
        for field_name, field_value in self.copy.items():
            if isinstance(field_value, list):
                for index, item in enumerate(field_value):
                    if isinstance(item, str):
                        text_fields.append((f"copy.{field_name}[{index}]", item))
            elif isinstance(field_value, str):
                text_fields.append((f"copy.{field_name}", field_value))
        return text_fields

    def lookup(self, field_name: str) -> Any:
        top_level_fields = {
            "persona_id": self.persona_id,
            "channel": self.channel,
            "journey_stage": self.journey_stage,
            "primary_kpi": self.primary_kpi,
            "disclosure": self.disclosure,
            "claims": self.claims,
        }
        if field_name in top_level_fields:
            return top_level_fields[field_name]
        return self.copy.get(field_name)


@lru_cache(maxsize=1)
def load_policy_rules() -> list[PolicyRule]:
    raw_rules = json.loads(RULES_FILE_PATH.read_text(encoding="utf-8"))
    return [PolicyRule.model_validate(raw_rule) for raw_rule in raw_rules]


def _variant_context(variant: CreativeVariant) -> _VariantContext:
    copy_json = variant.copy_json or {}
    copy_payload = copy_json.get("copy")
    if not isinstance(copy_payload, dict):
        copy_payload = {}
    claims = copy_json.get("claims")
    if not isinstance(claims, list):
        claims = []
    normalized_claims = [claim for claim in claims if isinstance(claim, str)]
    disclosure = copy_json.get("disclosure")
    if not isinstance(disclosure, str):
        disclosure = None
    client_variant_id = copy_json.get("client_variant_id")
    if not isinstance(client_variant_id, str) or not client_variant_id.strip():
        client_variant_id = str(variant.id)

    return _VariantContext(
        variant_id=variant.id,
        client_variant_id=client_variant_id,
        persona_id=variant.persona_id,
        channel=variant.channel,
        journey_stage=variant.journey_stage,
        primary_kpi=variant.primary_kpi,
        claims=normalized_claims,
        disclosure=disclosure,
        copy=copy_payload,
    )


def _has_value(field_value: Any) -> bool:
    if field_value is None:
        return False
    if isinstance(field_value, str):
        return bool(field_value.strip())
    if isinstance(field_value, list):
        return any(
            isinstance(item, str) and bool(item.strip())
            for item in field_value
        )
    return True


def _is_finance_related(brief: CampaignBrief) -> bool:
    category = brief.product_category.casefold()
    return any(keyword in category for keyword in FINANCE_CATEGORY_KEYWORDS)
