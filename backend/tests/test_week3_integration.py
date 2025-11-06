"""
Week 3 Integration Tests - Design Studio & Image Generation.

Tests the complete integration of all Week 3 components:
- Imagen Service
- Design Transformation Workflow
- Design Studio Agent
- Design Visualization Service
- Design Variation Service
- Database Models
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from PIL import Image
import uuid

from backend.services.imagen_service import ImagenService, DesignTransformationRequest, ImageGenerationResult
from backend.workflows.design_transformation_workflow import DesignTransformationWorkflow, DesignTransformationState
from backend.agents.design import DesignStudioAgent
from backend.services.design_visualization_service import DesignVisualizationService, ComparisonLayout
from backend.services.design_variation_service import DesignVariationService, VariationRequest
from backend.models.design import DesignProject, DesignTransformation, DesignVariation


@pytest.fixture
def sample_images(tmp_path):
    """Create sample images for testing."""
    images = {}
    
    # Original room image
    img = Image.new('RGB', (1024, 768), color='white')
    original_path = tmp_path / "original_room.png"
    img.save(original_path)
    images['original'] = str(original_path)
    
    # Transformed images
    for i, color in enumerate(['red', 'blue', 'green']):
        img = Image.new('RGB', (1024, 768), color=color)
        path = tmp_path / f"transformed_{color}.png"
        img.save(path)
        images[f'transformed_{i}'] = str(path)
    
    return images


@pytest.fixture
def mock_gemini_client():
    """Create mock Gemini client."""
    client = Mock()
    client.generate_content = AsyncMock(return_value="Modern, clean design with minimalist aesthetic")
    client.generate_image = AsyncMock(return_value={
        'images': ['base64_encoded_image'],
        'metadata': {'model': 'imagen-4.0'}
    })
    return client


class TestWeek3Integration:
    """Integration tests for Week 3 components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_design_transformation(self, sample_images, mock_gemini_client):
        """Test complete design transformation flow."""
        # Mock the generate_image to return proper format
        mock_gemini_client.generate_image.return_value = {
            'images': [Image.new('RGB', (1024, 768), color='blue')],
            'metadata': {'model': 'imagen-4.0'}
        }

        # 1. Create Imagen service
        imagen_service = ImagenService(gemini_client=mock_gemini_client)

        # 2. Create transformation request
        request = DesignTransformationRequest(
            original_image_path=sample_images['original'],
            transformation_type="style_transfer",
            transformation_params={"target_style": "modern"},
            num_variations=1
        )

        # 3. Transform design
        result = await imagen_service.transform_design(request)

        # Verify result
        assert result.success is True
        assert len(result.images) > 0
        assert mock_gemini_client.generate_image.called
    
    @pytest.mark.asyncio
    async def test_workflow_orchestration(self, sample_images, mock_gemini_client, tmp_path):
        """Test design transformation workflow orchestration."""
        # Mock the generate_image to return proper format
        mock_gemini_client.generate_image.return_value = {
            'images': [Image.new('RGB', (1024, 768), color='blue')],
            'metadata': {'model': 'imagen-4.0'}
        }

        # Create workflow
        workflow = DesignTransformationWorkflow(gemini_client=mock_gemini_client)

        # Execute workflow
        result = await workflow.execute(
            original_image_path=sample_images['original'],
            transformation_type="style_transfer",
            transformation_params={"target_style": "modern"}
        )

        # Verify workflow completed
        assert result['status'] == 'completed'
        assert 'transformed_images' in result
        assert len(result.get('errors', [])) == 0
    
    @pytest.mark.asyncio
    async def test_agent_orchestration(self, sample_images, mock_gemini_client):
        """Test design studio agent orchestration."""
        # Mock the generate_image to return proper format
        mock_gemini_client.generate_image.return_value = {
            'images': [Image.new('RGB', (1024, 768), color='blue')],
            'metadata': {'model': 'imagen-4.0'}
        }

        agent = DesignStudioAgent(gemini_client=mock_gemini_client)

        # Test transform action
        response = await agent.process({
            "action": "transform",
            "home_id": "home-123",
            "image_path": sample_images['original'],
            "transformation_type": "style_transfer",
            "transformation_params": {"target_style": "modern"}
        })

        assert response.success is True
        assert response.data is not None
    
    @pytest.mark.asyncio
    async def test_variation_generation_integration(self, sample_images, mock_gemini_client, tmp_path):
        """Test variation generation with preferences."""
        # Create variation service
        variation_service = DesignVariationService(
            gemini_client=mock_gemini_client,
            preferences_file=str(tmp_path / "prefs.json")
        )
        
        # Set up user preferences
        variation_service.update_style_preference("user-1", "modern", liked=True)
        variation_service.update_style_preference("user-1", "scandinavian", liked=True)
        
        # Generate variations
        request = VariationRequest(
            original_image_path=sample_images['original'],
            num_variations=2,
            user_id="user-1"
        )
        
        batch = await variation_service.generate_variations(request)
        
        # Verify variations
        assert batch.total_variations == 2
        assert len(batch.variations) == 2
        assert batch.recommended_variation is not None
    
    def test_visualization_integration(self, sample_images):
        """Test visualization service integration."""
        viz_service = DesignVisualizationService()
        
        # Create side-by-side comparison
        comparison_path = viz_service.create_comparison(
            before_image_path=sample_images['original'],
            after_image_path=sample_images['transformed_0'],
            layout=ComparisonLayout(
                type="side_by_side",
                label_position="top"
            )
        )
        
        assert comparison_path is not None
        assert Path(comparison_path).exists()
        
        # Create variation grid
        grid_path = viz_service.create_variation_grid(
            original_image_path=sample_images['original'],
            variation_paths=[
                sample_images['transformed_0'],
                sample_images['transformed_1'],
                sample_images['transformed_2']
            ],
            style_names=["Modern", "Traditional", "Minimalist"]
        )
        
        assert grid_path is not None
        assert Path(grid_path).exists()
    
    @pytest.mark.asyncio
    async def test_complete_design_project_workflow(self, sample_images, mock_gemini_client, tmp_path):
        """Test complete design project workflow from start to finish."""
        # Mock the generate_image to return proper format
        mock_gemini_client.generate_image.return_value = {
            'images': [Image.new('RGB', (1024, 768), color='blue')],
            'metadata': {'model': 'imagen-4.0'}
        }

        # 1. Initialize services
        imagen_service = ImagenService(gemini_client=mock_gemini_client)
        variation_service = DesignVariationService(
            imagen_service=imagen_service,
            gemini_client=mock_gemini_client,
            preferences_file=str(tmp_path / "prefs.json")
        )
        viz_service = DesignVisualizationService()

        # 2. Generate variations
        request = VariationRequest(
            original_image_path=sample_images['original'],
            num_variations=3,
            style_preferences=["modern", "scandinavian", "minimalist"]
        )

        batch = await variation_service.generate_variations(request)

        # 3. Create visualizations
        if batch.variations:
            # Use sample images for visualization (since we're mocking)
            comparison_path = viz_service.create_comparison(
                before_image_path=sample_images['original'],
                after_image_path=sample_images['transformed_0']
            )

            assert comparison_path is not None

        # 4. Verify complete workflow
        assert batch.total_variations == 3
        assert batch.recommended_variation is not None
    
    @pytest.mark.asyncio
    async def test_preference_learning_workflow(self, sample_images, mock_gemini_client, tmp_path):
        """Test preference learning across multiple generations."""
        variation_service = DesignVariationService(
            gemini_client=mock_gemini_client,
            preferences_file=str(tmp_path / "prefs.json")
        )
        
        user_id = "user-test"
        
        # First generation - no preferences
        request1 = VariationRequest(
            original_image_path=sample_images['original'],
            num_variations=3,
            user_id=user_id
        )
        batch1 = await variation_service.generate_variations(request1)
        
        # User provides feedback
        for var in batch1.variations[:2]:
            variation_service.update_style_preference(user_id, var.style, liked=True)
        
        # Second generation - should use preferences
        request2 = VariationRequest(
            original_image_path=sample_images['original'],
            num_variations=3,
            user_id=user_id
        )
        batch2 = await variation_service.generate_variations(request2)
        
        # Verify preferences were used
        preferred_styles = variation_service.get_user_preferred_styles(user_id)
        assert len(preferred_styles) > 0
        
        # At least one variation should match preferred styles
        batch2_styles = [v.style for v in batch2.variations]
        assert any(style in preferred_styles for style in batch2_styles)
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, tmp_path, mock_gemini_client):
        """Test batch processing of multiple images."""
        # Create multiple images
        image_paths = []
        for i in range(3):
            img = Image.new('RGB', (800, 600), color='white')
            path = tmp_path / f"room_{i}.png"
            img.save(path)
            image_paths.append(str(path))
        
        # Create variation service
        variation_service = DesignVariationService(
            gemini_client=mock_gemini_client,
            preferences_file=str(tmp_path / "prefs.json")
        )
        
        # Batch generate
        batches = await variation_service.generate_batch_variations(
            image_paths=image_paths,
            num_variations_per_image=2
        )
        
        # Verify all batches
        assert len(batches) == 3
        assert all(b.total_variations == 2 for b in batches)
    
    def test_database_model_integration(self):
        """Test database models can be instantiated."""
        # Create design project
        project = DesignProject(
            id=str(uuid.uuid4()),
            home_id="home-123",
            user_id="user-456",
            name="Kitchen Redesign",
            description="Modern kitchen transformation",
            room_type="kitchen",
            original_image_path="/path/to/image.png",
            status="draft"
        )
        
        assert project.id is not None
        assert project.name == "Kitchen Redesign"
        
        # Create transformation
        transformation = DesignTransformation(
            id=str(uuid.uuid4()),
            project_id=project.id,
            transformation_type="style_transfer",
            transformation_params={"target_style": "modern"},
            original_image_path="/path/to/original.png",
            status="pending"
        )
        
        assert transformation.project_id == project.id
        
        # Create variation
        variation = DesignVariation(
            id=str(uuid.uuid4()),
            project_id=project.id,
            batch_id="batch-123",
            style="modern",
            image_path="/path/to/variation.png",
            quality_score=0.85
        )
        
        assert variation.style == "modern"
        assert variation.quality_score == 0.85
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, sample_images, tmp_path):
        """Test error handling across integrated components."""
        # Create client that fails
        failing_client = Mock()
        failing_client.generate_image = AsyncMock(side_effect=Exception("API Error"))
        
        imagen_service = ImagenService(gemini_client=failing_client)
        
        # Should handle error gracefully
        request = DesignTransformationRequest(
            original_image_path=sample_images['original'],
            transformation_type="style_transfer",
            transformation_params={"target_style": "modern"}
        )
        
        result = await imagen_service.transform_design(request)
        
        # Should return failure result
        assert result.success is False
        assert result.error is not None
    
    @pytest.mark.asyncio
    async def test_style_recommendation_integration(self, sample_images, mock_gemini_client, tmp_path):
        """Test style recommendation system."""
        variation_service = DesignVariationService(
            gemini_client=mock_gemini_client,
            preferences_file=str(tmp_path / "prefs.json")
        )
        
        # Get recommendations without context
        recs1 = variation_service.get_style_recommendations()
        assert len(recs1) > 0
        
        # Get recommendations for specific room
        recs2 = variation_service.get_style_recommendations(room_type="kitchen")
        assert len(recs2) > 0
        assert any(r["is_room_recommended"] for r in recs2)
        
        # Add user preferences
        user_id = "user-test"
        variation_service.update_style_preference(user_id, "modern", liked=True)
        
        # Get recommendations with user context
        recs3 = variation_service.get_style_recommendations(user_id=user_id)
        modern_rec = next((r for r in recs3 if r["style"] == "modern"), None)
        assert modern_rec is not None
        assert modern_rec["is_user_preferred"] is True


class TestWeek3Performance:
    """Performance tests for Week 3 components."""
    
    @pytest.mark.asyncio
    async def test_variation_generation_performance(self, tmp_path, mock_gemini_client):
        """Test variation generation performance."""
        import time

        # Mock the generate_image to return proper format
        mock_gemini_client.generate_image.return_value = {
            'images': [Image.new('RGB', (1024, 768), color='blue')],
            'metadata': {'model': 'imagen-4.0'}
        }

        # Create test image
        img = Image.new('RGB', (1024, 768), color='white')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        variation_service = DesignVariationService(
            gemini_client=mock_gemini_client,
            preferences_file=str(tmp_path / "prefs.json")
        )

        # Measure generation time
        start = time.time()

        request = VariationRequest(
            original_image_path=str(img_path),
            num_variations=5
        )

        batch = await variation_service.generate_variations(request)

        elapsed = time.time() - start

        # Should complete in reasonable time (with mocking)
        assert elapsed < 60.0  # 60 seconds max (generous for mocked calls)
        assert batch.total_variations == 5

