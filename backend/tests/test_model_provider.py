from __future__ import annotations

from pydantic import BaseModel

from app.ai.provider import FakeModelProvider, ModelRequest


class ProviderProbe(BaseModel):
    value: str


def test_fake_provider_returns_parsed_structured_output() -> None:
    provider = FakeModelProvider(
        handlers={
            "probe": lambda _: {"value": "ok"},
        }
    )

    response = provider.generate_structured(
        ModelRequest(
            operation="probe",
            prompt="Return a probe payload.",
            prompt_version="probe.v1",
            response_model=ProviderProbe,
        )
    )

    assert response.output == ProviderProbe(value="ok")
    assert response.model_name == "fake-structured-provider"
    assert response.prompt_version == "probe.v1"
    assert response.attempts == 1


def test_fake_provider_retries_once_after_schema_failure() -> None:
    payloads = iter(
        [
            {"wrong": "shape"},
            {"value": "recovered"},
        ]
    )
    provider = FakeModelProvider(
        handlers={
            "probe": lambda _: next(payloads),
        }
    )

    response = provider.generate_structured(
        ModelRequest(
            operation="probe",
            prompt="Return a probe payload.",
            prompt_version="probe.v1",
            response_model=ProviderProbe,
        )
    )

    assert response.output == ProviderProbe(value="recovered")
    assert response.attempts == 2
