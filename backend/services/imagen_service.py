"""
Imagen Service for HomeView AI.

Production-ready service for AI image generation and editing using Gemini Imagen.
Provides high-level abstractions for design studio features.

Official Documentation:
- https://ai.google.dev/gemini-api/docs/imagen
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from io import BytesIO
from datetime import datetime
import uuid

from PIL import Image
from pydantic import BaseModel, Field

from backend.integrations.gemini.client import GeminiClient

logger = logging.getLogger(__name__)


class ImageGenerationRequest(BaseModel):
    """Request for image generation."""
    prompt: str = Field(..., max_length=480, description="Image generation prompt (max 480 tokens)")
    reference_image_path: Optional[str] = Field(None, description="Path to reference image for editing")
    aspect_ratio: str = Field("1:1", description="Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:4")
    num_images: int = Field(1, ge=1, le=4, description="Number of images to generate (1-4)")
    image_size: str = Field("1K", description="Image size: 1K or 2K")
    style: Optional[str] = Field(None, description="Style modifier (e.g., modern, traditional, minimalist)")
    preserve_elements: Optional[List[str]] = Field(None, description="Elements to preserve in transformation")


class ImageGenerationResult(BaseModel):
    """Result of image generation."""
    success: bool
    images: List[str] = Field(default_factory=list, description="Base64 encoded images")
    image_paths: List[str] = Field(default_factory=list, description="Saved image file paths")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    generation_time_ms: float = 0.0


class DesignTransformationRequest(BaseModel):
    """Request for design transformation."""
    original_image_path: str
    transformation_type: str = Field(..., description="Type: style_transfer, room_redesign, color_change, furniture_swap")
    transformation_params: Dict[str, Any] = Field(default_factory=dict)
    preserve_layout: bool = Field(True, description="Preserve room layout and perspective")
    num_variations: int = Field(1, ge=1, le=4)


class ImagenService:
    """
    Production-ready service for Gemini Imagen integration.
    
    Features:
    - Image generation from text prompts
    - Image editing and transformation
    - Style transfer
    - Room redesign
    - Design variations
    - Before/after comparisons
    """
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None, output_dir: Optional[str] = None):
        """
        Initialize Imagen service.
        
        Args:
            gemini_client: Gemini client instance. If None, creates new one.
            output_dir: Directory to save generated images. Defaults to 'generated_images'.
        """
        self.gemini_client = gemini_client or GeminiClient()
        self.output_dir = Path(output_dir or "generated_images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Imagen service initialized. Output directory: {self.output_dir}")
    
    async def generate_images(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """
        Generate images using Imagen.
        
        Args:
            request: Image generation request
            
        Returns:
            Image generation result with images and metadata
        """
        start_time = datetime.now()
        
        try:
            # Build enhanced prompt
            prompt = self._build_generation_prompt(request)
            
            # Validate prompt length (Imagen limit: 480 tokens)
            token_count = self.gemini_client.count_tokens(prompt)
            if token_count > 480:
                logger.warning(f"Prompt exceeds 480 tokens ({token_count}). Truncating...")
                # Truncate prompt to fit within limit
                prompt = prompt[:2000]  # Rough character limit
            
            # Generate images
            logger.info(f"Generating {request.num_images} images with Imagen...")
            images = await self.gemini_client.generate_image(
                prompt=prompt,
                reference_image=request.reference_image_path,
                aspect_ratio=request.aspect_ratio,
                num_images=request.num_images,
                image_size=request.image_size
            )
            
            # Save images and convert to base64
            image_paths = []
            image_base64 = []
            
            for idx, img in enumerate(images):
                # Save to disk
                filename = f"generated_{uuid.uuid4().hex[:8]}_{idx}.png"
                filepath = self.output_dir / filename
                img.save(filepath, format='PNG')
                image_paths.append(str(filepath))
                
                # Convert to base64
                buffered = BytesIO()
                img.save(buffered, format='PNG')
                import base64
                img_str = base64.b64encode(buffered.getvalue()).decode()
                image_base64.append(img_str)
            
            generation_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"Successfully generated {len(images)} images in {generation_time:.2f}ms")
            
            return ImageGenerationResult(
                success=True,
                images=image_base64,
                image_paths=image_paths,
                metadata={
                    "prompt": prompt,
                    "aspect_ratio": request.aspect_ratio,
                    "num_images": len(images),
                    "image_size": request.image_size,
                    "token_count": token_count,
                    "has_reference": request.reference_image_path is not None
                },
                generation_time_ms=generation_time
            )
            
        except Exception as e:
            generation_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Error generating images: {str(e)}", exc_info=True)
            
            return ImageGenerationResult(
                success=False,
                error=str(e),
                generation_time_ms=generation_time
            )
    
    async def transform_design(self, request: DesignTransformationRequest) -> ImageGenerationResult:
        """
        Transform a design using Imagen.
        
        Supports:
        - Style transfer (modern, traditional, minimalist, etc.)
        - Room redesign (change furniture, colors, materials)
        - Color palette changes
        - Furniture swapping
        
        Args:
            request: Design transformation request
            
        Returns:
            Transformed images with metadata
        """
        start_time = datetime.now()
        
        try:
            # Build transformation prompt
            prompt = self._build_transformation_prompt(request)
            
            # Generate transformed images
            logger.info(f"Transforming design: {request.transformation_type}")
            images = await self.gemini_client.generate_image(
                prompt=prompt,
                reference_image=request.original_image_path,
                aspect_ratio="1:1",  # Maintain original aspect ratio
                num_images=request.num_variations
            )
            
            # Save images
            image_paths = []
            image_base64 = []
            
            for idx, img in enumerate(images):
                filename = f"transformed_{request.transformation_type}_{uuid.uuid4().hex[:8]}_{idx}.png"
                filepath = self.output_dir / filename
                img.save(filepath, format='PNG')
                image_paths.append(str(filepath))
                
                # Convert to base64
                buffered = BytesIO()
                img.save(buffered, format='PNG')
                import base64
                img_str = base64.b64encode(buffered.getvalue()).decode()
                image_base64.append(img_str)
            
            generation_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"Successfully transformed design in {generation_time:.2f}ms")
            
            return ImageGenerationResult(
                success=True,
                images=image_base64,
                image_paths=image_paths,
                metadata={
                    "transformation_type": request.transformation_type,
                    "transformation_params": request.transformation_params,
                    "preserve_layout": request.preserve_layout,
                    "num_variations": len(images),
                    "original_image": request.original_image_path
                },
                generation_time_ms=generation_time
            )
            
        except Exception as e:
            generation_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Error transforming design: {str(e)}", exc_info=True)
            
            return ImageGenerationResult(
                success=False,
                error=str(e),
                generation_time_ms=generation_time
            )
    
    def _build_generation_prompt(self, request: ImageGenerationRequest) -> str:
        """Build enhanced prompt for image generation."""
        prompt_parts = []
        
        # Base prompt
        prompt_parts.append(request.prompt)
        
        # Add style if specified
        if request.style:
            prompt_parts.append(f"in a {request.style} style")
        
        # Add quality modifiers for better results
        quality_modifiers = [
            "high quality",
            "professional",
            "detailed",
            "4K"
        ]
        prompt_parts.extend(quality_modifiers)
        
        # If reference image, add preservation instructions
        if request.reference_image_path and request.preserve_elements:
            preserve_text = ", ".join(request.preserve_elements)
            prompt_parts.append(f"IMPORTANT: Preserve {preserve_text} from the reference image")
        
        return ", ".join(prompt_parts)
    
    def _build_transformation_prompt(self, request: DesignTransformationRequest) -> str:
        """Build prompt for design transformation."""
        transformation_prompts = {
            "style_transfer": self._build_style_transfer_prompt,
            "room_redesign": self._build_room_redesign_prompt,
            "color_change": self._build_color_change_prompt,
            "furniture_swap": self._build_furniture_swap_prompt
        }
        
        builder = transformation_prompts.get(request.transformation_type)
        if not builder:
            raise ValueError(f"Unknown transformation type: {request.transformation_type}")
        
        return builder(request)
    
    def _build_style_transfer_prompt(self, request: DesignTransformationRequest) -> str:
        """Build prompt for style transfer."""
        target_style = request.transformation_params.get("target_style", "modern")

        prompt = f"""Transform this room to a {target_style} style.

