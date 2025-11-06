"""Floor type normalization utilities.

Maps free-form floor labels to canonical floor types and numeric levels.
Canonical types: basement, main, second, third, attic, other
Numeric mapping (default): basement=0, main=1, second=2, third=3, attic=99
"""

import re
from typing import Tuple

CANONICAL = {
    "basement": "basement",
    "lower level": "basement",
    "lower": "basement",
    "bsmt": "basement",
    "garden": "basement",  # common in some regions

    "main": "main",
    "main floor": "main",
    "first": "main",
    "1st": "main",
    "ground": "main",
    "ground floor": "main",

    "second": "second",
    "2nd": "second",
    "upper": "second",

    "third": "third",
    "3rd": "third",

    "attic": "attic",
    "loft": "attic",  # treat loft as attic-level area for floor typing
}

LEVEL_MAP = {
    "basement": 0,
    "main": 1,
    "second": 2,
    "third": 3,
    "attic": 99,
    "other": 1,
}


def normalize_floor_type(label: str) -> str:
    """Normalize a free-form floor label to a canonical floor type."""
    if not label:
        return "other"
    s = str(label).strip().lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    # direct map
    if s in CANONICAL:
        return CANONICAL[s]
    # heuristics
    if any(tok in s for tok in ["basement", "bsmt", "lower"]):
        return "basement"
    if any(tok in s for tok in ["attic", "loft"]):
        return "attic"
    if any(tok in s for tok in ["second", "2nd", "upper"]):
        return "second"
    if any(tok in s for tok in ["third", "3rd"]):
        return "third"
    if any(tok in s for tok in ["main", "ground", "first", "1st"]):
        return "main"
    return "other"


def floor_level_from_type(floor_type: str) -> int:
    """Map canonical floor type to a numeric level."""
    ft = normalize_floor_type(floor_type)
    return LEVEL_MAP.get(ft, 1)


def parse_floor_label(text: str) -> Tuple[str, int]:
    """Parse a raw label into (canonical_type, numeric_level).

    Examples:
    - "Main Floor" -> ("main", 1)
    - "Second Floor" -> ("second", 2)
    - "Basement" -> ("basement", 0)
    - "Floor 3" -> ("third", 3)
    - "Loft" -> ("attic", 99)
    """
    if not text:
        return ("other", 1)
    s = str(text).strip().lower()
    # numeric hints
    m = re.search(r"floor\s*(\d)", s)
    if m:
        n = int(m.group(1))
        if n <= 1:
            return ("main", 1)
        if n == 2:
            return ("second", 2)
        if n >= 3:
            return ("third", 3)
    # fallback to type
    ft = normalize_floor_type(s)
    return (ft, floor_level_from_type(ft))
