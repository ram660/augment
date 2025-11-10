"""
Comprehensive tests for Journey API endpoints.
Tests all CRUD operations, image uploads, and journey progression.
"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.models.journey import Journey, JourneyStep, JourneyImage, JourneyStatus, StepStatus
from backend.models.base import get_async_db


@pytest_asyncio.fixture
async def test_user_id():
    """Generate a test user ID."""
    return str(uuid.uuid4())


@pytest_asyncio.fixture
async def test_journey_data(test_user_id):
    """Generate test journey creation data."""
    return {
        "user_id": test_user_id,
        "template_id": "kitchen_renovation",
        "home_id": None,
        "conversation_id": None
    }


@pytest_asyncio.fixture
async def async_client():
    """Create an async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_journey(async_client, test_journey_data):
    """Test creating a new journey from template."""
    response = await async_client.post(
        "/api/v1/journey/start",
        json=test_journey_data
    )

    assert response.status_code == 200
    data = response.json()

    # Verify journey structure
    assert "id" in data
    assert data["user_id"] == test_journey_data["user_id"]
    assert data["template_id"] == "kitchen_renovation"
    assert data["status"] == "in_progress"  # Journey starts in progress
    assert data["progress_percentage"] == 0.0
    assert "steps" in data
    assert len(data["steps"]) > 0

    # Verify first step
    first_step = data["steps"][0]
    assert first_step["step_number"] == 1
    assert first_step["status"] == "in_progress"  # First step starts in progress

    return data["id"]


@pytest.mark.asyncio
async def test_get_journey(async_client, test_journey_data):
    """Test retrieving a journey by ID."""
    # Create journey first
    create_response = await async_client.post(
        "/api/v1/journey/start",
        json=test_journey_data
    )
    journey_id = create_response.json()["id"]

    # Get journey
    response = await async_client.get(f"/api/v1/journey/{journey_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == journey_id
    assert "steps" in data


@pytest.mark.asyncio
async def test_get_journey_with_images(async_client, test_journey_data):
    """Test retrieving a journey with images included."""
    # Create journey
    create_response = await async_client.post(
        "/api/v1/journey/start",
        json=test_journey_data
    )
    journey_id = create_response.json()["id"]

    # Get journey with images
    response = await async_client.get(
        f"/api/v1/journey/{journey_id}",
        params={"include_images": True}
    )

    assert response.status_code == 200
    data = response.json()
    assert "steps" in data
    for step in data["steps"]:
        assert "images" in step


@pytest.mark.asyncio
async def test_get_user_journeys(async_client, test_journey_data):
    """Test retrieving all journeys for a user."""
    # Create multiple journeys
    journey_ids = []
    for _ in range(3):
        response = await async_client.post(
            "/api/v1/journey/start",
            json=test_journey_data
        )
        journey_ids.append(response.json()["id"])

    # Get all user journeys
    response = await async_client.get(
        f"/api/v1/journey/user/{test_journey_data['user_id']}"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    assert all(j["user_id"] == test_journey_data["user_id"] for j in data)


@pytest.mark.asyncio
async def test_filter_user_journeys_by_status(async_client, test_journey_data):
    """Test filtering user journeys by status."""
    # Create journey
    create_response = await async_client.post(
        "/api/v1/journey/start",
        json=test_journey_data
    )
    journey_id = create_response.json()["id"]

    # Get journeys with status filter
    response = await async_client.get(
        f"/api/v1/journey/user/{test_journey_data['user_id']}",
        params={"status": "in_progress"}
    )

    assert response.status_code == 200
    data = response.json()
    assert all(j["status"] == "in_progress" for j in data)


@pytest.mark.asyncio
async def test_update_step_status(async_client, test_journey_data):
    """Test updating a step's status."""
    # Create journey
    create_response = await async_client.post(
        "/api/v1/journey/start",
        json=test_journey_data
    )
    journey_data = create_response.json()
    journey_id = journey_data["id"]
    first_step = journey_data["steps"][0]
    step_id = first_step["id"]

    # Update step status
    update_data = {
        "status": "in_progress",
        "progress": 50.0
    }
    response = await async_client.put(
        f"/api/v1/journey/{journey_id}/steps/{step_id}",
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["progress_percentage"] == 50.0


@pytest.mark.asyncio
async def test_complete_step_advances_journey(async_client, test_journey_data):
    """Test that completing a step advances the journey."""
    # Create journey
    create_response = await async_client.post(
        "/api/v1/journey/start",
        json=test_journey_data
    )
    journey_data = create_response.json()
    journey_id = journey_data["id"]
    first_step = journey_data["steps"][0]
    step_id = first_step["id"]

    # Complete first step
    update_data = {
        "status": "completed",
        "progress": 100.0
    }
    await async_client.put(
        f"/api/v1/journey/{journey_id}/steps/{step_id}",
        json=update_data
    )

    # Get journey and verify progress
    response = await async_client.get(f"/api/v1/journey/{journey_id}")
    data = response.json()

    assert data["completed_steps"] == 1
    assert data["progress_percentage"] > 0
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_step_with_data(async_client, test_journey_data):
    """Test updating a step with custom data."""
    # Create journey
    create_response = await async_client.post(
        "/api/v1/journey/start",
        json=test_journey_data
    )
    journey_data = create_response.json()
    journey_id = journey_data["id"]
    step_id = journey_data["steps"][0]["id"]

    # Update step with data
    custom_data = {
        "room_dimensions": {"length": 12, "width": 10},
        "style_preference": "modern",
        "budget": 15000
    }
    update_data = {
        "status": "in_progress",
        "data": custom_data
    }
    response = await async_client.put(
        f"/api/v1/journey/{journey_id}/steps/{step_id}",
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["step_data"] == custom_data


@pytest.mark.asyncio
async def test_upload_step_image(async_client, test_journey_data):
    """Test uploading an image to a step."""
    # Create journey
    create_response = await async_client.post(
        "/api/v1/journey/start",
        json=test_journey_data
    )
    journey_data = create_response.json()
    journey_id = journey_data["id"]
    step_id = journey_data["steps"][0]["id"]

    # Create a test image file
    test_image_content = b"fake image content"
    files = {
        "file": ("test_kitchen.jpg", test_image_content, "image/jpeg")
    }
    data = {
        "label": "Current kitchen state",
        "image_type": "before"
    }

    response = await async_client.post(
        f"/api/v1/journey/{journey_id}/steps/{step_id}/images",
        files=files,
        data=data
    )

    assert response.status_code == 200
    image_data = response.json()
    assert image_data["filename"] == "test_kitchen.jpg"
    assert image_data["label"] == "Current kitchen state"
    assert image_data["image_type"] == "before"


@pytest.mark.asyncio
async def test_get_journey_images(async_client, test_journey_data):
    """Test retrieving all images for a journey."""
    # Create journey
    create_response = await async_client.post(
        "/api/v1/journey/start",
        json=test_journey_data
    )
    journey_id = create_response.json()["id"]

    # Get images (should be empty initially)
    response = await async_client.get(f"/api/v1/journey/{journey_id}/images")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_journey_not_found(async_client, test_journey_data):
    """Test getting a non-existent journey returns 404."""
    fake_id = str(uuid.uuid4())
    response = await async_client.get(f"/api/v1/journey/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_template_id(async_client, test_journey_data):
    """Test creating journey with invalid template returns error."""
    invalid_data = test_journey_data.copy()
    invalid_data["template_id"] = "invalid_template"

    response = await async_client.post(
        "/api/v1/journey/start",
        json=invalid_data
    )

    assert response.status_code in [400, 404]

