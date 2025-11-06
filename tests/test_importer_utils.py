import pytest

from scripts.import_enriched_csv_to_db import _json_load_maybe, _uuid


def test_json_load_maybe_parses_json_array():
    s = "[\"a\", \"b\", \"c\"]"
    out = _json_load_maybe(s)
    assert isinstance(out, list)
    assert out == ["a", "b", "c"]


def test_json_load_maybe_parses_comma_separated():
    s = "red, green, blue"
    out = _json_load_maybe(s)
    assert isinstance(out, list)
    assert out == ["red", "green", "blue"]


def test_uuid_parser_valid_and_invalid():
    good = "12345678-1234-5678-1234-567812345678"
    assert _uuid(good) is not None
    bad = "not-a-uuid"
    assert _uuid(bad) is None
