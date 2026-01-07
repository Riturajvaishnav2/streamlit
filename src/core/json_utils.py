import json
from typing import Any


# Extract a JSON fragment from a mixed LLM response.
def _extract_json_fragment(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
    for opener, closer in [("{", "}"), ("[", "]")]:
        start = cleaned.find(opener)
        end = cleaned.rfind(closer)
        if start != -1 and end != -1 and end > start:
            return cleaned[start : end + 1]
    return cleaned


# Parse JSON with a fallback for fenced or noisy outputs.
def _parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fragment = _extract_json_fragment(text)
        try:
            return json.loads(fragment)
        except json.JSONDecodeError:
            return {}


# Serialize Python data as JSONL (one JSON per line).
def _to_jsonl(data: Any) -> str:
    if isinstance(data, list):
        return "\n".join(json.dumps(item) for item in data)
    if isinstance(data, dict):
        return json.dumps(data)
    return json.dumps({"value": data})
