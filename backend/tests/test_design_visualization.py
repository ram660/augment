"""
Tests for Design Visualization Service.
"""

import pytest
from pathlib import Path
from PIL import Image

from backend.services.design_visualization_service import (
    DesignVisualizationService,
    ComparisonLayout,
    VariationGrid,
    DesignHistory
)


@pytest.fixture
def viz_service(tmp_path):
    """Create visualization service with temp output dir."""
    return DesignVisualizationService(output_dir=str(tmp_path / "viz"))


@pytest.fixture
def sample_images(tmp_path):
    """Create sample images for testing."""
    images = {}
    
    # Create before image (red)
    before = Image.new('RGB', (800, 600), color='red')
    before_path = tmp_path / "before.png"
    before.save(before_path)
    images['before'] = str(before_path)
    
    # Create after image (blue)
    after = Image.new('RGB', (800, 600), color='blue')
    after_path = tmp_path / "after.png"
    after.save(after_path)
    images['after'] = str(after_path)
    
    # Create variations (different colors)
    colors = ['green', 'yellow', 'purple', 'orange']
    images['variations'] = []
    for idx, color in enumerate(colors):
        var = Image.new('RGB', (800, 600), color=color)
        var_path = tmp_path / f"variation_{idx}.png"
        var.save(var_path)
        images['variations'].append(str(var_path))
    
    return images


class TestDesignVisualizationService:
    """Tests for DesignVisualizationService."""
    
    def test_service_initialization(self, viz_service):
        """Test service initializes correctly."""
        assert viz_service is not None
        assert viz_service.output_dir.exists()
    
    def test_create_side_by_side_comparison(self, viz_service, sample_images):
        """Test side-by-side comparison creation."""
        result_path = viz_service.create_comparison(
            before_image_path=sample_images['before'],
            after_image_path=sample_images['after'],
            layout=ComparisonLayout(layout_type="side_by_side")
        )
        
        assert Path(result_path).exists()
        
        # Verify image
        img = Image.open(result_path)
        assert img.width > 800  # Should be wider than single image
        assert img.height >= 600
    
    def test_create_stacked_comparison(self, viz_service, sample_images):
        """Test stacked comparison creation."""
        result_path = viz_service.create_comparison(
            before_image_path=sample_images['before'],
            after_image_path=sample_images['after'],
            layout=ComparisonLayout(layout_type="stacked")
        )
        
        assert Path(result_path).exists()
        
        # Verify image
        img = Image.open(result_path)
        assert img.height > 600  # Should be taller than single image
    
    def test_create_comparison_with_labels(self, viz_service, sample_images):
        """Test comparison with labels."""
        result_path = viz_service.create_comparison(
            before_image_path=sample_images['before'],
            after_image_path=sample_images['after'],
            layout=ComparisonLayout(
                layout_type="side_by_side",
                add_labels=True,
                label_position="top"
            )
        )
        
        assert Path(result_path).exists()
        
        # Verify image has extra height for labels
        img = Image.open(result_path)
        assert img.height > 600
    
    def test_create_comparison_without_labels(self, viz_service, sample_images):
        """Test comparison without labels."""
        result_path = viz_service.create_comparison(
            before_image_path=sample_images['before'],
            after_image_path=sample_images['after'],
            layout=ComparisonLayout(
                layout_type="side_by_side",
                add_labels=False
            )
        )
        
        assert Path(result_path).exists()
    
    def test_create_variation_grid(self, viz_service, sample_images):
        """Test variation grid creation."""
        result_path = viz_service.create_variation_grid(
            original_image_path=sample_images['before'],
            variation_paths=sample_images['variations'],
            style_names=["Modern", "Traditional", "Minimalist", "Industrial"]
        )
        
        assert Path(result_path).exists()
        
        # Verify grid
        img = Image.open(result_path)
        assert img.width > 400  # Should be wider than single variation
        assert img.height > 300  # Should be taller than single variation
    
    def test_create_variation_grid_without_original(self, viz_service, sample_images):
        """Test variation grid without original image."""
        result_path = viz_service.create_variation_grid(
            original_image_path=sample_images['before'],
            variation_paths=sample_images['variations'][:2],
            grid_config=VariationGrid(include_original=False, columns=2)
        )
        
        assert Path(result_path).exists()
    
    def test_create_variation_grid_custom_config(self, viz_service, sample_images):
        """Test variation grid with custom configuration."""
        result_path = viz_service.create_variation_grid(
            original_image_path=sample_images['before'],
            variation_paths=sample_images['variations'],
            grid_config=VariationGrid(
                columns=3,
                image_size=(300, 225),
                gap=15,
                add_style_labels=True
            )
        )
        
        assert Path(result_path).exists()
    
    def test_create_history_timeline(self, viz_service, sample_images):
        """Test history timeline creation."""
        history = [
            DesignHistory(
                timestamp="2024-01-01T10:00:00",
                transformation_type="style_transfer",
                image_path=sample_images['before'],
                parameters={"style": "modern"}
            ),
            DesignHistory(
                timestamp="2024-01-02T11:00:00",
                transformation_type="color_change",
                image_path=sample_images['variations'][0],
                parameters={"color": "green"}
            ),
            DesignHistory(
                timestamp="2024-01-03T12:00:00",
                transformation_type="furniture_swap",
                image_path=sample_images['variations'][1],
                parameters={"furniture": "modern"}
            )
        ]
        
        result_path = viz_service.create_history_timeline(history)
        
        assert Path(result_path).exists()
        
        # Verify timeline
        img = Image.open(result_path)
        assert img.width > 300  # Should be wider than single image
    
    def test_create_history_timeline_empty(self, viz_service):
        """Test timeline creation with empty history."""
        with pytest.raises(ValueError, match="History is empty"):
            viz_service.create_history_timeline([])
    
    def test_create_slider_comparison(self, viz_service, sample_images):
        """Test slider comparison creation."""
        result_path = viz_service.create_slider_comparison(
            before_image_path=sample_images['before'],
            after_image_path=sample_images['after'],
            slider_position=0.5
        )
        
        assert Path(result_path).exists()
        
        # Verify image
        img = Image.open(result_path)
        assert img.size == (800, 600)  # Should match original size
    
    def test_create_slider_comparison_different_positions(self, viz_service, sample_images):
        """Test slider at different positions."""
        positions = [0.25, 0.5, 0.75]
        
        for pos in positions:
            result_path = viz_service.create_slider_comparison(
                before_image_path=sample_images['before'],
                after_image_path=sample_images['after'],
                slider_position=pos
            )
            
            assert Path(result_path).exists()
    
    def test_export_comparison_set(self, viz_service, sample_images, tmp_path):
        """Test exporting complete comparison set."""
        output_dir = tmp_path / "comparison_set"
        
        results = viz_service.export_comparison_set(
            before_image_path=sample_images['before'],
            after_image_path=sample_images['after'],
            output_dir=str(output_dir)
        )
        
        assert len(results) == 3
        assert "side_by_side" in results
        assert "stacked" in results
        assert "slider" in results
        
        # Verify all files exist
        for path in results.values():
            assert Path(path).exists()
    
    def test_comparison_with_custom_output_path(self, viz_service, sample_images, tmp_path):
        """Test comparison with custom output path."""
        custom_path = tmp_path / "custom_comparison.png"
        
        result_path = viz_service.create_comparison(
            before_image_path=sample_images['before'],
            after_image_path=sample_images['after'],
            output_path=str(custom_path)
        )
        
        assert result_path == str(custom_path)
        assert Path(result_path).exists()
    
    def test_comparison_with_different_sizes(self, viz_service, tmp_path):
        """Test comparison with different sized images."""
        # Create images of different sizes
        img1 = Image.new('RGB', (800, 600), color='red')
        img2 = Image.new('RGB', (1024, 768), color='blue')
        
        path1 = tmp_path / "img1.png"
        path2 = tmp_path / "img2.png"
        img1.save(path1)
        img2.save(path2)
        
        result_path = viz_service.create_comparison(
            before_image_path=str(path1),
            after_image_path=str(path2),
            layout=ComparisonLayout(image_size=(600, 450))
        )
        
        assert Path(result_path).exists()
    
    def test_comparison_layout_configurations(self, viz_service, sample_images):
        """Test various layout configurations."""
        configs = [
            ComparisonLayout(layout_type="side_by_side", gap=10),
            ComparisonLayout(layout_type="side_by_side", gap=30),
            ComparisonLayout(layout_type="stacked", gap=20),
            ComparisonLayout(layout_type="side_by_side", background_color=(240, 240, 240))
        ]
        
        for config in configs:
            result_path = viz_service.create_comparison(
                before_image_path=sample_images['before'],
                after_image_path=sample_images['after'],
                layout=config
            )
            
            assert Path(result_path).exists()


