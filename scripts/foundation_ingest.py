"""
Foundation ingestion script

Creates a Home for this dataset (if missing), ingests floor plan analysis JSON, and ingests
pre-generated image analyses + links (from the notebook) into the database without re-running AI.

Default DB is SQLite as configured in backend.models.base (homevision.db in repo root).

Usage (PowerShell):

  # From repo root
  python -m scripts.foundation_ingest \
    --home-email demo@example.com \
    --home-name "Sample Home" \
    --floorplan-json "uploads/floor_plans/analysis/genMid.R2929648_1_4_analysis_gemini-2-5-flash_20251102_111958.json" \
    --links-json "uploads/analysis/image_room_links_v2.json" \
    --analyses-json "uploads/analysis/image_analyses_db_aligned.json" \
    --rename-files false

"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional
import uuid

# Ensure repo root on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import select
from backend.models.base import init_db_async, AsyncSessionLocal
from backend.models.user import User, UserType, HomeownerProfile, SubscriptionTier
from backend.models.home import Home, HomeType
from backend.services.digital_twin_service import DigitalTwinService


async def ensure_user_and_home(db, email: str, home_name: str) -> uuid.UUID:
    # Ensure user
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user:
        user = User(email=email, user_type=UserType.HOMEOWNER)
        db.add(user)
        await db.flush()
        # Basic homeowner profile
        hop = HomeownerProfile(user_id=user.id, subscription_tier=SubscriptionTier.FREE)
        db.add(hop)
        await db.commit()

    # Ensure home
    res = await db.execute(select(Home).where(Home.owner_id == user.id, Home.name == home_name))
    home = res.scalar_one_or_none()
    if not home:
        home = Home(
            owner_id=user.id,
            name=home_name,
            address={"street": "", "city": "", "province": "", "postal_code": "", "country": ""},
            home_type=HomeType.SINGLE_FAMILY,
            num_floors=1,
            extra_data={"source": "foundation_ingest"}
        )
        db.add(home)
        await db.commit()

    return home.id


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--home-email", type=str, default="demo@example.com")
    parser.add_argument("--home-name", type=str, default="Sample Home")
    parser.add_argument("--floorplan-json", type=str, required=True)
    parser.add_argument("--links-json", type=str, required=True)
    parser.add_argument("--analyses-json", type=str, required=True)
    parser.add_argument("--floorplan-image", type=str, default=None, help="Optional: path to the original floor plan image; stored in FloorPlan.image_url")
    parser.add_argument("--rename-files", type=str, default="false")
    args = parser.parse_args()

    rename_files = args.rename_files.strip().lower() in ("1", "true", "yes")

    # Init DB (create tables)
    await init_db_async()

    async with AsyncSessionLocal() as db:
        home_id = await ensure_user_and_home(db, args.home_email, args.home_name)

        svc = DigitalTwinService()

        # 1) Ingest floor plan JSON first
        fp_res = await svc.ingest_floor_plan_from_json(
            db=db,
            home_id=home_id,
            json_path=args.floorplan_json,
            image_url=(args.floorplan_image or args.floorplan_json),
            name_prefix=None,
        )
        print("Floor plan ingest:", fp_res)

        # 2) Ingest pre-generated image links + analyses
        im_res = await svc.ingest_image_links_and_analyses(
            db=db,
            home_id=home_id,
            links_path=args.links_json,
            analyses_path=args.analyses_json,
            rename_files=rename_files,
        )
        print("Image analyses ingest:", im_res)

        # 3) Summarize digital twin quickly (optional)
        twin = await svc.get_home_digital_twin(db, home_id)
        print("Digital Twin Summary:")
        print({
            "home_id": twin.get("home_id"),
            "total_rooms": twin.get("total_rooms"),
            "total_images": twin.get("total_images"),
        })

if __name__ == "__main__":
    asyncio.run(main())
