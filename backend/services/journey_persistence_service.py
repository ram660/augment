"""
Journey persistence service for database operations.

Handles saving/loading journey state, step updates, and image management.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.journey import Journey, JourneyStep, JourneyImage, JourneyStatus, StepStatus
from backend.services.journey_manager import JourneyManager, UserJourney, JourneyStep as MemoryJourneyStep

logger = logging.getLogger(__name__)


class JourneyPersistenceService:
    """
    Service for persisting journey state to database.
    
    Bridges the in-memory JourneyManager with database storage.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.journey_manager = JourneyManager()
    
    async def create_journey(
        self,
        user_id: str,
        template_id: str,
        home_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Journey:
        """
        Create a new journey in database.
        
        Args:
            user_id: User ID
            template_id: Journey template ID
            home_id: Optional home ID
            conversation_id: Optional conversation ID
            title: Optional custom title
            
        Returns:
            Journey database model
        """
        # Start journey in memory
        memory_journey = self.journey_manager.start_journey(user_id, template_id)
        
        # Get template for metadata
        template = self.journey_manager.templates.get(template_id)
        if not template:
            raise ValueError(f"Journey template '{template_id}' not found")
        
        # Create database journey (let SQLAlchemy generate a new UUID)
        journey = Journey(
            user_id=UUID(user_id),
            home_id=UUID(home_id) if home_id else None,
            conversation_id=UUID(conversation_id) if conversation_id else None,
            template_id=template_id,
            title=title or template.name,
            description=template.description,
            status=JourneyStatus.IN_PROGRESS,
            current_step_id=memory_journey.current_step_id,
            completed_steps=0,
            total_steps=len(template.steps),
            progress_percentage=0.0,
            started_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
            metadata={
                "category": template.category,
                "difficulty_level": template.difficulty_level,
                "estimated_duration_days": template.estimated_duration_days,
                "estimated_cost_range": template.estimated_cost_range,
                "tags": template.tags,
            },
            collected_data={
                "images": [],
                "decisions": [],
                "budget": {},
                "timeline": {},
                "contractors": [],
            }
        )
        
        self.db.add(journey)
        await self.db.flush()
        
        # Create steps
        for idx, step in enumerate(template.steps, start=1):
            db_step = JourneyStep(
                journey_id=journey.id,
                step_id=step.step_id,
                step_number=idx,
                name=step.name,
                description=step.description,
                required=step.required,
                estimated_duration_minutes=step.estimated_duration_minutes,
                depends_on=step.depends_on,
                required_actions=step.required_actions,
                status=StepStatus.IN_PROGRESS if idx == 1 else StepStatus.NOT_STARTED,
                progress_percentage=0.0,
                step_data={},
                sub_steps=[],
            )
            self.db.add(db_step)
        
        await self.db.commit()

        # Refresh journey with steps eagerly loaded
        await self.db.refresh(journey, ["steps"])

        logger.info(f"Created journey {journey.id} for user {user_id} with template {template_id}")
        return journey
    
    async def get_journey(self, journey_id: str, include_steps: bool = True, include_images: bool = False) -> Optional[Journey]:
        """
        Get journey by ID.
        
        Args:
            journey_id: Journey ID
            include_steps: Whether to load steps
            include_images: Whether to load images
            
        Returns:
            Journey or None if not found
        """
        query = select(Journey).where(Journey.id == UUID(journey_id))
        
        if include_steps:
            query = query.options(selectinload(Journey.steps))
            if include_images:
                query = query.options(selectinload(Journey.steps).selectinload(JourneyStep.images))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_journeys(
        self,
        user_id: str,
        status: Optional[JourneyStatus] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Journey]:
        """
        Get all journeys for a user.
        
        Args:
            user_id: User ID
            status: Optional status filter
            limit: Max results
            offset: Offset for pagination
            
        Returns:
            List of journeys
        """
        query = select(Journey).where(Journey.user_id == UUID(user_id))

        if status:
            query = query.where(Journey.status == status)

        # Load steps with each journey
        query = query.options(selectinload(Journey.steps))
        query = query.order_by(Journey.last_activity_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def update_step(
        self,
        journey_id: str,
        step_id: str,
        status: Optional[StepStatus] = None,
        progress: Optional[float] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[JourneyStep]:
        """
        Update a journey step.
        
        Args:
            journey_id: Journey ID
            step_id: Step ID
            status: New status
            progress: New progress percentage
            data: Data to merge into step_data
            
        Returns:
            Updated step or None
        """
        # Get step - try by UUID first, then by step_id string
        try:
            # Try as UUID (database id)
            query = select(JourneyStep).where(
                JourneyStep.journey_id == UUID(journey_id),
                JourneyStep.id == UUID(step_id)
            )
            result = await self.db.execute(query)
            step = result.scalar_one_or_none()
        except (ValueError, TypeError):
            # Not a valid UUID, try as step_id string
            step = None

        if not step:
            # Try as step_id string (e.g., "initial_consultation")
            query = select(JourneyStep).where(
                JourneyStep.journey_id == UUID(journey_id),
                JourneyStep.step_id == step_id
            )
            result = await self.db.execute(query)
            step = result.scalar_one_or_none()

        if not step:
            logger.warning(f"Step {step_id} not found in journey {journey_id}")
            return None
        
        # Update fields
        if status:
            step.status = status
            if status == StepStatus.IN_PROGRESS and not step.started_at:
                step.started_at = datetime.utcnow()
            elif status == StepStatus.COMPLETED:
                step.completed_at = datetime.utcnow()
                step.progress_percentage = 100.0
        
        if progress is not None:
            step.progress_percentage = progress
        
        if data:
            current_data = step.step_data or {}
            current_data.update(data)
            step.step_data = current_data
        
        # Update journey last_activity_at
        journey_query = select(Journey).where(Journey.id == UUID(journey_id))
        journey_result = await self.db.execute(journey_query)
        journey = journey_result.scalar_one_or_none()
        
        if journey:
            journey.last_activity_at = datetime.utcnow()
            
            # Recalculate progress
            steps_query = select(JourneyStep).where(JourneyStep.journey_id == UUID(journey_id))
            steps_result = await self.db.execute(steps_query)
            all_steps = list(steps_result.scalars().all())
            
            completed = sum(1 for s in all_steps if s.status == StepStatus.COMPLETED)
            journey.completed_steps = completed
            journey.progress_percentage = (completed / len(all_steps)) * 100 if all_steps else 0
            
            # Update current step
            if status == StepStatus.COMPLETED:
                # Move to next step - find by UUID id or step_id string
                current_index = -1
                try:
                    # Try matching by UUID id first
                    step_uuid = UUID(step_id)
                    current_index = next((i for i, s in enumerate(all_steps) if s.id == step_uuid), -1)
                except (ValueError, TypeError):
                    # Try matching by step_id string
                    current_index = next((i for i, s in enumerate(all_steps) if s.step_id == step_id), -1)

                if current_index >= 0 and current_index < len(all_steps) - 1:
                    next_step = all_steps[current_index + 1]
                    journey.current_step_id = next_step.step_id
                    next_step.status = StepStatus.IN_PROGRESS
                    next_step.started_at = datetime.utcnow()
                else:
                    # Journey completed
                    journey.status = JourneyStatus.COMPLETED
                    journey.completed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(step)
        
        logger.info(f"Updated step {step_id} in journey {journey_id}")
        return step
    
    async def add_image(
        self,
        journey_id: str,
        step_id: str,
        filename: str,
        file_path: str,
        url: str,
        content_type: str,
        file_size: int,
        thumbnail_url: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        is_generated: bool = False,
        image_type: Optional[str] = None,
        label: Optional[str] = None,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> JourneyImage:
        """
        Add an image to a journey step.
        
        Args:
            journey_id: Journey ID
            step_id: Step ID (step_id string, not UUID)
            filename: Original filename
            file_path: File path
            url: Public URL
            content_type: MIME type
            file_size: Size in bytes
            thumbnail_url: Optional thumbnail URL
            width: Image width
            height: Image height
            is_generated: Whether AI-generated
            image_type: Type of image
            analysis: AI analysis results
            
        Returns:
            Created JourneyImage
        """
        # Get step - try by UUID first, then by step_id string
        try:
            # Try as UUID (database id)
            query = select(JourneyStep).where(
                JourneyStep.journey_id == UUID(journey_id),
                JourneyStep.id == UUID(step_id)
            )
            result = await self.db.execute(query)
            step = result.scalar_one_or_none()
        except (ValueError, TypeError):
            # Not a valid UUID, try as step_id string
            step = None

        if not step:
            # Try as step_id string (e.g., "initial_consultation")
            query = select(JourneyStep).where(
                JourneyStep.journey_id == UUID(journey_id),
                JourneyStep.step_id == step_id
            )
            result = await self.db.execute(query)
            step = result.scalar_one_or_none()

        if not step:
            raise ValueError(f"Step {step_id} not found in journey {journey_id}")

        # Calculate next display_order for this step
        count_query = select(JourneyImage).where(JourneyImage.step_id == step.id)
        count_result = await self.db.execute(count_query)
        existing_images = count_result.scalars().all()
        next_order = len(existing_images) + 1

        image = JourneyImage(
            journey_id=UUID(journey_id),
            step_id=step.id,
            filename=filename,
            file_path=file_path,
            url=url,
            thumbnail_url=thumbnail_url,
            content_type=content_type,
            file_size=file_size,
            width=width,
            height=height,
            is_generated=is_generated,
            image_type=image_type,
            label=label,
            analysis=analysis or {},
            tags=[],
            related_image_ids=[],
            display_order=next_order,
        )
        
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        
        logger.info(f"Added image {image.id} to step {step_id} in journey {journey_id}")
        return image
    
    async def get_journey_images(
        self,
        journey_id: str,
        step_id: Optional[str] = None,
        image_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[JourneyImage]:
        """
        Get all images for a journey with filtering options.

        Args:
            journey_id: Journey ID
            step_id: Optional filter by step ID (string identifier)
            image_type: Optional filter by image type
            start_date: Optional filter by creation date (after)
            end_date: Optional filter by creation date (before)
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of journey images ordered by step and display_order
        """
        query = select(JourneyImage).where(JourneyImage.journey_id == UUID(journey_id))

        if step_id:
            # Get step UUID first
            step_query = select(JourneyStep).where(
                JourneyStep.journey_id == UUID(journey_id),
                JourneyStep.step_id == step_id
            )
            step_result = await self.db.execute(step_query)
            step = step_result.scalar_one_or_none()
            if step:
                query = query.where(JourneyImage.step_id == step.id)

        if image_type:
            query = query.where(JourneyImage.image_type == image_type)

        if start_date:
            query = query.where(JourneyImage.created_at >= start_date)

        if end_date:
            query = query.where(JourneyImage.created_at <= end_date)

        # Order by step and display_order
        query = query.order_by(JourneyImage.step_id, JourneyImage.display_order)
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_image(
        self,
        journey_id: str,
        image_id: str,
        label: Optional[str] = None,
        image_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> JourneyImage:
        """
        Update image metadata.

        Args:
            journey_id: Journey ID
            image_id: Image ID
            label: Optional new label
            image_type: Optional new image type
            metadata: Optional new metadata

        Returns:
            Updated image

        Raises:
            ValueError: If image not found or doesn't belong to journey
        """
        # Get image and verify it belongs to journey
        query = select(JourneyImage).where(
            JourneyImage.id == UUID(image_id),
            JourneyImage.journey_id == UUID(journey_id)
        )
        result = await self.db.execute(query)
        image = result.scalar_one_or_none()

        if not image:
            raise ValueError(f"Image {image_id} not found in journey {journey_id}")

        # Update fields
        if label is not None:
            image.label = label
        if image_type is not None:
            image.image_type = image_type
        if metadata is not None:
            image.analysis = metadata

        await self.db.commit()
        await self.db.refresh(image)

        logger.info(f"Updated image {image_id} in journey {journey_id}")
        return image

    async def delete_image(
        self,
        journey_id: str,
        image_id: str,
        delete_file: bool = True
    ) -> bool:
        """
        Delete image from journey and optionally from filesystem.

        Args:
            journey_id: Journey ID
            image_id: Image ID
            delete_file: Whether to delete the physical file

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If image not found or doesn't belong to journey
        """
        import os

        # Get image and verify it belongs to journey
        query = select(JourneyImage).where(
            JourneyImage.id == UUID(image_id),
            JourneyImage.journey_id == UUID(journey_id)
        )
        result = await self.db.execute(query)
        image = result.scalar_one_or_none()

        if not image:
            raise ValueError(f"Image {image_id} not found in journey {journey_id}")

        # Delete physical file if requested
        if delete_file and image.file_path:
            try:
                if os.path.exists(image.file_path):
                    os.remove(image.file_path)
                    logger.info(f"Deleted file {image.file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {image.file_path}: {e}")

        # Delete database record
        await self.db.delete(image)
        await self.db.commit()

        logger.info(f"Deleted image {image_id} from journey {journey_id}")
        return True

    async def reorder_images(
        self,
        journey_id: str,
        step_id: str,
        image_ids: List[str]
    ) -> List[JourneyImage]:
        """
        Reorder images within a step.

        Args:
            journey_id: Journey ID
            step_id: Step ID (UUID or string identifier)
            image_ids: Ordered list of image IDs

        Returns:
            List of reordered images

        Raises:
            ValueError: If any image doesn't belong to the step
        """
        # Get step UUID
        try:
            step_uuid = UUID(step_id)
            step_query = select(JourneyStep).where(JourneyStep.id == step_uuid)
        except ValueError:
            # step_id is a string identifier
            step_query = select(JourneyStep).where(
                JourneyStep.journey_id == UUID(journey_id),
                JourneyStep.step_id == step_id
            )

        step_result = await self.db.execute(step_query)
        step = step_result.scalar_one_or_none()

        if not step:
            raise ValueError(f"Step {step_id} not found in journey {journey_id}")

        # Get all images for this step
        query = select(JourneyImage).where(
            JourneyImage.step_id == step.id,
            JourneyImage.journey_id == UUID(journey_id)
        )
        result = await self.db.execute(query)
        images = {str(img.id): img for img in result.scalars().all()}

        # Validate all image_ids belong to this step
        for img_id in image_ids:
            if img_id not in images:
                raise ValueError(f"Image {img_id} not found in step {step_id}")

        # Update display_order for each image
        reordered_images = []
        for order, img_id in enumerate(image_ids, start=1):
            image = images[img_id]
            image.display_order = order
            reordered_images.append(image)

        await self.db.commit()

        # Refresh all images
        for image in reordered_images:
            await self.db.refresh(image)

        logger.info(f"Reordered {len(image_ids)} images in step {step_id}")
        return reordered_images

    async def delete_images_bulk(
        self,
        journey_id: str,
        image_ids: List[str],
        delete_files: bool = True
    ) -> tuple[List[str], List[dict]]:
        """
        Delete multiple images at once.

        Args:
            journey_id: Journey ID
            image_ids: List of image IDs to delete
            delete_files: Whether to delete physical files

        Returns:
            Tuple of (deleted_ids, errors)
            errors is a list of {image_id: str, error: str}
        """
        import os

        deleted_ids = []
        errors = []

        for image_id in image_ids:
            try:
                # Get image
                query = select(JourneyImage).where(
                    JourneyImage.id == UUID(image_id),
                    JourneyImage.journey_id == UUID(journey_id)
                )
                result = await self.db.execute(query)
                image = result.scalar_one_or_none()

                if not image:
                    errors.append({
                        "image_id": image_id,
                        "error": "Image not found"
                    })
                    continue

                # Delete physical file if requested
                if delete_files and image.file_path:
                    try:
                        if os.path.exists(image.file_path):
                            os.remove(image.file_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete file {image.file_path}: {e}")

                # Delete database record
                await self.db.delete(image)
                deleted_ids.append(image_id)

            except Exception as e:
                errors.append({
                    "image_id": image_id,
                    "error": str(e)
                })

        await self.db.commit()

        logger.info(f"Bulk deleted {len(deleted_ids)} images from journey {journey_id}")
        return deleted_ids, errors

