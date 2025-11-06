"""
Tests for Design Variation Service.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from PIL import Image

from backend.services.design_variation_service import (
    DesignVariationService,
    VariationRequest,
    StylePreference,
    VariationResult,
    VariationBatch
)
from backend.services.imagen_service import ImageGenerationResult


@pytest.fixture
def mock_imagen_service():
    """Create mock Imagen service."""
    service = Mock()
    service.transform_design = AsyncMock()
    return service


@pytest.fixture
def mock_gemini_client():
    """Create mock Gemini client."""
    client = Mock()
    client.generate_content = AsyncMock()
    return client


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample image."""
    img = Image.new('RGB', (800, 600), color='red')
    img_path = tmp_path / "test_room.png"
    img.save(img_path)
    return str(img_path)


@pytest.fixture
def variation_service(mock_imagen_service, mock_gemini_client, tmp_path):
    """Create variation service with mocks."""
    prefs_file = tmp_path / "preferences.json"
    return DesignVariationService(
        imagen_service=mock_imagen_service,
        gemini_client=mock_gemini_client,
        preferences_file=str(prefs_file)
    )


class TestDesignVariationService:
    """Tests for DesignVariationService."""
    
    def test_service_initialization(self, variation_service):
        """Test service initializes correctly."""
        assert variation_service is not None
        assert len(variation_service.STYLE_CATALOG) > 0
        assert variation_service.preferences is not None
    
    def test_style_catalog_completeness(self, variation_service):
        """Test style catalog has all required fields."""
        for style, info in variation_service.STYLE_CATALOG.items():
            assert "description" in info
            assert "keywords" in info
            assert "color_palette" in info
            assert isinstance(info["keywords"], list)
            assert isinstance(info["color_palette"], list)
    
    @pytest.mark.asyncio
    async def test_analyze_room_for_styles(self, variation_service, sample_image, mock_gemini_client):
        """Test room analysis for style recommendations."""
        mock_gemini_client.generate_content.return_value = "modern, scandinavian, minimalist"
        
        styles = await variation_service.analyze_room_for_styles(sample_image)
        
        assert len(styles) > 0
        assert all(s in variation_service.STYLE_CATALOG for s in styles)
        assert mock_gemini_client.generate_content.called
    
    @pytest.mark.asyncio
    async def test_analyze_room_invalid_styles_filtered(self, variation_service, sample_image, mock_gemini_client):
        """Test invalid styles are filtered out."""
        mock_gemini_client.generate_content.return_value = "modern, invalid_style, scandinavian"
        
        styles = await variation_service.analyze_room_for_styles(sample_image)
        
        assert "invalid_style" not in styles
        assert "modern" in styles
        assert "scandinavian" in styles
    
    def test_update_style_preference_new_user(self, variation_service):
        """Test updating preference for new user."""
        variation_service.update_style_preference("user-1", "modern", liked=True)
        
        assert "user-1" in variation_service.preferences
        assert "modern" in variation_service.preferences["user-1"]
        
        pref = variation_service.preferences["user-1"]["modern"]
        assert pref.preference_score > 0.5  # Should increase from 0.5
        assert pref.feedback_count == 1
    
    def test_update_style_preference_existing_user(self, variation_service):
        """Test updating preference for existing user."""
        # First feedback
        variation_service.update_style_preference("user-1", "modern", liked=True)
        score_1 = variation_service.preferences["user-1"]["modern"].preference_score
        
        # Second feedback
        variation_service.update_style_preference("user-1", "modern", liked=True)
        score_2 = variation_service.preferences["user-1"]["modern"].preference_score
        
        assert score_2 > score_1
        assert variation_service.preferences["user-1"]["modern"].feedback_count == 2
    
    def test_update_style_preference_dislike(self, variation_service):
        """Test updating preference with dislike."""
        variation_service.update_style_preference("user-1", "modern", liked=False)
        
        pref = variation_service.preferences["user-1"]["modern"]
        assert pref.preference_score < 0.5  # Should decrease from 0.5
    
    def test_get_user_preferred_styles_no_preferences(self, variation_service):
        """Test getting preferences for user with no history."""
        styles = variation_service.get_user_preferred_styles("new-user")
        
        assert styles == []
    
    def test_get_user_preferred_styles_with_preferences(self, variation_service):
        """Test getting preferences for user with history."""
        # Add some preferences
        variation_service.update_style_preference("user-1", "modern", liked=True)
        variation_service.update_style_preference("user-1", "modern", liked=True)
        variation_service.update_style_preference("user-1", "traditional", liked=False)
        variation_service.update_style_preference("user-1", "scandinavian", liked=True)
        
        styles = variation_service.get_user_preferred_styles("user-1", top_n=2)
        
        assert len(styles) <= 2
        assert "modern" in styles  # Should be top preference
    
    @pytest.mark.asyncio
    async def test_generate_variations_with_style_preferences(
        self, variation_service, sample_image, mock_imagen_service
    ):
        """Test generating variations with specified styles."""
        # Mock imagen service
        mock_result = ImageGenerationResult(
            success=True,
            images=["base64_image"],
            image_paths=["/path/image.png"],
            metadata={},
            generation_time_ms=1500.0
        )
        mock_imagen_service.transform_design.return_value = mock_result
        
        request = VariationRequest(
            original_image_path=sample_image,
            num_variations=3,
            style_preferences=["modern", "scandinavian", "minimalist"]
        )
        
        batch = await variation_service.generate_variations(request)
        
        assert batch.total_variations == 3
        assert len(batch.variations) == 3
        assert all(v.style in ["modern", "scandinavian", "minimalist"] for v in batch.variations)
    
    @pytest.mark.asyncio
    async def test_generate_variations_with_user_preferences(
        self, variation_service, sample_image, mock_imagen_service
    ):
        """Test generating variations using user preferences."""
        # Set up user preferences
        variation_service.update_style_preference("user-1", "modern", liked=True)
        variation_service.update_style_preference("user-1", "scandinavian", liked=True)
        
        # Mock imagen service
        mock_result = ImageGenerationResult(
            success=True,
            images=["base64_image"],
            image_paths=["/path/image.png"],
            metadata={},
            generation_time_ms=1500.0
        )
        mock_imagen_service.transform_design.return_value = mock_result
        
        request = VariationRequest(
            original_image_path=sample_image,
            num_variations=2,
            user_id="user-1"
        )
        
        batch = await variation_service.generate_variations(request)
        
        assert batch.total_variations == 2
        # Should use user's preferred styles
        styles = [v.style for v in batch.variations]
        assert "modern" in styles or "scandinavian" in styles
    
    @pytest.mark.asyncio
    async def test_generate_variations_with_exclusions(
        self, variation_service, sample_image, mock_imagen_service, mock_gemini_client
    ):
        """Test generating variations with excluded styles."""
        mock_gemini_client.generate_content.return_value = "modern, traditional, scandinavian"
        
        mock_result = ImageGenerationResult(
            success=True,
            images=["base64_image"],
            image_paths=["/path/image.png"],
            metadata={},
            generation_time_ms=1500.0
        )
        mock_imagen_service.transform_design.return_value = mock_result
        
        request = VariationRequest(
            original_image_path=sample_image,
            num_variations=2,
            exclude_styles=["traditional"]
        )
        
        batch = await variation_service.generate_variations(request)
        
        # Should not include excluded style
        styles = [v.style for v in batch.variations]
        assert "traditional" not in styles
    
    @pytest.mark.asyncio
    async def test_generate_variations_quality_scoring(
        self, variation_service, sample_image, mock_imagen_service
    ):
        """Test quality scoring of variations."""
        mock_result = ImageGenerationResult(
            success=True,
            images=["base64_image"],
            image_paths=["/path/image.png"],
            metadata={},
            generation_time_ms=1500.0
        )
        mock_imagen_service.transform_design.return_value = mock_result
        
        request = VariationRequest(
            original_image_path=sample_image,
            num_variations=2,
            style_preferences=["modern", "scandinavian"]
        )
        
        batch = await variation_service.generate_variations(request)
        
        # All variations should have quality scores
        assert all(0.0 <= v.quality_score <= 1.0 for v in batch.variations)
        # Should have a recommended variation
        assert batch.recommended_variation is not None
    
    @pytest.mark.asyncio
    async def test_generate_batch_variations(
        self, variation_service, tmp_path, mock_imagen_service
    ):
        """Test batch variation generation."""
        # Create multiple images
        images = []
        for i in range(3):
            img = Image.new('RGB', (800, 600), color='red')
            img_path = tmp_path / f"room_{i}.png"
            img.save(img_path)
            images.append(str(img_path))
        
        mock_result = ImageGenerationResult(
            success=True,
            images=["base64_image"],
            image_paths=["/path/image.png"],
            metadata={},
            generation_time_ms=1500.0
        )
        mock_imagen_service.transform_design.return_value = mock_result
        
        batches = await variation_service.generate_batch_variations(
            image_paths=images,
            num_variations_per_image=2
        )
        
        assert len(batches) == 3
        assert all(b.total_variations == 2 for b in batches)
    
    def test_get_style_recommendations_no_context(self, variation_service):
        """Test getting style recommendations without context."""
        recommendations = variation_service.get_style_recommendations()
        
        assert len(recommendations) > 0
        assert all("style" in rec for rec in recommendations)
        assert all("description" in rec for rec in recommendations)
    
    def test_get_style_recommendations_with_user(self, variation_service):
        """Test getting recommendations with user preferences."""
        # Set up preferences
        variation_service.update_style_preference("user-1", "modern", liked=True)
        variation_service.update_style_preference("user-1", "scandinavian", liked=True)
        
        recommendations = variation_service.get_style_recommendations(user_id="user-1")
        
        # User's preferred styles should be marked
        modern_rec = next((r for r in recommendations if r["style"] == "modern"), None)
        assert modern_rec is not None
        assert modern_rec["is_user_preferred"] is True
    
    def test_get_style_recommendations_with_room_type(self, variation_service):
        """Test getting recommendations for specific room type."""
        recommendations = variation_service.get_style_recommendations(room_type="kitchen")
        
        # Kitchen-appropriate styles should be marked
        kitchen_styles = ["modern", "farmhouse", "contemporary", "industrial"]
        for rec in recommendations:
            if rec["style"] in kitchen_styles:
                assert rec["is_room_recommended"] is True
    
    def test_preference_persistence(self, variation_service, tmp_path):
        """Test preferences are saved and loaded correctly."""
        # Add preferences
        variation_service.update_style_preference("user-1", "modern", liked=True)
        variation_service.update_style_preference("user-1", "scandinavian", liked=True)
        
        # Create new service instance (should load preferences)
        new_service = DesignVariationService(
            preferences_file=str(variation_service.preferences_file)
        )
        
        # Check preferences were loaded
        assert "user-1" in new_service.preferences
        assert "modern" in new_service.preferences["user-1"]
        assert new_service.preferences["user-1"]["modern"].feedback_count == 1