IMPORTANT: Maintain the exact room layout, perspective, and dimensions.
Only change the style, materials, and finishes to match the {target_style} aesthetic.
Preserve all structural elements like walls, windows, doors, and ceiling.

High quality, professional interior design, 4K, detailed."""

        return prompt

    def _build_room_redesign_prompt(self, request: DesignTransformationRequest) -> str:
        """Build prompt for room redesign."""
        changes = request.transformation_params.get("changes", {})

        change_descriptions = []
        if "flooring" in changes:
            change_descriptions.append(f"Change flooring to {changes['flooring']}")
        if "wall_color" in changes:
            change_descriptions.append(f"Change wall color to {changes['wall_color']}")
        if "furniture_style" in changes:
            change_descriptions.append(f"Replace furniture with {changes['furniture_style']} style")
        if "lighting" in changes:
            change_descriptions.append(f"Update lighting to {changes['lighting']}")

        changes_text = ". ".join(change_descriptions)

        prompt = f"""Redesign this room with the following changes: {changes_text}.

IMPORTANT: Maintain the exact room layout, perspective, and structural elements.
Only modify the specific elements mentioned above.
Keep the same room dimensions, window positions, and door locations.

High quality, professional interior design, 4K, detailed, realistic."""

        return prompt

    def _build_color_change_prompt(self, request: DesignTransformationRequest) -> str:
        """Build prompt for color palette change."""
        color_palette = request.transformation_params.get("color_palette", {})

        primary_color = color_palette.get("primary", "neutral")
        accent_color = color_palette.get("accent", "")

        prompt = f"""Change the color palette of this room to {primary_color}"""
        if accent_color:
            prompt += f" with {accent_color} accents"

        prompt += """.

