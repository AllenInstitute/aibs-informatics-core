import datetime as dt

from pytest import mark, param, raises

from aibs_informatics_core.utils.time import from_isoformat_8601, to_zulu_isoformat_8601
from test.base import does_not_raise


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
            dt.datetime(2022, 6, 9, 6, 58, 14, tzinfo=dt.timezone.utc),
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
            dt.datetime(2022, 6, 9, 6, 58, 14, tzinfo=dt.timezone.utc),
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
    isoformat_str: str, expected_dt: dt.datetime | None, raises_error
):
    with raises_error:
        actual_dt = from_isoformat_8601(iso8601_str=isoformat_str)

    if expected_dt is not None:
        assert actual_dt == expected_dt


@mark.parametrize(
    "value, expected_str",
    [
        param(
            dt.datetime(2022, 6, 9, 6, 58, 14, tzinfo=dt.timezone.utc),
            "2022-06-09T06:58:14+00:00".replace("+00:00", "Z"),
            id="UTC datetime",
        ),
        param(
            dt.datetime(2022, 6, 9, 6, 58, 14),
            "2022-06-09T06:58:14+00:00".replace("+00:00", "Z"),
            id="naive datetime assumed UTC",
        ),
        param(
            dt.datetime(2022, 6, 9, 6, 58, 14, 500000, tzinfo=dt.timezone.utc),
            "2022-06-09T06:58:14.500000+00:00".replace("+00:00", "Z"),
            id="UTC datetime with microseconds",
        ),
        param(
            dt.datetime(
                2022,
                6,
                9,
                17,
                58,
                14,
                tzinfo=dt.timezone(dt.timedelta(hours=11)),
            ),
            "2022-06-09T06:58:14+00:00".replace("+00:00", "Z"),
            id="non-UTC datetime converted to Zulu",
        ),
        param(
            "2022-06-09T06:58:14+05:30",
            "2022-06-09T01:28:14+00:00".replace("+00:00", "Z"),
            id="string input with +05:30 offset",
        ),
        param(
            "2022-06-09T06:58:14+00:00",
            "2022-06-09T06:58:14+00:00".replace("+00:00", "Z"),
            id="string input with +00:00 offset",
        ),
        param(
            "2022-06-09T17:58:14+11:00",
            "2022-06-09T06:58:14+00:00".replace("+00:00", "Z"),
            id="string input with non-UTC offset",
        ),
        param(
            "2022-06-09T06:58:14.000+00:00",
            "2022-06-09T06:58:14+00:00".replace("+00:00", "Z"),
            id="string input with microseconds and +00:00 offset",
        ),
        param(
            "2022-06-09T06:58:14Z",
            "2022-06-09T06:58:14+00:00".replace("+00:00", "Z"),
            id="string input with Z suffix",
        ),
        param(
            "2022-06-09T06:58:14.000Z",
            "2022-06-09T06:58:14+00:00".replace("+00:00", "Z"),
            id="string input with microseconds and Z suffix",
        ),
    ],
)
def test__to_zulu_isoformat_8601__works_as_expected(value: dt.datetime | str, expected_str: str):
    assert to_zulu_isoformat_8601(value) == expected_str


def test__to_zulu_isoformat_8601__naive_datetime_error_mode():
    naive = dt.datetime(2022, 6, 9, 6, 58, 14)
    with raises(ValueError, match="naive_handling='error'"):
        to_zulu_isoformat_8601(naive, naive_handling="error")


def test__to_zulu_isoformat_8601__naive_datetime_coerce_mode():
    naive = dt.datetime(2022, 6, 9, 6, 58, 14)
    assert to_zulu_isoformat_8601(naive, naive_handling="coerce") == "2022-06-09T06:58:14Z"
