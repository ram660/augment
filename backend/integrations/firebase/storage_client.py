"""
Firebase Storage Client for HomerView AI

This module provides a client for uploading and managing images in Firebase Storage.
It's an alternative to Google Cloud Storage with simpler permissions.
"""

import firebase_admin
from firebase_admin import credentials, storage
from PIL import Image
import io
import os
from pathlib import Path
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)


class FirebaseStorageClient:
    """
    Firebase Storage client for managing transformation images.
    
    This is a singleton class that provides methods to upload, download,
    and delete images from Firebase Storage.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        try:
            # Get credentials path
            cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
            if not cred_path:
                raise ValueError("FIREBASE_CREDENTIALS_PATH environment variable not set")
            
            if not os.path.exists(cred_path):
                raise ValueError(f"Firebase credentials file not found: {cred_path}")
            
            # Get storage bucket
            bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET', 'ai-studio-b9503.appspot.com')
            
            # Initialize Firebase Admin if not already initialized
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': bucket_name
                })
                logger.info(f"Firebase Admin initialized with bucket: {bucket_name}")
            
            # Get storage bucket
            self.bucket = storage.bucket()
            self.bucket_name = bucket_name
            self._initialized = True
            
            logger.info(f"Firebase Storage client initialized successfully")
            logger.info(f"Bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Storage client: {e}")
            raise
    
    def upload_image(
        self,
        image: Union[str, Path, Image.Image, bytes],
        path: str,
        content_type: str = "image/jpeg",
        make_public: bool = True
    ) -> str:
        """
        Upload an image to Firebase Storage.
        
        Args:
            image: Image to upload (file path, PIL Image, or bytes)
            path: Destination path in storage (e.g., 'transformations/uuid/image.jpg')
            content_type: MIME type of the image
            make_public: Whether to make the image publicly accessible
            
        Returns:
            Public URL of the uploaded image
        """
        try:
            # Convert image to bytes
            if isinstance(image, (str, Path)):
                with open(image, 'rb') as f:
                    image_bytes = f.read()
            elif isinstance(image, Image.Image):
                buffer = io.BytesIO()
                # Optimize image for web
                image.save(buffer, format='JPEG', quality=85, optimize=True)
                image_bytes = buffer.getvalue()
            elif isinstance(image, bytes):
                image_bytes = image
            else:
                raise ValueError(f"Unsupported image type: {type(image)}")
            
            # Upload to Firebase Storage
            blob = self.bucket.blob(path)
            blob.upload_from_string(image_bytes, content_type=content_type)

            # Note: Cannot use make_public() with uniform bucket-level access
            # The bucket must be configured with public access at the bucket level
            # Get public URL (works if bucket is publicly accessible)
            url = blob.public_url
            
            logger.info(f"✅ Uploaded image to Firebase Storage: {path}")
            logger.info(f"   URL: {url}")
            
            return url
            
        except Exception as e:
            logger.error(f"❌ Failed to upload image to Firebase Storage: {e}")
            raise
    
    def upload_transformation_image(
        self,
        transformation_id: str,
        image: Union[str, Path, Image.Image, bytes],
        variation_number: int = 1
    ) -> str:
        """
        Upload a transformation image with organized path structure.
        
        Args:
            transformation_id: UUID of the transformation
            image: Image to upload
            variation_number: Variation number (1, 2, 3, 4)
            
        Returns:
            Public URL of the uploaded image
        """
        path = f"transformations/{transformation_id}/variation_{variation_number}.jpg"
        return self.upload_image(image, path)
    
    def upload_room_image(
        self,
        room_id: str,
        image: Union[str, Path, Image.Image, bytes],
        image_id: Optional[str] = None
    ) -> str:
        """
        Upload a room image.
        
        Args:
            room_id: UUID of the room
            image: Image to upload
            image_id: Optional image UUID (generated if not provided)
            
        Returns:
            Public URL of the uploaded image
        """
        if image_id is None:
            import uuid
            image_id = str(uuid.uuid4())
        
        path = f"room_images/{room_id}/{image_id}.jpg"
        return self.upload_image(image, path)
    
    def upload_floor_plan(
        self,
        home_id: str,
        image: Union[str, Path, Image.Image, bytes],
        floor_plan_id: Optional[str] = None
    ) -> str:
        """
        Upload a floor plan image.
        
        Args:
            home_id: UUID of the home
            image: Image to upload
            floor_plan_id: Optional floor plan UUID
            
        Returns:
            Public URL of the uploaded image
        """
        if floor_plan_id is None:
            import uuid
            floor_plan_id = str(uuid.uuid4())
        
        path = f"floor_plans/{home_id}/{floor_plan_id}.jpg"
        return self.upload_image(image, path)
    
    def file_exists(self, path: str) -> bool:
        """
        Check if a file exists in Firebase Storage.
        
        Args:
            path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            blob = self.bucket.blob(path)
            return blob.exists()
        except Exception as e:
            logger.error(f"Failed to check file existence: {e}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """
        Delete a file from Firebase Storage.
        
        Args:
            path: Path to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            blob = self.bucket.blob(path)
            blob.delete()
            logger.info(f"✅ Deleted file from Firebase Storage: {path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete file: {e}")
            return False
    
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
            logger.info(f"✅ Deleted {count} images for transformation {transformation_id}")
            return count
        except Exception as e:
            logger.error(f"❌ Failed to delete transformation images: {e}")
            return 0
    
    def get_signed_url(self, path: str, expiration_minutes: int = 60) -> str:
        """
        Generate a signed URL for temporary access to a file.
        
        Args:
            path: Path to the file
            expiration_minutes: URL expiration time in minutes
            
        Returns:
            Signed URL
        """
        try:
            from datetime import timedelta
            blob = self.bucket.blob(path)
            url = blob.generate_signed_url(
                expiration=timedelta(minutes=expiration_minutes),
                method='GET'
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            # Fall back to public URL
            return blob.public_url


def get_firebase_storage_client() -> FirebaseStorageClient:
    """
    Get the Firebase Storage client singleton instance.
    
    Returns:
        FirebaseStorageClient instance
    """
    return FirebaseStorageClient()

