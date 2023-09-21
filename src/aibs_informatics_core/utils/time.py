__all__ = [
    "BEGINNING_OF_TIME",
    "get_current_time",
    "get_duration_in_secs",
    "from_isoformat_8601",
]

import datetime as dt
from typing import Optional

BEGINNING_OF_TIME = dt.datetime.fromtimestamp(0.0, tz=dt.timezone.utc)


def get_current_time(tz: Optional[dt.timezone] = None) -> dt.datetime:
    """Returns current time (in UTC) as a timezone aware datetime instance"""
    return dt.datetime.now(tz=tz or dt.timezone.utc)


def get_duration_in_secs(start: dt.datetime, stop: Optional[dt.datetime] = None) -> int:
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
    return dt.datetime.strptime(iso8601_str, fmt)
