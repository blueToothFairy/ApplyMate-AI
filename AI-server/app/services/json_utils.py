from __future__ import annotations

import json
import re
from typing import Any


def extract_json(text: str) -> Any:
    """Extract a JSON object/array from an LLM response.

    Gemini is asked to return JSON, but this helper makes the app tolerant of fenced
    markdown or short explanatory wrappers. It intentionally does not execute code.
    """
    raw = (text or "").strip()
    if not raw:
        raise ValueError("Empty LLM response; expected JSON.")

    # Remove common markdown fences.
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Find the first balanced-looking object or array range.
    starts = [i for i in [raw.find("{"), raw.find("[")] if i != -1]
    if not starts:
        raise ValueError(f"Could not locate JSON in LLM response: {raw[:300]}")
    start = min(starts)
    opener = raw[start]
    closer = "}" if opener == "{" else "]"
    end = raw.rfind(closer)
    if end <= start:
        raise ValueError(f"Could not locate JSON terminator in LLM response: {raw[:300]}")
    snippet = raw[start:end + 1]
    return json.loads(snippet)
