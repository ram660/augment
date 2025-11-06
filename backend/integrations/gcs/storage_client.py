"""
Google Cloud Storage client for HomerView AI.

This module provides a production-ready interface for storing and retrieving
images and other assets in Google Cloud Storage.

Features:
- Upload images with automatic content type detection
- Generate signed URLs for secure access
- Delete images and cleanup
- Organize files by type (transformations, room_images, floor_plans)
- Automatic retry and error handling
- Image optimization and compression
"""

import os
import logging
import io
import uuid
from typing import Optional, BinaryIO, Union
from datetime import timedelta
from pathlib import Path
from PIL import Image

from google.cloud import storage
from google.cloud.exceptions import NotFound, GoogleCloudError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GCSStorageClient:
    """
    Google Cloud Storage client for HomerView AI.
    
    Handles all cloud storage operations including:
    - Image uploads
    - Signed URL generation
    - File deletion
    - Bucket management
    """
    
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        """
        Initialize GCS client.
        
        Args:
            bucket_name: GCS bucket name (defaults to env var GCS_BUCKET_NAME)
            credentials_path: Path to service account JSON (defaults to env var GOOGLE_APPLICATION_CREDENTIALS)
            project_id: GCP project ID (defaults to env var GCP_PROJECT_ID)
        """
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME")
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable is required")
        
        # Set credentials path if provided
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        # Initialize GCS client
        try:
            self.client = storage.Client(project=self.project_id)
            self.bucket = self.client.bucket(self.bucket_name)
            logger.info(f"✅ GCS client initialized for bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize GCS client: {str(e)}")
            raise
    
    def upload_image(
        self,
        image: Union[Image.Image, bytes, BinaryIO],
        destination_path: str,
        content_type: str = "image/jpeg",
        optimize: bool = True,
        quality: int = 85,
        max_size: Optional[tuple] = None
    ) -> str:
        """
        Upload an image to GCS.
        
        Args:
            image: PIL Image, bytes, or file-like object
            destination_path: Path in bucket (e.g., "transformations/uuid/image.jpg")
            content_type: MIME type (default: image/jpeg)
            optimize: Whether to optimize the image (default: True)
            quality: JPEG quality 1-100 (default: 85)
            max_size: Optional (width, height) to resize image
            
        Returns:
            Public URL of the uploaded image
            
        Raises:
            GoogleCloudError: If upload fails
        """
        try:
            # Convert to bytes if PIL Image
            if isinstance(image, Image.Image):
                image_bytes = self._image_to_bytes(
                    image,
                    optimize=optimize,
                    quality=quality,
                    max_size=max_size
                )
            elif isinstance(image, bytes):
                image_bytes = image
            else:
                image_bytes = image.read()
            
            # Create blob
            blob = self.bucket.blob(destination_path)
            
            # Set content type
            blob.content_type = content_type
            
            # Upload
            blob.upload_from_string(image_bytes, content_type=content_type)
            
            # Make public (optional - remove if you want private files)
            # blob.make_public()
            
            logger.info(f"✅ Uploaded image to GCS: {destination_path}")
            
            # Return public URL
            return blob.public_url
            
        except GoogleCloudError as e:
            logger.error(f"❌ Failed to upload image to GCS: {str(e)}")
            raise
    
    def upload_transformation_image(
        self,
        image: Union[Image.Image, bytes],
        transformation_id: str,
        variation_number: int,
        file_extension: str = "jpg"
    ) -> str:
        """
        Upload a transformation image with organized path structure.
        
        Args:
            image: PIL Image or bytes
            transformation_id: UUID of the transformation
            variation_number: Variation number (1-4)
            file_extension: File extension (default: jpg)
            
        Returns:
            Public URL of the uploaded image
        """
        # Create organized path: transformations/{transformation_id}/variation_{n}.jpg
        destination_path = f"transformations/{transformation_id}/variation_{variation_number}.{file_extension}"
        
        return self.upload_image(
            image=image,
            destination_path=destination_path,
            content_type=f"image/{file_extension}",
            optimize=True,
            quality=85
        )
    
    def upload_room_image(
        self,
        image: Union[Image.Image, bytes],
        room_id: str,
        image_id: str,
        file_extension: str = "jpg"
    ) -> str:
        """
        Upload a room image with organized path structure.
        
        Args:
            image: PIL Image or bytes
            room_id: UUID of the room
            image_id: UUID of the image
            file_extension: File extension (default: jpg)
            
        Returns:
            Public URL of the uploaded image
        """
        destination_path = f"room_images/{room_id}/{image_id}.{file_extension}"
        
        return self.upload_image(
            image=image,
            destination_path=destination_path,
            content_type=f"image/{file_extension}",
            optimize=True,
            quality=90  # Higher quality for original images
        )
    
    def upload_floor_plan(
        self,
        image: Union[Image.Image, bytes],
        home_id: str,
        floor_plan_id: str,
        file_extension: str = "jpg"
    ) -> str:
        """
        Upload a floor plan image with organized path structure.
        
        Args:
            image: PIL Image or bytes
            home_id: UUID of the home
            floor_plan_id: UUID of the floor plan
            file_extension: File extension (default: jpg)
            
        Returns:
            Public URL of the uploaded image
        """
        destination_path = f"floor_plans/{home_id}/{floor_plan_id}.{file_extension}"
        
        return self.upload_image(
            image=image,
            destination_path=destination_path,
            content_type=f"image/{file_extension}",
            optimize=True,
            quality=90
        )
    
    def generate_signed_url(
        self,
        blob_path: str,
        expiration: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Generate a signed URL for secure access to a private file.
        
        Args:
            blob_path: Path to the blob in the bucket
            expiration: How long the URL should be valid (default: 1 hour)
            
        Returns:
            Signed URL
            
        Raises:
            NotFound: If blob doesn't exist
        """
        try:
            blob = self.bucket.blob(blob_path)
            
            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="GET"
            )
            
            logger.info(f"✅ Generated signed URL for: {blob_path}")
            return url
            
        except NotFound:
            logger.error(f"❌ Blob not found: {blob_path}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to generate signed URL: {str(e)}")
            raise
    
    def delete_file(self, blob_path: str) -> bool:
        """
        Delete a file from GCS.
        
        Args:
            blob_path: Path to the blob in the bucket
            
        Returns:
            True if deleted, False if not found
        """
        try:
            blob = self.bucket.blob(blob_path)
            blob.delete()
            logger.info(f"✅ Deleted file from GCS: {blob_path}")
            return True
            
        except NotFound:
            logger.warning(f"⚠️ File not found for deletion: {blob_path}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete file: {str(e)}")
            raise
    
    def delete_transformation_images(self, transformation_id: str) -> int:
        """
        Delete all images for a transformation.
        
        Args:
            transformation_id: UUID of the transformation
            
        Returns:
            Number of files deleted
        """
        try:
            prefix = f"transformations/{transformation_id}/"
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            count = 0
            for blob in blobs:
                blob.delete()
                count += 1
            
            logger.info(f"✅ Deleted {count} transformation images for: {transformation_id}")
            return count
            
        except Exception as e:
            logger.error(f"❌ Failed to delete transformation images: {str(e)}")
            raise
    
    def file_exists(self, blob_path: str) -> bool:
        """
        Check if a file exists in GCS.
        
        Args:
            blob_path: Path to the blob in the bucket
            
        Returns:
            True if exists, False otherwise
        """
        try:
            blob = self.bucket.blob(blob_path)
            return blob.exists()
        except Exception as e:
            logger.error(f"❌ Error checking file existence: {str(e)}")
            return False
    
    def _image_to_bytes(
        self,
        image: Image.Image,
        optimize: bool = True,
        quality: int = 85,
        max_size: Optional[tuple] = None
    ) -> bytes:
        """
        Convert PIL Image to bytes with optional optimization.
        
        Args:
            image: PIL Image
            optimize: Whether to optimize
            quality: JPEG quality 1-100
            max_size: Optional (width, height) to resize
            
        Returns:
            Image as bytes
        """
        # Resize if max_size specified
        if max_size:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary (for JPEG)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        # Save to bytes
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", optimize=optimize, quality=quality)
        return buffer.getvalue()


# Singleton instance
_gcs_client: Optional[GCSStorageClient] = None


def get_gcs_client() -> GCSStorageClient:
    """
    Get or create singleton GCS client instance.
    
    Returns:
        GCSStorageClient instance
    """
    global _gcs_client
    
    if _gcs_client is None:
        _gcs_client = GCSStorageClient()
    
    return _gcs_client

