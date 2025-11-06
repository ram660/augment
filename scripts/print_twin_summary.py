import argparse
import uuid
import asyncio
from sqlalchemy import select
from backend.models.base import AsyncSessionLocal, init_db_async
from backend.services.digital_twin_service import DigitalTwinService
from backend.models.home import FloorPlan, Room, RoomImage
from backend.models.analysis import FloorPlanAnalysis, ImageAnalysis

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--home-id', type=str, required=True)
    args = parser.parse_args()

    await init_db_async()
    async with AsyncSessionLocal() as session:
        svc = DigitalTwinService()
        hid = uuid.UUID(str(args.home_id))
        twin = await svc.get_home_digital_twin(session, hid)

        # Additional verification counts
        fp_count = len((await session.execute(select(FloorPlan).where(FloorPlan.home_id == hid))).scalars().all())
        fpa_count = len((await session.execute(
            select(FloorPlanAnalysis).join(FloorPlan, FloorPlanAnalysis.floor_plan_id == FloorPlan.id).where(FloorPlan.home_id == hid)
        )).scalars().all())
        ri_count = len((await session.execute(select(RoomImage).join(Room, RoomImage.room_id == Room.id).where(Room.home_id == hid))).scalars().all())
        ia_count = len((await session.execute(
            select(ImageAnalysis).join(RoomImage, ImageAnalysis.room_image_id == RoomImage.id).join(Room, RoomImage.room_id == Room.id).where(Room.home_id == hid)
        )).scalars().all())

        print({
            'home_id': twin.get('home_id'),
            'total_rooms': twin.get('total_rooms'),
            'total_images': twin.get('total_images'),
            'floor_plans': fp_count,
            'floor_plan_analyses': fpa_count,
            'room_images': ri_count,
            'image_analyses': ia_count,
        })

if __name__ == '__main__':
    asyncio.run(main())
