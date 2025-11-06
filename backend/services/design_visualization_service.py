"""
Design Visualization Service for HomeView AI.

Production-ready service for creating visual comparisons and design presentations.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from io import BytesIO
from datetime import datetime
import uuid

from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ComparisonLayout(BaseModel):
    """Configuration for comparison layout."""
    layout_type: str = Field("side_by_side", description="Layout: side_by_side, stacked, grid")
    image_size: Tuple[int, int] = Field((800, 600), description="Target size for each image")
    gap: int = Field(20, description="Gap between images in pixels")
    add_labels: bool = Field(True, description="Add before/after labels")
    label_position: str = Field("top", description="Label position: top, bottom, overlay")
    background_color: Tuple[int, int, int] = Field((255, 255, 255), description="Background color RGB")


class VariationGrid(BaseModel):
    """Configuration for variation grid."""
    columns: int = Field(2, description="Number of columns")
    image_size: Tuple[int, int] = Field((400, 300), description="Size for each variation")
    gap: int = Field(10, description="Gap between images")
    add_style_labels: bool = Field(True, description="Add style name labels")
    include_original: bool = Field(True, description="Include original image in grid")


class DesignHistory(BaseModel):
    """Design transformation history entry."""
    timestamp: str
    transformation_type: str
    image_path: str
    parameters: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DesignVisualizationService:
    """
    Production-ready service for design visualization and comparisons.
    
    Features:
    - Before/after comparisons with multiple layouts
    - Design variation grids
    - Design history timelines
    - Interactive comparison tools
    - Export to various formats
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize visualization service.
        
        Args:
            output_dir: Directory to save visualizations. Defaults to 'visualizations'.
        """
        self.output_dir = Path(output_dir or "visualizations")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to load a font, fall back to default if not available
        try:
            self.font_large = ImageFont.truetype("arial.ttf", 24)
            self.font_medium = ImageFont.truetype("arial.ttf", 18)
            self.font_small = ImageFont.truetype("arial.ttf", 14)
        except:
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
        
        logger.info(f"Design visualization service initialized. Output: {self.output_dir}")
    
    def create_comparison(
        self,
        before_image_path: str,
        after_image_path: str,
        layout: Optional[ComparisonLayout] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Create a before/after comparison image.
        
        Args:
            before_image_path: Path to before image
            after_image_path: Path to after image
            layout: Comparison layout configuration
            output_path: Optional output path
            
        Returns:
            Path to comparison image
        """
        layout = layout or ComparisonLayout()
        
        try:
            # Load images
            before_img = Image.open(before_image_path).convert('RGB')
            after_img = Image.open(after_image_path).convert('RGB')
            
            # Resize to target size
            before_img = before_img.resize(layout.image_size, Image.Resampling.LANCZOS)
            after_img = after_img.resize(layout.image_size, Image.Resampling.LANCZOS)
            
            # Create comparison based on layout type
            if layout.layout_type == "side_by_side":
                comparison = self._create_side_by_side(before_img, after_img, layout)
            elif layout.layout_type == "stacked":
                comparison = self._create_stacked(before_img, after_img, layout)
            elif layout.layout_type == "grid":
                comparison = self._create_grid([before_img, after_img], layout)
            else:
                raise ValueError(f"Unknown layout type: {layout.layout_type}")
            
            # Save
            if output_path is None:
                output_path = str(self.output_dir / f"comparison_{uuid.uuid4().hex[:8]}.png")
            
            comparison.save(output_path, format='PNG', quality=95)
            logger.info(f"Comparison created: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating comparison: {str(e)}", exc_info=True)
            raise
    
    def _create_side_by_side(
        self,
        before_img: Image.Image,
        after_img: Image.Image,
        layout: ComparisonLayout
    ) -> Image.Image:
        """Create side-by-side comparison."""
        width = before_img.width + after_img.width + layout.gap
        height = max(before_img.height, after_img.height)
        
        # Add space for labels if needed
        label_height = 40 if layout.add_labels and layout.label_position in ["top", "bottom"] else 0
        total_height = height + label_height
        
        # Create canvas
        comparison = Image.new('RGB', (width, total_height), layout.background_color)
        
        # Calculate positions
        y_offset = label_height if layout.label_position == "top" else 0
        
        # Paste images
        comparison.paste(before_img, (0, y_offset))
        comparison.paste(after_img, (before_img.width + layout.gap, y_offset))
        
        # Add labels
        if layout.add_labels:
            draw = ImageDraw.Draw(comparison)
            
            if layout.label_position == "top":
                draw.text((before_img.width // 2, 10), "BEFORE", fill=(0, 0, 0), font=self.font_medium, anchor="mt")
                draw.text((before_img.width + layout.gap + after_img.width // 2, 10), "AFTER", fill=(0, 0, 0), font=self.font_medium, anchor="mt")
            elif layout.label_position == "bottom":
                draw.text((before_img.width // 2, height + 10), "BEFORE", fill=(0, 0, 0), font=self.font_medium, anchor="mt")
                draw.text((before_img.width + layout.gap + after_img.width // 2, height + 10), "AFTER", fill=(0, 0, 0), font=self.font_medium, anchor="mt")
            elif layout.label_position == "overlay":
                # Add semi-transparent overlay for labels
                overlay = Image.new('RGBA', comparison.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                overlay_draw.rectangle([(0, 0), (before_img.width, 35)], fill=(0, 0, 0, 128))
                overlay_draw.rectangle([(before_img.width + layout.gap, 0), (width, 35)], fill=(0, 0, 0, 128))
                comparison = Image.alpha_composite(comparison.convert('RGBA'), overlay).convert('RGB')
                
                draw = ImageDraw.Draw(comparison)
                draw.text((before_img.width // 2, 10), "BEFORE", fill=(255, 255, 255), font=self.font_medium, anchor="mt")
                draw.text((before_img.width + layout.gap + after_img.width // 2, 10), "AFTER", fill=(255, 255, 255), font=self.font_medium, anchor="mt")
        
        return comparison
    
    def _create_stacked(
        self,
        before_img: Image.Image,
        after_img: Image.Image,
        layout: ComparisonLayout
    ) -> Image.Image:
        """Create stacked (vertical) comparison."""
        width = max(before_img.width, after_img.width)
        height = before_img.height + after_img.height + layout.gap
        
        label_height = 40 if layout.add_labels else 0
        total_height = height + (label_height * 2 if layout.add_labels else 0)
        
        comparison = Image.new('RGB', (width, total_height), layout.background_color)
        
        y_pos = 0
        if layout.add_labels:
            y_pos += label_height
        
        comparison.paste(before_img, (0, y_pos))
        y_pos += before_img.height + layout.gap
        
        if layout.add_labels:
            y_pos += label_height
        
        comparison.paste(after_img, (0, y_pos))
        
        if layout.add_labels:
            draw = ImageDraw.Draw(comparison)
            draw.text((width // 2, 10), "BEFORE", fill=(0, 0, 0), font=self.font_medium, anchor="mt")
            draw.text((width // 2, before_img.height + layout.gap + label_height + 10), "AFTER", fill=(0, 0, 0), font=self.font_medium, anchor="mt")
        
        return comparison
    
    def _create_grid(
        self,
        images: List[Image.Image],
        layout: ComparisonLayout
    ) -> Image.Image:
        """Create grid layout for multiple images."""
        # Simple 2-column grid
        cols = 2
        rows = (len(images) + cols - 1) // cols
        
        cell_width = images[0].width
        cell_height = images[0].height
        
        width = cols * cell_width + (cols - 1) * layout.gap
        height = rows * cell_height + (rows - 1) * layout.gap
        
        grid = Image.new('RGB', (width, height), layout.background_color)
        
        for idx, img in enumerate(images):
            row = idx // cols
            col = idx % cols
            x = col * (cell_width + layout.gap)
            y = row * (cell_height + layout.gap)
            grid.paste(img, (x, y))
        
        return grid
    
    def create_variation_grid(
        self,
        original_image_path: str,
        variation_paths: List[str],
        style_names: Optional[List[str]] = None,
        grid_config: Optional[VariationGrid] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Create a grid of design variations.
        
        Args:
            original_image_path: Path to original image
            variation_paths: List of variation image paths
            style_names: Optional list of style names for labels
            grid_config: Grid configuration
            output_path: Optional output path
            
        Returns:
            Path to grid image
        """
        grid_config = grid_config or VariationGrid()
        
        try:
            # Load images
            images = []
            labels = []
            
            if grid_config.include_original:
                images.append(Image.open(original_image_path).convert('RGB'))
                labels.append("Original")
            
            for idx, path in enumerate(variation_paths):
                images.append(Image.open(path).convert('RGB'))
                if style_names and idx < len(style_names):
                    labels.append(style_names[idx])
                else:
                    labels.append(f"Variation {idx + 1}")
            
            # Resize all images
            images = [img.resize(grid_config.image_size, Image.Resampling.LANCZOS) for img in images]
            
            # Calculate grid dimensions
            cols = grid_config.columns
            rows = (len(images) + cols - 1) // cols
            
            cell_width, cell_height = grid_config.image_size
            label_height = 30 if grid_config.add_style_labels else 0
            
            width = cols * cell_width + (cols - 1) * grid_config.gap
            height = rows * (cell_height + label_height) + (rows - 1) * grid_config.gap
            
            # Create grid
            grid = Image.new('RGB', (width, height), (255, 255, 255))
            draw = ImageDraw.Draw(grid) if grid_config.add_style_labels else None
            
            for idx, img in enumerate(images):
                row = idx // cols
                col = idx % cols
                
                x = col * (cell_width + grid_config.gap)
                y = row * (cell_height + label_height + grid_config.gap)
                
                grid.paste(img, (x, y))
                
                if grid_config.add_style_labels and draw:
                    label_y = y + cell_height + 5
                    draw.text((x + cell_width // 2, label_y), labels[idx], fill=(0, 0, 0), font=self.font_small, anchor="mt")
            
            # Save
            if output_path is None:
                output_path = str(self.output_dir / f"variations_{uuid.uuid4().hex[:8]}.png")
            
            grid.save(output_path, format='PNG', quality=95)
            logger.info(f"Variation grid created: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating variation grid: {str(e)}", exc_info=True)
            raise

    def create_history_timeline(
        self,
        history: List[DesignHistory],
        output_path: Optional[str] = None
    ) -> str:
        """
        Create a visual timeline of design transformations.

        Args:
            history: List of design history entries
            output_path: Optional output path

        Returns:
            Path to timeline image
        """
        try:
            if not history:
                raise ValueError("History is empty")

            # Load all images
            images = []
            for entry in history:
                img = Image.open(entry.image_path).convert('RGB')
                img = img.resize((300, 225), Image.Resampling.LANCZOS)
                images.append((img, entry))

            # Calculate dimensions
            gap = 20
            arrow_width = 50
            label_height = 60

            img_width = 300
            img_height = 225

            total_width = len(images) * img_width + (len(images) - 1) * (gap + arrow_width)
            total_height = img_height + label_height

            # Create timeline
            timeline = Image.new('RGB', (total_width, total_height), (255, 255, 255))
            draw = ImageDraw.Draw(timeline)

            x_pos = 0
            for idx, (img, entry) in enumerate(images):
                # Paste image
                timeline.paste(img, (x_pos, 0))

                # Add label
                label_text = f"{entry.transformation_type}\n{entry.timestamp[:10]}"
                draw.text((x_pos + img_width // 2, img_height + 10), label_text, fill=(0, 0, 0), font=self.font_small, anchor="mt")

                # Draw arrow to next image
                if idx < len(images) - 1:
                    arrow_x = x_pos + img_width + gap
                    arrow_y = img_height // 2

                    # Draw arrow line
                    draw.line([(arrow_x, arrow_y), (arrow_x + arrow_width, arrow_y)], fill=(100, 100, 100), width=3)
                    # Draw arrow head
                    draw.polygon([
                        (arrow_x + arrow_width, arrow_y),
                        (arrow_x + arrow_width - 10, arrow_y - 8),
                        (arrow_x + arrow_width - 10, arrow_y + 8)
                    ], fill=(100, 100, 100))

                x_pos += img_width + gap + arrow_width

            # Save
            if output_path is None:
                output_path = str(self.output_dir / f"timeline_{uuid.uuid4().hex[:8]}.png")

            timeline.save(output_path, format='PNG', quality=95)
            logger.info(f"History timeline created: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error creating timeline: {str(e)}", exc_info=True)
            raise

    def create_slider_comparison(
        self,
        before_image_path: str,
        after_image_path: str,
        slider_position: float = 0.5,
        output_path: Optional[str] = None
    ) -> str:
        """
        Create a slider-style comparison (split view).

        Args:
            before_image_path: Path to before image
            after_image_path: Path to after image
            slider_position: Position of slider (0.0 to 1.0)
            output_path: Optional output path

        Returns:
            Path to comparison image
        """
        try:
            # Load images
            before_img = Image.open(before_image_path).convert('RGB')
            after_img = Image.open(after_image_path).convert('RGB')

            # Ensure same size
            size = before_img.size
            after_img = after_img.resize(size, Image.Resampling.LANCZOS)

            # Calculate split position
            split_x = int(size[0] * slider_position)

            # Create comparison
            comparison = Image.new('RGB', size)

            # Paste left part (before)
            before_crop = before_img.crop((0, 0, split_x, size[1]))
            comparison.paste(before_crop, (0, 0))

            # Paste right part (after)
            after_crop = after_img.crop((split_x, 0, size[0], size[1]))
            comparison.paste(after_crop, (split_x, 0))

            # Draw slider line
            draw = ImageDraw.Draw(comparison)
            draw.line([(split_x, 0), (split_x, size[1])], fill=(255, 255, 255), width=4)

            # Draw slider handle
            handle_y = size[1] // 2
            handle_size = 30
            draw.ellipse([
                (split_x - handle_size, handle_y - handle_size),
                (split_x + handle_size, handle_y + handle_size)
            ], fill=(255, 255, 255), outline=(0, 0, 0), width=2)

            # Add arrows
            draw.polygon([
                (split_x - 15, handle_y),
                (split_x - 5, handle_y - 5),
                (split_x - 5, handle_y + 5)
            ], fill=(0, 0, 0))
            draw.polygon([
                (split_x + 15, handle_y),
                (split_x + 5, handle_y - 5),
                (split_x + 5, handle_y + 5)
            ], fill=(0, 0, 0))

            # Save
            if output_path is None:
                output_path = str(self.output_dir / f"slider_{uuid.uuid4().hex[:8]}.png")

            comparison.save(output_path, format='PNG', quality=95)
            logger.info(f"Slider comparison created: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error creating slider comparison: {str(e)}", exc_info=True)
            raise

    def export_comparison_set(
        self,
        before_image_path: str,
        after_image_path: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Export a complete set of comparison visualizations.

        Creates:
        - Side-by-side comparison
        - Stacked comparison
        - Slider comparison

        Args:
            before_image_path: Path to before image
            after_image_path: Path to after image
            output_dir: Optional output directory

        Returns:
            Dictionary mapping comparison type to file path
        """
        try:
            output_dir = Path(output_dir or self.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            results = {}

            # Side-by-side
            results["side_by_side"] = self.create_comparison(
                before_image_path,
                after_image_path,
                ComparisonLayout(layout_type="side_by_side"),
                str(output_dir / "side_by_side.png")
            )

            # Stacked
            results["stacked"] = self.create_comparison(
                before_image_path,
                after_image_path,
                ComparisonLayout(layout_type="stacked"),
                str(output_dir / "stacked.png")
            )

            # Slider
            results["slider"] = self.create_slider_comparison(
                before_image_path,
                after_image_path,
                output_path=str(output_dir / "slider.png")
            )

            logger.info(f"Exported {len(results)} comparison types")

            return results

        except Exception as e:
            logger.error(f"Error exporting comparison set: {str(e)}", exc_info=True)
            raise