class TestVariationRequest:
    """Tests for VariationRequest model."""
    
    def test_valid_request(self):
        """Test creating valid request."""
        request = VariationRequest(
            original_image_path="/path/image.png",
            num_variations=3,
            style_preferences=["modern", "scandinavian"]
        )
        assert request.num_variations == 3
        assert len(request.style_preferences) == 2
    
    def test_num_variations_validation(self):
        """Test num_variations validation."""
        with pytest.raises(ValueError):
            VariationRequest(
                original_image_path="/path/image.png",
                num_variations=10  # Exceeds max of 8
            )
    
    def test_variation_intensity_validation(self):
        """Test variation_intensity validation."""
        with pytest.raises(ValueError):
            VariationRequest(
                original_image_path="/path/image.png",
                variation_intensity=1.5  # Exceeds max of 1.0
            )


class TestStylePreference:
    """Tests for StylePreference model."""
    
    def test_preference_creation(self):
        """Test creating style preference."""
        pref = StylePreference(
            user_id="user-1",
            style_name="modern",
            preference_score=0.8
        )
        assert pref.user_id == "user-1"
        assert pref.style_name == "modern"
        assert pref.preference_score == 0.8
    
    def test_preference_score_validation(self):
        """Test preference score validation."""
        with pytest.raises(ValueError):
            StylePreference(
                user_id="user-1",
                style_name="modern",
                preference_score=1.5  # Exceeds max
            )

