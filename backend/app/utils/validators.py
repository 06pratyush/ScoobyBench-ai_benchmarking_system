"""Input validation helpers shared across API routes and services."""
import re
from typing import Any, Dict, List

# run_ids are UUIDs or "ollama-<epoch>-<suffix>" style identifiers. Anything
# outside this alphabet could be used for path traversal when building export
# file names, so reject early.
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

SUPPORTED_EXPORT_FORMATS = ("json", "html", "csv")

# Keys the /api/config endpoint is allowed to change, with expected types.
MUTABLE_CONFIG_KEYS: Dict[str, type] = {
    "telemetry_interval": float,
    "telemetry_retention_days": int,
    "max_telemetry_samples": int,
    "default_repeats": int,
    "warmup_tokens": int,
    "max_test_duration": int,
    "max_model_size_gb": float,
    "upload_enabled": bool,
    "anonymize": bool,
    "auto_start_monitor": bool,
    "minimize_to_tray": bool,
}


def is_valid_run_id(run_id: str) -> bool:
    """Return True when run_id is safe to embed in file paths and SQL."""
    return bool(run_id) and bool(_RUN_ID_RE.match(run_id))


def validate_export_format(fmt: str) -> str:
    """Normalize and validate an export format string."""
    fmt = (fmt or "").strip().lower()
    if fmt not in SUPPORTED_EXPORT_FORMATS:
        raise ValueError(
            f"Unsupported format '{fmt}'. Supported: {', '.join(SUPPORTED_EXPORT_FORMATS)}"
        )
    return fmt


def sanitize_filename(name: str, default: str = "report") -> str:
    """Strip characters that are unsafe in file names on Windows and POSIX."""
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", name or "").strip("._")
    return cleaned or default


def validate_config_updates(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Filter a config-update payload down to known keys with coerced types.

    Raises ValueError when a known key has a value that cannot be coerced.
    Unknown / read-only keys are silently ignored — the UI posts the whole
    config object back, so paths, port, etc. must not error out.
    """
    accepted: Dict[str, Any] = {}
    ignored: List[str] = []

    for key, value in updates.items():
        expected = MUTABLE_CONFIG_KEYS.get(key)
        if expected is None:
            ignored.append(key)
            continue
        try:
            if expected is bool:
                if isinstance(value, bool):
                    accepted[key] = value
                elif isinstance(value, str):
                    accepted[key] = value.strip().lower() in ("1", "true", "yes", "on")
                else:
                    accepted[key] = bool(value)
            else:
                accepted[key] = expected(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid value for '{key}': {value!r}") from exc

    # Basic sanity bounds
    if "telemetry_interval" in accepted and accepted["telemetry_interval"] < 0.5:
        raise ValueError("telemetry_interval must be >= 0.5 seconds")
    if "telemetry_retention_days" in accepted and accepted["telemetry_retention_days"] < 1:
        raise ValueError("telemetry_retention_days must be >= 1")
    if "default_repeats" in accepted and not (1 <= accepted["default_repeats"] <= 20):
        raise ValueError("default_repeats must be between 1 and 20")

    return accepted