class TestComparisonLayout:
    """Tests for ComparisonLayout model."""
    
    def test_default_layout(self):
        """Test default layout configuration."""
        layout = ComparisonLayout()
        assert layout.layout_type == "side_by_side"
        assert layout.image_size == (800, 600)
        assert layout.gap == 20
        assert layout.add_labels is True
    
    def test_custom_layout(self):
        """Test custom layout configuration."""
        layout = ComparisonLayout(
            layout_type="stacked",
            image_size=(1024, 768),
            gap=30,
            add_labels=False
        )
        assert layout.layout_type == "stacked"
        assert layout.image_size == (1024, 768)
        assert layout.gap == 30
        assert layout.add_labels is False


class TestVariationGrid:
    """Tests for VariationGrid model."""
    
    def test_default_grid(self):
        """Test default grid configuration."""
        grid = VariationGrid()
        assert grid.columns == 2
        assert grid.image_size == (400, 300)
        assert grid.gap == 10
        assert grid.add_style_labels is True
        assert grid.include_original is True
    
    def test_custom_grid(self):
        """Test custom grid configuration."""
        grid = VariationGrid(
            columns=3,
            image_size=(500, 375),
            gap=15,
            include_original=False
        )
        assert grid.columns == 3
        assert grid.image_size == (500, 375)
        assert grid.gap == 15
        assert grid.include_original is False


class TestDesignHistory:
    """Tests for DesignHistory model."""
    
    def test_design_history_creation(self):
        """Test creating design history entry."""
        history = DesignHistory(
            timestamp="2024-01-01T10:00:00",
            transformation_type="style_transfer",
            image_path="/path/to/image.png",
            parameters={"style": "modern"}
        )
        
        assert history.timestamp == "2024-01-01T10:00:00"
        assert history.transformation_type == "style_transfer"
        assert history.image_path == "/path/to/image.png"
        assert history.parameters["style"] == "modern"

