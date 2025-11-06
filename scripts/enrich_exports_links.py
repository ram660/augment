#!/usr/bin/env python3
"""
Enrich exported CSVs with inferred links and JSON fixes.

- Link room_images to rooms using filename parsing and image_analyses description heuristics
- Normalize image_analyses JSON array fields to valid JSON
- Add home_id to materials/products/fixtures when there is a single home in the export
- Write enriched CSVs under exports/analysis_run/enriched/

Non-destructive: original CSVs remain untouched.
"""
import csv
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "analysis_run"
ENRICHED_DIR = EXPORT_DIR / "enriched"

# Ensure we can import backend utils
sys.path.append(str(ROOT))

# Lazy imports of normalizers
from backend.utils.image_filename_parser import parse_image_filename
from backend.utils.room_type_normalizer import normalize_room_type


@dataclass
class Room:
    id: str
    home_id: str
    name: str
    room_type: str
    floor_level: Optional[int]


UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def build_room_lookup_by_slug(rooms: List[Room]) -> Dict[str, Room]:
    lookup: Dict[str, Room] = {}
    for r in rooms:
        if r.name:
            lookup.setdefault(slugify(r.name), r)
        if r.room_type:
            key = slugify(r.room_type + (f"-{r.floor_level}" if r.floor_level is not None else ""))
            if key not in lookup:
                lookup[key] = r
    return lookup


def extract_room_id_from_path_tags(path: str, room_ids: set, room_slug_map: Dict[str, Room]) -> Optional[str]:
    if not path:
        return None
    # explicit __roomid-<uuid> or roomid-<uuid>
    m = re.search(r"(?:__|\b)roomid-(" + UUID_RE.pattern + ")", path, flags=re.IGNORECASE)
    if m:
        rid = m.group(1)
        if rid in room_ids:
            return rid
    # any uuid in path matching a room id
    for m in UUID_RE.finditer(path):
        rid = m.group(0)
        if rid in room_ids:
            return rid
    # slug tags: __room-<slug> or room-<slug>
    m2 = re.search(r"(?:__|\b)room-([a-z0-9\-]+)", path, flags=re.IGNORECASE)
    if m2:
        slug = m2.group(1).lower()
        if slug in room_slug_map:
            return room_slug_map[slug].id
    # folder segments possibly containing room id
    parts = Path(path).parts
    for p in parts:
        if p.lower().startswith("roomid-"):
            cand = p[7:]
            if cand in room_ids:
                return cand
        if UUID_RE.fullmatch(p or "") and (p in room_ids):
            return p
    return None


def read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return reader.fieldnames or [], rows


def write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def first_nonblank(*vals: Optional[str]) -> Optional[str]:
    for v in vals:
        if v is not None and str(v).strip() != "":
            return v
    return None


def to_int_or_none(v: Optional[str]) -> Optional[int]:
    if v is None or str(v).strip() == "":
        return None
    try:
        return int(float(v))
    except Exception:
        return None


def infer_room_type_from_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    # Split by non-alphanumeric to tokens and try normalize progressively
    tokens = [t for t in re.split(r"[^a-zA-Z0-9]+", text) if t]
    # Try bi-grams first (kitchen_island -> kitchen)
    for i in range(len(tokens) - 1):
        joined = f"{tokens[i]}_{tokens[i+1]}"
        rt = normalize_room_type(joined)
        if rt and rt not in ("unknown", "other"):
            return rt
    # Then single tokens
    for t in tokens:
        rt = normalize_room_type(t)
        if rt and rt not in ("unknown", "other"):
            return rt
    return None


def fix_to_json_array(raw: Optional[str]) -> Optional[str]:
    """Attempt to coerce a raw string into a valid JSON array string.

    Strategy:
    - Empty or null -> return as-is
    - If already valid JSON array -> return canonical json.dumps
    - If looks like a single dict -> wrap in [dict]
    - If Python-like dicts separated by commas -> replace single quotes, True/False/None, wrap in [ ... ]
    - Validate with json.loads; if fails, return original
    """
    if raw is None or str(raw).strip() == "":
        return raw
    s = str(raw).strip()
    # Already JSON array?
    try:
        val = json.loads(s)
        if isinstance(val, list):
            return json.dumps(val, ensure_ascii=False)
        # Single dict -> wrap
        if isinstance(val, dict):
            return json.dumps([val], ensure_ascii=False)
    except json.JSONDecodeError:
        pass

    # Try to coerce Python-ish to JSON
    coerced = s
    # If not wrapped as list, but contains at least one dict, wrap later
    has_brace = "{" in s and "}" in s
    # Replace Python single quotes with double quotes carefully
    coerced = coerced.replace("\\'", "__SQUOTE_ESC__")  # escape any escaped quotes first
    # Replace single quotes surrounding words/keys with double quotes
    coerced = re.sub(r"'", '"', coerced)
    coerced = coerced.replace("__SQUOTE_ESC__", "'")
    # Replace Python bool/None
    coerced = coerced.replace(" None", " null").replace(": None", ": null")
    coerced = coerced.replace(" True", " true").replace(": True", ": true")
    coerced = coerced.replace(" False", " false").replace(": False", ": false")

    # Ensure brackets if looks like concatenated dicts
    if has_brace and not coerced.strip().startswith("["):
        coerced = f"[{coerced}]"

    try:
        val = json.loads(coerced)
        if isinstance(val, list):
            return json.dumps(val, ensure_ascii=False)
        if isinstance(val, dict):
            return json.dumps([val], ensure_ascii=False)
    except json.JSONDecodeError:
        return raw
    return raw


