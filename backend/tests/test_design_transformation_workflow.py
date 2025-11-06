"""
Tests for Design Transformation Workflow and Design Studio Agent.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from PIL import Image
from pathlib import Path

from backend.workflows.design_transformation_workflow import (
    DesignTransformationWorkflow,
    DesignTransformationState
)
from backend.agents.design.design_studio_agent import DesignStudioAgent
from backend.services.imagen_service import ImageGenerationResult


@pytest.fixture
def mock_imagen_service():
    """Create mock Imagen service."""
    service = Mock()
    service.transform_design = AsyncMock()
    service.generate_design_variations = AsyncMock()
    service.create_before_after_comparison = AsyncMock()
    return service


@pytest.fixture
def mock_gemini_client():
    """Create mock Gemini client."""
    client = Mock()
    client.generate_content = AsyncMock()
    return client


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample image file."""
    img = Image.new('RGB', (512, 512), color='red')
    img_path = tmp_path / "test_image.png"
    img.save(img_path)
    return str(img_path)


@pytest.fixture
def design_workflow(mock_imagen_service, mock_gemini_client):
    """Create design transformation workflow with mocks."""
    return DesignTransformationWorkflow(
        imagen_service=mock_imagen_service,
        gemini_client=mock_gemini_client
    )


@pytest.fixture
def design_agent(mock_imagen_service, mock_gemini_client):
    """Create design studio agent with mocks."""
    return DesignStudioAgent(
        imagen_service=mock_imagen_service,
        gemini_client=mock_gemini_client
    )


class TestDesignTransformationWorkflow:
    """Tests for DesignTransformationWorkflow."""
    
    @pytest.mark.asyncio
    async def test_workflow_initialization(self, design_workflow):
        """Test workflow initializes correctly."""
        assert design_workflow is not None
        assert design_workflow.imagen_service is not None
        assert design_workflow.gemini_client is not None
        assert design_workflow.app is not None
    
    @pytest.mark.asyncio
    async def test_validate_image_success(self, design_workflow, sample_image):
        """Test image validation succeeds."""
        state: DesignTransformationState = {
            "workflow_id": "test-123",
            "home_id": "home-1",
            "original_image_path": sample_image,
            "transformation_type": "style_transfer",
            "transformation_params": {},
            "num_variations": 1,
            "errors": [],
            "execution_metadata": {}
        }
        
        result = await design_workflow._validate_image(state)
        
        assert result["validated_image"] is True
        assert "image_metadata" in result
        assert result["image_metadata"]["width"] == 512
        assert result["image_metadata"]["height"] == 512
    
    @pytest.mark.asyncio
    async def test_validate_image_not_found(self, design_workflow):
        """Test image validation fails for missing file."""
        state: DesignTransformationState = {
            "workflow_id": "test-123",
            "home_id": "home-1",
            "original_image_path": "/nonexistent/image.png",
            "transformation_type": "style_transfer",
            "transformation_params": {},
            "num_variations": 1,
            "errors": [],
            "execution_metadata": {}
        }
        
        result = await design_workflow._validate_image(state)
        
        assert result["validated_image"] is False
        assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_design(self, design_workflow, sample_image, mock_gemini_client):
        """Test design analysis."""
        mock_gemini_client.generate_content.return_value = "Modern kitchen with white cabinets"
        
        state: DesignTransformationState = {
            "workflow_id": "test-123",
            "home_id": "home-1",
            "original_image_path": sample_image,
            "transformation_type": "style_transfer",
            "transformation_params": {},
            "num_variations": 1,
            "image_metadata": {},
            "errors": [],
            "execution_metadata": {}
        }
        
        result = await design_workflow._analyze_design(state)
        
        assert "design_analysis" in result["image_metadata"]
        assert mock_gemini_client.generate_content.called
    
    @pytest.mark.asyncio
    async def test_generate_transformed_images(self, design_workflow, sample_image, mock_imagen_service):
        """Test image generation."""
        mock_result = ImageGenerationResult(
            success=True,
            images=["base64_image_1", "base64_image_2"],
            image_paths=["/path/1.png", "/path/2.png"],
            metadata={},
            generation_time_ms=1500.0
        )
        mock_imagen_service.transform_design.return_value = mock_result
        
        state: DesignTransformationState = {
            "workflow_id": "test-123",
            "home_id": "home-1",
            "original_image_path": sample_image,
            "transformation_type": "style_transfer",
            "transformation_params": {"target_style": "modern"},
            "num_variations": 2,
            "errors": [],
            "execution_metadata": {}
        }
        
        result = await design_workflow._generate_transformed_images(state)
        
        assert len(result["generated_images"]) == 2
        assert len(result["image_paths"]) == 2
        assert result["execution_metadata"]["generation_time_ms"] == 1500.0
    
    @pytest.mark.asyncio
    async def test_create_before_after_comparison(self, design_workflow, sample_image, mock_imagen_service, tmp_path):
        """Test comparison creation."""
        comparison_path = str(tmp_path / "comparison.png")
        mock_imagen_service.create_before_after_comparison.return_value = comparison_path
        
        state: DesignTransformationState = {
            "workflow_id": "test-123",
            "home_id": "home-1",
            "original_image_path": sample_image,
            "transformation_type": "style_transfer",
            "transformation_params": {},
            "num_variations": 1,
            "image_paths": [sample_image],
            "errors": [],
            "execution_metadata": {}
        }
        
        result = await design_workflow._create_before_after_comparison(state)
        
        assert result["comparison_path"] == comparison_path
        assert mock_imagen_service.create_before_after_comparison.called
    
    @pytest.mark.asyncio
    async def test_full_workflow_execution(self, design_workflow, sample_image, mock_imagen_service, mock_gemini_client):
        """Test full workflow execution."""
        # Mock services
        mock_gemini_client.generate_content.return_value = "Modern kitchen"
        mock_result = ImageGenerationResult(
            success=True,
            images=["base64_image"],
            image_paths=["/path/transformed.png"],
            metadata={},
            generation_time_ms=1000.0
        )
        mock_imagen_service.transform_design.return_value = mock_result
        mock_imagen_service.create_before_after_comparison.return_value = "/path/comparison.png"
        
        result = await design_workflow.execute(
            home_id="home-1",
            original_image_path=sample_image,
            transformation_type="style_transfer",
            transformation_params={"target_style": "modern"},
            num_variations=1
        )
        
        assert result["workflow_id"] is not None
        assert result["validated_image"] is True
        assert len(result["generated_images"]) == 1
        assert result["comparison_path"] is not None


