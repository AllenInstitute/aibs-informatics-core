import datetime as dt
from test.base import does_not_raise
from typing import Optional

from pytest import mark, param, raises

from aibs_informatics_core.utils.time import from_isoformat_8601


@mark.parametrize(
    "isoformat_str, expected_dt, raises_error",
    [
        param(
            "2022-06-09T06:58:14",
            dt.datetime(2022, 6, 9, 6, 58, 14),
            does_not_raise(),
            id="VALID no microseconds, no timezone",
        ),
        param(
            "2022-06-09T06:58:14Z",
            dt.datetime(2022, 6, 9, 6, 58, 14),
            does_not_raise(),
            id="VALID no microseconds, Z timezone",
        ),
        param(
            "2022-06-09T06:58:14+00:00",
            dt.datetime(2022, 6, 9, 6, 58, 14, tzinfo=dt.timezone.utc),
            does_not_raise(),
            id="VALID no microseconds, +/-HH:MM timezone",
        ),
        param(
            "2022-06-09T06:58:14.000",
            dt.datetime(2022, 6, 9, 6, 58, 14),
            does_not_raise(),
            id="VALID with microseconds, no timezone",
        ),
        param(
            "2022-06-09T06:58:14.000Z",
            dt.datetime(2022, 6, 9, 6, 58, 14),
            does_not_raise(),
            id="VALID with microseconds, Z timezone",
        ),
        param(
            "2022-06-09T06:58:14.000+00:00",
            dt.datetime(2022, 6, 9, 6, 58, 14, tzinfo=dt.timezone.utc),
            does_not_raise(),
            id="VALID with microseconds, +/-HH:MM timezone",
        ),
        param("notastring", None, raises(ValueError), id="INVALID ISO format string"),
        param("", None, raises(ValueError), id="INVALID empty string"),
        param("", None, raises(ValueError), id="INVALID empty string"),
    ],
)
def test__from_isoformat_8601__works_as_expected(
    isoformat_str: str, expected_dt: Optional[dt.datetime], raises_error
):
    with raises_error:
        actual_dt = from_isoformat_8601(iso8601_str=isoformat_str)

    if expected_dt is not None:
        assert actual_dt == expected_dt