def build_room_index(rooms_rows: List[Dict[str, str]]) -> Tuple[List[Room], Dict[Tuple[str, Optional[int]], List[Room]]]:
    rooms: List[Room] = []
    by_type_and_floor: Dict[Tuple[str, Optional[int]], List[Room]] = {}
    for r in rooms_rows:
        room = Room(
            id=r.get("id", ""),
            home_id=r.get("home_id", ""),
            name=r.get("name", ""),
            room_type=r.get("room_type", ""),
            floor_level=to_int_or_none(r.get("floor_level")),
        )
        rooms.append(room)
        key = (room.room_type, room.floor_level)
        by_type_and_floor.setdefault(key, []).append(room)
        # Also index by only type for fallback
        key2 = (room.room_type, None)
        by_type_and_floor.setdefault(key2, []).append(room)
    return rooms, by_type_and_floor


def enrich_room_images(room_images_rows: List[Dict[str, str]], image_analyses_rows: List[Dict[str, str]], rooms_index: Dict[Tuple[str, Optional[int]], List[Room]], all_rooms: List[Room], manual_map: Dict[str, str]) -> Tuple[List[Dict[str, str]], int]:
    # Build analysis map by room_image_id
    analyses_by_image: Dict[str, List[Dict[str, str]]] = {}
    for a in image_analyses_rows:
        rid = a.get("room_image_id")
        if rid:
            analyses_by_image.setdefault(rid, []).append(a)

    room_ids = {r.id for r in all_rooms}
    room_slug_map = build_room_lookup_by_slug(all_rooms)

    updated_count = 0
    for img in room_images_rows:
        if img.get("room_id") and str(img.get("room_id")).strip() != "":
            continue  # already linked
        image_id = img.get("id")
        image_url = img.get("image_url") or ""
        base = os.path.basename(image_url)

        # Prefer manual map overrides
        maybe = manual_map.get(image_id) or manual_map.get(base) or manual_map.get(image_url)
        if maybe and maybe in room_ids:
            img["room_id"] = maybe
            updated_count += 1
            continue

        # Filename/path tags with explicit room ids or slugs
        rid_from_tags = extract_room_id_from_path_tags(image_url, room_ids, room_slug_map)
        if rid_from_tags:
            img["room_id"] = rid_from_tags
            updated_count += 1
            continue
        # Heuristics for room type: prefer analysis description/keywords, fallback filename
        rt_from_desc = None
        for a in analyses_by_image.get(image_id, []):
            rt_from_desc = first_nonblank(rt_from_desc, infer_room_type_from_text(a.get("description")))
            rt_from_desc = first_nonblank(rt_from_desc, infer_room_type_from_text(a.get("keywords")))
        parsed = parse_image_filename(image_url)
        rt_from_name = parsed.get("room_type")
        floor_from_name = parsed.get("floor_level")
        candidate_rt = first_nonblank(rt_from_desc, rt_from_name)
        if not candidate_rt:
            continue
        # Try to find matching rooms by (type, floor) then (type, None)
        candidates = rooms_index.get((candidate_rt, floor_from_name)) or rooms_index.get((candidate_rt, None)) or []
        # If multiple, do not guess; require manual mapping
        if len(candidates) == 1:
            img["room_id"] = candidates[0].id
            updated_count += 1
    return room_images_rows, updated_count