class TestDesignStudioAgent:
    """Tests for DesignStudioAgent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, design_agent):
        """Test agent initializes correctly."""
        assert design_agent is not None
        assert design_agent.config.name == "DesignStudioAgent"
        assert design_agent.imagen_service is not None
        assert design_agent.workflow is not None
    
    @pytest.mark.asyncio
    async def test_handle_transformation(self, design_agent, sample_image, mock_imagen_service, mock_gemini_client):
        """Test transformation handling."""
        # Mock workflow execution
        mock_gemini_client.generate_content.return_value = "Modern kitchen"
        mock_result = ImageGenerationResult(
            success=True,
            images=["base64_image"],
            image_paths=["/path/transformed.png"],
            metadata={},
            generation_time_ms=1000.0
        )
        mock_imagen_service.transform_design.return_value = mock_result
        mock_imagen_service.create_before_after_comparison.return_value = "/path/comparison.png"
        
        input_data = {
            "action": "transform",
            "home_id": "home-1",
            "image_path": sample_image,
            "transformation_type": "style_transfer",
            "transformation_params": {"target_style": "modern"},
            "num_variations": 1
        }
        
        response = await design_agent.process(input_data)
        
        assert response.success is True
        assert "generated_images" in response.data
        assert "workflow_id" in response.data
    
    @pytest.mark.asyncio
    async def test_handle_variations(self, design_agent, sample_image, mock_imagen_service):
        """Test variation generation."""
        mock_result = ImageGenerationResult(
            success=True,
            images=["base64_1"],
            image_paths=["/path/1.png"],
            metadata={},
            generation_time_ms=1000.0
        )
        mock_imagen_service.generate_design_variations.return_value = {
            "modern": mock_result,
            "traditional": mock_result
        }
        
        input_data = {
            "action": "generate_variations",
            "home_id": "home-1",
            "image_path": sample_image,
            "styles": ["modern", "traditional"],
            "num_variations": 1
        }
        
        response = await design_agent.process(input_data)
        
        assert response.success is True
        assert "by_style" in response.data
        assert len(response.data["by_style"]) == 2
    
    @pytest.mark.asyncio
    async def test_handle_comparison(self, design_agent, sample_image, mock_imagen_service):
        """Test comparison creation."""
        mock_imagen_service.create_before_after_comparison.return_value = "/path/comparison.png"
        
        input_data = {
            "action": "compare",
            "before_image": sample_image,
            "after_image": sample_image
        }
        
        response = await design_agent.process(input_data)
        
        assert response.success is True
        assert response.data["comparison_path"] == "/path/comparison.png"
    
    @pytest.mark.asyncio
    async def test_suggest_styles(self, design_agent, sample_image, mock_gemini_client):
        """Test style suggestions."""
        mock_gemini_client.generate_content.return_value = """1. Modern: Clean lines and minimalist aesthetic
2. Traditional: Classic and timeless design
3. Scandinavian: Light and airy with natural materials"""
        
        input_data = {
            "action": "suggest_styles",
            "image_path": sample_image
        }
        
        response = await design_agent.process(input_data)
        
        assert response.success is True
        assert "suggestions" in response.data
        assert len(response.data["style_list"]) > 0
    
    @pytest.mark.asyncio
    async def test_unknown_action(self, design_agent):
        """Test handling of unknown action."""
        input_data = {
            "action": "unknown_action"
        }
        
        response = await design_agent.process(input_data)
        
        assert response.success is False
        assert "Unknown action" in response.error

