"""
Test chat workflow integration with journey persistence.

Tests that chat workflow properly creates and tracks journeys in the database.
"""
import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base, get_async_db
from backend.workflows.chat_workflow import ChatWorkflow


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_db():
    """Create a test database."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_client(test_db):
    """Create an async test client."""
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_async_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_workflow_creates_journey_on_kitchen_renovation(test_db):
    """Test that chat workflow creates a journey when user mentions kitchen renovation."""

    # Generate a valid UUID for user_id
    user_id = str(uuid.uuid4())

    # Create chat workflow
    workflow = ChatWorkflow(test_db)

    # Execute workflow with kitchen renovation message
    result = await workflow.execute({
        "user_message": "I want to renovate my kitchen",
        "user_id": user_id,
        "conversation_id": None,
        "mode": "agent"
    })

    # Check that workflow completed successfully
    assert result.get("status") != "failed"

    # Check that journey was created
    journey_id = result.get("journey_id")
    assert journey_id is not None

    # Verify journey exists in database
    from backend.services.journey_persistence_service import JourneyPersistenceService
    service = JourneyPersistenceService(test_db)

    journey = await service.get_journey(journey_id)
    assert journey is not None
    assert journey.template_id == "kitchen_renovation"
    assert journey.status.value == "in_progress"
    assert str(journey.user_id) == user_id


@pytest.mark.asyncio
async def test_chat_workflow_tracks_existing_journey(test_db):
    """Test that chat workflow tracks progress on existing journey."""

    # Generate a valid UUID for user_id
    user_id = str(uuid.uuid4())

    # First, create a journey
    from backend.services.journey_persistence_service import JourneyPersistenceService
    service = JourneyPersistenceService(test_db)

    journey = await service.create_journey(
        user_id=user_id,
        template_id="kitchen_renovation"
    )
    journey_id = str(journey.id)

    # Create chat workflow
    workflow = ChatWorkflow(test_db)

    # Send a chat message from the same user
    result = await workflow.execute({
        "user_message": "What's the next step?",
        "user_id": user_id,
        "conversation_id": None,
        "mode": "agent"
    })

    # Verify the workflow tracked the existing journey
    assert result.get("journey_id") == journey_id
    assert result.get("journey_status") == "in_progress"
    assert result.get("current_step") is not None


@pytest.mark.asyncio
async def test_chat_workflow_updates_journey_last_activity(test_db):
    """Test that chat messages update journey's last_activity_at timestamp."""

    # Generate a valid UUID for user_id
    user_id = str(uuid.uuid4())

    # Create a journey
    from backend.services.journey_persistence_service import JourneyPersistenceService
    service = JourneyPersistenceService(test_db)

    journey = await service.create_journey(
        user_id=user_id,
        template_id="bathroom_upgrade"
    )
    journey_id = str(journey.id)
    original_last_activity = journey.last_activity_at

    # Wait a moment
    import asyncio
    await asyncio.sleep(0.1)

    # Create chat workflow and send a message
    workflow = ChatWorkflow(test_db)
    result = await workflow.execute({
        "user_message": "Show me design options",
        "user_id": user_id,
        "conversation_id": None,
        "mode": "agent"
    })

    # Get the journey again and check last_activity_at was updated
    updated_journey = await service.get_journey(journey_id)

    # The timestamp should be different (updated)
    assert updated_journey.last_activity_at >= original_last_activity


@pytest.mark.asyncio
async def test_chat_workflow_bathroom_renovation_detection(test_db):
    """Test that chat workflow detects bathroom renovation intent."""

    # Generate a valid UUID for user_id
    user_id = str(uuid.uuid4())

    # Create chat workflow
    workflow = ChatWorkflow(test_db)

    # Execute workflow with bathroom renovation message
    result = await workflow.execute({
        "user_message": "I want to upgrade my bathroom",
        "user_id": user_id,
        "conversation_id": None,
        "mode": "agent"
    })

    # Check that journey was created
    journey_id = result.get("journey_id")
    assert journey_id is not None

    # Verify journey template
    from backend.services.journey_persistence_service import JourneyPersistenceService
    service = JourneyPersistenceService(test_db)

    journey = await service.get_journey(journey_id)
    assert journey.template_id == "bathroom_upgrade"


@pytest.mark.asyncio
async def test_multiple_users_separate_journeys(test_db):
    """Test that different users have separate journeys."""

    # Generate valid UUIDs for user_ids
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())

    from backend.services.journey_persistence_service import JourneyPersistenceService
    service = JourneyPersistenceService(test_db)

    # User 1 starts a kitchen renovation
    journey1 = await service.create_journey(
        user_id=user1_id,
        template_id="kitchen_renovation"
    )

    # User 2 starts a bathroom upgrade
    journey2 = await service.create_journey(
        user_id=user2_id,
        template_id="bathroom_upgrade"
    )

    # Get journeys for each user
    user1_journeys = await service.get_user_journeys(user_id=user1_id)
    user2_journeys = await service.get_user_journeys(user_id=user2_id)

    # Each user should have their own journeys
    user1_journey_ids = [str(j.id) for j in user1_journeys]
    user2_journey_ids = [str(j.id) for j in user2_journeys]

    # Journey IDs should be different
    assert str(journey1.id) in user1_journey_ids
    assert str(journey2.id) in user2_journey_ids
    assert set(user1_journey_ids).isdisjoint(set(user2_journey_ids))

