"""
Journey API endpoints.

Provides REST API for journey management, step updates, and image uploads.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_async_db
from backend.services.journey_persistence_service import JourneyPersistenceService
from backend.models.journey import JourneyStatus, StepStatus
import os
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/journey", tags=["journey"])


# Request/Response Models

class CreateJourneyRequest(BaseModel):
    """Request to create a new journey."""
    user_id: str
    template_id: str
    home_id: Optional[str] = None
    conversation_id: Optional[str] = None
    title: Optional[str] = None


class UpdateStepRequest(BaseModel):
    """Request to update a journey step."""
    status: Optional[str] = None
    progress: Optional[float] = Field(None, ge=0, le=100)
    data: Optional[dict] = None


class JourneyResponse(BaseModel):
    """Journey response."""
    id: str
    user_id: str
    home_id: Optional[str]
    conversation_id: Optional[str]
    template_id: str
    title: str
    description: Optional[str]
    status: str
    current_step_id: Optional[str]
    completed_steps: int
    total_steps: int
    progress_percentage: float
    started_at: Optional[str]
    completed_at: Optional[str]
    last_activity_at: Optional[str]
    estimated_completion_date: Optional[str]
    metadata: dict
    collected_data: dict
    created_at: str
    updated_at: str
    steps: Optional[List[dict]] = None


class StepResponse(BaseModel):
    """Step response."""
    id: str
    journey_id: str
    step_id: str
    step_number: int
    name: str
    description: Optional[str]
    required: bool
    estimated_duration_minutes: int
    depends_on: List[str]
    required_actions: List[str]
    status: str
    progress_percentage: float
    started_at: Optional[str]
    completed_at: Optional[str]
    step_data: dict
    sub_steps: List[dict]
    created_at: str
    updated_at: str


class ImageResponse(BaseModel):
    """Image response."""
    id: str
    journey_id: str
    step_id: str
    filename: str
    url: str
    thumbnail_url: Optional[str]
    content_type: str
    file_size: int
    width: Optional[int]
    height: Optional[int]
    is_generated: bool
    image_type: Optional[str]
    analysis: dict
    label: Optional[str]
    notes: Optional[str]
    tags: List[str]
    display_order: int
    created_at: str


class UpdateImageRequest(BaseModel):
    """Request to update image metadata."""
    label: Optional[str] = None
    image_type: Optional[str] = None
    metadata: Optional[dict] = None


class ReorderImagesRequest(BaseModel):
    """Request to reorder images within a step."""
    image_ids: List[str] = Field(..., description="Ordered list of image IDs")


class BulkDeleteImagesRequest(BaseModel):
    """Request to delete multiple images."""
    image_ids: List[str] = Field(..., description="List of image IDs to delete")


class BulkImageUploadResponse(BaseModel):
    """Response for bulk image upload."""
    success_count: int
    failed_count: int
    images: List[ImageResponse]
    errors: List[dict]


class BulkDeleteResponse(BaseModel):
    """Response for bulk delete."""
    success_count: int
    failed_count: int
    deleted_ids: List[str]
    errors: List[dict]


class ImageGalleryResponse(BaseModel):
    """Response for image gallery."""
    journey_id: str
    total_images: int
    images: List[ImageResponse]


# Endpoints

@router.post("/start", response_model=JourneyResponse)
async def start_journey(
    request: CreateJourneyRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Start a new journey.

    Creates a new journey instance from a template and initializes all steps.
    """
    try:
        service = JourneyPersistenceService(db)
        journey = await service.create_journey(
            user_id=request.user_id,
            template_id=request.template_id,
            home_id=request.home_id,
            conversation_id=request.conversation_id,
            title=request.title,
        )

        # Build response with steps
        response_data = journey.to_dict()
        response_data["steps"] = [step.to_dict() for step in journey.steps]

        return JourneyResponse(**response_data)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting journey: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start journey")


