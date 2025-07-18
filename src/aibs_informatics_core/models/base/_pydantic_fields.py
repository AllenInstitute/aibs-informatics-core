import datetime
from typing import Annotated


import sys

from pydantic import PlainSerializer

from aibs_informatics_core.utils.time import from_isoformat_8601


if sys.version_info < (3, 11):
    pass  # type: ignore[import-untyped]
else:
    pass

try:
    from pydantic import BeforeValidator

except ModuleNotFoundError:  # pragma: no cover
    import types

    class _MissingPydantic(types.ModuleType):
        """Stub that raises a helpful error when any attribute is accessed."""

        __all__ = ()  # type: ignore

        def __getattr__(self, item):
            raise ImportError(
                "Optional dependency 'pydantic' is required for "
                "`aibs_informatics_core.models.base.PydanticBaseModel`. "
                "Install it with: pip install 'aibs-informatics-core[pydantic]'"
            )

    # Ensure subsequent `import pydantic` resolves to the stub so recursive
    # import attempts don’t continually re‑raise a generic ModuleNotFoundError.
    sys.modules.setdefault("pydantic", _MissingPydantic("pydantic"))

else:

    def _parse_isoish_dt(v: str | int | float | datetime.datetime) -> datetime.datetime:
        """Handle `2025-04-30T07:00:00.0` and plain `datetime` values."""
        # Convert epoch‑milliseconds first
        if isinstance(v, (int, float)):
            return datetime.datetime.fromtimestamp(v / 1_000, datetime.timezone.utc)
        # Handle ISO 8601 date‑time strings

        # Clean up iso‑format strings that may include a fractional component like ".0"
        if isinstance(v, str):
            return datetime.datetime.fromisoformat(v)
            return from_isoformat_8601(v)  # This will raise ValueError if the format is incorrect

        # Already a datetime instance → return unchanged
        return v

    # https://stackoverflow.com/a/27596917
    def is_aware(datetime: datetime.datetime) -> bool:
        return datetime.tzinfo is not None and datetime.tzinfo.utcoffset(datetime) is not None

    def _parse_epoch(v: str | int | float | datetime.datetime) -> datetime.datetime:
        """Handle epoch milliseconds and plain `datetime` values."""
        if isinstance(v, (int, float)):
            return datetime.datetime.fromtimestamp(v / 1_000, datetime.timezone.utc)
        if isinstance(v, str):
            # Accept ISO date‑time strings with optional fractional seconds
            if "." in v:
                v = v.split(".", 1)[0]
            return datetime.datetime.fromisoformat(v)
        return v

    def _parse_date(v: str | datetime.date) -> datetime.date:
        """Handle date strings and plain `datetime.date` values."""
        if isinstance(v, str):
            return datetime.date.fromisoformat(v)
        return v

    EpochDatetime = Annotated[datetime.datetime, BeforeValidator(_parse_epoch)]
    IsoDateTime = Annotated[
        datetime.datetime,
        BeforeValidator(_parse_isoish_dt),
        # ↓ this runs when .model_dump_json() or .model_dump(mode="json") is called
        PlainSerializer(
            lambda v: v.isoformat(),  # or v.isoformat(timespec="seconds") for no µs
            return_type=str,
            when_used="json",  # only affects JSON/dict output, not Python copy
        ),
    ]
    DateOrStr = Annotated[datetime.date, BeforeValidator(_parse_date)]
