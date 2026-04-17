__all__ = [
    "BEGINNING_OF_TIME",
    "get_current_time",
    "get_duration_in_secs",
    "from_isoformat_8601",
    "to_zulu_isoformat_8601",
]

import datetime as dt
from typing import Literal

BEGINNING_OF_TIME = dt.datetime.fromtimestamp(0.0, tz=dt.timezone.utc)


def get_current_time(tz: dt.timezone | None = None) -> dt.datetime:
    """Return the current time as a timezone-aware datetime.

    Args:
        tz: Timezone to use. Defaults to UTC.

    Returns:
        The current ``datetime`` in the specified timezone.
    """
    return dt.datetime.now(tz=tz or dt.timezone.utc)


def get_duration_in_secs(start: dt.datetime, stop: dt.datetime | None = None) -> int:
    """Calculate the duration between two datetimes in seconds.

    Args:
        start: Start datetime.
        stop: End datetime. Defaults to the current time.

    Returns:
        The rounded number of seconds between ``start`` and ``stop``.
    """
    return round(((stop or get_current_time()) - start).total_seconds())


def from_isoformat_8601(iso8601_str: str) -> dt.datetime:
    """Convert ISO Format datetime string into a datetime object

    Example Strings:
        - 2022-06-09T06:58:14
        - 2022-06-09T06:58:14Z
        - 2022-06-09T06:58:14+11:00
        - 2022-06-09T06:58:14.000
        - 2022-06-09T06:58:14.000Z
        - 2022-06-09T06:58:14.000+11:00

    Args:
        iso8601_str (str): datetime string

    Returns:
        dt.datetime
    """
    fmt = "%Y-%m-%dT%H:%M:%S.%f" if "." in iso8601_str else "%Y-%m-%dT%H:%M:%S"

    if len(iso8601_str) < 6:
        raise ValueError(f"{iso8601_str} does not match {fmt}")
    elif iso8601_str[-6] in frozenset(("+", "-")):
        fmt = fmt + "%z"
    elif iso8601_str[-1] == "Z":
        fmt = fmt + "Z"
    result = dt.datetime.strptime(iso8601_str, fmt)
    # strptime treats 'Z' as a literal, producing a naive datetime.
    # Since Z unambiguously means UTC, attach the UTC tzinfo.
    if result.tzinfo is None and iso8601_str[-1] == "Z":
        result = result.replace(tzinfo=dt.timezone.utc)
    return result


def to_zulu_isoformat_8601(
    value: dt.datetime | str,
    naive_handling: Literal["coerce", "error"] = "coerce",
) -> str:
    """Convert a datetime object or ISO 8601 string to a Zulu ISO 8601 formatted string.

    Args:
        value: The datetime object or ISO 8601 string to convert.
        naive_handling: How to handle naive (timezone-unaware) datetimes.
            ``"coerce"`` (default) treats them as UTC.
            ``"error"`` raises a :class:`ValueError`.

    Returns:
        The Zulu ISO 8601 formatted string.

    Raises:
        ValueError: If *naive_handling* is ``"error"`` and the datetime is naive.
    """
    dt_obj = from_isoformat_8601(value) if isinstance(value, str) else value
    if dt_obj.tzinfo is None:
        if naive_handling == "error":
            raise ValueError(
                "Naive datetime provided but naive_handling='error'. "
                "Supply a timezone-aware datetime or use naive_handling='coerce'."
            )
        dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
    return dt_obj.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
