"""
Analyze room images with agents and write a consolidated JSON without persisting to DB.
This uses Gemini via RoomAnalysisAgent and does not rely on filenames for linking (mapping is optional in output).

Usage (PowerShell):

  python -m scripts.analyze_images_to_json `
    --home-id <HOME_UUID> `
    --directory "uploads/room_images" `
    --output "uploads/analysis/image_analyses_agent_report.json"
"""

import argparse
import asyncio
from pathlib import Path
import sys

# Ensure repo root on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.models.base import init_db_async, AsyncSessionLocal
from backend.services.digital_twin_service import DigitalTwinService


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--home-id', type=str, required=True)
    parser.add_argument('--directory', type=str, default='uploads/room_images')
    parser.add_argument('--output', type=str, default='uploads/analysis/agent_analysis_report.json')
    args = parser.parse_args()

    await init_db_async()

    async with AsyncSessionLocal() as db:
        svc = DigitalTwinService()
        res = await svc.analyze_room_images_to_json(
            db=db,
            home_id=args.home_id,
            directory=args.directory,
            analysis_type='comprehensive',
            output_path=args.output,
            overwrite=True,
        )
        print(res)

if __name__ == '__main__':
    asyncio.run(main())
