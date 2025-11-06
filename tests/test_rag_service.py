import asyncio
import uuid
import pytest

from backend.models.base import init_db_async, AsyncSessionLocal
from backend.models.user import User, UserType
from backend.models.home import Home, HomeType, Room, RoomType, RoomImage
from backend.models.analysis import ImageAnalysis, FloorPlan, FloorPlanAnalysis
from backend.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_rag_build_and_query():
    await init_db_async()

    async with AsyncSessionLocal() as db:
        # Ensure minimal seed data
        u = User(email=f"test_{uuid.uuid4()}@example.com", user_type=UserType.HOMEOWNER)
        db.add(u)
        await db.flush()

        h = Home(owner_id=u.id, name="Test Home", address={}, home_type=HomeType.SINGLE_FAMILY, num_floors=2)
        db.add(h)
        await db.flush()

        # Room
        r = Room(home_id=h.id, name="Kitchen", room_type=RoomType.KITCHEN, floor_level=2)
        db.add(r)
        await db.flush()

        # Image + Analysis
        ri = RoomImage(room_id=r.id, image_url="uploads/room_images/kitchen1.jpg", image_type="original")
        db.add(ri)
        await db.flush()

        ia = ImageAnalysis(
            room_image_id=ri.id,
            description="A modern kitchen with white cabinets and a center island.",
            keywords=["kitchen", "modern", "island"],
            dominant_colors=["white", "gray"],
            objects_detected=[{"label": "cabinet"}, {"label": "island"}],
            materials_visible=[{"material_type": "granite"}],
            fixtures_visible=[{"fixture_type": "faucet"}],
        )
        db.add(ia)

        # Floor plan + analysis
        fp = FloorPlan(home_id=h.id, name="Main Plan", floor_level=2, image_url="uploads/floor_plans/floor2.png")
        db.add(fp)
        await db.flush()
        fpa = FloorPlanAnalysis(floor_plan_id=fp.id, detected_rooms=[{"room_type": "kitchen"}], layout_type="open_concept")
        db.add(fpa)

        await db.commit()

        # Build index
        svc = RAGService()
        res = await svc.build_index(db, home_id=str(h.id))
        assert res["documents"] >= 1
        assert res["chunks"] >= 1

        # Query
        q = await svc.query(db, query="kitchen island on floor 2", home_id=str(h.id), k=5)
        assert "matches" in q
        assert len(q["matches"]) >= 1
        # Top result should be related to image analysis or room
        assert any(m["source_type"] in ("image_analysis", "room", "floor_plan") for m in q["matches"]) 
