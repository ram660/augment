"""
Analyze a floor plan and a set of room images using the existing AI agents,
then save the results to CSV files instead of the database.

Usage (PowerShell):
  python scripts/analyze_to_csv.py --floor-plan uploads/floor_plans/example.png --images-dir uploads/room_images --output-dir exports/analysis_run

What it writes to --output-dir:
  - home.csv (synthetic home id & metadata)
  - floor_plans.csv
  - floor_plan_analyses.csv
  - rooms.csv (derived from floor plan)
  - room_images.csv (discovered images + mapping)
  - image_analyses.csv
  - materials.csv
  - fixtures.csv
  - products.csv

Notes:
  - No DB writes are performed.
  - Requires your Gemini credentials configured like the app (see backend/integrations/gemini/).
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root on sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.digital_twin import FloorPlanAnalysisAgent, RoomAnalysisAgent
from backend.utils.image_filename_parser import parse_image_filename
from backend.utils.room_type_normalizer import normalize_room_type

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class HomeRow:
    id: str
    name: str


@dataclass
class FloorPlanRow:
    id: str
    home_id: str
    name: Optional[str]
    floor_level: Optional[int]
    image_url: str
    scale: Optional[str]


@dataclass
class RoomRow:
    id: str
    home_id: str
    name: str
    room_type: str
    floor_level: Optional[int]
    length: Optional[float]
    width: Optional[float]
    height: Optional[float]
    area: Optional[float]


@dataclass
class RoomImageRow:
    id: str
    room_id: Optional[str]
    image_url: str
    view_angle: Optional[str]


@dataclass
class ImageAnalysisRow:
    id: str
    room_image_id: str
    description: Optional[str]
    keywords: str
    dominant_colors: str
    objects_detected: str
    materials_visible: str
    fixtures_visible: str
    confidence_score: Optional[float]
    analysis_model: Optional[str]


@dataclass
class FloorPlanAnalysisRow:
    id: str
    floor_plan_id: str
    room_count: Optional[int]
    layout_type: Optional[str]
    total_area: Optional[float]
    features: str


@dataclass
class MaterialRow:
    id: str
    room_id: str
    category: Optional[str]
    material_type: Optional[str]
    brand: Optional[str]
    color: Optional[str]
    finish: Optional[str]


@dataclass
class FixtureRow:
    id: str
    room_id: str
    fixture_type: Optional[str]
    brand: Optional[str]
    model: Optional[str]
    style: Optional[str]
    finish: Optional[str]
    location: Optional[str]


@dataclass
class ProductRow:
    id: str
    room_id: str
    product_category: Optional[str]
    product_type: Optional[str]
    brand: Optional[str]
    style: Optional[str]
    color: Optional[str]
    material: Optional[str]
    confidence_score: Optional[float]


# ------------- helpers -------------

def _csv_write(path: Path, rows: List[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        # Ensure file with headers-only
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["empty"])  # header only
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _norm_seq(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ",".join(str(v) for v in value)
    return str(value)


def _norm_name(s: str) -> str:
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


# ------------- core -------------

async def analyze_to_csv(
    floor_plan_path: Path,
    images_dir: Optional[Path],
    output_dir: Path,
    floor_level: int = 1,
    home_name: str = "Temp Home",
):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Synthetic home
    home_id = str(uuid.uuid4())
    home_rows = [HomeRow(id=home_id, name=home_name).__dict__]
    _csv_write(output_dir / "home.csv", home_rows)

    # Analyze floor plan
    fpa_agent = FloorPlanAnalysisAgent()
    fpa_resp = await fpa_agent.execute({
        "image": str(floor_plan_path),
        "floor_level": floor_level,
        "name": f"Floor {floor_level}",
    })
    if not getattr(fpa_resp, "success", False):
        raise RuntimeError(f"Floor plan analysis failed: {getattr(fpa_resp, 'error', 'unknown')}")

    fp_rows: List[dict] = []
    fpa_rows: List[dict] = []
    room_rows: List[dict] = []

    # Handle single or multi-floor response shapes similar to service
    data = getattr(fpa_resp, "data", {}) or {}
    floors = data.get("floors") or []
    is_multi = bool(floors)
    if not is_multi:
        floors = [{
            "floor_level_number": data.get("floor_level_number") or floor_level,
            "floor_level_name": data.get("floor_level_name") or None,
            "rooms": data.get("detected_rooms") or [],
            "layout_analysis": data.get("layout_analysis") or {},
            "units": data.get("units") or {},
            "pixel_to_unit": data.get("pixel_to_unit"),
            "section_bbox": data.get("section_bbox"),
            "confidence_metrics": data.get("confidence_metrics") or {},
        }]

    for idx, fl in enumerate(floors):
        fl_num = fl.get("floor_level_number") or floor_level
        try:
            fl_num_int = int(fl_num)
        except Exception:
            fl_num_int = floor_level
        fl_name = fl.get("floor_level_name") or f"Floor {fl_num_int}"
        fp_id = str(uuid.uuid4())

        fp_rows.append(FloorPlanRow(
            id=fp_id,
            home_id=home_id,
            name=f"{fl_name} (section {idx+1})" if is_multi else fl_name,
            floor_level=fl_num_int,
            image_url=str(floor_plan_path),
            scale=(fl.get("units") or {}).get("scale_text"),
        ).__dict__)

        rooms_arr = fl.get("rooms") or []
        layout = fl.get("layout_analysis", {}) or {}
        fpa_rows.append(FloorPlanAnalysisRow(
            id=str(uuid.uuid4()),
            floor_plan_id=fp_id,
            room_count=len(rooms_arr),
            layout_type=layout.get("layout_type", "unknown"),
            total_area=layout.get("total_area_sqft"),
            features=_norm_seq((fl.get("features") or [])),
        ).__dict__)

        for r in rooms_arr:
            dims = r.get("measured_dimensions") or r.get("dimensions") or {}
            length_ft = (dims.get("length") or {}).get("value") or dims.get("length_ft")
            width_ft = (dims.get("width") or {}).get("value") or dims.get("width_ft")
            height_ft = (dims.get("height") or {}).get("value") or dims.get("height_ft")
            area_sqft = (dims.get("area") or {}).get("value") or dims.get("area_sqft")

            rt_norm = normalize_room_type(r.get("room_type") or "other")
            room_rows.append(RoomRow(
                id=str(uuid.uuid4()),
                home_id=home_id,
                name=r.get("name") or r.get("id") or "Unnamed Room",
                room_type=rt_norm,
                floor_level=fl_num_int,
                length=length_ft,
                width=width_ft,
                height=height_ft,
                area=area_sqft,
            ).__dict__)

    _csv_write(output_dir / "floor_plans.csv", fp_rows)
    _csv_write(output_dir / "floor_plan_analyses.csv", fpa_rows)
    _csv_write(output_dir / "rooms.csv", room_rows)

    # Build a lookup for mapping images -> rooms
    norm_to_room: Dict[str, dict] = {}
    for rr in room_rows:
        norm_to_room[_norm_name(rr["name"])] = rr

    # Discover images
    img_rows: List[dict] = []
    ia_rows: List[dict] = []
    mat_rows: List[dict] = []
    fix_rows: List[dict] = []
    prod_rows: List[dict] = []

    if images_dir and images_dir.exists():
        files: List[Path] = []
        for root, _dirs, filenames in os.walk(images_dir):
            for fn in filenames:
                if Path(fn).suffix.lower() in ALLOWED_EXT:
                    files.append(Path(root) / fn)

        # Helper: choose a room for a given image path
        def choose_room(path: Path) -> Tuple[Optional[str], Optional[str]]:
            base = path.name
            nb = _norm_name(base)
            # direct name match
            for key, room in norm_to_room.items():
                if key and key in nb:
                    return room["id"], room.get("room_type")
            # filename hints
            hints = parse_image_filename(str(path))
            rt = hints.get("room_type")
            if rt:
                # pick first room of that type
                for room in room_rows:
                    if room.get("room_type") == rt:
                        return room["id"], rt
            return None, rt

        ra_agent = RoomAnalysisAgent()
        for p in files:
            room_id, rt_hint = choose_room(p)
            img_id = str(uuid.uuid4())
            img_rows.append(RoomImageRow(
                id=img_id,
                room_id=room_id,
                image_url=str(p),
                view_angle=None,
            ).__dict__)

            # Run analysis (pass room_type if we have hint or mapped room)
            room_type_for_agent = rt_hint
            if not room_type_for_agent and room_id:
                # derive from mapped room
                for rr in room_rows:
                    if rr["id"] == room_id:
                        room_type_for_agent = rr.get("room_type")
                        break

            resp = await ra_agent.execute({
                "image": str(p),
                "room_type": room_type_for_agent or "unknown",
                "analysis_type": "comprehensive",
            })
            if not getattr(resp, "success", False):
                # still record the image; skip analysis outputs
                continue
            data = getattr(resp, "data", {}) or {}

            ia_id = str(uuid.uuid4())
            ia_rows.append(ImageAnalysisRow(
                id=ia_id,
                room_image_id=img_id,
                description=f"{data.get('room_style', 'unknown')} {data.get('room_type', 'room')}",
                keywords=_norm_seq(data.get("keywords")),
                dominant_colors=_norm_seq((data.get("visual_characteristics", {}) or {}).get("dominant_colors")),
                objects_detected=_norm_seq(data.get("detected_products")),
                materials_visible=_norm_seq(data.get("detected_materials")),
                fixtures_visible=_norm_seq(data.get("detected_fixtures")),
                confidence_score=data.get("confidence_score"),
                analysis_model=(data.get("metadata", {}) or {}).get("model_used"),
            ).__dict__)

            # Materials
            for m in (data.get("detected_materials", []) or []):
                mat_rows.append(MaterialRow(
                    id=str(uuid.uuid4()),
                    room_id=room_id or "",
                    category=m.get("category"),
                    material_type=m.get("material_type"),
                    brand=m.get("brand_detected"),
                    color=m.get("color"),
                    finish=m.get("finish"),
                ).__dict__)

            # Fixtures
            for f in (data.get("detected_fixtures", []) or []):
                fix_rows.append(FixtureRow(
                    id=str(uuid.uuid4()),
                    room_id=room_id or "",
                    fixture_type=f.get("type") or f.get("fixture_type"),
                    brand=f.get("brand_detected"),
                    model=f.get("model_detected"),
                    style=f.get("style"),
                    finish=f.get("finish"),
                    location=(f.get("location") if isinstance(f.get("location"), str) else None),
                ).__dict__)

            # Products
            for pinfo in (data.get("detected_products", []) or []):
                prod_rows.append(ProductRow(
                    id=str(uuid.uuid4()),
                    room_id=room_id or "",
                    product_category=pinfo.get("product_category"),
                    product_type=pinfo.get("product_type"),
                    brand=pinfo.get("brand_detected"),
                    style=pinfo.get("style"),
                    color=pinfo.get("color"),
                    material=pinfo.get("material"),
                    confidence_score=pinfo.get("confidence"),
                ).__dict__)

    # Write CSVs
    _csv_write(output_dir / "room_images.csv", img_rows)
    _csv_write(output_dir / "image_analyses.csv", ia_rows)
    _csv_write(output_dir / "materials.csv", mat_rows)
    _csv_write(output_dir / "fixtures.csv", fix_rows)
    _csv_write(output_dir / "products.csv", prod_rows)

    print(f"\nWrote CSVs to: {output_dir}")
    print(f"- floor_plans.csv: {len(fp_rows)}")
    print(f"- floor_plan_analyses.csv: {len(fpa_rows)}")
    print(f"- rooms.csv: {len(room_rows)}")
    print(f"- room_images.csv: {len(img_rows)}")
    print(f"- image_analyses.csv: {len(ia_rows)}")
    print(f"- materials.csv: {len(mat_rows)}")
    print(f"- fixtures.csv: {len(fix_rows)}")
    print(f"- products.csv: {len(prod_rows)}")


def main():
    parser = argparse.ArgumentParser(description="Analyze floor plan + room images to CSV")
    parser.add_argument("--floor-plan", required=True, help="Path to the floor plan image")
    parser.add_argument("--images-dir", required=False, help="Directory of room images (optional)")
    parser.add_argument("--output-dir", required=False, default=str(Path("exports")/"analysis_run"), help="Output directory for CSVs")
    parser.add_argument("--floor-level", type=int, default=1, help="Floor level hint")
    parser.add_argument("--home-name", default="Temp Home", help="Synthetic home name for CSV context")
    args = parser.parse_args()

    floor_plan_path = Path(args.floor_plan)
    if not floor_plan_path.exists():
        raise SystemExit(f"Floor plan not found: {floor_plan_path}")

    images_dir = Path(args.images_dir) if args.images_dir else None
    if images_dir and not images_dir.exists():
        print(f"Warning: images directory not found: {images_dir}; continuing with floor plan only")
        images_dir = None

    output_dir = Path(args.output_dir)

    asyncio.run(analyze_to_csv(
        floor_plan_path=floor_plan_path,
        images_dir=images_dir,
        output_dir=output_dir,
        floor_level=args.floor_level,
        home_name=args.home_name,
    ))


if __name__ == "__main__":
    main()
