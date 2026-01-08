import json
from typing import Any, Dict

from langchain_openai.chat_models import ChatOpenAI

from src.core.json_utils import _parse_json


# Invoke the LLM with system/user messages.
def _call_llm(
    provider: str,
    api_key: str,
    model_name: str,
    base_url: str,
    system_prompt: str,
    user_content: str,
) -> str:
    provider_key = provider.strip().lower()
    if provider_key == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except Exception as exc:
            raise RuntimeError(
                "Ollama provider requires langchain-ollama to be installed."
            ) from exc
        ollama_base_url = base_url.rstrip("/")
        if ollama_base_url.endswith("/v1"):
            ollama_base_url = ollama_base_url[:-3]
        model = ChatOllama(
            temperature=0.2,
            base_url=ollama_base_url,
            model=model_name,
        )
    elif provider_key == "local":
        model = ChatOpenAI(
            temperature=0.2,
            api_key=api_key or "local",
            model=model_name,
            base_url=base_url,
        )
    else:
        model = ChatOpenAI(temperature=0.2, api_key=api_key, model=model_name)
    try:
        response = model.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]
        )
    except Exception as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc
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
    provider: str,
    api_key: str,
    model_name: str,
    base_url: str,
    prompt: str,
    md_text: str,
    user_note: str = "",
) -> Dict[str, Any]:
    provider_key = provider.strip().lower()
    if provider_key == "openai" and not api_key:
        return _mock_common_json(md_text)
    if provider_key in {"local", "ollama"} and not base_url.strip():
        return {"error": "Local LLM base URL is required."}
    if provider_key in {"local", "ollama"} and not model_name.strip():
        return {"error": "Local LLM model name is required."}
    if user_note.strip():
        user_content = f"{md_text}\n\nRegeneration notes:\n{user_note.strip()}"
    else:
        user_content = md_text
    try:
        response = _call_llm(provider, api_key, model_name, base_url, prompt, user_content)
    except RuntimeError as exc:
        return {"error": str(exc)}
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
    provider: str,
    api_key: str,
    model_name: str,
    base_url: str,
    prompt: str,
    pair: Dict[str, Any],
    user_note: str = "",
) -> Dict[str, Any]:
    provider_key = provider.strip().lower()
    if provider_key == "openai" and not api_key:
        return _mock_pair_output(pair)
    if provider_key in {"local", "ollama"} and not base_url.strip():
        return {"error": "Local LLM base URL is required."}
    if provider_key in {"local", "ollama"} and not model_name.strip():
        return {"error": "Local LLM model name is required."}
    user_content = json.dumps({"pair": pair, "note": user_note}, indent=2)
    try:
        response = _call_llm(provider, api_key, model_name, base_url, prompt, user_content)
    except RuntimeError as exc:
        return {"error": str(exc)}
    parsed = _parse_json(response)
    if not parsed:
        return {"error": "LLM response was not valid JSON.", "raw": response}
    return parsed
