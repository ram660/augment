import uuid
from typing import AsyncGenerator, List

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.models.memory import UserMemory
from backend.services.memory_service import MemoryService


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory async DB session for memory service tests."""

    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.mark.asyncio
async def test_add_and_get_memories_for_user(test_db: AsyncSession) -> None:
    service = MemoryService(test_db)

    user_id = str(uuid.uuid4())

    # Insert two memories under different topics
    await service.add_or_update_memory(
        user_id=user_id,
        home_id=None,
        conversation_id=None,
        topic="design_preferences",
        key="style",
        value={"description": "Scandinavian, light wood, white walls"},
        source="chat",
        confidence=0.95,
    )

    await service.add_or_update_memory(
        user_id=user_id,
        home_id=None,
        conversation_id=None,
        topic="budget",
        key="max_budget_cad",
        value={"amount": 50000, "currency": "CAD"},
        source="chat",
        confidence=0.9,
    )

    memories: List[UserMemory] = await service.get_memories_for_user(user_id=user_id)

    assert len(memories) == 2
    topics = {m.topic for m in memories}
    assert {"design_preferences", "budget"} == topics


@pytest.mark.asyncio
async def test_add_or_update_memory_upserts_by_topic_and_key(test_db: AsyncSession) -> None:
    service = MemoryService(test_db)

    user_id = str(uuid.uuid4())

    first = await service.add_or_update_memory(
        user_id=user_id,
        home_id=None,
        conversation_id=None,
        topic="design_preferences",
        key="style",
        value={"description": "Modern"},
        source="chat",
        confidence=0.8,
    )

    # Update same logical fact with richer details
    updated = await service.add_or_update_memory(
        user_id=user_id,
        home_id=None,
        conversation_id=None,
        topic="design_preferences",
        key="style",
        value={"description": "Modern coastal with light oak"},
        source="design_studio",
        confidence=0.95,
    )

    assert first.id == updated.id  # Upsert, so same row
    assert updated.value["description"].startswith("Modern coastal")
    assert updated.source == "design_studio"
    assert pytest.approx(updated.confidence, rel=1e-6) == 0.95


@pytest.mark.asyncio
async def test_to_prompt_rows_is_compact_and_includes_fields(test_db: AsyncSession) -> None:
    service = MemoryService(test_db)

    user_id = str(uuid.uuid4())

    mem = await service.add_or_update_memory(
        user_id=user_id,
        home_id=None,
        conversation_id=None,
        topic="home_constraints",
        key="ceiling_height",
        value={"description": "Low 7'6\" basement ceiling"},
        source="chat",
        confidence=0.88,
    )

    rows = MemoryService.to_prompt_rows([mem])

    assert len(rows) == 1
    row = rows[0]
    assert row["topic"] == "home_constraints"
    assert row["key"] == "ceiling_height"
    assert row["value"]["description"].startswith("Low 7'6")
    assert row["source"] == "chat"
    assert row["confidence"] == pytest.approx(0.88, rel=1e-6)

