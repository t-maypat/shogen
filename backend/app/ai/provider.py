from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

StructuredModelT = TypeVar("StructuredModelT", bound=BaseModel)


class ModelProviderError(Exception):
    """Raised when a provider cannot return a valid structured response."""


@dataclass(slots=True, frozen=True)
class ModelRequest(Generic[StructuredModelT]):
    operation: str
    prompt: str
    prompt_version: str
    response_model: type[StructuredModelT]
    timeout_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ModelResponse(Generic[StructuredModelT]):
    output: StructuredModelT
    model_name: str
    prompt_version: str
    duration_ms: int
    attempts: int


class ModelProvider(ABC):
    def generate_structured(
        self,
        request: ModelRequest[StructuredModelT],
    ) -> ModelResponse[StructuredModelT]:
        last_validation_error: ValidationError | None = None
        started_at = time.perf_counter()

        for attempt in range(1, 3):
            try:
                raw_output, model_name = self._invoke(request)
                output = _validate_structured_output(request.response_model, raw_output)
                duration_ms = int((time.perf_counter() - started_at) * 1000)
                logger.info(
                    "Model call completed",
                    extra={
                        "operation": request.operation,
                        "provider": self.__class__.__name__,
                        "model_name": model_name,
                        "prompt_version": request.prompt_version,
                        "duration_ms": duration_ms,
                        "attempt": attempt,
                    },
                )
                return ModelResponse(
                    output=output,
                    model_name=model_name,
                    prompt_version=request.prompt_version,
                    duration_ms=duration_ms,
                    attempts=attempt,
                )
            except ValidationError as exc:
                last_validation_error = exc
                logger.warning(
                    "Structured output validation failed",
                    extra={
                        "operation": request.operation,
                        "provider": self.__class__.__name__,
                        "prompt_version": request.prompt_version,
                        "attempt": attempt,
                        "errors": exc.errors(),
                    },
                )

        raise ModelProviderError(
            "Structured output validation failed after one retry"
        ) from last_validation_error

    @abstractmethod
    def _invoke(
        self,
        request: ModelRequest[StructuredModelT],
    ) -> tuple[Any, str]:
        """Execute a provider call and return raw output data with a model identifier."""


FakeModelHandler = Callable[[ModelRequest[Any]], Any]


class FakeModelProvider(ModelProvider):
    def __init__(
        self,
        *,
        model_name: str = "fake-structured-provider",
        handlers: dict[str, FakeModelHandler] | None = None,
    ) -> None:
        self.model_name = model_name
        self.handlers = handlers or {}

    def register_handler(self, operation: str, handler: FakeModelHandler) -> None:
        self.handlers[operation] = handler

    def _invoke(
        self,
        request: ModelRequest[StructuredModelT],
    ) -> tuple[Any, str]:
        handler = self.handlers.get(request.operation)
        if handler is None:
            raise ModelProviderError(
                f"No fake model handler registered for operation {request.operation}"
            )
        return handler(request), self.model_name


class AzureOpenAIModelProvider(ModelProvider):
    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        api_version: str,
        deployment: str,
        default_timeout_seconds: float,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_version = api_version
        self.deployment = deployment
        self.default_timeout_seconds = default_timeout_seconds

    def _invoke(
        self,
        request: ModelRequest[StructuredModelT],
    ) -> tuple[Any, str]:
        try:
            from openai import AzureOpenAI
        except ImportError as exc:  # pragma: no cover - depends on local environment
            raise ModelProviderError(
                "The openai package is required for Azure OpenAI structured outputs"
            ) from exc

        client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            timeout=request.timeout_seconds or self.default_timeout_seconds,
        )
        completion = client.beta.chat.completions.parse(
            model=self.deployment,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a structured-output assistant. Return only data that "
                        "matches the requested schema."
                    ),
                },
                {"role": "user", "content": request.prompt},
            ],
            response_format=request.response_model,
            timeout=request.timeout_seconds or self.default_timeout_seconds,
        )
        message = completion.choices[0].message
        if getattr(message, "parsed", None) is None:
            refusal = getattr(message, "refusal", None)
            if refusal:
                raise ModelProviderError(f"Azure OpenAI refused the request: {refusal}")
            raise ModelProviderError("Azure OpenAI returned no parsed structured output")
        return message.parsed, getattr(completion, "model", self.deployment)


def _validate_structured_output(
    response_model: type[StructuredModelT],
    raw_output: Any,
) -> StructuredModelT:
    if isinstance(raw_output, response_model):
        return raw_output
    if isinstance(raw_output, BaseModel):
        return response_model.model_validate(raw_output.model_dump(mode="json"))
    return response_model.model_validate(raw_output)
