"""
Design Transformation Service - AI-powered room transformations using Gemini Imagen.

This service provides precise, controlled transformations that only modify
what the customer requests while preserving all other aspects of the room.

Supported Transformations:
- Paint walls (color change only)
- Replace flooring (material/style change only)
- Update cabinets (color/finish change only)
- Change countertops (material/color change only)
- Update backsplash (tile/pattern change only)
- Replace fixtures (style/finish change only)
- Add/remove furniture (specific items only)
- Change lighting (fixtures/ambiance only)
"""

import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from PIL import Image
import io
import base64

from backend.integrations.gemini import GeminiClient

logger = logging.getLogger(__name__)


class DesignTransformationService:
    """
    Service for AI-powered design transformations using Gemini Imagen.
    
    Key Features:
    - Precise transformations (only modify requested elements)
    - Preserve room structure and layout
    - Maintain lighting and perspective
    - Keep unchanged elements identical
    - Generate photorealistic results
    """
    
    # Core transformation rules that apply to ALL transformations
    CORE_PRESERVATION_RULES = """
CRITICAL PRESERVATION RULES (MUST FOLLOW):
1. Preserve the exact room layout, dimensions, and spatial arrangement
2. Maintain the original camera angle, perspective, and viewpoint
3. Keep all lighting conditions identical (natural light, shadows, highlights)
4. Preserve all architectural features (windows, doors, moldings, ceiling details)
5. Keep the floor plan and room structure unchanged
6. Maintain the same image composition and framing
7. Preserve any people, pets, or personal items exactly as they are
8. Keep all unchanged elements in their exact original state
9. Match the original photo's quality, resolution, and style
10. Ensure photorealistic output that looks like a real photograph

STRICT NEGATIVE INSTRUCTIONS (DO NOT DO THESE):
- Do NOT add any new objects, furniture, decor, fixtures, or architectural elements
- Do NOT remove or hide existing objects (unless explicitly requested in the prompt)
- Do NOT move or reposition any existing objects or camera viewpoint
- Do NOT alter surfaces or materials outside the requested change scope
- Do NOT change wall/ceiling/floor colors or textures unless explicitly requested
- Do NOT change window/door positions, sizes, or styles; preserve exterior views
- Do NOT retouch, blur, beautify, or alter people/pets if present
- Do NOT change aspect ratio, crop, or reframe the image
- Do NOT introduce style drift; keep the overall look consistent with the original
- Do NOT over-smooth or apply global filters; keep natural grain and detail intact
"""

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """Initialize Design Transformation Service."""
        self.gemini = gemini_client or GeminiClient()
    
    async def transform_paint(
        self,
        image: Union[str, Path, Image.Image, bytes],
        target_color: str,
        target_finish: str = "matte",
        walls_only: bool = True,
        preserve_trim: bool = True,
        num_variations: int = 4
    ) -> List[Image.Image]:
        """
        Transform wall paint color while preserving everything else.

        Args:
            image: Original room image
            target_color: Desired wall color (e.g., "soft gray", "warm beige", "#F5F5DC")
            target_finish: Paint finish (matte, eggshell, satin, semi-gloss, gloss)
            walls_only: If True, only change walls (not ceiling)
            preserve_trim: If True, keep trim/molding original color
            num_variations: Number of variations to generate (1-4)

        Returns:
            List of transformed images with new wall color
        """
        prompt = f"""Transform this room image by changing ONLY the wall paint color.

TARGET CHANGE:
- Change wall color to: {target_color}
- Paint finish: {target_finish}
{'- Change walls only, keep ceiling original color' if walls_only else '- Change walls and ceiling'}
{'- Preserve all trim, molding, and baseboards in original color' if preserve_trim else ''}

{self.CORE_PRESERVATION_RULES}

SPECIFIC PRESERVATION FOR PAINT:
- Keep all flooring materials and patterns identical
- Preserve all furniture, decor, and fixtures exactly as they are
- Maintain all wall textures and imperfections
- Keep all artwork, photos, and wall decorations in place
- Preserve window treatments and their colors
- Maintain all electrical outlets, switches, and hardware
- Keep door colors and finishes unchanged
- Preserve any accent walls or architectural details

OUTPUT REQUIREMENTS:
- Generate a photorealistic image that looks like a professional photograph
- The new paint color should appear naturally applied with proper coverage
- Maintain realistic lighting interactions with the new wall color
- Ensure the finish ({target_finish}) is visually apparent
- The result should look like the room was actually painted, not digitally altered
"""

        return await self._generate_transformation(image, prompt, num_variations)
    
    async def transform_flooring(
        self,
        image: Union[str, Path, Image.Image, bytes],
        target_material: str,
        target_style: str,
        target_color: Optional[str] = None,
        preserve_rugs: bool = True,
        num_variations: int = 4
    ) -> List[Image.Image]:
        """
        Transform flooring while preserving everything else.

        Args:
            image: Original room image
            target_material: Flooring material (hardwood, tile, carpet, vinyl, laminate, etc.)
            target_style: Style details (e.g., "wide plank oak", "herringbone pattern", "12x24 porcelain")
            target_color: Optional color specification
            preserve_rugs: If True, keep area rugs unchanged
            num_variations: Number of variations to generate (1-4)

        Returns:
            List of transformed images with new flooring
        """
        color_spec = f"- Color: {target_color}" if target_color else ""
        
        prompt = f"""Transform this room image by changing ONLY the flooring.

TARGET CHANGE:
- Replace flooring with: {target_material}
- Style: {target_style}
{color_spec}
{'- Preserve all area rugs, runners, and floor coverings' if preserve_rugs else ''}

{self.CORE_PRESERVATION_RULES}

SPECIFIC PRESERVATION FOR FLOORING:
- Keep all walls, ceiling, and paint colors identical
- Preserve all furniture positions and styles exactly
- Maintain all fixtures, lighting, and hardware
- Keep all decor, artwork, and accessories unchanged
- Preserve baseboards and trim in original state
- Maintain all shadows and reflections naturally
- Keep any floor transitions or thresholds appropriate

FLOORING-SPECIFIC REQUIREMENTS:
- Ensure proper perspective and alignment with room geometry
- Match the flooring pattern/grain to the room's orientation
- Create realistic reflections and light interactions
- Show appropriate wear patterns for a lived-in space
- Maintain proper scale of flooring elements (plank width, tile size, etc.)
- Ensure grout lines (if applicable) are straight and properly aligned
- Show natural variation in material (wood grain, tile patterns, etc.)

OUTPUT REQUIREMENTS:
- Generate a photorealistic image that looks like professional flooring installation
- The new flooring should integrate seamlessly with existing baseboards
- Maintain realistic lighting and shadow interactions
- The result should look like actual installed flooring, not a digital overlay
"""

        return await self._generate_transformation(image, prompt, num_variations)
    
    async def transform_cabinets(
        self,
        image: Union[str, Path, Image.Image, bytes],
        target_color: str,
        target_finish: str = "painted",
        target_style: Optional[str] = None,
        preserve_hardware: bool = False,
        num_variations: int = 4
    ) -> List[Image.Image]:
        """
        Transform cabinet color/finish while preserving everything else.

        Args:
            image: Original room image
            target_color: Desired cabinet color
            target_finish: Finish type (painted, stained, natural wood, glazed)
            target_style: Optional style change (shaker, flat panel, raised panel)
            preserve_hardware: If True, keep existing hardware; if False, can update
            num_variations: Number of variations to generate (1-4)

        Returns:
            List of transformed images with updated cabinets
        """
        style_spec = f"- Cabinet style: {target_style}" if target_style else "- Keep existing cabinet door style"
        hardware_spec = "- Preserve all existing cabinet hardware (handles, knobs, hinges)" if preserve_hardware else "- Update hardware to complement new cabinet finish"
        
        prompt = f"""Transform this room image by changing ONLY the kitchen/bathroom cabinets.

TARGET CHANGE:
- Change cabinet color to: {target_color}
- Finish type: {target_finish}
{style_spec}
{hardware_spec}

{self.CORE_PRESERVATION_RULES}

SPECIFIC PRESERVATION FOR CABINETS:
- Keep all countertops, backsplash, and surfaces identical
- Preserve all appliances in original state
- Maintain all flooring materials and colors
- Keep all wall colors and finishes unchanged
- Preserve all lighting fixtures and their effects
- Maintain all sinks, faucets, and plumbing fixtures
- Keep all decor, accessories, and personal items
- Preserve the cabinet box structure and layout

CABINET-SPECIFIC REQUIREMENTS:
- Apply the new finish uniformly across all cabinet surfaces
- Maintain realistic wood grain (if applicable) or smooth painted surface
- Show appropriate sheen level for the finish type
- Create natural shadows in cabinet recesses and details
- Ensure consistent color across all cabinet doors and drawers
- Maintain proper light reflection based on finish type
- Show realistic aging or patina if appropriate

OUTPUT REQUIREMENTS:
- Generate a photorealistic image of professionally finished cabinets
- The new finish should look like expert craftsmanship
- Maintain realistic lighting interactions with cabinet surfaces
- The result should look like actual refinished cabinets, not a filter
"""

        return await self._generate_transformation(image, prompt, num_variations)
    
    async def _generate_transformation(
        self,
        image: Union[str, Path, Image.Image, bytes],
        prompt: str,
        num_variations: int = 4
    ) -> List[Image.Image]:
        """
        Generate transformation using Gemini Imagen.
        
        Args:
            image: Original image
            prompt: Detailed transformation prompt
            num_variations: Number of variations to generate (1-4)
        
        Returns:
            List of transformed images
        """
        try:
            # Edit original image using Gemini native image editing (gemini-2.5-flash-image)
            # Official docs: https://ai.google.dev/gemini-api/docs/image-generation
            generated_images = await self.gemini.edit_image(
                prompt=prompt,
                reference_image=image,
                num_images=num_variations
            )

            logger.info(f"Generated {len(generated_images)} transformation variations")
            return generated_images
            
        except Exception as e:
            logger.error(f"Error generating transformation: {str(e)}", exc_info=True)
            raise
    
    def _load_image(self, image: Union[str, Path, Image.Image, bytes]) -> Image.Image:
        """Load image from various formats."""
        if isinstance(image, Image.Image):
            return image
        elif isinstance(image, (str, Path)):
            return Image.open(image)
        elif isinstance(image, bytes):
            return Image.open(io.BytesIO(image))
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    async def transform_countertops(
        self,
        image: Union[str, Path, Image.Image, bytes],
        target_material: str,
        target_color: str,
        target_pattern: Optional[str] = None,
        edge_profile: str = "standard",
        num_variations: int = 4
    ) -> List[Image.Image]:
        """
        Transform countertops while preserving everything else.

        Args:
            image: Original room image
            target_material: Material type (granite, quartz, marble, butcher block, laminate, concrete)
            target_color: Color specification
            target_pattern: Optional pattern (veined, speckled, solid, etc.)
            edge_profile: Edge style (standard, beveled, bullnose, waterfall)
            num_variations: Number of variations to generate (1-4)

        Returns:
            List of transformed images
        """
        pattern_spec = f"- Pattern: {target_pattern}" if target_pattern else ""

        prompt = f"""Transform this room image by changing ONLY the countertops.

TARGET CHANGE:
- Replace countertops with: {target_material}
- Color: {target_color}
{pattern_spec}
- Edge profile: {edge_profile}

{self.CORE_PRESERVATION_RULES}

SPECIFIC PRESERVATION FOR COUNTERTOPS:
- Keep all cabinets, colors, and finishes identical
- Preserve all backsplash materials and patterns
- Maintain all appliances in original state
- Keep all sinks, faucets, and fixtures unchanged
- Preserve all flooring and wall colors
- Maintain all lighting and its effects
- Keep all decor and accessories in place

COUNTERTOP-SPECIFIC REQUIREMENTS:
- Show realistic material texture and depth
- Create natural veining or patterns (if applicable)
- Display appropriate sheen/finish for the material
- Show realistic edge profile details
- Maintain proper thickness for the material type
- Create natural light reflections and shadows
- Show realistic seams if countertop is large
- Display appropriate wear patterns for the material

OUTPUT REQUIREMENTS:
- Generate photorealistic countertops that look professionally installed
- Material should have authentic texture and appearance
- Lighting should interact naturally with the surface
- Result should look like actual stone/material, not a photograph overlay
"""

        return await self._generate_transformation(image, prompt, num_variations)

    async def transform_backsplash(
        self,
        image: Union[str, Path, Image.Image, bytes],
        target_material: str,
        target_pattern: str,
        target_color: str,
        grout_color: Optional[str] = None,
        num_variations: int = 4
    ) -> List[Image.Image]:
        """
        Transform backsplash while preserving everything else.

        Args:
            image: Original room image
            target_material: Material (ceramic tile, glass tile, subway tile, mosaic, stone, etc.)
            target_pattern: Pattern/layout (subway, herringbone, stacked, mosaic, etc.)
            target_color: Tile color
            grout_color: Optional grout color specification
            num_variations: Number of variations to generate (1-4)

        Returns:
            List of transformed images
        """
        grout_spec = f"- Grout color: {grout_color}" if grout_color else "- Grout color: complementary to tile"

        prompt = f"""Transform this room image by changing ONLY the backsplash.

TARGET CHANGE:
- Replace backsplash with: {target_material}
- Pattern/Layout: {target_pattern}
- Tile color: {target_color}
{grout_spec}

{self.CORE_PRESERVATION_RULES}

SPECIFIC PRESERVATION FOR BACKSPLASH:
- Keep all cabinets and their colors identical
- Preserve all countertops and their materials
- Maintain all appliances in original state
- Keep all outlets, switches, and electrical unchanged
- Preserve all wall colors outside backsplash area
- Maintain all lighting fixtures and effects
- Keep all windows and their treatments unchanged

BACKSPLASH-SPECIFIC REQUIREMENTS:
- Show precise tile pattern alignment and layout
- Display realistic grout lines with proper spacing
- Create appropriate tile texture and finish
- Show natural light reflections on tile surface
- Maintain proper scale of tiles relative to room
- Display realistic tile edges and corners
- Show appropriate sheen for the material type
- Ensure pattern alignment around outlets and edges

OUTPUT REQUIREMENTS:
- Generate photorealistic backsplash that looks professionally installed
- Tile pattern should be geometrically accurate
- Grout lines should be straight and consistent
- Result should look like actual tile installation
"""

        return await self._generate_transformation(image, prompt, num_variations)

    async def transform_lighting(
        self,
        image: Union[str, Path, Image.Image, bytes],
        target_fixture_style: str,
        target_finish: str,
        adjust_ambiance: Optional[str] = None,
        num_variations: int = 4
    ) -> List[Image.Image]:
        """
        Transform lighting fixtures while preserving everything else.

        Args:
            image: Original room image
            target_fixture_style: Fixture style (modern, traditional, industrial, farmhouse, etc.)
            target_finish: Finish (brushed nickel, oil-rubbed bronze, chrome, brass, black, etc.)
            adjust_ambiance: Optional ambiance adjustment (warmer, cooler, brighter, dimmer)
            num_variations: Number of variations to generate (1-4)

        Returns:
            List of transformed images
        """
        ambiance_spec = f"- Adjust lighting ambiance: {adjust_ambiance}" if adjust_ambiance else ""

        prompt = f"""Transform this room image by changing ONLY the lighting fixtures.

TARGET CHANGE:
- Replace light fixtures with: {target_fixture_style} style
- Fixture finish: {target_finish}
{ambiance_spec}

{self.CORE_PRESERVATION_RULES}

SPECIFIC PRESERVATION FOR LIGHTING:
- Keep all walls, floors, and ceilings in original colors
- Preserve all furniture and its arrangement
- Maintain all cabinets, countertops, and surfaces
- Keep all decor and accessories unchanged
- Preserve all architectural features
- Maintain room layout and spatial arrangement

LIGHTING-SPECIFIC REQUIREMENTS:
- Replace fixtures with appropriate style and scale
- Show realistic fixture materials and finishes
- Maintain proper fixture placement and mounting
- Create natural shadows from new fixtures
- Adjust light quality if ambiance change requested
- Show realistic light distribution patterns
- Display appropriate fixture details (shades, bulbs, etc.)
- Ensure fixtures are proportional to room size

OUTPUT REQUIREMENTS:
- Generate photorealistic lighting that looks professionally installed
- Fixtures should cast natural shadows and highlights
- Light quality should appear authentic
- Result should look like actual installed fixtures
"""

        return await self._generate_transformation(image, prompt, num_variations)

    async def transform_furniture(
        self,
        image: Union[str, Path, Image.Image, bytes],
        action: str,
        furniture_description: str,
        placement: Optional[str] = None,
        num_variations: int = 4
    ) -> List[Image.Image]:
        """
        Add, remove, or replace furniture while preserving everything else.

        Args:
            image: Original room image
            action: Action to perform (add, remove, replace)
            furniture_description: Description of furniture item
            placement: Optional placement description
            num_variations: Number of variations to generate (1-4)

        Returns:
            List of transformed images
        """
        placement_spec = f"- Placement: {placement}" if placement else ""

        if action == "add":
            change_desc = f"Add {furniture_description} to the room"
        elif action == "remove":
            change_desc = f"Remove {furniture_description} from the room"
        elif action == "replace":
            change_desc = f"Replace existing furniture with {furniture_description}"
        else:
            raise ValueError(f"Invalid action: {action}. Must be 'add', 'remove', or 'replace'")

        prompt = f"""Transform this room image by {action}ing furniture ONLY.

TARGET CHANGE:
- {change_desc}
{placement_spec}

{self.CORE_PRESERVATION_RULES}

SPECIFIC PRESERVATION FOR FURNITURE:
- Keep all walls, floors, and ceilings identical
- Preserve all built-in features (cabinets, shelves, etc.)
- Maintain all lighting fixtures and effects
- Keep all decor and accessories (unless on removed furniture)
- Preserve all architectural details
- Maintain all other furniture pieces unchanged

FURNITURE-SPECIFIC REQUIREMENTS:
- Ensure furniture scale is appropriate for room size
- Show realistic furniture materials and textures
- Create natural shadows beneath and around furniture
- Maintain proper perspective and spatial relationships
- Show realistic wear and lived-in appearance
- Ensure furniture style complements the room
- Display appropriate details (cushions, legs, hardware)
- If removing furniture, fill space naturally (show floor/wall behind)

OUTPUT REQUIREMENTS:
- Generate photorealistic furniture that looks real
- Furniture should integrate seamlessly into the space
- Shadows and lighting should be natural
- Result should look like actual furniture placement
"""

        return await self._generate_transformation(image, prompt, num_variations)

