"""
Ingest precomputed image links + DB-aligned analyses into the DB for an existing home.
Usage:
  python -m scripts.ingest_links_only --home-id <uuid> \
    --links-json uploads/analysis/image_room_links_v2.json \
    --analyses-json uploads/analysis/image_analyses_db_aligned.json \
    [--rename-files false]
"""
import argparse
import uuid
import asyncio
from pathlib import Path

from backend.models.base import AsyncSessionLocal, init_db_async
from backend.services.digital_twin_service import DigitalTwinService


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--home-id', type=str, required=True)
    parser.add_argument('--links-json', type=str, required=True)
    parser.add_argument('--analyses-json', type=str, required=True)
    parser.add_argument('--rename-files', type=str, default='false')
    args = parser.parse_args()

    try:
        home_id_val = uuid.UUID(str(args.home_id))
    except Exception:
        raise SystemExit("--home-id must be a valid UUID")
    links = Path(args.links_json)
    analyses = Path(args.analyses_json)

    if not links.exists() or not analyses.exists():
        raise SystemExit(f"Missing inputs. links={links} analyses={analyses}")

    rename = str(args.rename_files).lower() in {'1','true','yes','y'}

    await init_db_async()
    async with AsyncSessionLocal() as session:
        svc = DigitalTwinService()
        res = await svc.ingest_image_links_and_analyses(
            db=session,
            home_id=home_id_val,
            links_path=str(links),
            analyses_path=str(analyses),
            rename_files=rename,
        )
        print("Ingest result:", res)


if __name__ == '__main__':
    asyncio.run(main())
