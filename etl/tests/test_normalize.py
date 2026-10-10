from datetime import date

import pytest

from supplier_trail_etl.normalize import (
    check_date,
    identity_key,
    normalize_name,
    parse_fda_date,
    record_hash,
    slugify,
)

TODAY = date(2026, 10, 9)


class TestParseFdaDate:
    @pytest.mark.parametrize("raw,expected", [
        ("2026-09-30", date(2026, 9, 30)),
        ("09/30/2026", date(2026, 9, 30)),
        (" 08/24/2022 ", date(2022, 8, 24)),
        ("2026-09-30T00:00:00", date(2026, 9, 30)),
    ])
    def test_known_formats(self, raw, expected):
        assert parse_fda_date(raw) == expected

    @pytest.mark.parametrize("raw", [None, "", "  ", "N/A", "31/31/2020", "2026-13-01"])
    def test_unparseable_returns_none(self, raw):
        assert parse_fda_date(raw) is None


class TestCheckDate:
    def test_normal_date_is_ok(self):
        assert check_date(date(2026, 9, 30), today=TODAY) is None

    def test_future_date_is_quarantined(self):
        # Real case: an FDA warning letter dated 2026-10-29 seen on 2026-10-07.
        assert check_date(date(2026, 10, 29), today=TODAY) == "future_date"

    def test_one_day_ahead_tolerated_for_timezones(self):
        assert check_date(date(2026, 10, 10), today=TODAY) is None

    def test_implausibly_old_date_is_quarantined(self):
        assert check_date(date(1899, 1, 1), today=TODAY) == "implausible_date"

    def test_missing_date_is_quarantined(self):
        assert check_date(None, today=TODAY) == "missing_date"


class TestNormalizeName:
    def test_case_punctuation_and_spaces(self):
        assert normalize_name("FUJIAN SHENGLINMARK  TRADE CO.LTD.") == "fujian shenglinmark trade co ltd"

    def test_equivalent_spellings_normalize_equal(self):
        a = normalize_name("Anhui Xinong Pharma Co., Ltd.")
        b = normalize_name("ANHUI XINONG PHARMA CO.,LTD")
        assert a == b

    def test_ampersand_and_unicode(self):
        assert normalize_name("Dion Herbs & Spices") == "dion herbs and spices"
        assert normalize_name("Société Boudjebel S.A.") == "societe boudjebel s a"

    def test_blank(self):
        assert normalize_name("  ") == ""


class TestSlugify:
    def test_basic(self):
        assert slugify("Example Foods Co., Ltd") == "example-foods-co-ltd"

    def test_length_cap(self):
        assert len(slugify("x" * 300)) <= 80

    def test_empty_falls_back(self):
        assert slugify("!!!") == "firm"


class TestIdentityKey:
    def test_fei_wins(self):
        assert identity_key(fei="3015850818", name="Anything") == "fei:3015850818"

    def test_name_key_is_stable_and_normalized(self):
        a = identity_key(fei=None, name="Example Foods Co., Ltd", address="1 Road", country="CN")
        b = identity_key(fei=None, name="EXAMPLE FOODS CO LTD", address="1  road", country="cn")
        assert a == b and a.startswith("name:")

    def test_requires_name_without_fei(self):
        with pytest.raises(ValueError):
            identity_key(fei=None, name="")


class TestRecordHash:
    def test_stable_regardless_of_key_order(self):
        assert record_hash("src", {"a": 1, "b": 2}) == record_hash("src", {"b": 2, "a": 1})

    def test_source_is_part_of_hash(self):
        assert record_hash("a", {"x": 1}) != record_hash("b", {"x": 1})
