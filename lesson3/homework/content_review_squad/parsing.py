"""Parsing utilities for LLM outputs."""

from __future__ import annotations

import json
from typing import Any


def parse_json_dict(raw_text: str) -> dict[str, Any] | None:
    """Extract a JSON object from a model response string.

    Returns None if parsing fails.
    """
    if not raw_text:
        return None

    text = raw_text.strip()

    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        return None

    return None
