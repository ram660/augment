"""Utilities to parse room image filenames for room type and floor hints.

Heuristics:
- Accept tokens separated by space, underscore, hyphen, or dot.
- Recognize common room types via room_type_normalizer.normalize_room_type.
- Recognize floor labels via floor_type_normalizer.parse_floor_label.
- Extract a human-readable room name when available.
"""

import os
import re
from typing import Dict, Optional

from backend.utils.room_type_normalizer import normalize_room_type
from backend.utils.floor_type_normalizer import parse_floor_label


ROOM_TOKENS_HINTS = {
    "primary": {"aliases": ["primary", "master"], "weight": 1.5},
    "ensuite": {"aliases": ["ensuite", "en_suite", "en-suite"], "weight": 1.2},
}


def _tokenize(name: str):
    # Split by non-alphanumeric
    return [t for t in re.split(r"[^a-zA-Z0-9]+", name.lower()) if t]


def parse_image_filename(path: str) -> Dict[str, Optional[str]]:
    """Parse filename into possible room_type, floor label, and inferred name.

    Returns:
      {
        "room_type": Optional[str],  # normalized
        "floor_level_label": Optional[str],  # e.g., 'main', 'second', 'basement', '1', '2'
        "floor_level": Optional[int],
        "room_name_hint": Optional[str],
      }
    """
    base = os.path.basename(path)
    name, _ext = os.path.splitext(base)
    tokens = _tokenize(name)

    # Find room type
    room_type: Optional[str] = None
    for i in range(len(tokens)):
        # try single token or bi-gram like 'dining room' split as 'dining','room'
        tok = tokens[i]
        # Skip if this token is actually a floor label (e.g., 'main', 'second', 'basement')
        f_t, _ = parse_floor_label(tok)
        if f_t and f_t in {"basement", "main", "second", "third", "attic"}:
            pass
        else:
            single = normalize_room_type(tok)
            # Only accept concrete room types; ignore 'other'
            if single and single not in ("unknown", "other"):
                room_type = single
        if i + 1 < len(tokens):
            bi_tok = tokens[i] + "_" + tokens[i + 1]
            # Guard bi-gram against accidental floor label pairs
            f_bi, _ = parse_floor_label(tokens[i + 1])
            if not (f_bi and f_bi in {"basement", "main", "second", "third", "attic"}):
                bi = normalize_room_type(bi_tok)
                if bi and bi not in ("unknown", "other"):
                    room_type = bi
    # Floor label
    floor_label: Optional[str] = None
    floor_level: Optional[int] = None
    for tok in tokens:
        # parse_floor_label returns a tuple: (canonical_type, numeric_level)
        f_type, f_level = parse_floor_label(tok)
        # Only accept recognized floor types; ignore generic/unknown
        if f_type in {"basement", "main", "second", "third", "attic"}:
            floor_label = f_type
            floor_level = f_level
            break

    # Room name hint (human-friendly): capitalize words that aren't generic like 'img', 'photo'
    ignore = {"img", "image", "photo", "pic", "snapshot", "capture"}
    words = [w for w in tokens if w not in ignore]
    room_name_hint = None
    if words:
        room_name_hint = " ".join(w.capitalize() for w in words[:4])

    return {
        "room_type": room_type,
        "floor_level_label": floor_label,
        "floor_level": floor_level,
        "room_name_hint": room_name_hint,
    }