def normalize_image_analyses_json(rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
    json_cols = [
        "keywords",
        "dominant_colors",
        "objects_detected",
        "materials_visible",
        "fixtures_visible",
    ]
    fixed_counts = {c: 0 for c in json_cols}
    split_on_commas = {"keywords", "dominant_colors"}
    for r in rows:
        for c in json_cols:
            raw = r.get(c)
            fixed = fix_to_json_array(raw)
            # If still not JSON and we expect a simple list, split on commas
            if fixed == raw and raw and c in split_on_commas:
                s = str(raw)
                if ("[" not in s and "{" not in s) and ("," in s):
                    arr = [x.strip() for x in s.split(",") if x.strip()]
                    fixed = json.dumps(arr, ensure_ascii=False)
            if fixed != raw and fixed is not None:
                r[c] = fixed
                fixed_counts[c] += 1
    return rows, fixed_counts


def load_manual_map() -> Dict[str, str]:
    """Load manual image->room mapping from common CSV locations.

    Supported headers: image_id OR image_url (or filename), and room_id.
    Search paths:
      - exports/analysis_run/image_room_map.csv
      - uploads/room_images/image_room_map.csv
    """
    candidates = [
        EXPORT_DIR / "image_room_map.csv",
        ROOT / "uploads" / "room_images" / "image_room_map.csv",
    ]
    result: Dict[str, str] = {}
    for path in candidates:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rid = (row.get("room_id") or "").strip()
                if not rid:
                    continue
                for key in ("image_id", "image_url", "image", "filename"):
                    val = row.get(key)
                    if val:
                        v = val.strip()
                        result[v] = rid
                        result[os.path.basename(v)] = rid
    if result:
        print(f"Loaded manual mappings: {len(result)} keys")
    return result


def main():
    print(f"Reading exports from: {EXPORT_DIR}")
    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)

    # Load homes
    home_cols, home_rows = read_csv(EXPORT_DIR / "home.csv")
    home_ids = {h.get("id") for h in home_rows if h.get("id")}

    # Load rooms
    rooms_cols, rooms_rows = read_csv(EXPORT_DIR / "rooms.csv")
    rooms, rooms_index = build_room_index(rooms_rows)
    manual_map = load_manual_map()

    # Load room_images and analyses
    ri_cols, ri_rows = read_csv(EXPORT_DIR / "room_images.csv")
    ia_cols, ia_rows = read_csv(EXPORT_DIR / "image_analyses.csv")

    print(f"Rooms: {len(rooms_rows)}, Room Images: {len(ri_rows)}, Image Analyses: {len(ia_rows)}")

    # Enrich room_images with inferred room_id
    if "room_id" not in ri_cols:
        ri_cols.append("room_id")
    ri_rows_enriched, ri_updated = enrich_room_images(ri_rows, ia_rows, rooms_index, rooms, manual_map)
    print(f"room_images: linked {ri_updated} images to rooms (manual/tags/unique)")
    write_csv(ENRICHED_DIR / "room_images.csv", ri_cols, ri_rows_enriched)

    # Normalize image_analyses JSON array fields
    ia_rows_fixed, fixed_counts = normalize_image_analyses_json(ia_rows)
    print("image_analyses JSON fixes:")
    for k, v in fixed_counts.items():
        print(f"  - {k}: fixed {v}")
    write_csv(ENRICHED_DIR / "image_analyses.csv", ia_cols, ia_rows_fixed)

    # Pass-through others, with optional home_id addition if safe
    def passthrough_with_home_id(name: str):
        cols, rows = read_csv(EXPORT_DIR / name)
        if not rows:
            return
        added = False
        if "home_id" not in cols and len(home_ids) == 1:
            cols.append("home_id")
            hid = list(home_ids)[0]
            for r in rows:
                r["home_id"] = hid
            added = True
        write_csv(ENRICHED_DIR / name, cols, rows)
        if added:
            print(f"{name}: added home_id for {len(rows)} rows")

    passthrough_with_home_id("materials.csv")
    passthrough_with_home_id("products.csv")
    passthrough_with_home_id("fixtures.csv")
    # Always copy others for completeness
    for fname in [
        "home.csv",
        "floor_plans.csv",
        "floor_plan_analyses.csv",
        "rooms.csv",
    ]:
        cols, rows = read_csv(EXPORT_DIR / fname)
        if rows:
            write_csv(ENRICHED_DIR / fname, cols, rows)

    # Make image paths portable: attempt to relativize to uploads/ if present
    def make_paths_portable(rows: List[Dict[str, str]], col: str) -> int:
        changed = 0
        for r in rows:
            p = r.get(col)
            if not p:
                continue
            # If absolute path under project, try to strip ROOT
            try:
                path_obj = Path(p)
                if path_obj.is_absolute():
                    try:
                        rel = path_obj.relative_to(ROOT)
                        r[col] = str(rel).replace("\\", "/")
                        changed += 1
                    except ValueError:
                        # If contains uploads segment, strip up to uploads
                        parts = path_obj.parts
                        if "uploads" in parts:
                            idx = parts.index("uploads")
                            rel = Path(*parts[idx:])
                            r[col] = str(rel).replace("\\", "/")
                            changed += 1
            except Exception:
                continue
        return changed

    # Update enriched room_images paths
    eri_cols, eri_rows = read_csv(ENRICHED_DIR / "room_images.csv")
    if eri_rows and "image_url" in eri_cols:
        changed = make_paths_portable(eri_rows, "image_url")
        if changed:
            print(f"room_images: made {changed} paths portable")
            write_csv(ENRICHED_DIR / "room_images.csv", eri_cols, eri_rows)

    # Update enriched floor_plans paths
    efp_cols, efp_rows = read_csv(ENRICHED_DIR / "floor_plans.csv")
    if efp_rows and "image_url" in efp_cols:
        changed = make_paths_portable(efp_rows, "image_url")
        if changed:
            print(f"floor_plans: made {changed} paths portable")
            write_csv(ENRICHED_DIR / "floor_plans.csv", efp_cols, efp_rows)

    print(f"Enriched CSVs written to: {ENRICHED_DIR}")


if __name__ == "__main__":
    main()
