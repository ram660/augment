import uuid
from sqlalchemy import select

from backend.models.base import init_db_async, AsyncSessionLocal
from backend.models.home import Home
from backend.models.user import User
from backend.models.analysis import FloorPlanAnalysis
from backend.models.home import FloorPlan, Room
from backend.services.digital_twin_service import DigitalTwinService


class DummyFloorPlanAgent:
    async def execute(self, inputs):
        data = {
            "multi_floor": True,
            "floors": [
                {
                    "floor_level_number": 1,
                    "floor_level_name": "main",
                    "units": {"scale_text": "1/4 = 1'-0\""},
                    "pixel_to_unit": 0.5,
                    "section_bbox": [0, 0, 100, 100],
                    "layout_analysis": {"total_area_sqft": 1000, "layout_type": "open_concept"},
                    "rooms": [
                        {"name": "Living Room", "room_type": "living_room", "dimensions": {"area_sqft": 300}},
                        {"name": "Kitchen", "room_type": "kitchen", "dimensions": {"area_sqft": 150}},
                    ],
                    "confidence_metrics": {"overall_confidence": 0.9},
                },
                {
                    "floor_level_number": 2,
                    "floor_level_name": "second",
                    "units": {"scale_text": "1/4 = 1'-0\""},
                    "pixel_to_unit": 0.5,
                    "section_bbox": [0, 100, 100, 200],
                    "detected_rooms": [
                        {"name": "Bedroom", "room_type": "bedroom", "dimensions": {"area_sqft": 200}},
                    ],
                    "confidence_metrics": {"overall_confidence": 0.85},
                },
            ],
        }

        class Resp:
            def __init__(self, d):
                self.success = True
                self.error = None
                self.data = d

        return Resp(data)


def test_multifloor_split_and_persist():
    import asyncio

    async def _run():
        # Ensure tables exist
        await init_db_async()

        async with AsyncSessionLocal() as db:
            # Create a user and a home via ORM for convenience
            user = User(email=f"mf_{uuid.uuid4().hex[:8]}@test.local", user_type="homeowner")
            db.add(user)
            await db.flush()  # populate user.id

            home = Home(
                owner_id=user.id,
                name="MultiFloor Home",
                address={},
                home_type="single_family",
            )
            db.add(home)
            await db.commit()

            svc = DigitalTwinService()
            svc.floor_plan_agent = DummyFloorPlanAgent()  # stub out AI dependency

            result = await svc.analyze_and_save_floor_plan(
                db,
                home_id=home.id,
                image_path="uploads/floor_plans/analysis/test.png",
                floor_level=1,
                scale=None,
                name="Test Sheet",
            )

            # Should return multiple floor_plan_ids and a sheet_id
            assert "floor_plan_ids" in result
            assert len(result["floor_plan_ids"]) == 2
            assert result.get("sheet_id") is not None

            # Verify FloorPlan rows
            fps = (await db.execute(select(FloorPlan).where(FloorPlan.home_id == home.id))).scalars().all()
            assert len(fps) == 2
            # Each analysis_metadata should include sheet_id and section_index
            for idx, fp in enumerate(sorted(fps, key=lambda f: f.floor_level)):
                assert isinstance(fp.analysis_metadata, dict)
                assert "sheet_id" in fp.analysis_metadata
                assert fp.analysis_metadata.get("section_index") in (0, 1)

            # Verify FloorPlanAnalysis per floor with scale_info populated
            fpas = (
                await db.execute(select(FloorPlanAnalysis).where(FloorPlanAnalysis.floor_plan_id.in_([fp.id for fp in fps])))
            ).scalars().all()
            assert len(fpas) == 2
            for a in fpas:
                assert isinstance(a.scale_info, dict)
                assert "units" in a.scale_info
                assert "section_bbox" in a.scale_info

            # Verify Rooms persisted with correct floor levels (2 on level 1, 1 on level 2)
            rooms = (await db.execute(select(Room).where(Room.home_id == home.id))).scalars().all()
            assert len(rooms) == 3
            level_counts = {}
            for r in rooms:
                level_counts[r.floor_level] = level_counts.get(r.floor_level, 0) + 1
            assert level_counts.get(1) == 2
            assert level_counts.get(2) == 1

    asyncio.run(_run())
