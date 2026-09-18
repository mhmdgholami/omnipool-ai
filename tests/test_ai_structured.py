import asyncio

import pytest
from pydantic import BaseModel

from backend.ai.exceptions import InvalidStructuredOutput
from backend.ai.schemas import GenerationResult
from backend.ai.services.generation import generate_structured
from backend.ai.utils.parsing import parse_json_payload


class Example(BaseModel):
    value: str


class SequenceRouter:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs

    async def generate(self, request):
        text = self.outputs.pop(0)
        return GenerationResult(
            text=text,
            provider="fake",
            model="fake",
            latency_ms=1,
            input_tokens_estimate=1,
            output_tokens_estimate=1,
        )


def test_json_parser_accepts_fenced_json():
    payload = parse_json_payload(
        'prelude\n```json\n{"value":"ok"}\n```'
    )
    assert payload == {"value": "ok"}


def test_structured_output_repairs_once():
    router = SequenceRouter(
        [
            "not valid json",
            '{"value":"repaired"}',
        ]
    )
    result = asyncio.run(
        generate_structured(
            "extract",
            Example,
            router=router,
        )
    )
    assert result.value == "repaired"


def test_malformed_output_fails_after_repair():
    router = SequenceRouter(
        ["bad", "still bad"]
    )
    with pytest.raises(InvalidStructuredOutput):
        asyncio.run(
            generate_structured(
                "extract",
                Example,
                router=router,
            )
        )
