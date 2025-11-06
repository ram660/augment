"""
Tests for Imagen Service.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from PIL import Image
from pathlib import Path
import io

from backend.services.imagen_service import (
    ImagenService,
    ImageGenerationRequest,
    DesignTransformationRequest,
    ImageGenerationResult
)


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    client = Mock()
    client.count_tokens = Mock(return_value=100)
    client.generate_image = AsyncMock()
    return client


@pytest.fixture
def imagen_service(mock_gemini_client, tmp_path):
    """Create Imagen service with mocked client."""
    return ImagenService(
        gemini_client=mock_gemini_client,
        output_dir=str(tmp_path / "generated")
    )


@pytest.fixture
def sample_image():
    """Create a sample PIL image."""
    img = Image.new('RGB', (512, 512), color='red')
    return img


class TestImagenService:
    """Tests for ImagenService."""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, imagen_service):
        """Test service initializes correctly."""
        assert imagen_service is not None
        assert imagen_service.output_dir.exists()
    
    @pytest.mark.asyncio
    async def test_generate_images_success(self, imagen_service, mock_gemini_client, sample_image):
        """Test successful image generation."""
        # Mock generate_image to return sample images
        mock_gemini_client.generate_image.return_value = [sample_image, sample_image]
        
        request = ImageGenerationRequest(
            prompt="A modern kitchen with white cabinets",
            num_images=2,
            aspect_ratio="16:9"
        )
        
        result = await imagen_service.generate_images(request)
        
        assert result.success is True
        assert len(result.images) == 2
        assert len(result.image_paths) == 2
        assert result.metadata["num_images"] == 2
        assert result.metadata["aspect_ratio"] == "16:9"
        assert result.generation_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_generate_images_with_style(self, imagen_service, mock_gemini_client, sample_image):
        """Test image generation with style modifier."""
        mock_gemini_client.generate_image.return_value = [sample_image]
        
        request = ImageGenerationRequest(
            prompt="A living room",
            style="minimalist",
            num_images=1
        )
        
        result = await imagen_service.generate_images(request)
        
        assert result.success is True
        # Verify style was included in prompt
        call_args = mock_gemini_client.generate_image.call_args
        assert "minimalist" in call_args.kwargs["prompt"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_images_error_handling(self, imagen_service, mock_gemini_client):
        """Test error handling in image generation."""
        mock_gemini_client.generate_image.side_effect = Exception("API Error")
        
        request = ImageGenerationRequest(
            prompt="Test prompt",
            num_images=1
        )
        
        result = await imagen_service.generate_images(request)
        
        assert result.success is False
        assert result.error is not None
        assert "API Error" in result.error
    
    @pytest.mark.asyncio
    async def test_transform_design_style_transfer(self, imagen_service, mock_gemini_client, sample_image, tmp_path):
        """Test style transfer transformation."""
        # Create a temporary image file
        img_path = tmp_path / "original.png"
        sample_image.save(img_path)
        
        mock_gemini_client.generate_image.return_value = [sample_image]
        
        request = DesignTransformationRequest(
            original_image_path=str(img_path),
            transformation_type="style_transfer",
            transformation_params={"target_style": "modern"},
            num_variations=1
        )
        
        result = await imagen_service.transform_design(request)
        
        assert result.success is True
        assert len(result.images) == 1
        assert result.metadata["transformation_type"] == "style_transfer"
        assert result.metadata["transformation_params"]["target_style"] == "modern"
    
    @pytest.mark.asyncio
    async def test_transform_design_room_redesign(self, imagen_service, mock_gemini_client, sample_image, tmp_path):
        """Test room redesign transformation."""
        img_path = tmp_path / "original.png"
        sample_image.save(img_path)
        
        mock_gemini_client.generate_image.return_value = [sample_image]
        
        request = DesignTransformationRequest(
            original_image_path=str(img_path),
            transformation_type="room_redesign",
            transformation_params={
                "changes": {
                    "flooring": "hardwood",
                    "wall_color": "light gray",
                    "furniture_style": "modern"
                }
            },
            num_variations=1
        )
        
        result = await imagen_service.transform_design(request)
        
        assert result.success is True
        # Verify prompt includes changes
        call_args = mock_gemini_client.generate_image.call_args
        prompt = call_args.kwargs["prompt"]
        assert "hardwood" in prompt.lower()
        assert "gray" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_transform_design_color_change(self, imagen_service, mock_gemini_client, sample_image, tmp_path):
        """Test color palette change."""
        img_path = tmp_path / "original.png"
        sample_image.save(img_path)
        
        mock_gemini_client.generate_image.return_value = [sample_image]
        
        request = DesignTransformationRequest(
            original_image_path=str(img_path),
            transformation_type="color_change",
            transformation_params={
                "color_palette": {
                    "primary": "blue",
                    "accent": "gold"
                }
            },
            num_variations=1
        )
        
        result = await imagen_service.transform_design(request)
        
        assert result.success is True
        call_args = mock_gemini_client.generate_image.call_args
        prompt = call_args.kwargs["prompt"]
        assert "blue" in prompt.lower()
        assert "gold" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_transform_design_furniture_swap(self, imagen_service, mock_gemini_client, sample_image, tmp_path):
        """Test furniture swapping."""
        img_path = tmp_path / "original.png"
        sample_image.save(img_path)
        
        mock_gemini_client.generate_image.return_value = [sample_image]
        
        request = DesignTransformationRequest(
            original_image_path=str(img_path),
            transformation_type="furniture_swap",
            transformation_params={
                "swap": {
                    "remove": "old sofa",
                    "add": "modern sectional"
                }
            },
            num_variations=1
        )
        
        result = await imagen_service.transform_design(request)
        
        assert result.success is True
        call_args = mock_gemini_client.generate_image.call_args
        prompt = call_args.kwargs["prompt"]
        assert "sofa" in prompt.lower()
        assert "sectional" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_generate_design_variations(self, imagen_service, mock_gemini_client, sample_image, tmp_path):
        """Test generating multiple design variations."""
        img_path = tmp_path / "original.png"
        sample_image.save(img_path)
        
        mock_gemini_client.generate_image.return_value = [sample_image]
        
        styles = ["modern", "traditional", "minimalist"]
        results = await imagen_service.generate_design_variations(
            original_image_path=str(img_path),
            variation_styles=styles,
            num_variations_per_style=1
        )
        
        assert len(results) == 3
        assert all(style in results for style in styles)
        assert all(results[style].success for style in styles)
    
    @pytest.mark.asyncio
    async def test_create_before_after_comparison(self, imagen_service, sample_image, tmp_path):
        """Test creating before/after comparison image."""
        # Create before and after images
        before_path = tmp_path / "before.png"
        after_path = tmp_path / "after.png"
        
        before_img = Image.new('RGB', (512, 512), color='red')
        after_img = Image.new('RGB', (512, 512), color='blue')
        
        before_img.save(before_path)
        after_img.save(after_path)
        
        # Create comparison
        comparison_path = await imagen_service.create_before_after_comparison(
            before_image_path=str(before_path),
            after_image_path=str(after_path)
        )
        
        assert comparison_path is not None
        assert Path(comparison_path).exists()
        
        # Verify comparison image
        comparison_img = Image.open(comparison_path)
        assert comparison_img.width > 512  # Should be wider than single image
        assert comparison_img.height == 512
    
    @pytest.mark.asyncio
    async def test_prompt_token_limit(self, imagen_service, mock_gemini_client, sample_image):
        """Test prompt is truncated if exceeds token limit."""
        # Mock token count to exceed limit
        mock_gemini_client.count_tokens.return_value = 500  # Exceeds 480 limit
        mock_gemini_client.generate_image.return_value = [sample_image]
        
        request = ImageGenerationRequest(
            prompt="A" * 3000,  # Very long prompt
            num_images=1
        )
        
        result = await imagen_service.generate_images(request)
        
        # Should still succeed with truncated prompt
        assert result.success is True
        assert mock_gemini_client.generate_image.called


class TestImageGenerationRequest:
    """Tests for ImageGenerationRequest model."""
    
    def test_valid_request(self):
        """Test creating valid request."""
        request = ImageGenerationRequest(
            prompt="A modern kitchen",
            num_images=2,
            aspect_ratio="16:9"
        )
        assert request.prompt == "A modern kitchen"
        assert request.num_images == 2
        assert request.aspect_ratio == "16:9"
    
    def test_num_images_validation(self):
        """Test num_images validation (1-4)."""
        with pytest.raises(ValueError):
            ImageGenerationRequest(
                prompt="Test",
                num_images=5  # Exceeds max
            )
        
        with pytest.raises(ValueError):
            ImageGenerationRequest(
                prompt="Test",
                num_images=0  # Below min
            )


class TestDesignTransformationRequest:
    """Tests for DesignTransformationRequest model."""
    
    def test_valid_transformation_request(self):
        """Test creating valid transformation request."""
        request = DesignTransformationRequest(
            original_image_path="/path/to/image.png",
            transformation_type="style_transfer",
            transformation_params={"target_style": "modern"}
        )
        assert request.transformation_type == "style_transfer"
        assert request.preserve_layout is True

