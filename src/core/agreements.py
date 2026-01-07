import json
from typing import Any, Dict, List, Optional

import pandas as pd


# Extract agreements list from the common JSON payload.
def _agreements_from_common(common_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    agreements = common_json.get("agreements", [])
    if isinstance(agreements, list):
        return agreements
    return []


# (Legacy) normalize agreements for tabular editing.
def _normalize_agreements_for_editor(agreements: List[Dict[str, Any]]) -> pd.DataFrame:
    def _first_from_list(value: Any) -> Dict[str, Any]:
        if isinstance(value, list) and value:
            first = value[0]
            if isinstance(first, dict):
                return first
        return {}

    rows = []
    for agreement in agreements:
        validity = agreement.get("validity", {}) or {}
        services = agreement.get("services", {}) or {}
        gprs = services.get("gprs", {}) or {}
        sms = services.get("sms", {}) or {}
        sms_mo = sms.get("mo", {}) or {}
        sms_mt = sms.get("mt", {}) or {}
        moc = services.get("moc", {}) or {}
        moc_voice = _first_from_list(moc.get("voice"))
        moc_video = _first_from_list(moc.get("video"))
        mtc = services.get("mtc", {}) or {}
        rows.append(
            {
                "client": agreement.get("client", ""),
                "partner": agreement.get("partner", ""),
                "direction": agreement.get("direction", ""),
                "start_date": validity.get("start_date", ""),
                "end_date": validity.get("end_date", ""),
                "currency": agreement.get("currency", ""),
                "gprs_rate_per_mb": gprs.get("rate_per_mb", ""),
                "gprs_increment_bytes": gprs.get("increment_bytes", ""),
                "sms_mo_rate_per_event": sms_mo.get("rate_per_event", ""),
                "sms_mt_rate_per_event": sms_mt.get("rate_per_event", ""),
                "moc_voice_zone": moc_voice.get("zone", ""),
                "moc_voice_rate_per_min": moc_voice.get("rate_per_min", ""),
                "moc_voice_charging_interval_sec": moc_voice.get(
                    "charging_interval_sec", ""
                ),
                "moc_voice_video": moc_voice.get("video", ""),
                "moc_video_zone": moc_video.get("zone", ""),
                "moc_video_rate_per_min": moc_video.get("rate_per_min", ""),
                "moc_video_charging_interval_sec": moc_video.get(
                    "charging_interval_sec", ""
                ),
                "mtc_rate_per_min": mtc.get("rate_per_min", ""),
                "mtc_charging_interval_sec": mtc.get("charging_interval_sec", ""),
                "mtc_video": mtc.get("video", ""),
                "services_json": json.dumps(services) if services else "",
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "client",
            "partner",
            "direction",
            "start_date",
            "end_date",
            "currency",
            "gprs_rate_per_mb",
            "gprs_increment_bytes",
            "sms_mo_rate_per_event",
            "sms_mt_rate_per_event",
            "moc_voice_zone",
            "moc_voice_rate_per_min",
            "moc_voice_charging_interval_sec",
            "moc_voice_video",
            "moc_video_zone",
            "moc_video_rate_per_min",
            "moc_video_charging_interval_sec",
            "mtc_rate_per_min",
            "mtc_charging_interval_sec",
            "mtc_video",
            "services_json",
        ],
    )


# (Legacy) transform edited table back into agreements.
def _update_agreements_from_editor(df: pd.DataFrame) -> List[Dict[str, Any]]:
    def _parse_float(value: Any) -> Optional[float]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, str) and not value.strip():
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _parse_int(value: Any) -> Optional[int]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, str) and not value.strip():
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def _parse_services_json(value: Any) -> Optional[Dict[str, Any]]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return None
        return None

    rows = df.to_dict(orient="records")
    return [
        {
            "client": row.get("client", ""),
            "partner": row.get("partner", ""),
            "direction": row.get("direction", ""),
            "validity": {
                "start_date": row.get("start_date", ""),
                "end_date": row.get("end_date", ""),
            },
            "currency": row.get("currency", ""),
            "services": _parse_services_json(row.get("services_json"))
            or {
                "gprs": {
                    "rate_per_mb": _parse_float(row.get("gprs_rate_per_mb"))
                    or 0.0,
                    "increment_bytes": _parse_int(row.get("gprs_increment_bytes"))
                    or 0,
                },
                "sms": {
                    "mo": {
                        "rate_per_event": _parse_float(
                            row.get("sms_mo_rate_per_event")
                        )
                        or 0.0
                    },
                    "mt": (
                        {
                            "rate_per_event": _parse_float(
                                row.get("sms_mt_rate_per_event")
                            )
                            or 0.0
                        }
                        if _parse_float(row.get("sms_mt_rate_per_event")) is not None
                        else None
                    ),
                },
                "moc": {
                    "voice": [
                        {
                            "zone": row.get("moc_voice_zone", ""),
                            "rate_per_min": _parse_float(
                                row.get("moc_voice_rate_per_min")
                            )
                            or 0.0,
                            "charging_interval_sec": _parse_int(
                                row.get("moc_voice_charging_interval_sec")
                            )
                            or 0,
                            "video": row.get("moc_voice_video", ""),
                        }
                    ],
                    "video": [
                        {
                            "zone": row.get("moc_video_zone", ""),
                            "rate_per_min": _parse_float(
                                row.get("moc_video_rate_per_min")
                            )
                            or 0.0,
                            "charging_interval_sec": _parse_int(
                                row.get("moc_video_charging_interval_sec")
                            )
                            or 0,
                        }
                    ],
                },
                "mtc": (
                    {
                        "rate_per_min": _parse_float(row.get("mtc_rate_per_min"))
                        or 0.0,
                        "charging_interval_sec": _parse_int(
                            row.get("mtc_charging_interval_sec")
                        )
                        or 0,
                        "video": row.get("mtc_video", ""),
                    }
                    if any(
                        row.get(key, "")
                        for key in (
                            "mtc_rate_per_min",
                            "mtc_charging_interval_sec",
                            "mtc_video",
                        )
                    )
                    else None
                ),
            },
        }
        for row in rows
    ]
