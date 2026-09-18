from __future__ import annotations

import json
import re
from typing import Any

from backend.ai.exceptions import InvalidStructuredOutput

_FENCE = re.compile(
    r"^\s*```(?:json)?\s*|\s*```\s*$",
    re.IGNORECASE,
)


def parse_json_payload(raw: str) -> Any:
    text = _FENCE.sub("", raw.strip()).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character not in "[{":
            continue
        try:
            payload, _ = decoder.raw_decode(text[index:])
            return payload
        except json.JSONDecodeError:
            continue

    raise InvalidStructuredOutput("model_returned_invalid_json")
