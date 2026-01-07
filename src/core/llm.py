import json
from typing import Any, Dict

from langchain_openai.chat_models import ChatOpenAI

from src.core.json_utils import _parse_json


# Invoke the LLM with system/user messages.
def _call_llm(api_key: str, system_prompt: str, user_content: str) -> str:
    model = ChatOpenAI(temperature=0.2, api_key=api_key)
    response = model.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
    )
    return response.content


# Mock agreements when no API key is configured.
def _mock_common_json(md_text: str) -> Dict[str, Any]:
    sample_agreements = [
        {
            "client": "Alpha Health",
            "partner": "Omni Network",
            "direction": "TI",
            "validity": {"start_date": "20240101", "end_date": "20241231"},
            "currency": "EUR",
            "services": {
                "gprs": {"rate_per_mb": 0.0, "increment_bytes": 1024},
                "sms": {"mo": {"rate_per_event": 0.0}, "mt": None},
                "moc": {
                    "voice": [
                        {
                            "zone": "NATIONAL",
                            "rate_per_min": 0.0,
                            "charging_interval_sec": 60,
                            "video": "EXCLUDED",
                        }
                    ],
                    "video": [
                        {
                            "zone": "NATIONAL",
                            "rate_per_min": 0.0,
                            "charging_interval_sec": 60,
                        }
                    ],
                },
                "mtc": None,
            },
        },
        {
            "client": "Beta Care",
            "partner": "North Clinics",
            "direction": "TO",
            "validity": {"start_date": "20240101", "end_date": "20241231"},
            "currency": "USD",
            "services": {
                "gprs": {"rate_per_mb": 0.0, "increment_bytes": 1024},
                "sms": {"mo": {"rate_per_event": 0.0}, "mt": None},
                "moc": {
                    "voice": [
                        {
                            "zone": "ROW",
                            "rate_per_min": 0.0,
                            "charging_interval_sec": 60,
                            "video": "EXCLUDED",
                        }
                    ],
                    "video": [
                        {
                            "zone": "ROW",
                            "rate_per_min": 0.0,
                            "charging_interval_sec": 60,
                        }
                    ],
                },
                "mtc": None,
            },
        },
    ]
    return {
        "metadata": {"source_filename": "DISCOUNT_IOT", "record_count": 2},
        "agreements": sample_agreements,
        "source_note": "Mocked data (no API key).",
    }


# Mock pair output when no API key is configured.
def _mock_pair_output(pair: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "metadata": {"source_filename": "DISCOUNT_IOT", "record_count": 1},
        "agreements": [
            {
                "client": pair.get("client", ""),
                "partner": pair.get("partner", ""),
                "direction": "TI",
                "validity": {"start_date": "20240101", "end_date": "20241231"},
                "currency": "EUR",
                "services": {
                    "gprs": {"rate_per_mb": 0.0, "increment_bytes": 1024},
                    "sms": {"mo": {"rate_per_event": 0.0}, "mt": None},
                    "moc": {
                        "voice": [
                            {
                                "zone": "NATIONAL",
                                "rate_per_min": 0.0,
                                "charging_interval_sec": 60,
                                "video": "EXCLUDED",
                            }
                        ],
                        "video": [
                            {
                                "zone": "NATIONAL",
                                "rate_per_min": 0.0,
                                "charging_interval_sec": 60,
                            }
                        ],
                    },
                    "mtc": None,
                },
            }
        ],
        "status": "mocked",
    }


# Generate common JSON from Markdown (plus optional note).
def _generate_common_json(
    api_key: str,
    prompt: str,
    md_text: str,
    user_note: str = "",
) -> Dict[str, Any]:
    if not api_key:
        return _mock_common_json(md_text)
    if user_note.strip():
        user_content = f"{md_text}\n\nRegeneration notes:\n{user_note.strip()}"
    else:
        user_content = md_text
    response = _call_llm(api_key, prompt, user_content)
    parsed = _parse_json(response)
    if not parsed:
        return {"error": "LLM response was not valid JSON.", "raw": response}
    agreements = parsed.get("agreements")
    if isinstance(agreements, list):
        for agreement in agreements:
            validity = agreement.get("validity")
            if isinstance(validity, dict) and not validity.get("end_date"):
                validity["end_date"] = "20991231"
    return parsed


# Generate one agreement output for the current pair.
def _generate_pair_output(
    api_key: str,
    prompt: str,
    pair: Dict[str, Any],
    user_note: str = "",
) -> Dict[str, Any]:
    if not api_key:
        return _mock_pair_output(pair)
    user_content = json.dumps({"pair": pair, "note": user_note}, indent=2)
    response = _call_llm(api_key, prompt, user_content)
    parsed = _parse_json(response)
    if not parsed:
        return {"error": "LLM response was not valid JSON.", "raw": response}
    return parsed
