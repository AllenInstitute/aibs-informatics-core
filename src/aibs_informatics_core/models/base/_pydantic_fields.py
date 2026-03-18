from __future__ import annotations

import datetime
from typing import Annotated, Literal

from pydantic import BeforeValidator, PlainSerializer

from aibs_informatics_core.utils.time import from_isoformat_8601


def _parse_isoish_dt(v: str | int | float | datetime.datetime) -> datetime.datetime:
    """Handle epoch milliseconds, ISO 8601 strings, and plain `datetime` values."""
    # Convert epoch‑milliseconds first
    if isinstance(v, (int, float)):
        return datetime.datetime.fromtimestamp(v / 1_000, datetime.UTC)
    # Handle ISO 8601 date‑time strings

    # Clean up iso‑format strings that may include a fractional component like ".0"
    if isinstance(v, str):
        original = v
        v = from_isoformat_8601(v)  # This will raise ValueError if the format is incorrect
        if v.tzinfo is None and original.endswith("Z"):
            # Handle the common case of a UTC time represented with "Z"
            # but no timezone info after parsing.
            v = v.replace(tzinfo=datetime.timezone.utc)

    # Already a datetime instance → return unchanged
    return v


def _parse_isoish_tz_aware_dt(
    v: str | int | float | datetime.datetime,
    if_missing: Literal["assume_utc", "raise"] = "assume_utc",
) -> datetime.datetime:
    """Handle epoch milliseconds, ISO 8601 strings, and plain `datetime` values, ensuring timezone awareness."""  # noqa: E501
    dt = _parse_isoish_dt(v)
    if dt.tzinfo is None:
        if if_missing == "assume_utc":
            return dt.replace(tzinfo=datetime.timezone.utc)
        elif if_missing == "raise":
            raise ValueError("Timezone information is missing")
    return dt


def _parse_date(v: str | datetime.date) -> datetime.date:
    """Handle date strings and plain `datetime.date` values."""
    if isinstance(v, str):
        return datetime.date.fromisoformat(v)
    return v


# --------------------------------------------------------------
#                     Pydantic Fields
# --------------------------------------------------------------

IsoDateTime = Annotated[
    datetime.datetime,
    BeforeValidator(_parse_isoish_dt),
    # ↓ this runs when .model_dump_json() or .model_dump(mode="json") is called
    PlainSerializer(
        lambda v: v.isoformat().replace("+00:00", "Z"),
        return_type=str,
        when_used="json",  # only affects JSON/dict output, not Python copy
    ),
]
AwareIsoDateTime = Annotated[
    datetime.datetime,
    BeforeValidator(_parse_isoish_tz_aware_dt),
    PlainSerializer(
        lambda v: v.isoformat().replace("+00:00", "Z"),
        return_type=str,
        when_used="json",
    ),
]
IsoDate = Annotated[
    datetime.date,
    BeforeValidator(_parse_date),
    PlainSerializer(
        lambda v: v.isoformat(),  # or v.isoformat(timespec="seconds") for no µs
        return_type=str,
        when_used="json",  # only affects JSON/dict output, not Python copy
    ),
]
