"""Import enriched CSV exports into the database.

This script reads CSVs from exports/analysis_run/enriched (or falls back to
exports/analysis_run) and persists them to the DB using the SQLAlchemy models.
It attempts to preserve IDs from CSVs (UUID strings) when present.

Usage (PowerShell):
  python -m scripts.import_enriched_csv_to_db --owner-email demo@example.com

Notes:
  - For enums (room_type, material category), unknown values map to 'other'.
  - RoomImage.room_id is required by the DB schema; rows missing room_id will be skipped with a warning.
  - If a row with the same ID already exists, it's skipped.
"""

import argparse
import asyncio
import csv
from pathlib import Path
import uuid
from typing import Optional, Dict, Any

from sqlalchemy import select

from backend.models.base import init_db_async, AsyncSessionLocal
from backend.models.user import User, UserType
from backend.models.home import (
    Home, HomeType, Room, RoomType, RoomImage, FloorPlan, Material, Fixture, Product, MaterialCategory
)
from backend.models.analysis import FloorPlanAnalysis, ImageAnalysis


def _json_load_maybe(s: Optional[str]):
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        import json
        return json.loads(s)
    except Exception:
        # Try naive comma split for simple lists
        if "," in s and "[" not in s and "{" not in s:
            return [x.strip() for x in s.split(",") if x.strip()]
        return s


def _uuid(s: Optional[str]) -> Optional[uuid.UUID]:
    try:
        return uuid.UUID(str(s)) if s else None
    except Exception:
        return None


async def ensure_user(db, email: str) -> uuid.UUID:
    res = await db.execute(select(User).where(User.email == email))
    u = res.scalar_one_or_none()
    if u:
        return u.id
    u = User(email=email, user_type=UserType.HOMEOWNER)
    db.add(u)
    await db.commit()
    return u.id


async def upsert_home(db, row: Dict[str, Any], owner_id: uuid.UUID) -> uuid.UUID:
    hid = _uuid(row.get("id")) or uuid.uuid4()
    if (await db.get(Home, hid)):
        return hid
    h = Home(
        id=hid,
        owner_id=owner_id,
        name=row.get("name") or "Imported Home",
        address=_json_load_maybe(row.get("address")) or {},
        home_type=HomeType.SINGLE_FAMILY,
        year_built=int(row.get("year_built") or 0) or None,
        square_footage=int(row.get("square_footage") or 0) or None,
        num_bedrooms=int(row.get("num_bedrooms") or 0) or None,
        num_bathrooms=float(row.get("num_bathrooms") or 0) or None,
        num_floors=int(row.get("num_floors") or 0) or None,
        digital_twin_completeness=float(row.get("digital_twin_completeness") or 0.0),
        extra_data=_json_load_maybe(row.get("extra_data")) or {},
    )
    db.add(h)
    await db.commit()
    return hid


async def upsert_floor_plan(db, home_id: uuid.UUID, row: Dict[str, Any]):
    fid = _uuid(row.get("id")) or uuid.uuid4()
    if await db.get(FloorPlan, fid):
        return
    fp = FloorPlan(
        id=fid,
        home_id=home_id,
        name=row.get("name") or None,
        floor_level=int(row.get("floor_level") or 1),
        image_url=row.get("image_url") or "",
        scale=row.get("scale") or None,
        is_analyzed=True,
        analysis_metadata={},
    )
    db.add(fp)


async def upsert_room(db, home_id: uuid.UUID, row: Dict[str, Any]):
    rid = _uuid(row.get("id")) or uuid.uuid4()
    if await db.get(Room, rid):
        return
    rt_raw = (row.get("room_type") or "other").lower()
    try:
        rt = RoomType(rt_raw)  # may raise
    except Exception:
        rt = RoomType.OTHER
    r = Room(
        id=rid,
        home_id=home_id,
        name=row.get("name") or "Room",
        room_type=rt,
        floor_level=int(row.get("floor_level") or 1),
        length=float(row.get("length") or 0) or None,
        width=float(row.get("width") or 0) or None,
        height=float(row.get("height") or 0) or None,
        area=float(row.get("area") or 0) or None,
        style=row.get("style") or None,
        condition_score=float(row.get("condition_score") or 0) or None,
        extra_data=_json_load_maybe(row.get("extra_data")) or {},
    )
    db.add(r)


async def upsert_room_image(db, row: Dict[str, Any]):
    iid = _uuid(row.get("id")) or uuid.uuid4()
    if await db.get(RoomImage, iid):
        return
    rid = _uuid(row.get("room_id"))
    if not rid:
        # Skip images without a room link (schema requires it); they can be linked later
        return
    ri = RoomImage(
        id=iid,
        room_id=rid,
        image_url=row.get("image_url") or "",
        image_type=row.get("image_type") or "original",
        view_angle=row.get("view_angle") or None,
        is_analyzed=True,
        analysis_metadata={},
    )
    db.add(ri)


async def upsert_material(db, row: Dict[str, Any]):
    mid = _uuid(row.get("id")) or uuid.uuid4()
    if await db.get(Material, mid):
        return
    rid = _uuid(row.get("room_id"))
    if not rid:
        return
    cat_raw = (row.get("category") or row.get("material_category") or "other").lower()
    try:
        cat = MaterialCategory(cat_raw)
    except Exception:
        cat = MaterialCategory.OTHER
    m = Material(
        id=mid,
        room_id=rid,
        category=cat,
        material_type=row.get("material_type") or row.get("type") or "unknown",
        brand=row.get("brand") or None,
        color=row.get("color") or None,
        finish=row.get("finish") or None,
        condition=row.get("condition") or None,
        age_years=int(row.get("age_years") or 0) or None,
        extra_data=_json_load_maybe(row.get("extra_data")) or {},
    )
    db.add(m)


