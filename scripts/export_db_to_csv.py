"""Export current database contents and a per-home CSV ZIP.

- Prints a summary of counts per table
- Writes exports/home_<home_id>_export.zip with CSVs similar to the API export

Usage:
    python scripts/export_db_to_csv.py
"""
from __future__ import annotations

import csv
import io
import os
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import select, text, inspect
from sqlalchemy.orm import Session

# Ensure project root is on sys.path so 'backend' package can be imported when
# running this script directly (e.g., `python scripts/export_db_to_csv.py`).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Local imports
from backend.models.base import SessionLocal
from backend.models import (
    Home,
    Room,
    RoomImage,
    Material,
    Fixture,
    Product,
    FloorPlan,
    FloorPlanAnalysis,
    RoomAnalysis,
    ImageAnalysis,
)

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def as_dict_list(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return rows


def write_zip_csv(zipf: zipfile.ZipFile, name: str, rows: List[Dict[str, Any]]):
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    else:
        writer = csv.DictWriter(buf, fieldnames=["empty"]) 
        writer.writeheader()
    zipf.writestr(name, buf.getvalue())


def _normalize_seq(value: Any) -> Any:
    """Normalize list-like JSON columns to comma-separated strings for CSV.

    If value is a list/tuple, join by comma. If it's already a string or None,
    return as-is. For other types (e.g., dict), convert to string.
    """
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return ",".join(str(v) for v in value)
    if isinstance(value, str):
        return value
    return str(value)


def summarize(session: Session) -> Dict[str, int]:
    summary = {
        "homes": session.query(Home).count(),
        "rooms": session.query(Room).count(),
        "room_images": session.query(RoomImage).count(),
        "materials": session.query(Material).count(),
        "fixtures": session.query(Fixture).count(),
        "products": session.query(Product).count(),
        "floor_plans": session.query(FloorPlan).count(),
        "floor_plan_analyses": session.query(FloorPlanAnalysis).count(),
        "room_analyses": session.query(RoomAnalysis).count(),
        "image_analyses": session.query(ImageAnalysis).count(),
    }
    return summary


def export_home(session: Session, home: Home) -> Path:
    out_path = EXPORT_DIR / f"home_{home.id}_export.zip"
    with zipfile.ZipFile(out_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Home
        home_row = [{
            "id": str(home.id),
            "name": home.name,
            "home_type": getattr(home.home_type, "value", str(home.home_type)),
            "year_built": home.year_built,
            "square_footage": home.square_footage,
            "num_bedrooms": home.num_bedrooms,
            "num_bathrooms": home.num_bathrooms,
            "num_floors": home.num_floors,
        }]
        write_zip_csv(zf, "home.csv", home_row)

        # Floor plans (use text() to avoid enum coercion issues elsewhere)
        fps = session.execute(
            text(
                """
                SELECT id, home_id, name, floor_level, image_url, scale
                FROM floor_plans
                WHERE home_id = :home_id
                """
            ),
            {"home_id": str(home.id)},
        ).mappings().all()
        floor_plans = [{
            "id": str(fp["id"]),
            "home_id": str(fp["home_id"]),
            "name": fp.get("name"),
            "floor_level": fp.get("floor_level"),
            "image_url": fp.get("image_url"),
            "scale": fp.get("scale"),
        } for fp in fps]
        write_zip_csv(zf, "floor_plans.csv", floor_plans)

        # Rooms - fallback to raw SQL to bypass Enum coercion errors (e.g., unexpected room_type)
        try:
            rooms = session.query(Room).filter(Room.home_id == home.id).all()
            room_rows = [{
                "id": str(r.id),
                "home_id": str(home.id),
                "name": r.name,
                "room_type": getattr(r.room_type, "value", str(r.room_type)),
                "floor_level": r.floor_level,
                "length": r.length,
                "width": r.width,
                "height": r.height,
                "area": r.area,
            } for r in rooms]
        except Exception:
            rooms = session.execute(
                text(
                    """
                    SELECT id, home_id, name, room_type, floor_level, length, width, height, area
                    FROM rooms
                    WHERE home_id = :home_id
                    """
                ),
                {"home_id": str(home.id)},
            ).mappings().all()
            room_rows = [{
                "id": str(r["id"]),
                "home_id": str(r["home_id"]),
                "name": r.get("name"),
                "room_type": r.get("room_type"),
                "floor_level": r.get("floor_level"),
                "length": r.get("length"),
                "width": r.get("width"),
                "height": r.get("height"),
                "area": r.get("area"),
            } for r in rooms]
        write_zip_csv(zf, "rooms.csv", room_rows)

        # Room images via join to rooms by home_id
        images = session.execute(
            text(
                """
                SELECT i.id, i.room_id, i.image_url, i.image_type, i.view_angle, i.is_analyzed
                FROM room_images i
                JOIN rooms r ON r.id = i.room_id
                WHERE r.home_id = :home_id
                """
            ),
            {"home_id": str(home.id)},
        ).mappings().all()
        image_rows = [{
            "id": str(img["id"]),
            "room_id": str(img["room_id"]),
            "image_url": img.get("image_url"),
            "image_type": img.get("image_type"),
            "view_angle": img.get("view_angle"),
            "is_analyzed": img.get("is_analyzed"),
        } for img in images]
        write_zip_csv(zf, "room_images.csv", image_rows)

        # Image analyses via join
        ia = session.execute(
            text(
                """
                SELECT a.id, a.room_image_id, a.description, a.keywords, a.dominant_colors,
                       a.objects_detected, a.materials_visible, a.fixtures_visible,
                       a.confidence_score, a.analysis_model
                FROM image_analyses a
                JOIN room_images i ON i.id = a.room_image_id
                JOIN rooms r ON r.id = i.room_id
                WHERE r.home_id = :home_id
                """
            ),
            {"home_id": str(home.id)},
        ).mappings().all()
        ia_rows = [{
            "id": str(a["id"]),
            "room_image_id": str(a["room_image_id"]),
            "description": a.get("description"),
            "keywords": _normalize_seq(a.get("keywords")),
            "dominant_colors": _normalize_seq(a.get("dominant_colors")),
            "objects_detected": _normalize_seq(a.get("objects_detected")),
            "materials_visible": _normalize_seq(a.get("materials_visible")),
            "fixtures_visible": _normalize_seq(a.get("fixtures_visible")),
            "confidence_score": a.get("confidence_score"),
            "analysis_model": a.get("analysis_model"),
        } for a in ia]
        write_zip_csv(zf, "image_analyses.csv", ia_rows)

        fpas = session.execute(
            text(
                """
                SELECT a.id, a.floor_plan_id, a.room_count, a.layout_type, a.total_area, a.features
                FROM floor_plan_analyses a
                JOIN floor_plans f ON f.id = a.floor_plan_id
                WHERE f.home_id = :home_id
                """
            ),
            {"home_id": str(home.id)},
        ).mappings().all()
        fpa_rows = [{
            "id": str(fpa["id"]),
            "floor_plan_id": str(fpa["floor_plan_id"]),
            "room_count": fpa.get("room_count"),
            "layout_type": fpa.get("layout_type"),
            "total_area": fpa.get("total_area"),
            "features": _normalize_seq(fpa.get("features")),
        } for fpa in fpas]
        write_zip_csv(zf, "floor_plan_analyses.csv", fpa_rows)

        # Materials, Fixtures, Products via joins (avoid enum coercion on category)
        mats = session.execute(
            text(
                """
                SELECT m.id, m.room_id, m.category, m.material_type, m.brand, m.color, m.finish
                FROM materials m
                JOIN rooms r ON r.id = m.room_id
                WHERE r.home_id = :home_id
                """
            ),
            {"home_id": str(home.id)},
        ).mappings().all()
        fixes = session.execute(
            text(
                """
                SELECT f.id, f.room_id, f.fixture_type, f.brand, f.model, f.style, f.finish, f.location
                FROM fixtures f
                JOIN rooms r ON r.id = f.room_id
                WHERE r.home_id = :home_id
                """
            ),
            {"home_id": str(home.id)},
        ).mappings().all()
        prods = session.execute(
            text(
                """
                SELECT p.id, p.room_id, p.product_category, p.product_type, p.brand, p.style, p.color, p.material, p.confidence_score
                FROM products p
                JOIN rooms r ON r.id = p.room_id
                WHERE r.home_id = :home_id
                """
            ),
            {"home_id": str(home.id)},
        ).mappings().all()

        mat_rows = [{
            "id": str(m["id"]),
            "room_id": str(m["room_id"]),
            "category": m.get("category"),
            "material_type": m.get("material_type"),
            "brand": m.get("brand"),
            "color": m.get("color"),
            "finish": m.get("finish"),
        } for m in mats]
        write_zip_csv(zf, "materials.csv", mat_rows)

        fix_rows = [{
            "id": str(f["id"]),
            "room_id": str(f["room_id"]),
            "fixture_type": f.get("fixture_type"),
            "brand": f.get("brand"),
            "model": f.get("model"),
            "style": f.get("style"),
            "finish": f.get("finish"),
            "location": str(f.get("location")) if f.get("location") is not None else None,
        } for f in fixes]
        write_zip_csv(zf, "fixtures.csv", fix_rows)

        prod_rows = [{
            "id": str(p["id"]),
            "room_id": str(p["room_id"]),
            "product_category": p.get("product_category"),
            "product_type": p.get("product_type"),
            "brand": p.get("brand"),
            "style": p.get("style"),
            "color": p.get("color"),
            "material": p.get("material"),
            "confidence_score": p.get("confidence_score"),
        } for p in prods]
        write_zip_csv(zf, "products.csv", prod_rows)

        # Room analyses via join - dynamically select only existing columns to avoid schema mismatches
        inspector = inspect(session.bind)
        try:
            ra_cols = {c["name"] for c in inspector.get_columns("room_analyses")}
        except Exception:
            ra_cols = {"id", "room_id", "summary", "confidence_score"}

        desired_cols = [
            "id",
            "room_id",
            "analysis_type",
            "summary",
            "confidence_score",
            "estimated_renovation_priority",
            "improvement_suggestions",
            "analysis_notes",
            "created_at",
            "updated_at",
        ]
        ra_select_cols = [c for c in desired_cols if c in ra_cols]
        if not ra_select_cols:
            ra_select_cols = ["id", "room_id", "summary", "confidence_score"]

        sql = (
            "SELECT "
            + ", ".join([f"a.{c}" for c in ra_select_cols])
            + " FROM room_analyses a JOIN rooms r ON r.id = a.room_id WHERE r.home_id = :home_id"
        )
        ras = session.execute(text(sql), {"home_id": str(home.id)}).mappings().all()
        ra_rows = []
        for ra in ras:
            row = {"id": str(ra["id"]), "room_id": str(ra["room_id"]) if ra.get("room_id") is not None else None}
            for c in ra_select_cols:
                if c in ("id", "room_id"):
                    continue
                row[c] = ra.get(c)
            ra_rows.append(row)
        write_zip_csv(zf, "room_analyses.csv", ra_rows)

    return out_path


def main():
    with SessionLocal() as session:
        summary = summarize(session)
        print("DB Summary:")
        for k, v in summary.items():
            print(f"- {k}: {v}")

        homes = session.query(Home).all()
        if not homes:
            print("\nNo homes found. Nothing to export.")
            return

        print(f"\nExporting {len(homes)} home(s) to '{EXPORT_DIR}/' ...")
        for h in homes:
            path = export_home(session, h)
            print(f"- Exported {h.name} ({h.id}) -> {path}")

        print("\nDone.")


if __name__ == "__main__":
    main()
