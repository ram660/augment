"""
Test chat workflow integration with image uploads and journey persistence.

Tests that images uploaded during chat are automatically attached to the current journey step.
"""
import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.workflows.chat_workflow import ChatWorkflow
from backend.services.journey_persistence_service import JourneyPersistenceService


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


@pytest.mark.asyncio
async def test_image_upload_attaches_to_active_journey_step(test_db):
    """Test that images uploaded during chat are attached to the current journey step."""
    
    # Generate a valid UUID for user_id
    user_id = str(uuid.uuid4())
    
    # Create a journey first
    service = JourneyPersistenceService(test_db)
    journey = await service.create_journey(
        user_id=user_id,
        template_id="kitchen_renovation"
    )
    journey_id = str(journey.id)
    
    # Get the first step
    first_step = journey.steps[0] if journey.steps else None
    assert first_step is not None
    
    # Create chat workflow
    workflow = ChatWorkflow(test_db)
    
    # Simulate image upload with attachment
    attachments = [
        {
            "filename": "kitchen_before.jpg",
            "content_type": "image/jpeg",
            "path": "/uploads/chat/test/kitchen_before.jpg",
            "url": "/uploads/chat/test/kitchen_before.jpg",
            "type": "image",
            "file_size": 1024000,
            "label": "Before photo of kitchen",
            "analysis": {
                "description": "Modern kitchen with white cabinets",
                "styles": ["modern", "minimalist"],
                "colors": [{"name": "white"}, {"name": "gray"}]
            }
        }
    ]
    
    # Execute workflow with image attachment
    result = await workflow.execute({
        "user_message": "Here's a photo of my current kitchen",
        "user_id": user_id,
        "conversation_id": None,
        "mode": "agent",
        "attachments": attachments
    })
    
    # Verify the workflow tracked the journey
    assert result.get("journey_id") == journey_id
    
    # Get the journey again and check if image was attached
    updated_journey = await service.get_journey(journey_id)
    assert updated_journey is not None
    
    # Check if the first step has the image
    updated_first_step = next(
        (step for step in updated_journey.steps if step.id == first_step.id),
        None
    )
    assert updated_first_step is not None
    assert len(updated_first_step.images) == 1
    
    # Verify image details
    image = updated_first_step.images[0]
    assert image.filename == "kitchen_before.jpg"
    assert image.content_type == "image/jpeg"
    assert image.image_type == "user_upload"
    assert image.label == "User uploaded image"
    assert image.metadata.get("description") == "Modern kitchen with white cabinets"


@pytest.mark.asyncio
async def test_multiple_images_attach_to_same_step(test_db):
    """Test that multiple images uploaded in one message attach to the same step."""
    
    user_id = str(uuid.uuid4())
    
    # Create a journey
    service = JourneyPersistenceService(test_db)
    journey = await service.create_journey(
        user_id=user_id,
        template_id="bathroom_upgrade"
    )
    
    # Create workflow
    workflow = ChatWorkflow(test_db)
    
    # Simulate multiple image uploads
    attachments = [
        {
            "filename": f"bathroom_{i}.jpg",
            "content_type": "image/jpeg",
            "path": f"/uploads/chat/test/bathroom_{i}.jpg",
            "url": f"/uploads/chat/test/bathroom_{i}.jpg",
            "type": "image",
            "file_size": 1024000 + i * 1000,
        }
        for i in range(3)
    ]
    
    # Execute workflow
    result = await workflow.execute({
        "user_message": "Here are three photos of my bathroom",
        "user_id": user_id,
        "conversation_id": None,
        "mode": "agent",
        "attachments": attachments
    })
    
    # Get the journey and verify all images attached
    updated_journey = await service.get_journey(str(journey.id))
    first_step = updated_journey.steps[0]
    
    assert len(first_step.images) == 3
    assert all(img.image_type == "user_upload" for img in first_step.images)