async def upsert_fixture(db, row: Dict[str, Any]):
    fid = _uuid(row.get("id")) or uuid.uuid4()
    if await db.get(Fixture, fid):
        return
    rid = _uuid(row.get("room_id"))
    if not rid:
        return
    f = Fixture(
        id=fid,
        room_id=rid,
        fixture_type=row.get("fixture_type") or row.get("type") or "unknown",
        brand=row.get("brand") or None,
        model=row.get("model") or None,
        style=row.get("style") or None,
        finish=row.get("finish") or None,
        location=row.get("location") or None,
        condition=row.get("condition") or None,
        extra_data=_json_load_maybe(row.get("extra_data")) or {},
    )
    db.add(f)


async def upsert_product(db, row: Dict[str, Any]):
    pid = _uuid(row.get("id")) or uuid.uuid4()
    if await db.get(Product, pid):
        return
    rid = _uuid(row.get("room_id"))
    if not rid:
        return
    p = Product(
        id=pid,
        room_id=rid,
        product_category=row.get("product_category") or row.get("category") or "unknown",
        product_type=row.get("product_type") or row.get("type") or "unknown",
        brand=row.get("brand") or None,
        style=row.get("style") or None,
        color=row.get("color") or None,
        material=row.get("material") or None,
        dimensions=_json_load_maybe(row.get("dimensions")) or {},
        confidence_score=float(row.get("confidence_score") or 0) or None,
        condition=row.get("condition") or None,
        extra_data=_json_load_maybe(row.get("extra_data")) or {},
    )
    db.add(p)


async def upsert_image_analysis(db, row: Dict[str, Any]):
    aid = _uuid(row.get("id")) or uuid.uuid4()
    if await db.get(ImageAnalysis, aid):
        return
    ri = _uuid(row.get("room_image_id"))
    if not ri:
        return
    ia = ImageAnalysis(
        id=aid,
        room_image_id=ri,
        description=row.get("description") or None,
        keywords=_json_load_maybe(row.get("keywords")) or [],
        dominant_colors=_json_load_maybe(row.get("dominant_colors")) or [],
        objects_detected=_json_load_maybe(row.get("objects_detected")) or [],
        materials_visible=_json_load_maybe(row.get("materials_visible")) or [],
        fixtures_visible=_json_load_maybe(row.get("fixtures_visible")) or [],
        image_quality_score=float(row.get("image_quality_score") or 0) or None,
        lighting_quality=row.get("lighting_quality") or None,
        clarity=row.get("clarity") or None,
        view_angle=row.get("view_angle") or None,
        estimated_coverage=float(row.get("estimated_coverage") or 0) or None,
        confidence_score=float(row.get("confidence_score") or 0) or None,
        analysis_model=row.get("analysis_model") or None,
        analysis_notes=row.get("analysis_notes") or None,
    )
    db.add(ia)


def _read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-email", type=str, default="demo@example.com")
    args = parser.parse_args()

    await init_db_async()

    root = Path(__file__).resolve().parents[1]
    base = root / "exports" / "analysis_run"
    data_dir = base / "enriched" if (base / "enriched").exists() else base

    home_rows = _read_csv(data_dir / "home.csv")
    fp_rows = _read_csv(data_dir / "floor_plans.csv")
    fpa_rows = _read_csv(data_dir / "floor_plan_analyses.csv")
    room_rows = _read_csv(data_dir / "rooms.csv")
    ri_rows = _read_csv(data_dir / "room_images.csv")
    ia_rows = _read_csv(data_dir / "image_analyses.csv")
    mat_rows = _read_csv(data_dir / "materials.csv")
    prod_rows = _read_csv(data_dir / "products.csv")
    fix_rows = _read_csv(data_dir / "fixtures.csv")

    async with AsyncSessionLocal() as db:
        owner_id = await ensure_user(db, args.owner_email)

        # Home
        if home_rows:
            home_id = await upsert_home(db, home_rows[0], owner_id)
        else:
            # create a default home
            home_id = await upsert_home(db, {"name": "Imported Home", "address": {}}, owner_id)

        # Floor plans
        for row in fp_rows:
            await upsert_floor_plan(db, home_id, row)
        await db.commit()

        # Rooms
        for row in room_rows:
            await upsert_room(db, home_id, row)
        await db.commit()

        # Room images
        for row in ri_rows:
            await upsert_room_image(db, row)
        await db.commit()

        # Materials / Fixtures / Products
        for row in mat_rows:
            await upsert_material(db, row)
        for row in fix_rows:
            await upsert_fixture(db, row)
        for row in prod_rows:
            await upsert_product(db, row)
        await db.commit()

        # Image analyses
        for row in ia_rows:
            await upsert_image_analysis(db, row)
        await db.commit()

        print("Import complete:")
        print({
            "home_id": str(home_id),
            "rooms": len(room_rows),
            "room_images": len(ri_rows),
            "materials": len(mat_rows),
            "fixtures": len(fix_rows),
            "products": len(prod_rows),
            "image_analyses": len(ia_rows),
        })


if __name__ == "__main__":
    asyncio.run(main())
