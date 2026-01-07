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

# Default system prompt for extracting agreements from Markdown.
DEFAULT_COMMON_PROMPT = """You are an expert data extraction assistant.
Given the Markdown content, extract a common JSON in the exact schema below.
Use YYYYMMDD for dates and numeric values with up to 10 decimal places. If a field
is unknown, use null where allowed. The agreements array can contain multiple items.
Return ONLY valid JSON with the following schema:
{
  "metadata": {
    "source_filename": "DISCOUNT_IOT",
    "record_count": 0
  },
  "agreements": [
    {
      "client": "XXXXX",
      "partner": "YYYYY",
      "direction": "TI | TO",
      "validity": {
        "start_date": "YYYYMMDD",
        "end_date": "YYYYMMDD"
      },
      "currency": "EUR | USD | PLN | AED | null",
      "services": {
        "gprs": {
          "rate_per_mb": 0.0000000000,
          "increment_bytes": 1024
        },
        "sms": {
          "mo": { "rate_per_event": 0.0000000000 },
          "mt": { "rate_per_event": 0.0000000000 } | null
        },
        "moc": {
          "voice": [
            {
              "zone": "NATIONAL | BACK_HOME | ROW | PREMIUM | SATELLITE | VAS",
              "rate_per_min": 0.0000000000,
              "charging_interval_sec": 0,
              "video": "INCLUDED | EXCLUDED | VIDEO_RATES"
            }
          ],
          "video": [
            {
              "zone": "NATIONAL | BACK_HOME | ROW | PREMIUM | SATELLITE | VAS",
              "rate_per_min": 0.0000000000,
              "charging_interval_sec": 0
            }
          ]
        },
        "mtc": {
          "rate_per_min": 0.0000000000,
          "charging_interval_sec": 0,
          "video": "INCLUDED | EXCLUDED"
        } | null
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
if end date is null or not exits or undefine put 2099/12/31.
Return ONLY valid JSON with the following schema:
{
  "metadata": {
    "source_filename": "DISCOUNT_IOT",
    "record_count": 0
  },
  "agreements": [
    {
      "client": "XXXXX",
      "partner": "YYYYY",
      "direction": "TI | TO",
      "validity": {
        "start_date": "YYYYMMDD",
        "end_date": "YYYYMMDD"
      },
      "currency": "EUR | USD | PLN | AED | null",
      "services": {
        "gprs": {
          "rate_per_mb": 0.0000000000,
          "increment_bytes": 1024
        },
        "sms": {
          "mo": { "rate_per_event": 0.0000000000 },
          "mt": { "rate_per_event": 0.0000000000 } | null
        },
        "moc": {
          "voice": [
            {
              "zone": "NATIONAL | BACK_HOME | ROW | PREMIUM | SATELLITE | VAS",
              "rate_per_min": 0.0000000000,
              "charging_interval_sec": 0,
              "video": "INCLUDED | EXCLUDED | VIDEO_RATES"
            }
          ],
          "video": [
            {
              "zone": "NATIONAL | BACK_HOME | ROW | PREMIUM | SATELLITE | VAS",
              "rate_per_min": 0.0000000000,
              "charging_interval_sec": 0
            }
          ]
        },
        "mtc": {
          "rate_per_min": 0.0000000000,
          "charging_interval_sec": 0,
          "video": "INCLUDED | EXCLUDED"
        } | null
      }
    }
  ]
}
"""
