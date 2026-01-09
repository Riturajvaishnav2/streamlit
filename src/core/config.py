import os

# App-level constants for UI and prompt defaults.
APP_TITLE = "Client–Partner Workflow"

# Optional .env loading for local defaults.
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

# Load environment variables if available.
if load_dotenv:
    load_dotenv()

# Runtime configuration from environment.
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "prompt_history")
QDRANT_TOP_K = int(os.getenv("QDRANT_TOP_K", "20"))
DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
DEFAULT_LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
DEFAULT_LOCAL_LLM_BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")
DEFAULT_LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "llama3")
DEFAULT_LOCAL_LLM_API_KEY = os.getenv("LOCAL_LLM_API_KEY", "")
DEFAULT_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Default system prompt for extracting agreements from Markdown.
DEFAULT_COMMON_PROMPT = """You are an expert data extraction assistant.
Given the Markdown content, extract a common JSON in the exact schema below.
Use YYYYMMDD for dates and numeric values with up to 10 decimal places. If a field
is unknown, use null where allowed. The agreements array can contain multiple items.
Allowed values:
- direction: TI or TO
- currency: EUR, USD, PLN, AED, or null
- moc.voice[].zone and moc.video[].zone: NATIONAL, BACK_HOME, ROW, PREMIUM, SATELLITE, VAS
- moc.voice[].video: INCLUDED, EXCLUDED, or VIDEO_RATES
- mtc.video: INCLUDED or EXCLUDED
Return ONLY valid JSON. Do not wrap the response in code fences or add commentary.
Schema:
{
  "metadata": {
    "source_filename": "DISCOUNT_IOT",
    "record_count": 0
  },
  "agreements": [
    {
      "client": "XXXXX",
      "partner": "YYYYY",
      "direction": "TI",
      "validity": {
        "start_date": "YYYYMMDD",
        "end_date": "YYYYMMDD"
      },
      "currency": "EUR",
      "services": {
        "gprs": {
          "rate_per_mb": 0.0000000000,
          "increment_bytes": 1024
        },
        "sms": {
          "mo": { "rate_per_event": 0.0000000000 },
          "mt": null
        },
        "moc": {
          "voice": [
            {
              "zone": "NATIONAL",
              "rate_per_min": 0.0000000000,
              "charging_interval_sec": 0,
              "video": "EXCLUDED"
            }
          ],
          "video": [
            {
              "zone": "NATIONAL",
              "rate_per_min": 0.0000000000,
              "charging_interval_sec": 0
            }
          ]
        },
        "mtc": null
      }
    }
  ]
}
"""

# Default system prompt for generating agreement output JSON.
DEFAULT_PAIR_PROMPT = """You are an expert mapping assistant.
Given one client-partner pair and the discount agreement, generate the output JSON
in the exact schema below. Use YYYYMMDD for dates and numeric values with up to 10
decimal places. If a field is unknown, use null where allowed.
If end_date is null or missing, set it to 20991231.
Allowed values:
- direction: TI or TO
- currency: EUR, USD, PLN, AED, or null
- moc.voice[].zone and moc.video[].zone: NATIONAL, BACK_HOME, ROW, PREMIUM, SATELLITE, VAS
- moc.voice[].video: INCLUDED, EXCLUDED, or VIDEO_RATES
- mtc.video: INCLUDED or EXCLUDED
Return ONLY valid JSON. Do not wrap the response in code fences or add commentary.
Schema:
{
  "metadata": {
    "source_filename": "DISCOUNT_IOT",
    "record_count": 0
  },
  "agreements": [
    {
      "client": "XXXXX",
      "partner": "YYYYY",
      "direction": "TI",
      "validity": {
        "start_date": "YYYYMMDD",
        "end_date": "YYYYMMDD"
      },
      "currency": "EUR",
      "services": {
        "gprs": {
          "rate_per_mb": 0.0000000000,
          "increment_bytes": 1024
        },
        "sms": {
          "mo": { "rate_per_event": 0.0000000000 },
          "mt": null
        },
        "moc": {
          "voice": [
            {
              "zone": "NATIONAL",
              "rate_per_min": 0.0000000000,
              "charging_interval_sec": 0,
              "video": "EXCLUDED"
            }
          ],
          "video": [
            {
              "zone": "NATIONAL",
              "rate_per_min": 0.0000000000,
              "charging_interval_sec": 0
            }
          ]
        },
        "mtc": null
      }
    }
  ]
}
"""