@router.get("/{journey_id}", response_model=JourneyResponse)
async def get_journey(
    journey_id: str,
    include_steps: bool = True,
    include_images: bool = False,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get journey by ID.
    
    Returns journey details with optional steps and images.
    """
    try:
        service = JourneyPersistenceService(db)
        journey = await service.get_journey(journey_id, include_steps, include_images)
        
        if not journey:
            raise HTTPException(status_code=404, detail="Journey not found")
        
        response_data = journey.to_dict()
        
        if include_steps:
            response_data["steps"] = [step.to_dict() for step in journey.steps]
            
            if include_images:
                for step_dict in response_data["steps"]:
                    step_obj = next((s for s in journey.steps if str(s.id) == step_dict["id"]), None)
                    if step_obj:
                        step_dict["images"] = [img.to_dict() for img in step_obj.images]
        
        return JourneyResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting journey: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get journey")


@router.get("/user/{user_id}", response_model=List[JourneyResponse])
async def get_user_journeys(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all journeys for a user.
    
    Returns list of journeys with optional status filter.
    """
    try:
        service = JourneyPersistenceService(db)
        
        status_enum = None
        if status:
            try:
                status_enum = JourneyStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        journeys = await service.get_user_journeys(user_id, status_enum, limit, offset)

        # Build response with steps for each journey
        result = []
        for journey in journeys:
            response_data = journey.to_dict()
            response_data["steps"] = [step.to_dict() for step in journey.steps]
            result.append(JourneyResponse(**response_data))

        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user journeys: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get user journeys")


@router.put("/{journey_id}/steps/{step_id}", response_model=StepResponse)
async def update_step(
    journey_id: str,
    step_id: str,
    request: UpdateStepRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a journey step.
    
    Updates step status, progress, and data.
    """
    try:
        service = JourneyPersistenceService(db)
        
        status_enum = None
        if request.status:
            try:
                status_enum = StepStatus(request.status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
        
        step = await service.update_step(
            journey_id=journey_id,
            step_id=step_id,
            status=status_enum,
            progress=request.progress,
            data=request.data,
        )
        
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")
        
        return StepResponse(**step.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating step: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update step")


@router.post("/{journey_id}/steps/{step_id}/images", response_model=ImageResponse)
async def upload_step_image(
    journey_id: str,
    step_id: str,
    file: UploadFile = File(...),
    image_type: Optional[str] = Form(None),
    label: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Upload an image to a journey step.
    
    Saves the image and optionally runs AI analysis.
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique filename
        ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        # Save file
        upload_dir = f"uploads/journeys/{journey_id}/{step_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_size = len(content)
        
        # Generate URL (adjust based on your setup)
        url = f"/uploads/journeys/{journey_id}/{step_id}/{unique_filename}"
        
        # Add to database
        service = JourneyPersistenceService(db)
        image = await service.add_image(
            journey_id=journey_id,
            step_id=step_id,
            filename=file.filename or unique_filename,
            file_path=file_path,
            url=url,
            content_type=file.content_type,
            file_size=file_size,
            is_generated=False,
            image_type=image_type,
            label=label,
        )
        
        # TODO: Run AI analysis asynchronously
        
        return ImageResponse(**image.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload image")


@router.get("/{journey_id}/images", response_model=ImageGalleryResponse)
async def get_journey_images(
    journey_id: str,
    step_id: Optional[str] = None,
    image_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all images for a journey with filtering options.

    Query Parameters:
    - step_id: Filter by step ID
    - image_type: Filter by image type ('before', 'after', 'inspiration', 'user_upload')
    - start_date: Filter by creation date (ISO format)
    - end_date: Filter by creation date (ISO format)
    - limit: Maximum number of results (default 50)
    - offset: Pagination offset (default 0)
    """
    try:
        service = JourneyPersistenceService(db)

        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        images = await service.get_journey_images(
            journey_id=journey_id,
            step_id=step_id,
            image_type=image_type,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit,
            offset=offset
        )

        return ImageGalleryResponse(
            journey_id=journey_id,
            total_images=len(images),
            images=[ImageResponse(**img.to_dict()) for img in images]
        )

    except Exception as e:
        logger.error(f"Error getting journey images: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get journey images")


@router.put("/{journey_id}/images/{image_id}", response_model=ImageResponse)
async def update_image(
    journey_id: str,
    image_id: str,
    request: UpdateImageRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update image metadata (label, type, metadata).
    """
    try:
        service = JourneyPersistenceService(db)
        image = await service.update_image(
            journey_id=journey_id,
            image_id=image_id,
            label=request.label,
            image_type=request.image_type,
            metadata=request.metadata
        )

        return ImageResponse(**image.to_dict())

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update image")


@router.delete("/{journey_id}/images/{image_id}")
async def delete_image(
    journey_id: str,
    image_id: str,
    delete_file: bool = True,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete an image from the journey.

    Query Parameters:
    - delete_file: Whether to delete the physical file (default true)
    """
    try:
        service = JourneyPersistenceService(db)
        await service.delete_image(
            journey_id=journey_id,
            image_id=image_id,
            delete_file=delete_file
        )

        return {"message": "Image deleted successfully", "image_id": image_id}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete image")


@router.put("/{journey_id}/steps/{step_id}/images/reorder", response_model=List[ImageResponse])
async def reorder_images(
    journey_id: str,
    step_id: str,
    request: ReorderImagesRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Reorder images within a step.

    Provide an ordered list of image IDs to set the new display order.
    """
    try:
        service = JourneyPersistenceService(db)
        images = await service.reorder_images(
            journey_id=journey_id,
            step_id=step_id,
            image_ids=request.image_ids
        )

        return [ImageResponse(**img.to_dict()) for img in images]

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error reordering images: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reorder images")


@router.post("/{journey_id}/steps/{step_id}/images/bulk", response_model=BulkImageUploadResponse)
async def bulk_upload_images(
    journey_id: str,
    step_id: str,
    files: List[UploadFile] = File(...),
    image_type: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Upload multiple images to a step at once.

    Form Parameters:
    - files: List of image files
    - image_type: Optional image type for all images
    """
    try:
        service = JourneyPersistenceService(db)

        images = []
        errors = []

        for file in files:
            try:
                # Validate file type
                if not file.content_type or not file.content_type.startswith("image/"):
                    errors.append({
                        "filename": file.filename,
                        "error": "File must be an image"
                    })
                    continue

                # Generate unique filename
                ext = os.path.splitext(file.filename or "image.jpg")[1]
                unique_filename = f"{uuid.uuid4()}{ext}"

                # Create directory structure
                upload_dir = os.path.join("uploads", "journeys", journey_id, step_id)
                os.makedirs(upload_dir, exist_ok=True)

                # Save file
                file_path = os.path.join(upload_dir, unique_filename)
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)

                # Get file size
                file_size = len(content)

                # Create URL
                url = f"/uploads/journeys/{journey_id}/{step_id}/{unique_filename}"

                # Add to database
                image = await service.add_image(
                    journey_id=journey_id,
                    step_id=step_id,
                    filename=file.filename or unique_filename,
                    file_path=file_path,
                    url=url,
                    content_type=file.content_type,
                    file_size=file_size,
                    is_generated=False,
                    image_type=image_type or "user_upload",
                    label=file.filename or "Uploaded image"
                )

                images.append(ImageResponse(**image.to_dict()))

            except Exception as e:
                errors.append({
                    "filename": file.filename,
                    "error": str(e)
                })

        return BulkImageUploadResponse(
            success_count=len(images),
            failed_count=len(errors),
            images=images,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Error bulk uploading images: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to bulk upload images")


@router.delete("/{journey_id}/images/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_images(
    journey_id: str,
    request: BulkDeleteImagesRequest,
    delete_files: bool = True,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete multiple images at once.

    Query Parameters:
    - delete_files: Whether to delete physical files (default true)
    """
    try:
        service = JourneyPersistenceService(db)
        deleted_ids, errors = await service.delete_images_bulk(
            journey_id=journey_id,
            image_ids=request.image_ids,
            delete_files=delete_files
        )

        return BulkDeleteResponse(
            success_count=len(deleted_ids),
            failed_count=len(errors),
            deleted_ids=deleted_ids,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Error bulk deleting images: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to bulk delete images")

