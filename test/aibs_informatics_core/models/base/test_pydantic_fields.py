import datetime
import unittest

from pydantic import BaseModel

from aibs_informatics_core.models.base._pydantic_fields import (
    AwareIsoDateTime,
    IsoDate,
    IsoDateTime,
    _parse_date,
    _parse_isoish_dt,
    _parse_isoish_tz_aware_dt,
)


# ── helper models ──────────────────────────────────────────────
class DateTimeModel(BaseModel):
    ts: IsoDateTime


class AwareDateTimeModel(BaseModel):
    ts: AwareIsoDateTime


class DateModel(BaseModel):
    d: IsoDate


TZ_UTC = datetime.timezone.utc


# ── _parse_isoish_dt ──────────────────────────────────────────
class ParseIsoishDtTests(unittest.TestCase):
    """Tests for the _parse_isoish_dt validator function."""

    # -- epoch millis --------------------------------------------------
    def test_epoch_millis_int(self):
        # 1_000_000_000_000 ms == 2001-09-09T01:46:40 UTC
        result = _parse_isoish_dt(1_000_000_000_000)
        self.assertEqual(
            result, datetime.datetime(2001, 9, 9, 1, 46, 40, tzinfo=datetime.timezone.utc)
        )
        self.assertEqual(result.tzinfo, datetime.timezone.utc)

    def test_epoch_millis_float(self):
        result = _parse_isoish_dt(0.0)
        self.assertEqual(result, datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc))
        self.assertEqual(result.tzinfo, datetime.timezone.utc)

    # -- ISO strings ---------------------------------------------------
    def test_iso_string_basic(self):
        result = _parse_isoish_dt("2025-04-30T07:00:00")
        self.assertEqual(result, datetime.datetime(2025, 4, 30, 7, 0, 0))
        self.assertIsNone(result.tzinfo)

    def test_iso_string_with_fractional(self):
        result = _parse_isoish_dt("2025-04-30T07:00:00.0")
        self.assertEqual(result, datetime.datetime(2025, 4, 30, 7, 0, 0))
        self.assertIsNone(result.tzinfo)

    def test_iso_string_with_z_suffix(self):
        result = _parse_isoish_dt("2022-06-09T06:58:14Z")
        self.assertIsInstance(result, datetime.datetime)
        self.assertEqual(result.year, 2022)
        self.assertEqual(result.month, 6)

    def test_iso_string_with_tz_offset(self):
        result = _parse_isoish_dt("2022-06-09T06:58:14+11:00")
        self.assertIsInstance(result, datetime.datetime)
        self.assertEqual(result.utcoffset(), datetime.timedelta(hours=11))

    def test_iso_string_fractional_with_z(self):
        result = _parse_isoish_dt("2022-06-09T06:58:14.000Z")
        self.assertIsInstance(result, datetime.datetime)

    def test_iso_string_fractional_with_tz_offset(self):
        result = _parse_isoish_dt("2022-06-09T06:58:14.000+11:00")
        self.assertIsInstance(result, datetime.datetime)
        self.assertEqual(result.utcoffset(), datetime.timedelta(hours=11))

    # -- passthrough datetime ------------------------------------------
    def test_datetime_passthrough(self):
        dt = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        self.assertIs(_parse_isoish_dt(dt), dt)

    def test_datetime_passthrough_naive(self):
        """Naive datetime passes through unchanged."""
        dt = datetime.datetime(2024, 1, 1, 12, 0, 0)
        result = _parse_isoish_dt(dt)
        self.assertIs(result, dt)
        self.assertIsNone(result.tzinfo)

    # -- invalid strings -----------------------------------------------
    def test_invalid_string_raises(self):
        with self.assertRaises(ValueError):
            _parse_isoish_dt("not-a-date")


# ── _parse_date ───────────────────────────────────────────────
class ParseDateTests(unittest.TestCase):
    """Tests for the _parse_date validator function."""

    def test_date_string(self):
        result = _parse_date("2025-04-30")
        self.assertEqual(result, datetime.date(2025, 4, 30))

    def test_date_passthrough(self):
        d = datetime.date(2024, 1, 1)
        self.assertIs(_parse_date(d), d)

    def test_invalid_date_string_raises(self):
        with self.assertRaises(ValueError):
            _parse_date("not-a-date")


