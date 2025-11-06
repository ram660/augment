"""
Transformation Storage Service - Handles saving and retrieving transformations.

This service manages the storage of transformation requests and results,
including uploading images to cloud storage and saving metadata to the database.
"""

import logging
import time
import os
from typing import List, Dict, Any, Optional
from uuid import UUID
from io import BytesIO
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.models import (
    Transformation,
    TransformationImage,
    TransformationType,
    TransformationStatus,
    RoomImage
)
from backend.integrations.gcs import GCSStorageClient
from backend.integrations.firebase.storage_client import get_firebase_storage_client

logger = logging.getLogger(__name__)

# Check which storage backend to use
USE_FIREBASE_STORAGE = os.getenv("USE_FIREBASE_STORAGE", "false").lower() == "true"
USE_GCS = os.getenv("USE_GCS", "false").lower() == "true"


class TransformationStorageService:
    """Service for storing and retrieving design transformations."""

    def __init__(self):
        """Initialize the storage service."""
        self.storage_client = None
        self.storage_type = "none"

        # Try Firebase Storage first (easier permissions)
        if USE_FIREBASE_STORAGE:
            try:
                self.storage_client = get_firebase_storage_client()
                self.storage_type = "firebase"
                logger.info("✅ Firebase Storage client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Firebase Storage client: {str(e)}")
                logger.warning("⚠️ Falling back to placeholder URLs")

        # Fall back to GCS if Firebase not enabled
        elif USE_GCS:
            try:
                self.storage_client = GCSStorageClient()
                self.storage_type = "gcs"
                logger.info("✅ GCS storage client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize GCS client: {str(e)}")
                logger.warning("⚠️ Falling back to placeholder URLs")

        # No cloud storage enabled
        else:
            logger.info("ℹ️ Cloud storage disabled - using placeholder URLs")
    
    async def create_transformation(
        self,
        db: AsyncSession,
        room_image_id: UUID,
        transformation_type: TransformationType,
        parameters: Dict[str, Any],
        num_variations: int = 4,
        user_id: Optional[UUID] = None
    ) -> Transformation:
        """
        Create a new transformation record in the database.
        
        Args:
            db: Database session
            room_image_id: ID of the room image being transformed
            transformation_type: Type of transformation
            parameters: Transformation parameters
            num_variations: Number of variations to generate
            user_id: Optional user ID
            
        Returns:
            Created Transformation object
        """
        transformation = Transformation(
            room_image_id=room_image_id,
            transformation_type=transformation_type,
            status=TransformationStatus.PENDING,
            parameters=parameters,
            num_variations=num_variations,
            user_id=user_id
        )
        
        db.add(transformation)
        await db.commit()
        await db.refresh(transformation)
        
        logger.info(f"Created transformation {transformation.id} - Type: {transformation_type.value}")
        return transformation
    
    async def update_transformation_status(
        self,
        db: AsyncSession,
        transformation_id: UUID,
        status: TransformationStatus,
        error_message: Optional[str] = None,
        processing_time_seconds: Optional[int] = None
    ) -> Transformation:
        """
        Update the status of a transformation.
        
        Args:
            db: Database session
            transformation_id: ID of the transformation
            status: New status
            error_message: Optional error message if failed
            processing_time_seconds: Optional processing time
            
        Returns:
            Updated Transformation object
        """
        result = await db.execute(
            select(Transformation).where(Transformation.id == transformation_id)
        )
        transformation = result.scalar_one_or_none()
        
        if not transformation:
            raise ValueError(f"Transformation {transformation_id} not found")
        
        transformation.status = status
        if error_message:
            transformation.error_message = error_message
        if processing_time_seconds:
            transformation.processing_time_seconds = processing_time_seconds
        
        await db.commit()
        await db.refresh(transformation)
        
        logger.info(f"Updated transformation {transformation_id} status to {status.value}")
        return transformation
    
    async def save_transformation_images(
        self,
        db: AsyncSession,
        transformation_id: UUID,
        images: List[Image.Image]
    ) -> List[TransformationImage]:
        """
        Save generated transformation images.

        This method:
        1. Uploads images to GCS (if enabled)
        2. Generates public/signed URLs
        3. Saves metadata to database

        Args:
            db: Database session
            transformation_id: ID of the transformation
            images: List of PIL Image objects

        Returns:
            List of created TransformationImage objects
        """
        transformation_images = []

        for idx, image in enumerate(images, start=1):
            # Get image dimensions
            width, height = image.size

            # Upload to GCS or create placeholder URL
            if self.storage_client:
                try:
                    # Upload to GCS
                    image_url = self.storage_client.upload_transformation_image(
                        image=image,
                        transformation_id=str(transformation_id),
                        variation_number=idx,
                        file_extension="jpg"
                    )
                    logger.info(f"✅ Uploaded variation {idx} to GCS: {image_url}")

                    # Calculate file size from optimized image
                    img_byte_arr = BytesIO()
                    image.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
                    file_size_bytes = len(img_byte_arr.getvalue())

                except Exception as e:
                    logger.error(f"❌ Failed to upload to GCS: {str(e)}")
                    logger.warning("⚠️ Falling back to placeholder URL")
                    image_url = f"placeholder://transformation/{transformation_id}/variation_{idx}.jpg"

                    # Estimate file size
                    img_byte_arr = BytesIO()
                    image.save(img_byte_arr, format='JPEG')
                    file_size_bytes = len(img_byte_arr.getvalue())
            else:
                # Create placeholder URL
                image_url = f"placeholder://transformation/{transformation_id}/variation_{idx}.jpg"

                # Estimate file size
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format='JPEG')
                file_size_bytes = len(img_byte_arr.getvalue())

            # Create database record
            transformation_image = TransformationImage(
                transformation_id=transformation_id,
                image_url=image_url,
                variation_number=idx,
                width=width,
                height=height,
                file_size_bytes=file_size_bytes,
                is_selected=False,
                is_applied=False
            )

            db.add(transformation_image)
            transformation_images.append(transformation_image)

        await db.commit()

        # Refresh all objects
        for img in transformation_images:
            await db.refresh(img)

        logger.info(f"✅ Saved {len(transformation_images)} images for transformation {transformation_id}")
        return transformation_images
    
    async def get_transformation(
        self,
        db: AsyncSession,
        transformation_id: UUID
    ) -> Optional[Transformation]:
        """
        Get a transformation by ID.
        
        Args:
            db: Database session
            transformation_id: ID of the transformation
            
        Returns:
            Transformation object or None
        """
        result = await db.execute(
            select(Transformation).where(Transformation.id == transformation_id)
        )
        return result.scalar_one_or_none()
    
    async def get_transformations_for_room_image(
        self,
        db: AsyncSession,
        room_image_id: UUID,
        limit: int = 50
    ) -> List[Transformation]:
        """
        Get all transformations for a room image.
        
        Args:
            db: Database session
            room_image_id: ID of the room image
            limit: Maximum number of transformations to return
            
        Returns:
            List of Transformation objects
        """
        result = await db.execute(
            select(Transformation)
            .where(Transformation.room_image_id == room_image_id)
            .order_by(desc(Transformation.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_transformation_images(
        self,
        db: AsyncSession,
        transformation_id: UUID
    ) -> List[TransformationImage]:
        """
        Get all images for a transformation.
        
        Args:
            db: Database session
            transformation_id: ID of the transformation
            
        Returns:
            List of TransformationImage objects
        """
        result = await db.execute(
            select(TransformationImage)
            .where(TransformationImage.transformation_id == transformation_id)
            .order_by(TransformationImage.variation_number)
        )
        return list(result.scalars().all())
    
    async def select_favorite_variation(
        self,
        db: AsyncSession,
        transformation_image_id: UUID
    ) -> TransformationImage:
        """
        Mark a transformation image as the user's favorite.
        
        Args:
            db: Database session
            transformation_image_id: ID of the transformation image
            
        Returns:
            Updated TransformationImage object
        """
        result = await db.execute(
            select(TransformationImage)
            .where(TransformationImage.id == transformation_image_id)
        )
        transformation_image = result.scalar_one_or_none()
        
        if not transformation_image:
            raise ValueError(f"TransformationImage {transformation_image_id} not found")
        
        # Unselect all other variations for this transformation
        result = await db.execute(
            select(TransformationImage)
            .where(TransformationImage.transformation_id == transformation_image.transformation_id)
        )
        all_images = result.scalars().all()
        
        for img in all_images:
            img.is_selected = (img.id == transformation_image_id)
        
        await db.commit()
        await db.refresh(transformation_image)
        
        logger.info(f"Selected variation {transformation_image.variation_number} for transformation {transformation_image.transformation_id}")
        return transformation_image
    
    async def delete_transformation(
        self,
        db: AsyncSession,
        transformation_id: UUID
    ) -> bool:
        """
        Delete a transformation and all its images.

        This method:
        1. Deletes images from GCS (if enabled)
        2. Deletes database records (cascade deletes images)

        Args:
            db: Database session
            transformation_id: ID of the transformation

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(Transformation).where(Transformation.id == transformation_id)
        )
        transformation = result.scalar_one_or_none()

        if not transformation:
            return False

        # Delete images from GCS if enabled
        if self.storage_client:
            try:
                count = self.storage_client.delete_transformation_images(str(transformation_id))
                logger.info(f"✅ Deleted {count} images from GCS for transformation {transformation_id}")
            except Exception as e:
                logger.error(f"❌ Failed to delete images from GCS: {str(e)}")
                logger.warning("⚠️ Continuing with database deletion")

        # Delete from database (cascade deletes transformation_images)
        await db.delete(transformation)
        await db.commit()

        logger.info(f"✅ Deleted transformation {transformation_id}")
        return True