IMPORTANT: Maintain the exact room layout, furniture placement, and perspective.
Only change the colors of walls, furniture, and decor.
Preserve all structural elements and room dimensions.

High quality, professional interior design, 4K, detailed, realistic."""

        return prompt

    def _build_furniture_swap_prompt(self, request: DesignTransformationRequest) -> str:
        """Build prompt for furniture swapping."""
        swap_params = request.transformation_params.get("swap", {})

        old_furniture = swap_params.get("remove", "existing furniture")
        new_furniture = swap_params.get("add", "modern furniture")

        prompt = f"""Replace {old_furniture} with {new_furniture} in this room.

IMPORTANT: Maintain the exact room layout, perspective, and dimensions.
Keep the same wall colors, flooring, and structural elements.
Only swap the specified furniture while maintaining realistic placement and scale.

High quality, professional interior design, 4K, detailed, realistic."""

        return prompt

    async def generate_design_variations(
        self,
        original_image_path: str,
        variation_styles: List[str],
        num_variations_per_style: int = 1
    ) -> Dict[str, ImageGenerationResult]:
        """
        Generate multiple design variations with different styles.

        Args:
            original_image_path: Path to original room image
            variation_styles: List of styles to generate (e.g., ["modern", "traditional", "minimalist"])
            num_variations_per_style: Number of variations per style

        Returns:
            Dictionary mapping style to generation results
        """
        results = {}

        for style in variation_styles:
            logger.info(f"Generating {num_variations_per_style} variations for style: {style}")

            request = DesignTransformationRequest(
                original_image_path=original_image_path,
                transformation_type="style_transfer",
                transformation_params={"target_style": style},
                num_variations=num_variations_per_style
            )

            result = await self.transform_design(request)
            results[style] = result

        return results

    async def create_before_after_comparison(
        self,
        before_image_path: str,
        after_image_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Create a side-by-side before/after comparison image.

        Args:
            before_image_path: Path to before image
            after_image_path: Path to after image
            output_path: Optional output path. If None, auto-generates.

        Returns:
            Path to comparison image
        """
        try:
            # Load images
            before_img = Image.open(before_image_path)
            after_img = Image.open(after_image_path)

            # Resize to same height
            target_height = min(before_img.height, after_img.height)
            before_img = before_img.resize(
                (int(before_img.width * target_height / before_img.height), target_height),
                Image.Resampling.LANCZOS
            )
            after_img = after_img.resize(
                (int(after_img.width * target_height / after_img.height), target_height),
                Image.Resampling.LANCZOS
            )

            # Create side-by-side image
            total_width = before_img.width + after_img.width + 20  # 20px gap
            comparison = Image.new('RGB', (total_width, target_height), (255, 255, 255))

            # Paste images
            comparison.paste(before_img, (0, 0))
            comparison.paste(after_img, (before_img.width + 20, 0))

            # Save
            if output_path is None:
                output_path = str(self.output_dir / f"comparison_{uuid.uuid4().hex[:8]}.png")

            comparison.save(output_path, format='PNG')
            logger.info(f"Created before/after comparison: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error creating comparison: {str(e)}", exc_info=True)
            raise