# ── IsoDateTime (Pydantic integration) ───────────────────────
class IsoDateTimeFieldTests(unittest.TestCase):
    """Tests for the IsoDateTime annotated type inside a Pydantic model."""

    def test_model_from_iso_string(self):
        m = DateTimeModel(ts="2025-04-30T07:00:00")  # type: ignore[arg-type]
        self.assertIsInstance(m.ts, datetime.datetime)
        self.assertEqual(m.ts, datetime.datetime(2025, 4, 30, 7, 0, 0))
        self.assertIsNone(m.ts.tzinfo)

    def test_model_from_epoch_millis(self):
        m = DateTimeModel(ts=0)  # type: ignore[arg-type]
        self.assertEqual(m.ts, datetime.datetime(1970, 1, 1, tzinfo=TZ_UTC))
        self.assertEqual(m.ts.tzinfo, TZ_UTC)

    def test_model_from_datetime(self):
        dt = datetime.datetime(2024, 6, 15, 12, 30, tzinfo=TZ_UTC)
        m = DateTimeModel(ts=dt)
        self.assertEqual(m.ts, dt)

    def test_json_serialization_naive(self):
        dt = datetime.datetime(2025, 4, 30, 7, 0, 0)
        m = DateTimeModel(ts=dt)
        data = m.model_dump(mode="json")
        # Naive datetimes stay naive — no Z suffix
        self.assertEqual(data["ts"], "2025-04-30T07:00:00")

    def test_json_serialization_utc_uses_z(self):
        dt = datetime.datetime(2025, 4, 30, 7, 0, 0, tzinfo=datetime.timezone.utc)
        m = DateTimeModel(ts=dt)
        data = m.model_dump(mode="json")
        self.assertEqual(data["ts"], "2025-04-30T07:00:00Z")
        self.assertNotIn("+00:00", data["ts"])

    def test_json_serialization_non_utc_offset_preserved(self):
        tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        dt = datetime.datetime(2025, 4, 30, 7, 0, 0, tzinfo=tz)
        m = DateTimeModel(ts=dt)
        data = m.model_dump(mode="json")
        self.assertEqual(data["ts"], "2025-04-30T07:00:00+05:30")

    def test_json_round_trip(self):
        raw = '{"ts": "2025-04-30T07:00:00"}'
        m = DateTimeModel.model_validate_json(raw)
        self.assertEqual(m.ts, datetime.datetime(2025, 4, 30, 7, 0, 0))
        self.assertIsNone(m.ts.tzinfo)
        dumped = m.model_dump_json()
        self.assertIn("2025-04-30", dumped)

    def test_python_dump_returns_datetime(self):
        dt = datetime.datetime(2025, 1, 1, tzinfo=TZ_UTC)
        m = DateTimeModel(ts=dt)
        data = m.model_dump()
        self.assertIsInstance(data["ts"], datetime.datetime)


# ── _parse_isoish_tz_aware_dt ─────────────────────────────────
class ParseIsoishTzAwareDtTests(unittest.TestCase):
    """Tests for the _parse_isoish_tz_aware_dt validator function."""

    def test_naive_datetime_gets_utc(self):
        dt = datetime.datetime(2024, 1, 1, 12, 0, 0)
        result = _parse_isoish_tz_aware_dt(dt)
        self.assertEqual(result.tzinfo, TZ_UTC)
        self.assertEqual(result.replace(tzinfo=None), dt)

    def test_aware_datetime_preserved(self):
        tz = datetime.timezone(datetime.timedelta(hours=5))
        dt = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=tz)
        result = _parse_isoish_tz_aware_dt(dt)
        self.assertEqual(result.utcoffset(), datetime.timedelta(hours=5))

    def test_iso_string_no_tz_gets_utc(self):
        result = _parse_isoish_tz_aware_dt("2025-04-30T07:00:00")
        self.assertEqual(result.tzinfo, TZ_UTC)

    def test_iso_string_with_tz_preserved(self):
        result = _parse_isoish_tz_aware_dt("2025-04-30T07:00:00+05:30")
        self.assertEqual(result.utcoffset(), datetime.timedelta(hours=5, minutes=30))

    def test_epoch_millis(self):
        result = _parse_isoish_tz_aware_dt(1_000_000_000_000)
        self.assertEqual(result.tzinfo, TZ_UTC)

    def test_raise_mode(self):
        dt = datetime.datetime(2024, 1, 1, 12, 0, 0)
        with self.assertRaises(ValueError):
            _parse_isoish_tz_aware_dt(dt, if_missing="raise")


