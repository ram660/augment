import asyncio
import uuid
from datetime import datetime

from sqlalchemy import text

from backend.models.base import init_db_async, AsyncSessionLocal
from backend.models.user import User
from backend.models.home import Home
from backend.services.digital_twin_service import DigitalTwinService


def test_room_type_sanitizer_coerces_invalid_enum_value():
    async def _run():
        # Ensure tables exist
        await init_db_async()

        # Create minimal User and Home, then insert a Room with an invalid room_type via raw SQL
        async with AsyncSessionLocal() as db:
            user_id = None
            home_id = None
            room_id = uuid.uuid4()
            # Create user and home via ORM to satisfy timestamp defaults
            user = User(email=f"sanitizer_{uuid.uuid4().hex[:8]}@test.local", user_type="homeowner")
            db.add(user)
            await db.flush()
            user_id = user.id

            home = Home(owner_id=user_id, name="Sanitizer Home", address={}, home_type="single_family")
            db.add(home)
            await db.flush()
            home_id = home.id

            # Insert a room with an invalid enum value for room_type
            now = datetime.utcnow().isoformat(sep=" ")
            await db.execute(
                text(
                    """
                    INSERT INTO rooms (id, home_id, name, room_type, floor_level, created_at, updated_at)
                    VALUES (:id, :home_id, :name, :room_type, :floor_level, :created_at, :updated_at)
                    """
                ),
                {
                    "id": str(room_id),
                    "home_id": str(home_id),
                    "name": "Flex Space",
                    "room_type": "flex_room",  # invalid value not in enum
                    "floor_level": 1,
                    "created_at": now,
                    "updated_at": now,
                },
            )

            await db.commit()

            # Run sanitizer
            svc = DigitalTwinService()
            await svc._sanitize_room_types(db, home_id)

            # Verify the room_type is coerced to 'other'
            res = await db.execute(text("SELECT room_type FROM rooms WHERE id = :id"), {"id": str(room_id)})
            sanitized_value = res.scalar_one()
            assert sanitized_value == "other"

    asyncio.run(_run())
