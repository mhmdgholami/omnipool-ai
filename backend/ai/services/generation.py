from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, ValidationError

from backend.ai.exceptions import InvalidStructuredOutput
from backend.ai.router import AIRouter, ai_router
from backend.ai.schemas import (
    GenerationRequest,
    GenerationResult,
    TaskKind,
)
from backend.ai.utils.parsing import parse_json_payload

T = TypeVar("T", bound=BaseModel)


async def generate_text(
    prompt: str,
    *,
    system: str = "",
    task: TaskKind = TaskKind.GENERATION,
    max_tokens: int = 600,
    temperature: float = 0.4,
    router: AIRouter = ai_router,
) -> GenerationResult:
    return await router.generate(
        GenerationRequest(
            prompt=prompt,
            system=system,
            task=task,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    )


def _validate_structured(
    raw: str,
    schema: type[T],
) -> T:
    try:
        payload = parse_json_payload(raw)
        return schema.model_validate(payload)
    except (InvalidStructuredOutput, ValidationError) as exc:
        raise InvalidStructuredOutput(
            "model_output_failed_schema_validation"
        ) from exc


async def generate_structured(
    prompt: str,
    schema: type[T],
    *,
    system: str = "",
    task: TaskKind = TaskKind.EXTRACTION,
    max_tokens: int = 700,
    temperature: float = 0.2,
    router: AIRouter = ai_router,
) -> T:
    request = GenerationRequest(
        prompt=prompt,
        system=system,
        task=task,
        max_tokens=max_tokens,
        temperature=temperature,
        json_mode=True,
    )
    first = await router.generate(request)

    try:
        return _validate_structured(first.text, schema)
    except InvalidStructuredOutput:
        repair_prompt = (
            "Repair the following model output into valid JSON that matches "
            "the requested schema. Return JSON only. Do not add new claims.\n\n"
            + first.text[:6000]
        )
        repaired = await router.generate(
            request.model_copy(
                update={
                    "prompt": repair_prompt,
                    "temperature": 0.0,
                }
            )
        )
        return _validate_structured(repaired.text, schema)