# ── AwareIsoDateTime (Pydantic integration) ──────────────────
class AwareIsoDateTimeFieldTests(unittest.TestCase):
    """Tests for the AwareIsoDateTime annotated type inside a Pydantic model."""

    def test_model_from_iso_string_no_tz_gets_utc(self):
        m = AwareDateTimeModel(ts="2025-04-30T07:00:00")  # type: ignore[arg-type]
        self.assertIsInstance(m.ts, datetime.datetime)
        self.assertEqual(m.ts.tzinfo, TZ_UTC)
        self.assertEqual(m.ts, datetime.datetime(2025, 4, 30, 7, 0, 0, tzinfo=TZ_UTC))

    def test_model_from_iso_string_with_tz_preserved(self):
        tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        m = AwareDateTimeModel(ts="2025-04-30T07:00:00+05:30")  # type: ignore[arg-type]
        self.assertEqual(m.ts.utcoffset(), datetime.timedelta(hours=5, minutes=30))
        self.assertEqual(m.ts, datetime.datetime(2025, 4, 30, 7, 0, 0, tzinfo=tz))

    def test_model_from_epoch_millis(self):
        m = AwareDateTimeModel(ts=0)  # type: ignore[arg-type]
        self.assertEqual(m.ts, datetime.datetime(1970, 1, 1, tzinfo=TZ_UTC))
        self.assertEqual(m.ts.tzinfo, TZ_UTC)

    def test_model_from_naive_datetime_gets_utc(self):
        dt = datetime.datetime(2024, 6, 15, 12, 30)
        m = AwareDateTimeModel(ts=dt)
        self.assertEqual(m.ts.tzinfo, TZ_UTC)
        self.assertEqual(m.ts, datetime.datetime(2024, 6, 15, 12, 30, tzinfo=TZ_UTC))

    def test_model_from_aware_datetime_preserved(self):
        tz = datetime.timezone(datetime.timedelta(hours=-7))
        dt = datetime.datetime(2024, 6, 15, 12, 30, tzinfo=tz)
        m = AwareDateTimeModel(ts=dt)
        self.assertEqual(m.ts.utcoffset(), datetime.timedelta(hours=-7))

    def test_json_serialization_naive_gets_utc_z(self):
        dt = datetime.datetime(2025, 4, 30, 7, 0, 0)
        m = AwareDateTimeModel(ts=dt)
        data = m.model_dump(mode="json")
        self.assertEqual(data["ts"], "2025-04-30T07:00:00Z")

    def test_json_serialization_non_utc_offset_preserved(self):
        tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        dt = datetime.datetime(2025, 4, 30, 7, 0, 0, tzinfo=tz)
        m = AwareDateTimeModel(ts=dt)
        data = m.model_dump(mode="json")
        self.assertEqual(data["ts"], "2025-04-30T07:00:00+05:30")

    def test_json_round_trip(self):
        raw = '{"ts": "2025-04-30T07:00:00"}'
        m = AwareDateTimeModel.model_validate_json(raw)
        self.assertEqual(m.ts, datetime.datetime(2025, 4, 30, 7, 0, 0, tzinfo=TZ_UTC))
        self.assertIsNotNone(m.ts.tzinfo)
        dumped = m.model_dump_json()
        self.assertIn("2025-04-30", dumped)

    def test_python_dump_returns_datetime(self):
        dt = datetime.datetime(2025, 1, 1, tzinfo=TZ_UTC)
        m = AwareDateTimeModel(ts=dt)
        data = m.model_dump()
        self.assertIsInstance(data["ts"], datetime.datetime)


# ── IsoDate (Pydantic integration) ───────────────────────────
class IsoDateFieldTests(unittest.TestCase):
    """Tests for the IsoDate annotated type inside a Pydantic model."""

    def test_model_from_date_string(self):
        m = DateModel(d="2025-04-30")  # type: ignore[arg-type]
        self.assertIsInstance(m.d, datetime.date)
        self.assertEqual(m.d, datetime.date(2025, 4, 30))

    def test_model_from_date(self):
        d = datetime.date(2024, 12, 25)
        m = DateModel(d=d)
        self.assertEqual(m.d, d)

    def test_json_serialization(self):
        m = DateModel(d=datetime.date(2025, 4, 30))
        data = m.model_dump(mode="json")
        self.assertEqual(data["d"], "2025-04-30")

    def test_json_round_trip(self):
        raw = '{"d": "2025-04-30"}'
        m = DateModel.model_validate_json(raw)
        self.assertEqual(m.d, datetime.date(2025, 4, 30))
        dumped = m.model_dump_json()
        self.assertIn("2025-04-30", dumped)

    def test_python_dump_returns_date(self):
        m = DateModel(d=datetime.date(2025, 1, 1))
        data = m.model_dump()
        self.assertIsInstance(data["d"], datetime.date)
