"""
Design Transformation API - Endpoints for AI-powered room transformations.

This API provides endpoints for transforming room images using Gemini Imagen.
All transformations preserve unchanged elements while only modifying what the customer requests.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import io
import base64
import uuid
from PIL import Image, ImageChops, ImageStat, ImageDraw

from backend.database import get_async_db
from backend.models import RoomImage, Room, TransformationType, TransformationStatus
from backend.services.design_transformation_service import DesignTransformationService
from backend.services.transformation_storage_service import TransformationStorageService
import time
import os
import math


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/design", tags=["design"])


# Heuristic extraction of requested change categories from user prompt
# Keeps logic minimal to avoid false promises; used to guide grounded product suggestions
_DEF_CHANGE_KEYWORDS = {
    "paint": ["paint", "wall color", "walls"],
    "flooring": ["floor", "flooring", "hardwood", "tile", "carpet", "vinyl", "laminate"],
    "lighting": ["light", "lighting", "pendant", "sconce", "chandelier"],
    "cabinets": ["cabinet", "cabinets"],
    "countertops": ["countertop", "countertops"],
    "backsplash": ["backsplash"],
    "decor": ["decor", "rug", "art", "curtain", "drape", "vase"],
    "furniture": ["sofa", "couch", "chair", "table", "furniture"],
}

def _extract_requested_changes(prompt_text: str) -> List[str]:
    t = (prompt_text or "").lower()
    cats: List[str] = []
    for cat, keys in _DEF_CHANGE_KEYWORDS.items():
        if any(k in t for k in keys):
            cats.append(cat)
    # Deduplicate and sort for stability
    return sorted(set(cats))


# Request/Response Models
class PaintTransformRequest(BaseModel):
    """Request model for paint transformation."""
    room_image_id: UUID = Field(..., description="ID of the room image to transform")
    target_color: str = Field(..., description="Target wall color (e.g., 'soft gray', '#F5F5DC')")
    target_finish: str = Field(default="matte", description="Paint finish (matte, eggshell, satin, semi-gloss, gloss)")
    walls_only: bool = Field(default=True, description="If true, only change walls (not ceiling)")
    preserve_trim: bool = Field(default=True, description="If true, keep trim/molding original color")
    num_variations: int = Field(default=4, ge=1, le=4, description="Number of variations to generate")


class FlooringTransformRequest(BaseModel):
    """Request model for flooring transformation."""
    room_image_id: UUID
    target_material: str = Field(..., description="Flooring material (hardwood, tile, carpet, vinyl, laminate)")
    target_style: str = Field(..., description="Style details (e.g., 'wide plank oak', 'herringbone pattern')")
    target_color: Optional[str] = Field(None, description="Optional color specification")
    preserve_rugs: bool = Field(default=True, description="If true, keep area rugs unchanged")
    num_variations: int = Field(default=4, ge=1, le=4)


class CabinetTransformRequest(BaseModel):
    """Request model for cabinet transformation."""
    room_image_id: UUID
    target_color: str = Field(..., description="Desired cabinet color")
    target_finish: str = Field(default="painted", description="Finish type (painted, stained, natural wood, glazed)")
    target_style: Optional[str] = Field(None, description="Optional style (shaker, flat panel, raised panel)")
    preserve_hardware: bool = Field(default=False, description="If true, keep existing hardware")
    num_variations: int = Field(default=4, ge=1, le=4)


class CountertopTransformRequest(BaseModel):
    """Request model for countertop transformation."""
    room_image_id: UUID
    target_material: str = Field(..., description="Material (granite, quartz, marble, butcher block, laminate, concrete)")
    target_color: str = Field(..., description="Color specification")
    target_pattern: Optional[str] = Field(None, description="Optional pattern (veined, speckled, solid)")
    edge_profile: str = Field(default="standard", description="Edge style (standard, beveled, bullnose, waterfall)")
    num_variations: int = Field(default=4, ge=1, le=4)


class BacksplashTransformRequest(BaseModel):
    """Request model for backsplash transformation."""
    room_image_id: UUID
    target_material: str = Field(..., description="Material (ceramic tile, glass tile, subway tile, mosaic, stone)")
    target_pattern: str = Field(..., description="Pattern/layout (subway, herringbone, stacked, mosaic)")
    target_color: str = Field(..., description="Tile color")
    grout_color: Optional[str] = Field(None, description="Optional grout color")
    num_variations: int = Field(default=4, ge=1, le=4)


class LightingTransformRequest(BaseModel):
    """Request model for lighting transformation."""
    room_image_id: UUID
    target_fixture_style: str = Field(..., description="Fixture style (modern, traditional, industrial, farmhouse)")
    target_finish: str = Field(..., description="Finish (brushed nickel, oil-rubbed bronze, chrome, brass, black)")
    adjust_ambiance: Optional[str] = Field(None, description="Optional ambiance (warmer, cooler, brighter, dimmer)")
    num_variations: int = Field(default=4, ge=1, le=4)


class FurnitureTransformRequest(BaseModel):
    """Request model for furniture transformation."""
    room_image_id: UUID
    action: str = Field(..., description="Action (add, remove, replace)")
    furniture_description: str = Field(..., description="Description of furniture item")
    placement: Optional[str] = Field(None, description="Optional placement description")
    num_variations: int = Field(default=4, ge=1, le=4)


class VirtualStagingRequest(BaseModel):
    """Request model for Virtual Staging (add furnishings without altering envelope)."""
    room_image_id: UUID
    style_preset: Optional[str] = Field(None, description="Style preset (e.g., Modern, Scandinavian, Minimal)")
    style_prompt: Optional[str] = Field(None, description="Custom style cues or theme")
    furniture_density: str = Field(default="medium", description="Amount of furniture: light | medium | full")
    lock_envelope: bool = Field(default=True, description="Preserve floors/walls/ceilings/windows/doors exactly")
    num_variations: int = Field(default=2, ge=1, le=4)


class UnstagingRequest(BaseModel):
    """Request model for Unstaging (remove furnishings)."""
    room_image_id: UUID
    strength: str = Field(default="medium", description="light | medium | full")
    num_variations: int = Field(default=2, ge=1, le=4)


class MaskedEditRequest(BaseModel):
    """Masked edit: replace or remove inside a user-provided mask (data URL)."""
    room_image_id: UUID
    mask_data_url: str = Field(..., description="Base64 data URL for a single-channel (L) mask; white = editable")
    operation: str = Field(..., description="remove | replace")
    replacement_prompt: Optional[str] = Field(None, description="Description of what to place for replace operation")
    num_variations: int = Field(default=2, ge=1, le=4)


class PolygonMaskFromPointsRequest(BaseModel):
    """Create a binary mask from polygon points (click-to-segment helper)."""
    room_image_id: Optional[UUID] = Field(None, description="If provided, infer width/height from this image")
    width: Optional[int] = Field(None, description="Mask width in pixels (required if no room_image_id)")
    height: Optional[int] = Field(None, description="Mask height in pixels (required if no room_image_id)")
    points: List[List[int]] = Field(..., description="List of [x,y] points defining a polygon (closed)")


class PolygonMaskResponse(BaseModel):
    mask_data_url: str


class SegmentRequest(BaseModel):
    room_image_id: UUID
    segment_class: str = Field(..., description="Target class to segment (e.g., floor, walls, cabinets)")
    points: Optional[List[Dict[str, int]]] = Field(None, description="Optional point hints as {'x':int,'y':int}")
    num_masks: int = Field(default=1, ge=1, le=4)


class SegmentResponse(BaseModel):
    mask_data_urls: List[str]


class PreciseEditRequest(BaseModel):
    """Orchestrates polygon/segment -> masked edit for precise changes."""
    room_image_id: UUID
    mode: str = Field(default="polygon", description="polygon | segment")
    points: Optional[List[List[int]]] = Field(None, description="Polygon points [[x,y],...] for polygon mode (absolute pixels)")
    points_normalized: Optional[List[List[float]]] = Field(
        None,
        description="Optional normalized polygon points [[x,y] in 0..1] relative to the image; if provided, overrides 'points'"
    )
    segment_class: Optional[str] = Field(None, description="Class for segmentation (e.g., floor, walls)")
    operation: str = Field(..., description="remove | replace")
    replacement_prompt: Optional[str] = Field(None, description="Describe what to place for 'replace'")
    num_variations: int = Field(default=2, ge=1, le=4)


# Upload-capable request models (no Digital Twin required)
class VirtualStagingUploadRequest(BaseModel):
    image_data_url: str = Field(..., description="Base64 data URL of the image (data:image/...;base64,...) or raw base64")
    style_preset: Optional[str] = Field(None, description="Style preset (e.g., Modern, Scandinavian, Minimal)")
    style_prompt: Optional[str] = Field(None, description="Custom style cues or theme")
    furniture_density: str = Field(default="medium", description="Amount of furniture: light | medium | heavy")
    lock_envelope: bool = Field(default=True, description="Preserve floors/walls/ceilings/windows/doors exactly")
    num_variations: int = Field(default=2, ge=1, le=4)
    enable_grounding: bool = Field(default=False, description="If true, suggest products (Canada-first) using Google Search grounding")

class UnstagingUploadRequest(BaseModel):
    image_data_url: str = Field(..., description="Base64 data URL of the image (data:image/...;base64,...) or raw base64")
    strength: str = Field(default="medium", description="light | medium | full")
    num_variations: int = Field(default=2, ge=1, le=4)

class MaskedEditUploadRequest(BaseModel):
    image_data_url: str = Field(..., description="Base64 data URL of the image (data:image/...;base64,...) or raw base64")
    mask_data_url: str = Field(..., description="Base64 data URL for a single-channel (L) mask; white = editable")
    operation: str = Field(..., description="remove | replace")
    replacement_prompt: Optional[str] = Field(None, description="Describe what to place for 'replace' operation")
    num_variations: int = Field(default=2, ge=1, le=4)

class SegmentUploadRequest(BaseModel):
    image_data_url: str = Field(..., description="Base64 data URL of the image (data:image/...;base64,...) or raw base64")
    segment_class: str = Field(..., description="Target class to segment (e.g., floor, walls, cabinets)")
    points: Optional[List[Dict[str, int]]] = Field(None, description="Optional point hints as {'x':int,'y':int}")
    num_masks: int = Field(default=1, ge=1, le=4)


class MultiAngleUploadRequest(BaseModel):
    image_data_url: str = Field(..., description="Base64 data URL of the image (data:image/...;base64,...) or raw base64")
    num_angles: int = Field(default=3, ge=1, le=4)
    yaw_degrees: int = Field(default=6, ge=1, le=15)
    pitch_degrees: int = Field(default=4, ge=0, le=15)

class EnhanceUploadRequest(BaseModel):
    image_data_url: str = Field(..., description="Base64 data URL of the image (data:image/...;base64,...) or raw base64")
    upscale_2x: bool = Field(default=True, description="If true, attempt 2x upscaling while preserving detail")


class CustomTransformRequest(BaseModel):
    """Request model for custom transformation with user prompt."""
    room_image_id: UUID
    custom_prompt: str = Field(..., description="Custom transformation prompt describing desired changes")
    transformation_type: str = Field(default="custom", description="Type of transformation")
    num_variations: int = Field(default=4, ge=1, le=4)


class TransformationResponse(BaseModel):
    """Response model for transformations."""
    success: bool
    message: str
    transformation_id: UUID
    num_variations: int
    transformation_type: str
    original_image_id: UUID
    status: str
    image_urls: List[str] = []  # Placeholder URLs for now



class PromptedTransformRequest(BaseModel):
    """Request model for prompt-driven transformation from media selection."""
    room_image_id: UUID = Field(..., description="ID of the room image to transform")
    prompt: str = Field(..., description="User's freeform transformation prompt")
    num_variations: int = Field(default=2, ge=1, le=4, description="Number of variations to generate")
    enable_grounding: bool = Field(default=False, description="If true, use Google Search grounding to suggest products")


class PromptedTransformResponse(BaseModel):
    """Response model for prompt-driven transformations including analysis."""
    success: bool
    message: str
    transformation_id: UUID
    num_variations: int
    transformation_type: str
    original_image_id: UUID
    status: str
    image_urls: List[str] = []
    summary: Dict[str, Any] = {}
    products: List[Dict[str, Any]] = []
    sources: List[str] = []
    grounding_unavailable: bool = False
    grounding_notice: Optional[str] = None
    follow_up_ideas: Dict[str, List[str]] = {}

class UploadPromptedTransformRequest(BaseModel):
    """Request model for prompt-driven transformation from an uploaded image (no Digital Twin required)."""
    image_data_url: str = Field(..., description="Base64 data URL of the image (data:image/...;base64,...) or raw base64")
    prompt: str = Field(..., description="User's freeform transformation prompt")
    num_variations: int = Field(default=2, ge=1, le=4, description="Number of variations to generate")
    enable_grounding: bool = Field(default=False, description="If true, use Google Search grounding to suggest products")


class PromptedTransformUploadResponse(BaseModel):
    """Response model for prompt-driven transformations from uploaded image."""
    success: bool
    message: str
    num_variations: int
    image_urls: List[str] = []
    summary: Dict[str, Any] = {}
    products: List[Dict[str, Any]] = []
    sources: List[str] = []
    grounding_unavailable: bool = False
    grounding_notice: Optional[str] = None
    follow_up_ideas: Dict[str, List[str]] = {}



class AnalyzeImageRequest(BaseModel):
    """Analyze an existing room image and suggest ideas."""
    room_image_id: UUID
    max_ideas: int = Field(default=4, ge=1, le=6)


class AnalyzeImageResponse(BaseModel):
    """Summary and suggested idea chips for the selected image."""
    summary: Dict[str, Any] = {}
    ideas: List[str] = []
    ideas_by_theme: Dict[str, List[str]] = {}
    style_transformations: List[Dict[str, Any]] = []

class TransformationHistoryItem(BaseModel):
    """Model for transformation history item."""
    id: UUID
    transformation_type: str
    status: str
    parameters: Dict[str, Any]
    num_variations: int
    created_at: str
    processing_time_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class TransformationHistoryResponse(BaseModel):
    """Response model for transformation history."""
    room_image_id: UUID
    transformations: List[TransformationHistoryItem]
    total_count: int


# Helper Functions
async def load_room_image(room_image_id: UUID, db: AsyncSession) -> RoomImage:
    """Load room image from database."""
    from sqlalchemy import select

    result = await db.execute(
        select(RoomImage).where(RoomImage.id == room_image_id)
    )
    room_image = result.scalar_one_or_none()

    if not room_image:
        raise HTTPException(status_code=404, detail=f"Room image {room_image_id} not found")

    return room_image


async def get_image_from_url(image_url: str) -> Image.Image:
    """Download and load image from URL."""
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))


# API Endpoints
@router.post("/transform-paint", response_model=TransformationResponse)
async def transform_paint(
    request: PaintTransformRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Transform wall paint color while preserving everything else.

    This endpoint changes only the wall paint color and finish, keeping all
    furniture, flooring, fixtures, and other elements unchanged.
    """
    start_time = time.time()
    storage_service = TransformationStorageService()

    try:
        # Load room image
        room_image = await load_room_image(request.room_image_id, db)

        # Create transformation record
        transformation = await storage_service.create_transformation(
            db=db,
            room_image_id=request.room_image_id,
            transformation_type=TransformationType.PAINT,
            parameters={
                "target_color": request.target_color,
                "target_finish": request.target_finish,
                "walls_only": request.walls_only,
                "preserve_trim": request.preserve_trim
            },
            num_variations=request.num_variations
        )

        # Update status to processing
        await storage_service.update_transformation_status(
            db=db,
            transformation_id=transformation.id,
            status=TransformationStatus.PROCESSING
        )

        # Get image from URL
        image = await get_image_from_url(room_image.image_url)

        # Perform transformation
        service = DesignTransformationService()
        transformed_images = await service.transform_paint(
            image=image,
            target_color=request.target_color,
            target_finish=request.target_finish,
            walls_only=request.walls_only,
            preserve_trim=request.preserve_trim,
            num_variations=request.num_variations
        )

        # Save transformed images
        transformation_images = await storage_service.save_transformation_images(
            db=db,
            transformation_id=transformation.id,
            images=transformed_images
        )

        # Calculate processing time
        processing_time = int(time.time() - start_time)

        # Update status to completed
        await storage_service.update_transformation_status(
            db=db,
            transformation_id=transformation.id,
            status=TransformationStatus.COMPLETED,
            processing_time_seconds=processing_time
        )

        return TransformationResponse(
            success=True,
            message=f"Successfully generated {len(transformed_images)} paint transformation variations",
            transformation_id=transformation.id,
            num_variations=len(transformed_images),
            transformation_type="paint",
            original_image_id=request.room_image_id,
            status="completed",
            image_urls=[img.image_url for img in transformation_images]
        )

    except Exception as e:
        logger.error(f"Error transforming paint: {str(e)}", exc_info=True)

        # Update transformation status to failed if it was created
        if 'transformation' in locals():
            await storage_service.update_transformation_status(
                db=db,
                transformation_id=transformation.id,
                status=TransformationStatus.FAILED,
                error_message=str(e)
            )

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transform-flooring", response_model=TransformationResponse)
async def transform_flooring(
    request: FlooringTransformRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Transform flooring while preserving everything else.

    This endpoint changes only the flooring material and style, keeping all
    walls, furniture, fixtures, and other elements unchanged.
    """
    try:
        room_image = await load_room_image(request.room_image_id, db)
        image = await get_image_from_url(room_image.image_url)

        service = DesignTransformationService()
        transformed_images = await service.transform_flooring(
            image=image,
            target_material=request.target_material,
            target_style=request.target_style,
            target_color=request.target_color,
            preserve_rugs=request.preserve_rugs
        )

        return TransformationResponse(
            success=True,
            message=f"Successfully generated {len(transformed_images)} flooring transformation variations",
            num_variations=len(transformed_images),
            transformation_type="flooring",
            original_image_id=request.room_image_id
        )

    except Exception as e:
        logger.error(f"Error transforming flooring: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transform-cabinets", response_model=TransformationResponse)
async def transform_cabinets(
    request: CabinetTransformRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Transform cabinet color/finish while preserving everything else.

    This endpoint changes only the cabinet color and finish, keeping all
    countertops, backsplash, appliances, and other elements unchanged.
    """
    try:
        room_image = await load_room_image(request.room_image_id, db)
        image = await get_image_from_url(room_image.image_url)

        service = DesignTransformationService()
        transformed_images = await service.transform_cabinets(
            image=image,
            target_color=request.target_color,
            target_finish=request.target_finish,
            target_style=request.target_style,
            preserve_hardware=request.preserve_hardware
        )

        return TransformationResponse(
            success=True,
            message=f"Successfully generated {len(transformed_images)} cabinet transformation variations",
            num_variations=len(transformed_images),
            transformation_type="cabinets",
            original_image_id=request.room_image_id
        )

    except Exception as e:
        logger.error(f"Error transforming cabinets: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transform-countertops", response_model=TransformationResponse)
async def transform_countertops(
    request: CountertopTransformRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Transform countertops while preserving everything else."""
    try:
        room_image = await load_room_image(request.room_image_id, db)
        image = await get_image_from_url(room_image.image_url)

        service = DesignTransformationService()
        transformed_images = await service.transform_countertops(
            image=image,
            target_material=request.target_material,
            target_color=request.target_color,
            target_pattern=request.target_pattern,
            edge_profile=request.edge_profile
        )

        return TransformationResponse(
            success=True,
            message=f"Successfully generated {len(transformed_images)} countertop transformation variations",
            num_variations=len(transformed_images),

            transformation_type="countertops",
            original_image_id=request.room_image_id
        )

    except Exception as e:
        logger.error(f"Error transforming countertops: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/virtual-staging", response_model=TransformationResponse)
async def virtual_staging(
    request: VirtualStagingRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Virtual Staging: add furnishings/decor while preserving the room envelope.
    Uses Gemini image editing per official docs: https://ai.google.dev/gemini-api/docs/image-generation
    """
    start_time = time.time()
    storage_service = TransformationStorageService()
    try:
        # Load room image
        room_image = await load_room_image(request.room_image_id, db)
        image = await get_image_from_url(room_image.image_url)

        # Create transformation record (use FURNITURE type)
        transformation = await storage_service.create_transformation(
            db=db,
            room_image_id=request.room_image_id,
            transformation_type=TransformationType.FURNITURE,
            parameters={
                "mode": "virtual_staging",
                "style_preset": request.style_preset,
                "style_prompt": request.style_prompt,
                "furniture_density": request.furniture_density,
                "lock_envelope": request.lock_envelope,
            },
            num_variations=request.num_variations,
        )
        await storage_service.update_transformation_status(
            db=db,
            transformation_id=transformation.id,
            status=TransformationStatus.PROCESSING,
        )

        # Generate
        service = DesignTransformationService()
        images = await service.transform_virtual_staging(
            image=image,
            style_preset=request.style_preset,
            style_prompt=request.style_prompt,
            furniture_density=request.furniture_density,
            lock_envelope=request.lock_envelope,
            num_variations=request.num_variations,
        )

        # Save
        transformation_images = await storage_service.save_transformation_images(
            db=db,
            transformation_id=transformation.id,
            images=images,
        )

        processing_time = int(time.time() - start_time)
        await storage_service.update_transformation_status(
            db=db,
            transformation_id=transformation.id,
            status=TransformationStatus.COMPLETED,
            processing_time_seconds=processing_time,
        )

        return TransformationResponse(
            success=True,
            message=f"Generated {len(images)} virtual staging variations",
            transformation_id=transformation.id,
            num_variations=len(images),
            transformation_type="furniture",
            original_image_id=request.room_image_id,
            status="completed",
            image_urls=[img.image_url for img in transformation_images],
        )
    except Exception as e:
        logger.error(f"virtual_staging failed: {e}", exc_info=True)
        if 'transformation' in locals():
            await storage_service.update_transformation_status(
                db=db,
                transformation_id=transformation.id,
                status=TransformationStatus.FAILED,
                error_message=str(e),
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unstage", response_model=TransformationResponse)
async def unstage(
    request: UnstagingRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Unstaging: remove furnishings/decor; preserve floors/walls/ceilings/windows/doors.
    """
    start_time = time.time()
    storage_service = TransformationStorageService()
    try:
        room_image = await load_room_image(request.room_image_id, db)
        image = await get_image_from_url(room_image.image_url)

        transformation = await storage_service.create_transformation(
            db=db,
            room_image_id=request.room_image_id,
            transformation_type=TransformationType.FURNITURE,
            parameters={
                "mode": "unstage",
                "strength": request.strength,
            },
            num_variations=request.num_variations,
        )
        await storage_service.update_transformation_status(
            db=db,
            transformation_id=transformation.id,
            status=TransformationStatus.PROCESSING,
        )

        service = DesignTransformationService()
        images = await service.transform_unstaging(
            image=image,
            strength=request.strength,
            num_variations=request.num_variations,
        )

        transformation_images = await storage_service.save_transformation_images(
            db=db,
            transformation_id=transformation.id,
            images=images,
        )

        processing_time = int(time.time() - start_time)
        await storage_service.update_transformation_status(
            db=db,
            transformation_id=transformation.id,
            status=TransformationStatus.COMPLETED,
            processing_time_seconds=processing_time,
        )

        return TransformationResponse(
            success=True,
            message=f"Generated {len(images)} unstaging variations",
            transformation_id=transformation.id,
            num_variations=len(images),
            transformation_type="furniture",
            original_image_id=request.room_image_id,
            status="completed",
            image_urls=[img.image_url for img in transformation_images],
        )
    except Exception as e:
        logger.error(f"unstage failed: {e}", exc_info=True)
        if 'transformation' in locals():
            await storage_service.update_transformation_status(
                db=db,
                transformation_id=transformation.id,
                status=TransformationStatus.FAILED,
                error_message=str(e),
            )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/edit-with-mask", response_model=TransformationResponse)
async def edit_with_mask(
    request: MaskedEditRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Precise remove/replace inside a provided binary mask (white = editable).
    Follows Gemini masked multimodal pattern: https://ai.google.dev/gemini-api/docs/image-generation
    """
    start_time = time.time()
    storage_service = TransformationStorageService()
    try:
        # Load room image
        room_image = await load_room_image(request.room_image_id, db)
        image = await get_image_from_url(room_image.image_url)

        # Decode mask data URL
        if not request.mask_data_url.startswith("data:"):
            raise HTTPException(status_code=400, detail="mask_data_url must be a data URL")
        header, b64data = request.mask_data_url.split(",", 1)
        mask_bytes = base64.b64decode(b64data)

        # Create transformation record
        transformation = await storage_service.create_transformation(
            db=db,
            room_image_id=request.room_image_id,
            transformation_type=TransformationType.MULTI,
            parameters={
                "mode": "masked_edit",
                "operation": request.operation,
                "replacement_prompt": request.replacement_prompt,
            },
            num_variations=request.num_variations,
        )
        await storage_service.update_transformation_status(
            db=db,
            transformation_id=transformation.id,
            status=TransformationStatus.PROCESSING,
        )

        # Perform masked edit
        service = DesignTransformationService()
        images = await service.transform_masked_edit(
            image=image,
            mask_image=mask_bytes,
            operation=request.operation,
            replacement_prompt=request.replacement_prompt,
            num_variations=request.num_variations,
        )

        # Save
        transformation_images = await storage_service.save_transformation_images(
            db=db,
            transformation_id=transformation.id,
            images=images,
        )

        processing_time = int(time.time() - start_time)
        await storage_service.update_transformation_status(
            db=db,
            transformation_id=transformation.id,
            status=TransformationStatus.COMPLETED,
            processing_time_seconds=processing_time,
        )

        return TransformationResponse(
            success=True,
            message=f"Generated {len(images)} masked edit variations",
            transformation_id=transformation.id,
            num_variations=len(images),
            transformation_type="multi",
            original_image_id=request.room_image_id,
            status="completed",
            image_urls=[img.image_url for img in transformation_images],
        )
    except Exception as e:
        logger.error(f"edit_with_mask failed: {e}", exc_info=True)
        if 'transformation' in locals():
            await storage_service.update_transformation_status(
                db=db,
                transformation_id=transformation.id,
                status=TransformationStatus.FAILED,
                error_message=str(e),
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mask-from-polygon", response_model=PolygonMaskResponse)
async def mask_from_polygon(
    request: PolygonMaskFromPointsRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Builds a white-on-black binary mask PNG from polygon points (click-to-segment helper).
    - If room_image_id is provided, the mask size is inferred from that image.
    - Otherwise, width/height must be provided.
    Returns a base64 data URL suitable for /edit-with-mask.
    """
    try:
        width = request.width
        height = request.height

        if request.room_image_id:
            room_image = await load_room_image(request.room_image_id, db)
            base_img = await get_image_from_url(room_image.image_url)
            width, height = base_img.size

        if not width or not height:
            raise HTTPException(status_code=400, detail="width and height are required when room_image_id is not provided")

        # Create binary mask
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        # Flatten list of [x,y] to tuples
        polygon = [(int(x), int(y)) for x, y in request.points]
        if len(polygon) < 3:
            raise HTTPException(status_code=400, detail="At least 3 points are required to form a polygon")
        draw.polygon(polygon, fill=255)

        # Encode to data URL (PNG)

        buf = io.BytesIO()
        mask.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        data_url = f"data:image/png;base64,{b64}"
        return PolygonMaskResponse(mask_data_url=data_url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"mask_from_polygon failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/segment", response_model=SegmentResponse)
async def segment(
    request: SegmentRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    AI segmentation assist: returns binary mask(s) data URLs for the requested class.
    Uses Gemini image generation per official docs to output mask images (beta).
    """
    try:
        room_image = await load_room_image(request.room_image_id, db)
        image = await get_image_from_url(room_image.image_url)

        service = DesignTransformationService()
        masks = await service.gemini.segment_image(
            reference_image=image,
            segment_class=request.segment_class,
            points=request.points,
            num_masks=request.num_masks,
        )

        data_urls: List[str] = []
        for m in masks:
            buf = io.BytesIO()
            m.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            data_urls.append(f"data:image/png;base64,{b64}")


        return SegmentResponse(mask_data_urls=data_urls)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"segment failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/precise-edit", response_model=TransformationResponse)
async def precise_edit(
    request: PreciseEditRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Orchestrates polygon/segment selection -> masked edit remove/replace.
    - If mode == 'polygon': uses absolute 'points' or normalized 'points_normalized' scaled to the base image size
    - If mode == 'segment': uses AI segmentation to obtain a mask for the given class

    Editing follows Gemini masked multimodal guidance:
    https://ai.google.dev/gemini-api/docs/image-generation
    """
    start_time = time.time()
    storage_service = TransformationStorageService()
    try:
        # Load base image for this room image
        room_image = await load_room_image(request.room_image_id, db)
        image = await get_image_from_url(room_image.image_url)

        # Build or obtain mask
        mask_img: Image.Image
        if (request.mode or "").lower() == "polygon":
            width, height = image.size
            pts: List[Tuple[int, int]] = []
            if request.points_normalized:
                for x, y in request.points_normalized:
                    x = max(0.0, min(1.0, float(x)))
                    y = max(0.0, min(1.0, float(y)))
                    pts.append((int(round(x * width)), int(round(y * height))))
            elif request.points:
                for x, y in request.points:
                    pts.append((int(x), int(y)))
            else:
                raise HTTPException(status_code=400, detail="polygon requires 'points' or 'points_normalized'")
            if len(pts) < 3:
                raise HTTPException(status_code=400, detail="polygon needs >= 3 points")

            mask_img = Image.new("L", (width, height), 0)
            draw = ImageDraw.Draw(mask_img)
            draw.polygon(pts, outline=255, fill=255)
        elif (request.mode or "").lower() == "segment":
            if not request.segment_class:
                raise HTTPException(status_code=400, detail="segment_class required for segment mode")
            svc = DesignTransformationService()
            masks = await svc.gemini.segment_image(
                reference_image=image,
                segment_class=request.segment_class,
                points=None,
                num_masks=1,
            )
            if not masks:
                raise HTTPException(status_code=424, detail="segmentation produced no mask")
            mask_img = masks[0]
        else:
            raise HTTPException(status_code=400, detail="mode must be 'polygon' or 'segment'")

        # Create transformation record
        transformation = await storage_service.create_transformation(
            db=db,
            room_image_id=request.room_image_id,
            transformation_type=TransformationType.MULTI,
            parameters={
                "mode": request.mode,
                "operation": request.operation,
                "segment_class": request.segment_class,
                "points_len": len(request.points or request.points_normalized or []),
                "source": "precise_edit",
            },
            num_variations=request.num_variations,
        )
        await storage_service.update_transformation_status(
            db=db,
            transformation_id=transformation.id,
            status=TransformationStatus.PROCESSING,
        )

        # Perform masked edit
        svc = DesignTransformationService()
        images = await svc.transform_masked_edit(
            image=image,
            mask_image=mask_img,
            operation=request.operation,
            replacement_prompt=request.replacement_prompt,
            num_variations=request.num_variations,
        )

        # Persist results
        transformation_images = await storage_service.save_transformation_images(
            db=db,
            transformation_id=transformation.id,
            images=images,
        )

        processing_time = int(time.time() - start_time)
        await storage_service.update_transformation_status(
            db=db,
            transformation_id=transformation.id,
            status=TransformationStatus.COMPLETED,
            processing_time_seconds=processing_time,
        )

        return TransformationResponse(
            success=True,
            message=f"Generated {len(images)} precise edit variations",
            transformation_id=transformation.id,
            num_variations=len(images),
            transformation_type="multi",
            original_image_id=request.room_image_id,
            status="completed",
            image_urls=[img.image_url for img in transformation_images],
        )
    except Exception as e:
        logger.error(f"precise_edit failed: {e}", exc_info=True)
        if 'transformation' in locals():
            await storage_service.update_transformation_status(
                db=db,
                transformation_id=transformation.id,
                status=TransformationStatus.FAILED,
                error_message=str(e),
            )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transform-backsplash", response_model=TransformationResponse)
async def transform_backsplash(
    request: BacksplashTransformRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Transform backsplash while preserving everything else."""
    try:
        room_image = await load_room_image(request.room_image_id, db)
        image = await get_image_from_url(room_image.image_url)

        service = DesignTransformationService()
        transformed_images = await service.transform_backsplash(
            image=image,
            target_material=request.target_material,
            target_pattern=request.target_pattern,
            target_color=request.target_color,
            grout_color=request.grout_color
        )

        return TransformationResponse(
            success=True,
            message=f"Successfully generated {len(transformed_images)} backsplash transformation variations",
            num_variations=len(transformed_images),
            transformation_type="backsplash",
            original_image_id=request.room_image_id
        )

    except Exception as e:
        logger.error(f"Error transforming backsplash: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transform-custom", response_model=TransformationResponse)
async def transform_custom(
    request: CustomTransformRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Apply a custom transformation based on user's prompt.

    This endpoint allows users to describe any transformation they want in natural language.
    The AI will interpret the prompt and apply the changes while preserving everything else.
    """
    try:
        service = DesignTransformationService(db)

        # Build a custom prompt from the user's description
        custom_instructions = f"""
Transform this room image based on the following request:
{request.custom_prompt}

CRITICAL PRESERVATION RULES:
- Only modify what is explicitly mentioned in the request
- Preserve all other elements exactly as they are
- Maintain the room's layout, dimensions, and perspective
- Keep lighting and shadows realistic
- Ensure the transformation looks natural and professionally done
"""

        # Use the generic transformation method with custom prompt
        transformed_images = await service.transform_room_image(
            room_image_id=request.room_image_id,
            transformation_type=request.transformation_type,
            custom_prompt=custom_instructions,
            num_variations=request.num_variations
        )

        return TransformationResponse(
            success=True,
            message=f"Successfully generated {len(transformed_images)} custom transformation variations",
            num_variations=len(transformed_images),
            transformation_type=request.transformation_type,
            original_image_id=request.room_image_id
        )

    except Exception as e:
        logger.error(f"Error applying custom transformation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Transformation History Endpoints
@router.get("/transformations/{room_image_id}", response_model=TransformationHistoryResponse)
async def get_transformation_history(
    room_image_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get transformation history for a room image.

    Returns all transformations performed on a specific room image,
    ordered by most recent first.
    """
    try:
        storage_service = TransformationStorageService()

        # Get transformations
        transformations = await storage_service.get_transformations_for_room_image(
            db=db,
            room_image_id=room_image_id
        )

        # Convert to response format
        history_items = []
        for t in transformations:
            history_items.append(TransformationHistoryItem(
                id=t.id,
                transformation_type=t.transformation_type.value,
                status=t.status.value,
                parameters=t.parameters,
                num_variations=t.num_variations,
                created_at=t.created_at.isoformat(),
                processing_time_seconds=t.processing_time_seconds
            ))

        return TransformationHistoryResponse(
            room_image_id=room_image_id,
            transformations=history_items,
            total_count=len(history_items)
        )

    except Exception as e:
        logger.error(f"Error getting transformation history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transformation/{transformation_id}")
async def get_transformation_details(
    transformation_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get detailed information about a specific transformation.

    Returns the transformation record and all generated image variations.
    """
    try:
        storage_service = TransformationStorageService()

        # Get transformation
        transformation = await storage_service.get_transformation(
            db=db,
            transformation_id=transformation_id
        )

        if not transformation:
            raise HTTPException(status_code=404, detail=f"Transformation {transformation_id} not found")

        # Get images
        images = await storage_service.get_transformation_images(
            db=db,
            transformation_id=transformation_id
        )

        return {
            "id": transformation.id,
            "room_image_id": transformation.room_image_id,
            "transformation_type": transformation.transformation_type.value,
            "status": transformation.status.value,
            "parameters": transformation.parameters,
            "num_variations": transformation.num_variations,
            "created_at": transformation.created_at.isoformat(),
            "processing_time_seconds": transformation.processing_time_seconds,
            "error_message": transformation.error_message,
            "images": [
                {
                    "id": img.id,
                    "image_url": img.image_url,
                    "variation_number": img.variation_number,
                    "is_selected": img.is_selected,
                    "is_applied": img.is_applied,
                    "width": img.width,
                    "height": img.height
                }
                for img in images
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transformation details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transformation/{transformation_image_id}/select")
async def select_favorite_variation(
    transformation_image_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Mark a transformation image as the user's favorite variation.

    This will unselect all other variations for the same transformation.
    """
    try:
        storage_service = TransformationStorageService()

        transformation_image = await storage_service.select_favorite_variation(
            db=db,
            transformation_image_id=transformation_image_id
        )

        return {
            "success": True,
            "message": f"Selected variation {transformation_image.variation_number} as favorite",
            "transformation_image_id": transformation_image.id,
            "variation_number": transformation_image.variation_number
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error selecting favorite variation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/transformation/{transformation_id}")
async def delete_transformation(
    transformation_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a transformation and all its generated images.

    Also deletes images from cloud storage if a storage backend is configured.
    """
    try:
        storage_service = TransformationStorageService()
        deleted = await storage_service.delete_transformation(db=db, transformation_id=transformation_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Transformation not found")
        return {"success": True, "message": "Transformation deleted", "transformation_id": transformation_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transformation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transform-prompted", response_model=PromptedTransformResponse)
async def transform_prompted(
    request: PromptedTransformRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Transform a room image based on a freeform prompt selected from media.

    - Applies strict preservation rules (only change requested items)
    - Generates 1-4 variations via Gemini image editing (gemini-2.5-flash-image)
    - Analyzes the first result to summarize colors/materials/styles
    - Optionally suggests products using Google Search grounding
    """
    start_time = time.time()
    storage_service = TransformationStorageService()

    logger.info("[Transform MEDIA] Request: prompt_len=%s, num_variations=%s, enable_grounding=%s, room_image_id=%s",
                len(getattr(request, "prompt", "") or ""),
                getattr(request, "num_variations", None),
                getattr(request, "enable_grounding", False),
                str(getattr(request, "room_image_id", None)))

    try:
        # Load DB entities
        room_image = await load_room_image(request.room_image_id, db)
        # Fetch room for context (room name)
        from sqlalchemy import select
        room = None
        try:
            result = await db.execute(select(Room).where(Room.id == room_image.room_id))
            room = result.scalar_one_or_none()
        except Exception:
            room = None

        # Create transformation record
        transformation = await storage_service.create_transformation(
            db=db,
            room_image_id=request.room_image_id,
            transformation_type=TransformationType.CUSTOM,
            parameters={
                "prompt": request.prompt,
                "source": "media_prompt"
            },
            num_variations=request.num_variations,
        )

        await storage_service.update_transformation_status(
            db=db,
            transformation_id=transformation.id,
            status=TransformationStatus.PROCESSING,
        )

        # Load original image
        image = await get_image_from_url(room_image.image_url)

        # Build combined instructions with preservation rules
        service = DesignTransformationService()
        combined_prompt = f"""
Transform this exact room photo according to the user's request below.
Only modify what is asked. Keep all other elements unchanged.

USER REQUEST:
{request.prompt}

{service.CORE_PRESERVATION_RULES}
"""

        # Generate images
        transformed_images = await service._generate_transformation(
            image=image,
            prompt=combined_prompt,
            num_variations=request.num_variations,
        )

        # Drift guard: compute drift vs original; if too high, re-generate once with stricter instructions
        def _compute_drift(a_img: Image.Image, b_img: Image.Image) -> float:
            try:
                a2 = a_img.convert("L").resize((128, 128))
                b2 = b_img.convert("L").resize((128, 128))
                diff = ImageChops.difference(a2, b2)
                stat = ImageStat.Stat(diff)
                return min(1.0, max(0.0, (stat.mean[0] / 255.0)))
            except Exception:
                return 0.0

        DRIFT_THRESHOLD = 0.18
        drift_scores = []
        try:
            drift_scores = [_compute_drift(image, img) for img in transformed_images]
        except Exception:
            drift_scores = []

        strict_regen_applied = False
        if drift_scores and max(drift_scores) > DRIFT_THRESHOLD:
            strict_block = """
STRICT MODE (apply only if drift is high):
- Make only the smallest necessary pixel-level change to fulfill the request.
- Do NOT add or remove any objects; do NOT move anything; do NOT change lighting or perspective.
- If any part is ambiguous, leave it unchanged.
"""
            strict_prompt = combined_prompt + "\n" + strict_block
            try:
                transformed_images = await service._generate_transformation(
                    image=image,
                    prompt=strict_prompt,
                    num_variations=request.num_variations,
                )
                strict_regen_applied = True
                try:
                    drift_scores = [_compute_drift(image, img) for img in transformed_images]
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Strict-mode regeneration failed: {e}")

        # Save generated images
        transformation_images = await storage_service.save_transformation_images(
            db=db,
            transformation_id=transformation.id,
            images=transformed_images,
        )

        # Post-process: analyze first image
        summary = {}
        try:
            first_img = transformed_images[0] if transformed_images else None
            if first_img:
                room_hint = getattr(room, "name", None)
                summary = await service.gemini.analyze_design(first_img, room_hint=room_hint)
        except Exception as e:
            logger.warning(f"Design analysis failed: {e}")
            summary = {}

        # Analyze original image for diff-aware grounding (best-effort)
        original_summary: Dict[str, Any] = {}
        try:
            room_hint = getattr(room, "name", None)
            original_summary = await service.gemini.analyze_design(image, room_hint=room_hint)
        except Exception as e:
            logger.warning(f"Original image analysis failed: {e}")
            original_summary = {}
        # Attach image details (dimensions/MP/aspect) and spatial/material quantities; generate follow-up ideas
        try:
            def _ratio_str(_w: int, _h: int) -> str:
                try:
                    g = math.gcd(int(_w), int(_h)) if _w > 0 and _h > 0 else 1
                    return f"{int(_w)//g}:{int(_h)//g}" if g else f"{_w}:{_h}"
                except Exception:
                    return "n/a"
            _ow, _oh = (image.width, image.height)
            _rw, _rh = (transformed_images[0].width, transformed_images[0].height) if transformed_images else (None, None)
            summary = summary or {}
            summary.setdefault("image_details", {})
            summary["image_details"] = {
                "original": {
                    "width": _ow,
                    "height": _oh,
                    "megapixels": round((_ow * _oh) / 1_000_000, 2),
                    "aspect_ratio": _ratio_str(_ow, _oh),
                },
                "result": {
                    "width": _rw,
                    "height": _rh,
                    "megapixels": (round((_rw * _rh) / 1_000_000, 2) if (_rw and _rh) else None),
                    "aspect_ratio": (_ratio_str(_rw, _rh) if (_rw and _rh) else None),
                },
            }
        except Exception as e:
            logger.warning(f"Failed to attach image_details (media): {e}")

        try:
            logger.info("[Analysis MEDIA] colors=%s materials=%s styles=%s",
                        len((summary or {}).get("colors", [])),
                        len((summary or {}).get("materials", [])),
                        len((summary or {}).get("styles", [])))
        except Exception:
            pass

        # Spatial analysis and material quantity estimation (best-effort)
        try:
            spatial_media = await service.gemini.analyze_spatial_and_quantities(first_img or image)
            dims = (spatial_media or {}).get("dimensions") or {}
            openings = (spatial_media or {}).get("openings") or {}
            Lm = dims.get("length_m") or None
            Wm = dims.get("width_m") or None
            Hm = dims.get("height_m") or None

            def _calc_numbers_med(Lm, Wm, Hm, openings):
                out = {}
                try:
                    import math as _math
                    if all(isinstance(x, (int, float)) for x in [Lm, Wm]):
                        floor_m2 = max(0.0, float(Lm) * float(Wm))
                        ceil_m2 = floor_m2
                    else:
                        floor_m2 = ceil_m2 = None
                    if all(isinstance(x, (int, float)) for x in [Lm, Wm, Hm]):
                        perimeter_m = 2.0 * (float(Lm) + float(Wm))
                        walls_m2_raw = perimeter_m * float(Hm)
                        windows = (openings.get("windows") if isinstance(openings, dict) else None)
                        doors = (openings.get("doors") if isinstance(openings, dict) else None)
                        openings_m2 = 0.0
                        try:
                            if isinstance(windows, int):
                                openings_m2 += windows * 1.5
                            if isinstance(doors, int):
                                openings_m2 += doors * 1.9
                        except Exception:
                            pass
                        walls_m2 = max(0.0, walls_m2_raw - openings_m2)
                    else:
                        walls_m2 = None

                    coverage_m2_per_liter = 10.0
                    coats = 2
                    waste_pct = 0.10

                    if floor_m2 is not None:
                        flooring_m2_with_waste = floor_m2 * (1.0 + waste_pct)
                        flooring_sqft = round(flooring_m2_with_waste * 10.7639, 1)
                    else:
                        flooring_m2_with_waste = None
                        flooring_sqft = None

                    if walls_m2 is not None:
                        paint_liters = round((walls_m2 / coverage_m2_per_liter) * coats, 1)
                        paint_gallons = round(paint_liters / 3.785, 2)
                    else:
                        paint_liters = None
                        paint_gallons = None

                    if all(isinstance(x, (int, float)) for x in [Lm, Wm]):
                        baseboard_m = (2.0 * (float(Lm) + float(Wm))) * (1.0 + waste_pct)
                        baseboard_ft = round(baseboard_m * 3.28084, 1)
                    else:
                        baseboard_m = None
                        baseboard_ft = None

                    if floor_m2 is not None:
                        tile_m2 = floor_m2
                        tile_area_m2 = 0.3 * 0.6
                        tile_count = int(_math.ceil(tile_m2 / tile_area_m2))
                    else:
                        tile_count = None

                    out = {
                        "areas": {
                            "floor_m2": (round(floor_m2, 2) if floor_m2 is not None else None),
                            "walls_m2": (round(walls_m2, 2) if walls_m2 is not None else None),
                            "ceiling_m2": (round(ceil_m2, 2) if ceil_m2 is not None else None),
                        },
                        "quantities": {
                            "flooring_sqft": flooring_sqft,
                            "flooring_m2": (round(flooring_m2_with_waste, 2) if flooring_m2_with_waste is not None else None),
                            "paint_liters_two_coats": paint_liters,
                            "paint_gallons_two_coats": paint_gallons,
                            "baseboard_linear_ft": baseboard_ft,
                            "tile_30x60cm_count": tile_count,
                        },
                        "assumptions": [
                            "Paint coverage ~10 m2/liter/coat; 2 coats",
                            "~10% waste added to flooring and trim",
                            "Windows ~1.5 m2 each; doors ~1.9 m2 each (approx.)",
                        ],
                    }
                except Exception:
                    pass
                return out

            numbers_med = _calc_numbers_med(Lm, Wm, Hm, openings)
            summary.setdefault("spatial_analysis", {})
            summary["spatial_analysis"].update({
                "dimensions_m": {"length_m": Lm, "width_m": Wm, "height_m": Hm},
                "openings": openings,
                "confidence": (spatial_media or {}).get("confidence"),
                **numbers_med,
            })
            try:
                logger.info("[Spatial MEDIA] LxWxH= %s x %s x %s m; floor= %s m2; walls= %s m2; paint (2 coats)= %s L",
                            Lm, Wm, Hm,
                            numbers_med.get("areas",{}).get("floor_m2"),
                            numbers_med.get("areas",{}).get("walls_m2"),
                            numbers_med.get("quantities",{}).get("paint_liters_two_coats") )
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Spatial analysis/quantities (media) failed: {e}")

        # Follow-up idea suggestions
        follow_up_ideas: Dict[str, List[str]] = {}
        try:
            room_hint = getattr(room, "name", None) if 'room' in locals() else None
            follow_up_ideas = await service.gemini.generate_transformation_ideas(summary=summary or {}, room_hint=room_hint, max_ideas=6)
        except Exception as e:
            logger.warning(f"Follow-up idea generation (media) failed: {e}")


        # Optional: grounded product suggestions using requested changes + diffs
        products: List[Dict[str, Any]] = []
        sources: List[str] = []
        grounding_unavailable: bool = False
        grounding_notice: Optional[str] = None
        # Google Search grounding per official docs: https://ai.google.dev/gemini-api/docs/google-search
        # Structured output (JSON) per docs: https://ai.google.dev/gemini-api/docs/structured-output
        if request.enable_grounding:
            try:
                # Canada-first search and local preference: derive location from home if available
                location_hint: str = "Canada"
                try:
                    if room is not None:
                        from sqlalchemy import select as _select
                        from backend.models.home import Home as _Home
                        res_home = await db.execute(_select(_Home).where(_Home.id == room.home_id))
                        home_obj = res_home.scalar_one_or_none()
                        if home_obj and getattr(home_obj, "address", None):
                            addr = home_obj.address or {}
                            parts = [
                                addr.get("city"),
                                addr.get("province"),
                                addr.get("postal_code"),
                                addr.get("country") or "Canada",
                            ]
                            location_hint = ", ".join([p for p in parts if p]) or "Canada"
                except Exception:
                    location_hint = "Canada"

                grounding_input = {
                    "user_prompt": request.prompt,
                    "requested_changes": _extract_requested_changes(request.prompt),
                    "original_summary": original_summary,
                    "new_summary": summary,
                    "location_hint": location_hint,
                }
                grounding = await service.gemini.suggest_products_with_grounding(grounding_input, max_items=5)
                products = grounding.get("products", []) or []
                sources = grounding.get("sources", []) or []
            except Exception as e:
                logger.warning(f"Grounded suggestion failed: {e}")
                # Fallback: function-calling (no google_search) per official docs
                try:
                    fallback = await service.gemini.suggest_products_without_grounding_function_calling(grounding_input, max_items=5)
                    products = fallback.get("products", []) or []
                    sources = fallback.get("sources", []) or []
                except Exception as e2:
                    logger.warning(f"Fallback (function-calling) also failed: {e2}")
                grounding_unavailable = True
                grounding_notice = (
                    "Google Search grounding unavailable. Showing AI suggestions without live web sources."
                )

        # Update status to completed
        processing_time = int(time.time() - start_time)
        await storage_service.update_transformation_status(
            db=db,
            transformation_id=transformation.id,
            status=TransformationStatus.COMPLETED,
            processing_time_seconds=processing_time,
        )

        message_text = f"Generated {len(transformed_images)} variations"
        if 'strict_regen_applied' in locals() and strict_regen_applied:
            if drift_scores and max(drift_scores) > DRIFT_THRESHOLD:
                message_text += " (strict mode applied; high drift persists — consider refining the prompt)"
            else:
                message_text += " (strict mode applied due to high drift)"

        return PromptedTransformResponse(
            success=True,
            message=message_text,
            transformation_id=transformation.id,
            num_variations=len(transformed_images),
            transformation_type="custom",
            original_image_id=request.room_image_id,
            status="completed",
            image_urls=[img.image_url for img in transformation_images],
            summary=summary or {},
            products=products,
            sources=sources,
            grounding_unavailable=grounding_unavailable,
            grounding_notice=grounding_notice,
            follow_up_ideas=follow_up_ideas,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in transform_prompted: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/transform-prompted-upload", response_model=PromptedTransformUploadResponse)
async def transform_prompted_upload(
    request: UploadPromptedTransformRequest,
):
    """
    Transform an uploaded room image (no Digital Twin) based on a freeform prompt.

    - Accepts a base64 data URL or raw base64 image bytes
    - Applies strict preservation rules (only change requested items)
    - Generates 1-4 variations via Gemini image editing (gemini-2.5-flash-image)
    - Stores results to cloud storage when configured, else returns data URLs
    - Analyzes the first result to summarize colors/materials/styles
    - Optionally suggests products using Google Search grounding
    """
    try:
        logger.info("[Transform UPLOAD] Request: prompt_len=%s, num_variations=%s, enable_grounding=%s",
                    len(getattr(request, "prompt", "") or ""),
                    getattr(request, "num_variations", None),
                    getattr(request, "enable_grounding", False))

        # Decode the incoming image (supports data URL or raw base64)
        data = request.image_data_url.strip()
        try:
            b64_part = data.split(",", 1)[1] if data.startswith("data:") else data
            image_bytes = base64.b64decode(b64_part)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image_data_url/base64: {e}")
        image = Image.open(io.BytesIO(image_bytes))
        # Log original size prior to any pre-enhancement
        try:
            logger.info("[HD Pre-enhance UPLOAD] original=%sx%s short_side=%s", image.width, image.height, min(image.width, image.height))
        except Exception:
            pass

        # Pre-enhance low-res uploads to ensure a clean HD baseline (optimized threshold)
        try:
            MIN_SHORT_SIDE = 720  # Reduced from 1080 for faster processing
            if min(image.width, image.height) < MIN_SHORT_SIDE:
                _svc_pre = DesignTransformationService()
                # Only upscale if really needed
                _enh = await _svc_pre.enhance_quality(image=image, upscale_2x=False)
                image = _enh[0] if _enh else image
        except Exception as e:
            logger.warning(f"Pre-enhance (upload) skipped: {e}")

        try:
            logger.info("[HD Pre-enhance UPLOAD] working_size=%sx%s", image.width, image.height)
        except Exception:
            pass

        # Build combined instructions with preservation rules
        service = DesignTransformationService()
        combined_prompt = f"""
Transform this exact room photo according to the user's request below.
Only modify what is asked. Keep all other elements unchanged.

USER REQUEST:
{request.prompt}

{service.CORE_PRESERVATION_RULES}
"""

        # Generate images with Imagen (per official Gemini docs)
        transformed_images = await service._generate_transformation(
            image=image,
            prompt=combined_prompt,
            num_variations=request.num_variations,
        )

        # Drift guard: compute drift vs original; if too high, re-generate once with stricter instructions
        def _compute_drift(a_img: Image.Image, b_img: Image.Image) -> float:
            try:
                a2 = a_img.convert("L").resize((128, 128))
                b2 = b_img.convert("L").resize((128, 128))
                diff = ImageChops.difference(a2, b2)
                stat = ImageStat.Stat(diff)
                return min(1.0, max(0.0, (stat.mean[0] / 255.0)))
            except Exception:
                return 0.0

        # Drift guard disabled for speed optimization
        # Users can regenerate if quality is not satisfactory
        DRIFT_THRESHOLD = 0.25  # Increased threshold to reduce re-generations
        drift_scores = []
        try:
            drift_scores = [_compute_drift(image, img) for img in transformed_images]
        except Exception:
            drift_scores = []

        strict_regen_applied = False
        # Skip strict regeneration for faster results (can be enabled if needed)
        # if drift_scores and max(drift_scores) > DRIFT_THRESHOLD:
        #     ... strict regeneration code ...


        # Enforce HD-quality outputs (upscale if needed)
        try:
            MIN_SHORT_SIDE = 1080
            _svc_hd = DesignTransformationService()
            _hd_images: List[Image.Image] = []
            for _img in transformed_images:
                if min(_img.width, _img.height) < MIN_SHORT_SIDE:
                    # Logging: we are about to upscale this variation to enforce HD
                    try:
                        logger.info("[HD Post-enforce UPLOAD] upscaling variation size=%sx%s", _img.width, _img.height)
                    except Exception:
                        pass

                    try:
                        _enhanced = await _svc_hd.enhance_quality(image=_img, upscale_2x=True)
                        _hd_images.append(_enhanced[0] if _enhanced else _img)
                        try:
                            logger.info("[HD Post-enforce UPLOAD] result size=%sx%s",
                                        (_enhanced[0].width if _enhanced else _img.width),
                                        (_enhanced[0].height if _enhanced else _img.height))
                        except Exception:
                            pass

                    except Exception as ie:
                        logger.warning(f"HD enforce (upload) failed on a variation: {ie}")
                        _hd_images.append(_img)
                else:
                    _hd_images.append(_img)
            transformed_images = _hd_images
        except Exception as e:
            logger.warning(f"HD enforce (upload) skipped: {e}")

        # Prefer hosted URLs when storage is configured; else data URLs
        image_urls: List[str] = []
        storage_service = TransformationStorageService()
        uploaded_session_id = str(uuid.uuid4())

        for idx, img in enumerate(transformed_images, start=1):
            # Try uploading to storage backends
            if storage_service.storage_client is not None:
                try:
                    # Upload using the same organized path as transformations
                    upload_url = storage_service.storage_client.upload_transformation_image(
                        image=img,
                        transformation_id=uploaded_session_id,
                        variation_number=idx,
                        file_extension="jpg",
                    )

                    # Prefer a signed URL for GCS to ensure browser access; otherwise use returned URL
                    url: Optional[str] = upload_url
                    if getattr(storage_service, "storage_type", "").lower() == "gcs" and getattr(storage_service.storage_client, "generate_signed_url", None):
                        try:
                            blob_path = f"transformations/{uploaded_session_id}/variation_{idx}.jpg"
                            url = storage_service.storage_client.generate_signed_url(blob_path)
                        except Exception:
                            # Keep the original upload_url if signing fails
                            url = upload_url
                    image_urls.append(url)
                    continue
                except Exception as e:
                    logger.warning(f"Upload to storage failed, falling back to data URL: {e}")
            # Data URL fallback
            try:
                buf = io.BytesIO()
                img = img.convert("RGB")
                img.save(buf, format="JPEG", quality=90)
                encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
                image_urls.append(f"data:image/jpeg;base64,{encoded}")
            except Exception as e:
                logger.warning(f"Failed to encode generated image: {e}")

        # Post-process: analyze first image
        summary: Dict[str, Any] = {}
        try:
            first_img = transformed_images[0] if transformed_images else None
            if first_img:
                summary = await service.gemini.analyze_design(first_img)
        except Exception as e:
            logger.warning(f"Design analysis (upload) failed: {e}")
            summary = {}

        try:
            logger.info("[Analysis UPLOAD] colors=%s materials=%s styles=%s",
                        len((summary or {}).get("colors", [])),
                        len((summary or {}).get("materials", [])),
                        len((summary or {}).get("styles", [])))
        except Exception:
            pass

        # Analyze original image for diff-aware grounding (best-effort)
        original_summary: Dict[str, Any] = {}
        try:
            original_summary = await service.gemini.analyze_design(image)
        except Exception as e:
            logger.warning(f"Original image analysis (upload) failed: {e}")
            original_summary = {}

        # Optional: grounded product suggestions using requested changes + diffs
        products: List[Dict[str, Any]] = []
        sources: List[str] = []

        # Attach helpful image dimensions to summary
        try:
            def _ratio_str(_w: int, _h: int) -> str:
                try:
                    g = math.gcd(int(_w), int(_h)) if _w > 0 and _h > 0 else 1
                    return f"{int(_w)//g}:{int(_h)//g}" if g else f"{_w}:{_h}"
                except Exception:
                    return "n/a"
            _ow, _oh = (image.width, image.height)
            _rw, _rh = (transformed_images[0].width, transformed_images[0].height) if transformed_images else (None, None)
            summary = summary or {}
            summary["image_details"] = {
                "original": {
                    "width": _ow,
                    "height": _oh,
                    "megapixels": round((_ow * _oh) / 1_000_000, 2),
                    "aspect_ratio": _ratio_str(_ow, _oh),
                },
                "result": {
                    "width": _rw,
                    "height": _rh,
                    "megapixels": (round((_rw * _rh) / 1_000_000, 2) if (_rw and _rh) else None),
                    "aspect_ratio": (_ratio_str(_rw, _rh) if (_rw and _rh) else None),
                },
            }
        except Exception as e:
            logger.warning(f"Failed to attach image_details: {e}")
        # Spatial analysis and material quantity estimation (best-effort)
        try:
            spatial = await service.gemini.analyze_spatial_and_quantities(first_img or image)
            dims = (spatial or {}).get("dimensions") or {}
            openings = (spatial or {}).get("openings") or {}
            Lm = dims.get("length_m") or None
            Wm = dims.get("width_m") or None
            Hm = dims.get("height_m") or None

            def _calc_numbers(Lm, Wm, Hm, openings):
                out = {}
                try:
                    import math as _math
                    if all(isinstance(x, (int, float)) for x in [Lm, Wm]):
                        floor_m2 = max(0.0, float(Lm) * float(Wm))
                        ceil_m2 = floor_m2
                    else:
                        floor_m2 = ceil_m2 = None
                    if all(isinstance(x, (int, float)) for x in [Lm, Wm, Hm]):
                        perimeter_m = 2.0 * (float(Lm) + float(Wm))
                        walls_m2_raw = perimeter_m * float(Hm)
                        # Subtract estimated openings if counts available
                        windows = (openings.get("windows") if isinstance(openings, dict) else None)
                        doors = (openings.get("doors") if isinstance(openings, dict) else None)
                        openings_m2 = 0.0
                        try:
                            if isinstance(windows, int):
                                openings_m2 += windows * 1.5  # ~1.5 m2 per window
                            if isinstance(doors, int):
                                openings_m2 += doors * 1.9   # ~1.9 m2 per door
                        except Exception:
                            pass
                        walls_m2 = max(0.0, walls_m2_raw - openings_m2)
                    else:
                        walls_m2 = None

                    # Paint assumptions
                    coverage_m2_per_liter = 10.0  # 1L covers ~10 m2 per coat
                    coats = 2
                    waste_pct = 0.10

                    # Flooring and trim
                    if floor_m2 is not None:
                        flooring_m2_with_waste = floor_m2 * (1.0 + waste_pct)
                        flooring_sqft = round(flooring_m2_with_waste * 10.7639, 1)
                    else:
                        flooring_m2_with_waste = None
                        flooring_sqft = None

                    if walls_m2 is not None:
                        paint_liters = round((walls_m2 / coverage_m2_per_liter) * coats, 1)
                        paint_gallons = round(paint_liters / 3.785, 2)
                    else:
                        paint_liters = None
                        paint_gallons = None

                    # Baseboard linear length (perimeter)
                    if all(isinstance(x, (int, float)) for x in [Lm, Wm]):
                        baseboard_m = (2.0 * (float(Lm) + float(Wm))) * (1.0 + waste_pct)
                        baseboard_ft = round(baseboard_m * 3.28084, 1)
                    else:
                        baseboard_m = None
                        baseboard_ft = None

                    # Simple tile estimate (e.g., 30x60cm tile on floor)
                    if floor_m2 is not None:
                        tile_m2 = floor_m2
                        tile_area_m2 = 0.3 * 0.6
                        tile_count = int(_math.ceil(tile_m2 / tile_area_m2))
                    else:
                        tile_count = None

                    out = {
                        "areas": {
                            "floor_m2": (round(floor_m2, 2) if floor_m2 is not None else None),
                            "walls_m2": (round(walls_m2, 2) if walls_m2 is not None else None),
                            "ceiling_m2": (round(ceil_m2, 2) if ceil_m2 is not None else None),
                        },
                        "quantities": {
                            "flooring_sqft": flooring_sqft,
                            "flooring_m2": (round(flooring_m2_with_waste, 2) if flooring_m2_with_waste is not None else None),
                            "paint_liters_two_coats": paint_liters,
                            "paint_gallons_two_coats": paint_gallons,
                            "baseboard_linear_ft": baseboard_ft,
                            "tile_30x60cm_count": tile_count,
                        },
                        "assumptions": [
                            "Paint coverage ~10 m2/liter/coat; 2 coats",
                            "~10% waste added to flooring and trim",
                            "Windows ~1.5 m2 each; doors ~1.9 m2 each (approx.)",
                        ],
                    }
                except Exception:
                    pass
                return out

            numbers = _calc_numbers(Lm, Wm, Hm, openings)
            summary.setdefault("spatial_analysis", {})
            summary["spatial_analysis"].update({
                "dimensions_m": {"length_m": Lm, "width_m": Wm, "height_m": Hm},
                "openings": openings,
                "confidence": (spatial or {}).get("confidence"),
                **numbers,
            })
            try:
                logger.info("[Spatial] LxWxH= %s x %s x %s m; floor= %s m2; walls= %s m2; paint (2 coats)= %s L",
                            Lm, Wm, Hm,
                            numbers.get("areas",{}).get("floor_m2"),
                            numbers.get("areas",{}).get("walls_m2"),
                            numbers.get("quantities",{}).get("paint_liters_two_coats") )
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Spatial analysis/quantities failed: {e}")

        # Follow-up transformation suggestions
        follow_up_ideas: Dict[str, List[str]] = {}
        try:
            follow_up_ideas = await service.gemini.generate_transformation_ideas(summary=summary or {}, room_hint=None, max_ideas=6)
        except Exception as e:
            logger.warning(f"Follow-up idea generation failed: {e}")


        grounding_unavailable: bool = False
        grounding_notice: Optional[str] = None
        # Google Search grounding per official docs: https://ai.google.dev/gemini-api/docs/google-search
        # Structured output (JSON) per docs: https://ai.google.dev/gemini-api/docs/structured-output
        if request.enable_grounding:
            try:
                grounding_input = {
                    "user_prompt": request.prompt,
                    "requested_changes": _extract_requested_changes(request.prompt),
                    "original_summary": original_summary,
                    "new_summary": summary,
                    "location_hint": os.getenv("DEFAULT_LOCATION_HINT", "Vancouver, BC, Canada"),

                }
                grounding = await service.gemini.suggest_products_with_grounding(grounding_input, max_items=5)
                products = grounding.get("products", []) or []
                sources = grounding.get("sources", []) or []
                grounding_notice = grounding.get("grounding_notice") or grounding_notice
                if not products:
                    try:
                        fallback2 = await service.gemini.suggest_products_without_grounding_function_calling(grounding_input, max_items=5)
                        products = fallback2.get("products", []) or []
                        sources = fallback2.get("sources", []) or []
                        if not products:
                            grounding_notice = grounding_notice or "No Canadian product pages were found via Google Search. Showing AI-suggested alternatives when available."
                    except Exception as e3:
                        logger.warning(f"Secondary fallback (no results, upload) failed: {e3}")

            except Exception as e:
                logger.warning(f"Grounded suggestion (upload) failed: {e}")
                # Fallback: function-calling (no google_search) per official docs
                try:
                    fallback = await service.gemini.suggest_products_without_grounding_function_calling(grounding_input, max_items=5)
                    products = fallback.get("products", []) or []
                    sources = fallback.get("sources", []) or []
                except Exception as e2:
                    logger.warning(f"Fallback (function-calling, upload) also failed: {e2}")
                grounding_unavailable = True


        return PromptedTransformUploadResponse(
            success=True,
            message=f"Generated {len(image_urls)} variations",
            num_variations=len(image_urls),
            image_urls=image_urls,
            summary=summary or {},
            products=products,
            sources=sources,
            grounding_unavailable=grounding_unavailable,
            grounding_notice=grounding_notice,
            follow_up_ideas=follow_up_ideas or {},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"transform_prompted_upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/virtual-staging-upload", response_model=PromptedTransformUploadResponse)
async def virtual_staging_upload(request: VirtualStagingUploadRequest):
    """
    Virtual Staging for uploaded images (no Digital Twin required).
    Accepts a base64 data URL and returns hosted URLs or data URLs of results.
    """
    try:
        logger.info("[VirtualStaging UPLOAD] Request: preset=%s, prompt_len=%s, density=%s, lock_envelope=%s, num_variations=%s, enable_grounding=%s",
                    getattr(request, "style_preset", None),
                    len(getattr(request, "style_prompt", "") or ""),
                    getattr(request, "furniture_density", None),
                    getattr(request, "lock_envelope", None),
                    getattr(request, "num_variations", None),
                    getattr(request, "enable_grounding", False))

        # Decode uploaded image
        data = request.image_data_url.strip()
        try:
            b64_part = data.split(",", 1)[1] if data.startswith("data:") else data
            image_bytes = base64.b64decode(b64_part)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image_data_url/base64: {e}")
        image = Image.open(io.BytesIO(image_bytes))

        try:
            logger.info("[HD Pre-enhance VS] original=%sx%s short_side=%s", image.width, image.height, min(image.width, image.height))
        except Exception:
            pass

        # Pre-enhance low-res uploads to ensure a clean HD baseline
        try:
            MIN_SHORT_SIDE = 1080
            if min(image.width, image.height) < MIN_SHORT_SIDE:
                _svc_pre_vs = DesignTransformationService()
                _enh_vs = await _svc_pre_vs.enhance_quality(image=image, upscale_2x=True)
                image = _enh_vs[0] if _enh_vs else image
        except Exception as e:
            logger.warning(f"Pre-enhance (virtual-staging-upload) skipped: {e}")

        try:
            logger.info("[HD Pre-enhance VS] working_size=%sx%s", image.width, image.height)
        except Exception:
            pass


        # Generate
        service = DesignTransformationService()
        transformed_images = await service.transform_virtual_staging(
            image=image,
            style_preset=request.style_preset,
            style_prompt=request.style_prompt,
            furniture_density=request.furniture_density,
            lock_envelope=request.lock_envelope,
            num_variations=request.num_variations,
        )

        # Enforce HD-quality outputs (upscale if needed)
        try:
            MIN_SHORT_SIDE = 1080
            _svc_hd_vs = DesignTransformationService()
            _hd_images_vs: List[Image.Image] = []
            for _img in transformed_images:
                if min(_img.width, _img.height) < MIN_SHORT_SIDE:
                    try:
                        logger.info("[HD Post-enforce VS] upscaling variation size=%sx%s", _img.width, _img.height)
                    except Exception:
                        pass

                    try:
                        _enhanced_vs = await _svc_hd_vs.enhance_quality(image=_img, upscale_2x=True)
                        _hd_images_vs.append(_enhanced_vs[0] if _enhanced_vs else _img)
                        try:
                            logger.info("[HD Post-enforce VS] result size=%sx%s",
                                        (_enhanced_vs[0].width if _enhanced_vs else _img.width),
                                        (_enhanced_vs[0].height if _enhanced_vs else _img.height))
                        except Exception:
                            pass

                    except Exception as ie:
                        logger.warning(f"HD enforce (virtual-staging-upload) failed on a variation: {ie}")
                        _hd_images_vs.append(_img)
                else:
                    _hd_images_vs.append(_img)
            transformed_images = _hd_images_vs
        except Exception as e:
            logger.warning(f"HD enforce (virtual-staging-upload) skipped: {e}")

        # Upload to storage when configured; else return data URLs


        image_urls: List[str] = []
        storage_service = TransformationStorageService()
        uploaded_session_id = str(uuid.uuid4())
        for idx, img in enumerate(transformed_images, start=1):
            if storage_service.storage_client is not None:
                try:
                    upload_url = storage_service.storage_client.upload_transformation_image(
                        image=img,
                        transformation_id=uploaded_session_id,
                        variation_number=idx,
                        file_extension="jpg",
                    )
                    url: Optional[str] = upload_url
                    if getattr(storage_service, "storage_type", "").lower() == "gcs" and getattr(storage_service.storage_client, "generate_signed_url", None):
                        try:
                            blob_path = f"transformations/{uploaded_session_id}/variation_{idx}.jpg"
                            url = storage_service.storage_client.generate_signed_url(blob_path)
                        except Exception:
                            url = upload_url
                    image_urls.append(url)
                    continue
                except Exception as e:
                    logger.warning(f"Upload to storage failed, falling back to data URL: {e}")
            # Fallback to data URL
            try:
                buf = io.BytesIO()
                img = img.convert("RGB")
                img.save(buf, format="JPEG", quality=90)
                encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
                image_urls.append(f"data:image/jpeg;base64,{encoded}")
            except Exception as e:
                logger.warning(f"Failed to encode generated image: {e}")

        # Analyze results
        summary: Dict[str, Any] = {}
        try:
            first_img = transformed_images[0] if transformed_images else None
            if first_img:
                summary = await service.gemini.analyze_design(first_img)
        except Exception as e:
            logger.warning(f"Design analysis (virtual-staging-upload) failed: {e}")
            summary = {}

        try:
            logger.info("[Analysis VS] colors=%s materials=%s styles=%s",
                        len((summary or {}).get("colors", [])),
                        len((summary or {}).get("materials", [])),
                        len((summary or {}).get("styles", [])))
        except Exception:
            pass

        # Attach helpful image dimensions to summary
        try:
            def _ratio_str_vs(_w: int, _h: int) -> str:
                try:
                    g = math.gcd(int(_w), int(_h)) if _w > 0 and _h > 0 else 1
                    return f"{int(_w)//g}:{int(_h)//g}" if g else f"{_w}:{_h}"
                except Exception:
                    return "n/a"
            _ow, _oh = (image.width, image.height)
            _rw, _rh = (transformed_images[0].width, transformed_images[0].height) if transformed_images else (None, None)
            summary = summary or {}
            summary["image_details"] = {
                "original": {
                    "width": _ow,
                    "height": _oh,
                    "megapixels": round((_ow * _oh) / 1_000_000, 2),
                    "aspect_ratio": _ratio_str_vs(_ow, _oh),
                },
                "result": {
                    "width": _rw,
                    "height": _rh,
                    "megapixels": (round((_rw * _rh) / 1_000_000, 2) if (_rw and _rh) else None),
                    "aspect_ratio": (_ratio_str_vs(_rw, _rh) if (_rw and _rh) else None),
                },
            }
        except Exception as e:
            logger.warning(f"Failed to attach image_details (virtual staging): {e}")

        # Spatial analysis and material quantity estimation (best-effort)
        try:
            spatial_vs = await service.gemini.analyze_spatial_and_quantities(first_img or image)
            dims = (spatial_vs or {}).get("dimensions") or {}
            openings = (spatial_vs or {}).get("openings") or {}
            Lm = dims.get("length_m") or None
            Wm = dims.get("width_m") or None
            Hm = dims.get("height_m") or None

            def _calc_numbers_vs(Lm, Wm, Hm, openings):
                out = {}
                try:
                    import math as _math
                    if all(isinstance(x, (int, float)) for x in [Lm, Wm]):
                        floor_m2 = max(0.0, float(Lm) * float(Wm))
                        ceil_m2 = floor_m2
                    else:
                        floor_m2 = ceil_m2 = None
                    if all(isinstance(x, (int, float)) for x in [Lm, Wm, Hm]):
                        perimeter_m = 2.0 * (float(Lm) + float(Wm))
                        walls_m2_raw = perimeter_m * float(Hm)
                        # openings
                        windows = (openings.get("windows") if isinstance(openings, dict) else None)
                        doors = (openings.get("doors") if isinstance(openings, dict) else None)
                        openings_m2 = 0.0
                        try:
                            if isinstance(windows, int):
                                openings_m2 += windows * 1.5
                            if isinstance(doors, int):
                                openings_m2 += doors * 1.9
                        except Exception:
                            pass
                        walls_m2 = max(0.0, walls_m2_raw - openings_m2)
                    else:
                        walls_m2 = None

                    coverage_m2_per_liter = 10.0
                    coats = 2
                    waste_pct = 0.10

                    if floor_m2 is not None:
                        flooring_m2_with_waste = floor_m2 * (1.0 + waste_pct)
                        flooring_sqft = round(flooring_m2_with_waste * 10.7639, 1)
                    else:
                        flooring_m2_with_waste = None
                        flooring_sqft = None

                    if walls_m2 is not None:
                        paint_liters = round((walls_m2 / coverage_m2_per_liter) * coats, 1)
                        paint_gallons = round(paint_liters / 3.785, 2)
                    else:
                        paint_liters = None
                        paint_gallons = None

                    if all(isinstance(x, (int, float)) for x in [Lm, Wm]):
                        baseboard_m = (2.0 * (float(Lm) + float(Wm))) * (1.0 + waste_pct)
                        baseboard_ft = round(baseboard_m * 3.28084, 1)
                    else:
                        baseboard_m = None
                        baseboard_ft = None

                    if floor_m2 is not None:
                        tile_m2 = floor_m2
                        tile_area_m2 = 0.3 * 0.6
                        tile_count = int(_math.ceil(tile_m2 / tile_area_m2))
                    else:
                        tile_count = None

                    out = {
                        "areas": {
                            "floor_m2": (round(floor_m2, 2) if floor_m2 is not None else None),
                            "walls_m2": (round(walls_m2, 2) if walls_m2 is not None else None),
                            "ceiling_m2": (round(ceil_m2, 2) if ceil_m2 is not None else None),
                        },
                        "quantities": {
                            "flooring_sqft": flooring_sqft,
                            "flooring_m2": (round(flooring_m2_with_waste, 2) if flooring_m2_with_waste is not None else None),
                            "paint_liters_two_coats": paint_liters,
                            "paint_gallons_two_coats": paint_gallons,
                            "baseboard_linear_ft": baseboard_ft,
                            "tile_30x60cm_count": tile_count,
                        },
                        "assumptions": [
                            "Paint coverage ~10 m2/liter/coat; 2 coats",
                            "~10% waste added to flooring and trim",
                            "Windows ~1.5 m2 each; doors ~1.9 m2 each (approx.)",
                        ],
                    }
                except Exception:
                    pass
                return out

            numbers_vs = _calc_numbers_vs(Lm, Wm, Hm, openings)
            summary.setdefault("spatial_analysis", {})
            summary["spatial_analysis"].update({
                "dimensions_m": {"length_m": Lm, "width_m": Wm, "height_m": Hm},
                "openings": openings,
                "confidence": (spatial_vs or {}).get("confidence"),
                **numbers_vs,
            })
            try:
                logger.info("[Spatial VS] LxWxH= %s x %s x %s m; floor= %s m2; walls= %s m2; paint (2 coats)= %s L",
                            Lm, Wm, Hm,
                            numbers_vs.get("areas",{}).get("floor_m2"),
                            numbers_vs.get("areas",{}).get("walls_m2"),
                            numbers_vs.get("quantities",{}).get("paint_liters_two_coats") )
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Spatial analysis/quantities (virtual-staging) failed: {e}")

        # Follow-up transformation suggestions (virtual staging)
        follow_up_ideas: Dict[str, List[str]] = {}
        try:
            follow_up_ideas = await service.gemini.generate_transformation_ideas(summary=summary or {}, room_hint=None, max_ideas=6)
        except Exception as e:
            logger.warning(f"Follow-up idea generation (virtual staging) failed: {e}")

        # Diff-aware grounding (optional)
        products: List[Dict[str, Any]] = []
        sources: List[str] = []
        grounding_unavailable: bool = False
        grounding_notice: Optional[str] = None
        if getattr(request, "enable_grounding", False):
            try:
                original_summary: Dict[str, Any] = {}
                try:
                    original_summary = await service.gemini.analyze_design(image)
                except Exception:
                    original_summary = {}
                user_prompt = f"Virtual staging. Preset: {request.style_preset or ''}. Style: {request.style_prompt or ''}. Density: {request.furniture_density}."
                grounding_input = {
                    "user_prompt": user_prompt,
                    "requested_changes": ["furniture", "decor"],
                    "original_summary": original_summary,
                    "new_summary": summary,
                    "location_hint": os.getenv("DEFAULT_LOCATION_HINT", "Vancouver, BC, Canada"),
                }
                grounding = await service.gemini.suggest_products_with_grounding(grounding_input, max_items=5)
                products = grounding.get("products", []) or []
                sources = grounding.get("sources", []) or []
                # If grounding returns empty, try function-calling fallback
                if not products:
                    try:
                        fallback2 = await service.gemini.suggest_products_without_grounding_function_calling(grounding_input, max_items=5)
                        products = fallback2.get("products", []) or []
                        sources = fallback2.get("sources", []) or []
                        if not products:
                            grounding_notice = "No Canadian product pages were found via Google Search. Showing AI-suggested alternatives when available."
                    except Exception as e3:
                        logger.warning(f"Secondary fallback (no results, virtual-staging-upload) failed: {e3}")

            except Exception as e:
                logger.warning(f"Grounded suggestion (virtual-staging-upload) failed: {e}")
                grounding_unavailable = True
                grounding_notice = (
                    "Google Search grounding unavailable. Showing AI suggestions without live web sources."
                )
                try:
                    fallback = await service.gemini.suggest_products_without_grounding_function_calling(grounding_input, max_items=5)  # type: ignore[name-defined]
                    products = fallback.get("products", []) or []
                    sources = fallback.get("sources", []) or []
                except Exception as e2:
                    logger.warning(f"Fallback (function-calling, virtual-staging-upload) also failed: {e2}")

        return PromptedTransformUploadResponse(
            success=True,
            message=f"Generated {len(image_urls)} variations",
            num_variations=len(image_urls),
            image_urls=image_urls,
            summary=summary or {},
            products=products,
            sources=sources,
            grounding_unavailable=grounding_unavailable,
            grounding_notice=grounding_notice,
            follow_up_ideas=follow_up_ideas or {},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"virtual_staging_upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unstage-upload", response_model=PromptedTransformUploadResponse)
async def unstage_upload(request: UnstagingUploadRequest):
    """
    Unstaging for uploaded images (no Digital Twin): remove furnishings/decor.
    """
    try:
        data = request.image_data_url.strip()
        try:
            b64_part = data.split(",", 1)[1] if data.startswith("data:") else data
            image_bytes = base64.b64decode(b64_part)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image_data_url/base64: {e}")
        image = Image.open(io.BytesIO(image_bytes))

        service = DesignTransformationService()
        transformed_images = await service.transform_unstaging(
            image=image,
            strength=request.strength,
            num_variations=request.num_variations,
        )

        image_urls: List[str] = []
        storage_service = TransformationStorageService()
        uploaded_session_id = str(uuid.uuid4())
        for idx, img in enumerate(transformed_images, start=1):
            if storage_service.storage_client is not None:
                try:
                    upload_url = storage_service.storage_client.upload_transformation_image(
                        image=img,
                        transformation_id=uploaded_session_id,
                        variation_number=idx,
                        file_extension="jpg",
                    )
                    url: Optional[str] = upload_url
                    if getattr(storage_service, "storage_type", "").lower() == "gcs" and getattr(storage_service.storage_client, "generate_signed_url", None):
                        try:
                            blob_path = f"transformations/{uploaded_session_id}/variation_{idx}.jpg"
                            url = storage_service.storage_client.generate_signed_url(blob_path)
                        except Exception:
                            url = upload_url
                    image_urls.append(url)
                    continue
                except Exception as e:
                    logger.warning(f"Upload to storage failed, falling back to data URL: {e}")
            try:
                buf = io.BytesIO()
                img = img.convert("RGB")
                img.save(buf, format="JPEG", quality=90)
                encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
                image_urls.append(f"data:image/jpeg;base64,{encoded}")
            except Exception as e:
                logger.warning(f"Failed to encode generated image: {e}")


        return PromptedTransformUploadResponse(
            success=True,
            message=f"Generated {len(image_urls)} variations",
            num_variations=len(image_urls),
            image_urls=image_urls,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"unstage_upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edit-with-mask-upload", response_model=PromptedTransformUploadResponse)
async def edit_with_mask_upload(request: MaskedEditUploadRequest):
    """
    Masked edit for uploaded images (no Digital Twin): remove/replace within white mask.
    """
    try:
        # Decode image
        data = request.image_data_url.strip()
        try:
            b64_part = data.split(",", 1)[1] if data.startswith("data:") else data
            image_bytes = base64.b64decode(b64_part)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image_data_url/base64: {e}")
        image = Image.open(io.BytesIO(image_bytes))

        # Decode mask
        if not request.mask_data_url.startswith("data:"):
            raise HTTPException(status_code=400, detail="mask_data_url must be a data URL")
        _, b64mask = request.mask_data_url.split(",", 1)
        mask_bytes = base64.b64decode(b64mask)

        service = DesignTransformationService()
        transformed_images = await service.transform_masked_edit(
            image=image,
            mask_image=mask_bytes,
            operation=request.operation,
            replacement_prompt=request.replacement_prompt,
            num_variations=request.num_variations,
        )

        image_urls: List[str] = []
        storage_service = TransformationStorageService()
        uploaded_session_id = str(uuid.uuid4())
        for idx, img in enumerate(transformed_images, start=1):
            if storage_service.storage_client is not None:
                try:
                    upload_url = storage_service.storage_client.upload_transformation_image(
                        image=img,
                        transformation_id=uploaded_session_id,
                        variation_number=idx,
                        file_extension="jpg",
                    )
                    url: Optional[str] = upload_url
                    if getattr(storage_service, "storage_type", "").lower() == "gcs" and getattr(storage_service.storage_client, "generate_signed_url", None):
                        try:
                            blob_path = f"transformations/{uploaded_session_id}/variation_{idx}.jpg"
                            url = storage_service.storage_client.generate_signed_url(blob_path)
                        except Exception:
                            url = upload_url
                    image_urls.append(url)
                    continue
                except Exception as e:
                    logger.warning(f"Upload to storage failed, falling back to data URL: {e}")
            try:
                buf = io.BytesIO()
                img = img.convert("RGB")
                img.save(buf, format="JPEG", quality=90)
                encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
                image_urls.append(f"data:image/jpeg;base64,{encoded}")
            except Exception as e:
                logger.warning(f"Failed to encode generated image: {e}")

        return PromptedTransformUploadResponse(
            success=True,
            message=f"Generated {len(image_urls)} variations",
            num_variations=len(image_urls),
            image_urls=image_urls,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"edit_with_mask_upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/segment-upload", response_model=SegmentResponse)
async def segment_upload(request: SegmentUploadRequest):
    """
    AI segmentation assist for uploaded images: returns mask data URLs.
    """
    try:
        data = request.image_data_url.strip()
        try:
            b64_part = data.split(",", 1)[1] if data.startswith("data:") else data
            image_bytes = base64.b64decode(b64_part)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image_data_url/base64: {e}")
        image = Image.open(io.BytesIO(image_bytes))

        service = DesignTransformationService()
        masks = await service.gemini.segment_image(
            reference_image=image,
            segment_class=request.segment_class,
            points=request.points,
            num_masks=request.num_masks,
        )

        data_urls: List[str] = []
        for m in masks:
            buf = io.BytesIO()
            m.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            data_urls.append(f"data:image/png;base64,{b64}")

        return SegmentResponse(mask_data_urls=data_urls)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"segment_upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-angle-upload", response_model=PromptedTransformUploadResponse)
async def multi_angle_upload(request: MultiAngleUploadRequest):
    """
    Generate small, plausible viewpoint variations of an uploaded room image.
    Returns 1-4 images representing slight camera shifts (yaw/pitch) while preserving scene content.
    """
    try:
        data = request.image_data_url.strip()
        try:
            b64_part = data.split(",", 1)[1] if data.startswith("data:") else data
            image_bytes = base64.b64decode(b64_part)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image_data_url/base64: {e}")
        image = Image.open(io.BytesIO(image_bytes))

        service = DesignTransformationService()
        generated = await service.transform_multi_angle_views(
            image=image,
            num_angles=request.num_angles,
            yaw_degrees=request.yaw_degrees,
            pitch_degrees=request.pitch_degrees,
        )

        image_urls: List[str] = []
        storage_service = TransformationStorageService()
        uploaded_session_id = str(uuid.uuid4())
        for idx, img in enumerate(generated, start=1):
            if storage_service.storage_client is not None:
                try:
                    upload_url = await storage_service.upload_transformed_image(
                        img,
                        uploaded_session_id=uploaded_session_id,
                        index=idx,
                        variant="multi_angle",
                    )
                    url = upload_url
                    if storage_service.storage_client is not None:
                        try:
                            url = await storage_service.sign_url(upload_url)
                        except Exception:
                            url = upload_url
                    image_urls.append(url)
                    continue
                except Exception as e:
                    logger.warning(f"Upload to storage failed, falling back to data URL: {e}")
            try:
                buf = io.BytesIO()
                img = img.convert("RGB")
                img.save(buf, format="JPEG", quality=90)
                encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
                image_urls.append(f"data:image/jpeg;base64,{encoded}")
            except Exception as e:
                logger.warning(f"Failed to encode generated image: {e}")

        return PromptedTransformUploadResponse(
            success=True,
            message=f"Generated {len(image_urls)} multi-angle views",
            num_variations=len(image_urls),
            image_urls=image_urls,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"multi_angle_upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance-upload", response_model=PromptedTransformUploadResponse)
async def enhance_upload(request: EnhanceUploadRequest):
    """
    Enhance image quality (denoise, deblur, sharpen, optional 2x upscale) for uploaded images.
    Preserves scene content and composition.
    """
    try:
        data = request.image_data_url.strip()
        try:
            b64_part = data.split(",", 1)[1] if data.startswith("data:") else data
            image_bytes = base64.b64decode(b64_part)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image_data_url/base64: {e}")
        image = Image.open(io.BytesIO(image_bytes))

        service = DesignTransformationService()
        enhanced_list = await service.enhance_quality(
            image=image,
            upscale_2x=bool(request.upscale_2x),
        )
        enhanced = enhanced_list[0] if enhanced_list else image

        image_urls: List[str] = []
        storage_service = TransformationStorageService()
        if storage_service.storage_client is not None:
            try:
                upload_url = await storage_service.upload_transformed_image(
                    enhanced,
                    uploaded_session_id=str(uuid.uuid4()),
                    index=1,
                    variant="enhanced",
                )
                url = upload_url
                if storage_service.storage_client is not None:
                    try:
                        url = await storage_service.sign_url(upload_url)
                    except Exception:
                        url = upload_url
                image_urls.append(url)
            except Exception as e:
                logger.warning(f"Upload to storage failed, falling back to data URL: {e}")
        if not image_urls:
            try:
                buf = io.BytesIO()
                enhanced = enhanced.convert("RGB")
                enhanced.save(buf, format="JPEG", quality=92)
                encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
                image_urls.append(f"data:image/jpeg;base64,{encoded}")
            except Exception as e:
                logger.warning(f"Failed to encode enhanced image: {e}")

        return PromptedTransformUploadResponse(
            success=True,
            message="Enhanced image",
            num_variations=len(image_urls),
            image_urls=image_urls,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"enhance_upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))




# Analyze uploaded image (no Digital Twin) for idea chips
class AnalyzeUploadedImageRequest(BaseModel):
    image_data_url: str
    max_ideas: int = Field(default=4, ge=1, le=6)


@router.post("/analyze-uploaded-image", response_model=AnalyzeImageResponse)
async def analyze_uploaded_image(
    request: AnalyzeUploadedImageRequest,
):
    """Analyze an uploaded image and return summary + categorized ideas."""
    try:
        data = request.image_data_url.strip()
        try:
            b64_part = data.split(",", 1)[1] if data.startswith("data:") else data
            image_bytes = base64.b64decode(b64_part)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image_data_url/base64: {e}")

        image = Image.open(io.BytesIO(image_bytes))

        service = DesignTransformationService()
        summary = await service.gemini.analyze_design(image)

        max_ideas = max(1, min(request.max_ideas, 6))
        ideas_by_theme: Dict[str, List[str]] = await service.gemini.generate_transformation_ideas(
            summary=summary or {}, room_hint=None, max_ideas=max_ideas
        )

        ordered_keys = ["color", "flooring", "lighting", "decor", "other"]
        ideas: List[str] = []
        for key in ordered_keys:
            for idea in ideas_by_theme.get(key, []) or []:
                if len(ideas) >= max_ideas:
                    break
                if idea not in ideas:
                    ideas.append(idea)

        if not ideas:
            try:
                colors = summary.get("colors") or []
                if isinstance(colors, list) and colors:
                    c = colors[0] or {}
                    color_name = c.get("name") or c.get("hex")
                    if color_name:
                        ideas.append(f"Change walls to {color_name}")
                materials = [str(m).lower() for m in (summary.get("materials") or [])]
                mats = " ".join(materials)
                if "oak" in mats:
                    ideas.append("Replace with light oak hardwood")
                if "tile" in mats:
                    ideas.append("Update flooring with patterned tile")
                styles = summary.get("styles") or []
                if isinstance(styles, list) and styles:
                    style0 = str(styles[0])
                    ideas.append(f"Add {style0} decor elements")
                    ideas.append(f"Use a {style0} palette")
            except Exception:
                pass
            if not ideas:
                ideas.extend(["Warm neutral palette", "Add matte-black pendant lights"])
            ideas = ideas[:max_ideas]

        # Suggested style transformations (Gemini text)
        try:
            style_transformations = await service.gemini.generate_style_transformations(summary=summary or {}, room_hint=None, max_items=4)
        except Exception:
            style_transformations = []

        return AnalyzeImageResponse(summary=summary or {}, ideas=ideas, ideas_by_theme=ideas_by_theme or {}, style_transformations=style_transformations)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"analyze_uploaded_image failed: {e}", exc_info=True)
        return AnalyzeImageResponse(summary={}, ideas=[])



@router.post("/analyze-image", response_model=AnalyzeImageResponse)
async def analyze_image(
    request: AnalyzeImageRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze a selected room image and return a structured summary plus suggested idea chips.
    """
    try:
        # Load the room image and its room for context
        room_image = await load_room_image(request.room_image_id, db)
        from sqlalchemy import select
        room = None
        try:
            result = await db.execute(select(Room).where(Room.id == room_image.room_id))
            room = result.scalar_one_or_none()
        except Exception:
            room = None

        # Fetch the image
        image = await get_image_from_url(room_image.image_url)

        # Analyze with Gemini vision per official docs
        service = DesignTransformationService()
        room_hint = getattr(room, "name", None)
        summary = await service.gemini.analyze_design(image, room_hint=room_hint)

        # Generate room-aware, multi-step ideas grouped by theme via Gemini text model
        max_ideas = max(1, min(request.max_ideas, 6))
        ideas_by_theme: Dict[str, List[str]] = await service.gemini.generate_transformation_ideas(
            summary=summary or {}, room_hint=room_hint, max_ideas=max_ideas
        )

        # Flatten into a simple chips list (preserving category ordering)
        ordered_keys = ["color", "flooring", "lighting", "decor", "other"]
        ideas: List[str] = []
        for key in ordered_keys:
            for idea in ideas_by_theme.get(key, []) or []:
                if len(ideas) >= max_ideas:
                    break
                if idea not in ideas:
                    ideas.append(idea)

        # Fallback heuristics if the model returned nothing
        if not ideas:
            def add_idea(text: str):
                if text and text not in ideas:
                    ideas.append(text)
            try:
                colors = summary.get("colors") or []
                if isinstance(colors, list) and colors:
                    c = colors[0] or {}
                    color_name = c.get("name") or c.get("hex")
                    if color_name:
                        add_idea(f"Change walls to {color_name}")
                materials = [str(m).lower() for m in (summary.get("materials") or [])]
                mats = " ".join(materials)
                if "oak" in mats:
                    add_idea("Replace with light oak hardwood")
                if "tile" in mats:
                    add_idea("Update flooring with patterned tile")
                if "marble" in mats:
                    add_idea("Add marble accents on surfaces")
                styles = summary.get("styles") or []
                if isinstance(styles, list) and styles:
                    style0 = str(styles[0])
                    add_idea(f"Add {style0} decor elements")
                    add_idea(f"Use a {style0} palette")
            except Exception:
                pass
            add_idea("Warm neutral palette")
            add_idea("Add matte-black pendant lights")
            ideas = ideas[:max_ideas]

        # Suggested style transformations (Gemini text)
        try:
            style_transformations = await service.gemini.generate_style_transformations(summary=summary or {}, room_hint=room_hint, max_items=4)
        except Exception:
            style_transformations = []

        return AnalyzeImageResponse(summary=summary or {}, ideas=ideas, ideas_by_theme=ideas_by_theme or {}, style_transformations=style_transformations)
    except Exception as e:
        logger.warning(f"analyze_image failed: {e}", exc_info=True)
        # Degrade gracefully with empty ideas so the UI still renders
        return AnalyzeImageResponse(summary={}, ideas=[])


# ============================================================================
# Enhanced Spatial Analysis Endpoints
# ============================================================================

class BoundingBoxAnalysisRequest(BaseModel):
    """Request for bounding box object detection."""
    image_data_url: str
    objects_to_detect: Optional[List[str]] = Field(None, description="Specific objects to detect (e.g., ['sofa', 'lamp'])")
    room_hint: Optional[str] = Field(None, description="Room type hint")


class BoundingBoxAnalysisResponse(BaseModel):
    """Response with detected objects and bounding boxes."""
    objects: List[Dict[str, Any]]
    image_dimensions: Dict[str, int]


@router.post("/analyze-bounding-boxes", response_model=BoundingBoxAnalysisResponse)
async def analyze_bounding_boxes(request: BoundingBoxAnalysisRequest):
    """
    Detect objects in an image and return bounding boxes with normalized coordinates.

    Based on Google Gemini spatial understanding capabilities.
    """
    try:
        service = DesignTransformationService()

        # Decode image
        image_data = request.image_data_url.split(",")[1] if "," in request.image_data_url else request.image_data_url
        image_bytes = base64.b64decode(image_data)

        # Analyze with bounding boxes
        result = await service.gemini.analyze_with_bounding_boxes(
            image=image_bytes,
            objects_to_detect=request.objects_to_detect,
            room_hint=request.room_hint
        )

        logger.info(f"[BoundingBoxes] Detected {len(result.get('objects', []))} objects")

        return BoundingBoxAnalysisResponse(
            objects=result.get("objects", []),
            image_dimensions=result.get("image_dimensions", {})
        )

    except Exception as e:
        logger.error(f"analyze_bounding_boxes failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class SegmentationAnalysisRequest(BaseModel):
    """Request for image segmentation."""
    image_data_url: str
    objects_to_segment: Optional[List[str]] = Field(None, description="Specific objects to segment")
    room_hint: Optional[str] = None


class SegmentationAnalysisResponse(BaseModel):
    """Response with segmented objects and masks."""
    segments: List[Dict[str, Any]]


@router.post("/analyze-segmentation", response_model=SegmentationAnalysisResponse)
async def analyze_segmentation(request: SegmentationAnalysisRequest):
    """
    Segment objects in an image and return segmentation masks.

    Note: Segmentation masks are experimental and may not be available in all regions.
    """
    try:
        service = DesignTransformationService()

        # Decode image
        image_data = request.image_data_url.split(",")[1] if "," in request.image_data_url else request.image_data_url
        image_bytes = base64.b64decode(image_data)

        # Analyze with segmentation
        result = await service.gemini.analyze_with_segmentation(
            image=image_bytes,
            objects_to_segment=request.objects_to_segment,
            room_hint=request.room_hint
        )

        logger.info(f"[Segmentation] Segmented {len(result.get('segments', []))} objects")

        return SegmentationAnalysisResponse(
            segments=result.get("segments", [])
        )

    except Exception as e:
        logger.error(f"analyze_segmentation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class MultiImageSequenceRequest(BaseModel):
    """Request for multi-image sequence analysis."""
    image_data_urls: List[str] = Field(..., description="List of image data URLs in sequence order")
    sequence_type: str = Field(default="transformation", description="Type: transformation, before_after, progress, variations")
    custom_prompt: Optional[str] = None


class MultiImageSequenceResponse(BaseModel):
    """Response with sequence analysis."""
    analysis: Dict[str, Any]


@router.post("/analyze-sequence", response_model=MultiImageSequenceResponse)
async def analyze_image_sequence(request: MultiImageSequenceRequest):
    """
    Analyze a sequence of images to detect patterns, changes, or progression.

    Perfect for before/after comparisons and design variation analysis.
    """
    try:
        service = DesignTransformationService()

        # Decode all images
        image_bytes_list = []
        for data_url in request.image_data_urls:
            image_data = data_url.split(",")[1] if "," in data_url else data_url
            image_bytes_list.append(base64.b64decode(image_data))

        # Analyze sequence
        result = await service.gemini.analyze_multi_image_sequence(
            images=image_bytes_list,
            sequence_type=request.sequence_type,
            prompt=request.custom_prompt
        )

        logger.info(f"[MultiImage] Analyzed {len(image_bytes_list)} images, type={request.sequence_type}")

        return MultiImageSequenceResponse(analysis=result)

    except Exception as e:
        logger.error(f"analyze_image_sequence failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class DIYInstructionsRequest(BaseModel):
    """Request for DIY instructions generation."""
    project_description: str
    reference_image_url: Optional[str] = None


class DIYInstructionsResponse(BaseModel):
    """Response with structured DIY instructions."""
    instructions: Dict[str, Any]


@router.post("/generate-diy-instructions", response_model=DIYInstructionsResponse)
async def generate_diy_instructions(request: DIYInstructionsRequest):
    """
    Generate structured DIY instructions for a home improvement project.

    Returns detailed steps, materials, tools, safety tips, and cost estimates.
    """
    try:
        service = DesignTransformationService()

        # Decode image if provided
        image_bytes = None
        if request.reference_image_url:
            image_data = request.reference_image_url.split(",")[1] if "," in request.reference_image_url else request.reference_image_url
            image_bytes = base64.b64decode(image_data)

        # Generate instructions
        result = await service.gemini.generate_diy_instructions(
            project_description=request.project_description,
            image=image_bytes
        )

        logger.info(f"[DIY] Generated instructions for: {request.project_description[:50]}")

        return DIYInstructionsResponse(instructions=result)

    except Exception as e:
        logger.error(f"generate_diy_instructions failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Video Analysis Endpoints
# ============================================================================

class VideoAnalysisRequest(BaseModel):
    """Request for video analysis."""
    video_url: str = Field(..., description="YouTube URL or uploaded video path")
    analysis_type: str = Field(default="summary", description="Type: summary, search, extract_text, tutorial")
    custom_prompt: Optional[str] = None
    fps: Optional[int] = Field(None, description="Frames per second to analyze (default: 1)")
    start_offset_seconds: Optional[int] = Field(None, description="Start time for clipping")
    end_offset_seconds: Optional[int] = Field(None, description="End time for clipping")


class VideoAnalysisResponse(BaseModel):
    """Response with video analysis results."""
    analysis: Dict[str, Any]


@router.post("/analyze-video", response_model=VideoAnalysisResponse)
async def analyze_video(request: VideoAnalysisRequest):
    """
    Analyze a video file or YouTube URL.

    Supports:
    - Video summarization with timestamps
    - Scene detection and captioning
    - Text extraction from video frames
    - DIY tutorial analysis with step-by-step instructions
    """
    try:
        service = DesignTransformationService()

        # Check if it's a YouTube URL
        is_youtube = any(domain in request.video_url.lower() for domain in ['youtube.com', 'youtu.be'])

        if is_youtube:
            result = await service.gemini.analyze_youtube_video(
                youtube_url=request.video_url,
                prompt=request.custom_prompt or "",
                start_offset_seconds=request.start_offset_seconds,
                end_offset_seconds=request.end_offset_seconds
            )
        else:
            result = await service.gemini.analyze_video(
                video_path=request.video_url,
                prompt=request.custom_prompt or "",
                analysis_type=request.analysis_type,
                fps=request.fps,
                start_offset_seconds=request.start_offset_seconds,
                end_offset_seconds=request.end_offset_seconds
            )

        logger.info(f"[Video] Analyzed video: {request.video_url[:50]}, type={request.analysis_type}")

        return VideoAnalysisResponse(analysis=result)

    except Exception as e:
        logger.error(f"analyze_video failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class VideoUploadAnalysisRequest(BaseModel):
    """Request for uploaded video analysis."""
    analysis_type: str = Field(default="summary", description="Type: summary, search, extract_text, tutorial")
    custom_prompt: Optional[str] = None
    fps: Optional[int] = None
    start_offset_seconds: Optional[int] = None
    end_offset_seconds: Optional[int] = None


@router.post("/analyze-video-upload")
async def analyze_video_upload(
    file: UploadFile = File(...),
    analysis_type: str = Form(default="summary"),
    custom_prompt: Optional[str] = Form(None),
    fps: Optional[int] = Form(None),
    start_offset_seconds: Optional[int] = Form(None),
    end_offset_seconds: Optional[int] = Form(None),
):
    """
    Analyze an uploaded video file.

    Accepts video file upload and returns analysis based on the specified type.
    """
    try:
        service = DesignTransformationService()

        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Analyze video
            result = await service.gemini.analyze_video(
                video_path=tmp_path,
                prompt=custom_prompt or "",
                analysis_type=analysis_type,
                fps=fps,
                start_offset_seconds=start_offset_seconds,
                end_offset_seconds=end_offset_seconds
            )

            logger.info(f"[VideoUpload] Analyzed: {file.filename}, type={analysis_type}")

            return {"analysis": result}

        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass

    except Exception as e:
        logger.error(f"analyze_video_upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

