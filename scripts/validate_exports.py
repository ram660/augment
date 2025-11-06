#!/usr/bin/env python3
import csv
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "analysis_run"

FILES = {
    "home.csv": {
        "required_columns": ["id", "name"],
        "critical_links": [],
    },
    "floor_plans.csv": {
        "required_columns": ["id", "home_id", "name", "floor_level", "image_url"],
        "critical_links": ["home_id"],
        "path_columns": ["image_url"],
    },
    "floor_plan_analyses.csv": {
        "required_columns": ["id", "floor_plan_id"],
        "critical_links": ["floor_plan_id"],
    },
    "rooms.csv": {
        "required_columns": ["id", "home_id", "name", "room_type", "floor_level"],
        "critical_links": ["home_id"],
        # Optional but recommended: floor_plan_id
        "recommended_columns": ["floor_plan_id"],
    },
    "room_images.csv": {
        "required_columns": ["id", "image_url"],
        "critical_links": ["room_id"],
        "path_columns": ["image_url"],
    },
    "image_analyses.csv": {
        "required_columns": ["id", "room_image_id", "analysis_model"],
        "critical_links": ["room_image_id"],
        "json_array_columns": [
            "keywords",
            "dominant_colors",
            "objects_detected",
            "materials_visible",
            "fixtures_visible",
        ],
    },
    "materials.csv": {
        "required_columns": ["id", "category", "material_type"],
        "critical_links": ["room_id"],
        "recommended_columns": ["home_id"],
    },
    "products.csv": {
        "required_columns": ["id", "product_category", "product_type"],
        "critical_links": ["room_id"],
        "recommended_columns": ["home_id"],
    },
    "fixtures.csv": {
        "required_columns": ["id", "fixture_type"],
        "critical_links": ["room_id"],
        "recommended_columns": ["home_id"],
    },
}

WINDOWS_ABS_RE = re.compile(r"^[A-Za-z]:\\\\")


def read_csv_rows(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return reader.fieldnames or [], rows


def is_blank(v: str) -> bool:
    return v is None or str(v).strip() == ""


def count_missing(rows: List[Dict[str, str]], field: str) -> int:
    return sum(1 for r in rows if field not in r or is_blank(r.get(field)))


def count_abs_paths(rows: List[Dict[str, str]], columns: List[str]) -> int:
    cnt = 0
    for r in rows:
        for c in columns:
            v = r.get(c)
            if not is_blank(v):
                if WINDOWS_ABS_RE.match(v) or os.path.isabs(v):
                    cnt += 1
                    break
    return cnt


def is_valid_json_array(s: str) -> bool:
    if is_blank(s):
        return True  # treat empty as acceptable/nullable
    try:
        val = json.loads(s)
        return isinstance(val, list)
    except json.JSONDecodeError:
        return False


def summarize_file(name: str, spec: Dict) -> Dict:
    path = EXPORT_DIR / name
    columns, rows = read_csv_rows(path)
    present = bool(rows)
    total = len(rows)

    missing_columns = []
    for col in spec.get("required_columns", []):
        if col not in columns:
            missing_columns.append(col)

    recommended_missing = []
    for col in spec.get("recommended_columns", []):
        if col not in columns:
            recommended_missing.append(col)

    missing_links = {}
    for link in spec.get("critical_links", []):
        if link in columns:
            missing_links[link] = count_missing(rows, link)
        else:
            missing_links[link] = "column_missing"

    abs_path_count = 0
    if spec.get("path_columns"):
        abs_path_count = count_abs_paths(rows, spec["path_columns"])

    json_invalid = {}
    for jcol in spec.get("json_array_columns", []):
        if jcol in columns:
            invalid = sum(1 for r in rows if not is_valid_json_array(r.get(jcol)))
            json_invalid[jcol] = invalid
        else:
            json_invalid[jcol] = "column_missing"

    return {
        "file": name,
        "present": present,
        "rows": total,
        "missing_required_columns": missing_columns,
        "missing_recommended_columns": recommended_missing,
        "missing_critical_links": missing_links,
        "absolute_paths_detected": abs_path_count,
        "invalid_json_columns": json_invalid,
    }


def main():
    print(f"Scanning exports in: {EXPORT_DIR}")
    if not EXPORT_DIR.exists():
        print("ERROR: export directory does not exist.")
        return

    reports = []
    for fname, spec in FILES.items():
        rep = summarize_file(fname, spec)
        reports.append(rep)

    # Pretty print summary
    for rep in reports:
        print("\n== ", rep["file"], "==")
        if not rep["present"]:
            print("(missing)")
            continue
        print(f"Rows: {rep['rows']}")
        if rep["missing_required_columns"]:
            print("Missing required columns:", ", ".join(rep["missing_required_columns"]))
        if rep["missing_recommended_columns"]:
            print("Missing recommended columns:", ", ".join(rep["missing_recommended_columns"]))
        if rep["missing_critical_links"]:
            print("Missing critical links (count or 'column_missing'):")
            for k, v in rep["missing_critical_links"].items():
                print(f"  - {k}: {v}")
        if rep["absolute_paths_detected"]:
            print(f"Absolute (likely non-portable) paths: {rep['absolute_paths_detected']}")
        if rep["invalid_json_columns"]:
            bad = {k: v for k, v in rep["invalid_json_columns"].items() if v not in (0, True)}
            if bad:
                print("Invalid JSON array columns (count of invalid or 'column_missing'):")
                for k, v in bad.items():
                    print(f"  - {k}: {v}")

    # Overall guidance
    print("\nGuidance:")
    print("- Ensure room_images.room_id, materials.room_id, products.room_id, fixtures.room_id are populated.")
    print("- Convert image_analyses arrays (objects/materials/fixtures/colors/keywords) to valid JSON.")
    print("- Replace absolute Windows paths with storage URIs or relative paths under uploads/.")
    print("- Consider adding rooms.floor_plan_id and adding home_id denorm columns to child tables for fast filtering.")


if __name__ == "__main__":
    main()