@pytest.mark.asyncio
async def test_image_upload_without_journey_does_not_fail(test_db):
    """Test that image uploads work even when there's no active journey."""
    
    user_id = str(uuid.uuid4())
    
    # Create workflow (no journey created)
    workflow = ChatWorkflow(test_db)
    
    # Simulate image upload
    attachments = [
        {
            "filename": "random_image.jpg",
            "content_type": "image/jpeg",
            "path": "/uploads/chat/test/random_image.jpg",
            "url": "/uploads/chat/test/random_image.jpg",
            "type": "image",
            "file_size": 1024000,
        }
    ]
    
    # Execute workflow - should not fail
    result = await workflow.execute({
        "user_message": "Here's a random image",
        "user_id": user_id,
        "conversation_id": None,
        "mode": "agent",
        "attachments": attachments
    })
    
    # Workflow should complete successfully
    assert result.get("status") != "failed"
    # No journey should be created for random images
    assert result.get("journey_id") is None


@pytest.mark.asyncio
async def test_pdf_attachment_does_not_attach_to_journey(test_db):
    """Test that PDF attachments are not attached to journey steps (only images)."""
    
    user_id = str(uuid.uuid4())
    
    # Create a journey
    service = JourneyPersistenceService(test_db)
    journey = await service.create_journey(
        user_id=user_id,
        template_id="kitchen_renovation"
    )
    
    # Create workflow
    workflow = ChatWorkflow(test_db)
    
    # Simulate PDF upload (not an image)
    attachments = [
        {
            "filename": "contractor_quote.pdf",
            "content_type": "application/pdf",
            "path": "/uploads/chat/test/contractor_quote.pdf",
            "url": "/uploads/chat/test/contractor_quote.pdf",
            "type": "pdf",
            "file_size": 2048000,
        }
    ]
    
    # Execute workflow
    result = await workflow.execute({
        "user_message": "Here's the contractor quote",
        "user_id": user_id,
        "conversation_id": None,
        "mode": "agent",
        "attachments": attachments
    })
    
    # Get the journey and verify no images attached (PDF should be ignored)
    updated_journey = await service.get_journey(str(journey.id))
    first_step = updated_journey.steps[0]
    
    assert len(first_step.images) == 0


@pytest.mark.asyncio
async def test_image_analysis_metadata_saved_to_journey(test_db):
    """Test that image analysis metadata is saved to the journey image."""
    
    user_id = str(uuid.uuid4())
    
    # Create a journey
    service = JourneyPersistenceService(test_db)
    journey = await service.create_journey(
        user_id=user_id,
        template_id="kitchen_renovation"
    )
    
    # Create workflow
    workflow = ChatWorkflow(test_db)
    
    # Simulate image upload with rich analysis
    attachments = [
        {
            "filename": "kitchen_design.jpg",
            "content_type": "image/jpeg",
            "path": "/uploads/chat/test/kitchen_design.jpg",
            "url": "/uploads/chat/test/kitchen_design.jpg",
            "type": "image",
            "file_size": 1024000,
            "analysis": {
                "description": "Contemporary kitchen with stainless steel appliances",
                "styles": ["contemporary", "industrial"],
                "colors": [
                    {"name": "stainless steel", "hex": "#C0C0C0"},
                    {"name": "black", "hex": "#000000"}
                ],
                "materials": ["stainless steel", "granite", "wood"],
                "fixtures": ["range hood", "sink", "faucet"],
                "confidence": 0.95
            }
        }
    ]
    
    # Execute workflow
    result = await workflow.execute({
        "user_message": "What do you think of this kitchen design?",
        "user_id": user_id,
        "conversation_id": None,
        "mode": "agent",
        "attachments": attachments
    })
    
    # Get the journey and verify analysis metadata
    updated_journey = await service.get_journey(str(journey.id))
    first_step = updated_journey.steps[0]
    
    assert len(first_step.images) == 1
    image = first_step.images[0]
    
    # Verify analysis metadata was saved
    assert image.metadata is not None
    assert image.metadata.get("description") == "Contemporary kitchen with stainless steel appliances"
    assert "contemporary" in image.metadata.get("styles", [])
    assert len(image.metadata.get("materials", [])) == 3
    assert image.metadata.get("confidence") == 0.95

