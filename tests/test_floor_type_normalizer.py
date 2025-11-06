import pytest

from backend.utils.floor_type_normalizer import normalize_floor_type, floor_level_from_type, parse_floor_label

@pytest.mark.parametrize("label,expected", [
    ("Basement", "basement"),
    ("BSMT", "basement"),
    ("Lower Level", "basement"),
    ("Main Floor", "main"),
    ("Ground", "main"),
    ("First", "main"),
    ("Second Floor", "second"),
    ("2nd", "second"),
    ("Third Floor", "third"),
    ("3rd", "third"),
    ("Loft", "attic"),
    ("Attic", "attic"),
    (None, "other"),
])
def test_normalize_floor_type(label, expected):
    assert normalize_floor_type(label) == expected

@pytest.mark.parametrize("canon,level", [
    ("basement", 0),
    ("main", 1),
    ("second", 2),
    ("third", 3),
    ("attic", 99),
    ("other", 1),
])
def test_floor_level_from_type(canon, level):
    assert floor_level_from_type(canon) == level

@pytest.mark.parametrize("text,canon,level", [
    ("Floor 1", "main", 1),
    ("Floor 2", "second", 2),
    ("Floor 3", "third", 3),
    ("Main Floor", "main", 1),
    ("Basement", "basement", 0),
    ("Loft", "attic", 99),
])
def test_parse_floor_label(text, canon, level):
    c, l = parse_floor_label(text)
    assert c == canon
    assert l == level
