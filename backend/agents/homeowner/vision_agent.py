"""
Vision Analysis Agent - Image understanding and analysis for HomeVision AI.

This agent uses Gemini Vision to:
- Extract room dimensions from photos
- Identify products and materials
- Classify room style and features
- Calculate quality metrics
- Detect issues and opportunities
"""

import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from enum import Enum

from PIL import Image
import json

from backend.agents.base import BaseAgent, AgentConfig, AgentRole, AgentResponse
from backend.integrations.gemini import GeminiClient

logger = logging.getLogger(__name__)


class AnalysisType(str, Enum):
    """Types of vision analysis."""
    DIMENSIONS = "dimensions"
    STYLE_CLASSIFICATION = "style_classification"
    PRODUCT_IDENTIFICATION = "product_identification"
    QUALITY_ASSESSMENT = "quality_assessment"
    COMPREHENSIVE = "comprehensive"


class VisionAnalysisAgent(BaseAgent):
    """
    Vision Analysis Agent for image understanding.
    
    Capabilities:
    - Room dimension extraction
    - Style and aesthetic classification
    - Product and material identification
    - Quality and condition assessment
    - Feature detection
    """
    
    DIMENSION_PROMPT = """Analyze this room image and extract dimensional information.

Provide your analysis in JSON format with the following structure:
{
    "room_type": "kitchen|bathroom|bedroom|living_room|dining_room|other",
    "estimated_dimensions": {
        "length_feet": <number>,
        "width_feet": <number>,
        "height_feet": <number>,
        "confidence": "high|medium|low"
    },
    "spatial_features": {
        "ceiling_type": "flat|vaulted|coffered|other",
        "window_count": <number>,
        "door_count": <number>,
        "notable_features": ["feature1", "feature2"]
    },
    "measurement_notes": "Any important notes about measurements or spatial constraints"
}

Be as accurate as possible. If you cannot determine exact dimensions, provide reasonable estimates based on visible reference objects (doors, windows, appliances, etc.)."""

    STYLE_PROMPT = """Analyze the style and aesthetic of this room.

Provide your analysis in JSON format:
{
    "primary_style": "modern|traditional|farmhouse|industrial|coastal|transitional|contemporary|rustic|other",
    "style_confidence": "high|medium|low",
    "style_elements": ["element1", "element2"],
    "color_palette": {
        "dominant_colors": ["color1", "color2"],
        "accent_colors": ["color1", "color2"],
        "overall_tone": "warm|cool|neutral"
    },
    "materials_visible": {
        "flooring": "hardwood|tile|carpet|laminate|other",
        "walls": "paint|wallpaper|tile|wood|other",
        "cabinetry": "wood|painted|laminate|none",
        "countertops": "granite|quartz|marble|laminate|wood|none"
    },
    "design_quality": "high-end|mid-range|budget|mixed",
    "condition": "excellent|good|fair|needs_work"
}"""

    PRODUCT_IDENTIFICATION_PROMPT = """Identify all visible products, fixtures, and materials in this room.

Provide your analysis in JSON format:
{
    "products": [
        {
            "category": "appliance|fixture|furniture|lighting|hardware",
            "item": "specific item name",
            "brand_if_visible": "brand name or unknown",
            "approximate_size": "dimensions if determinable",
            "condition": "new|good|worn|needs_replacement",
            "location": "where in the room"
        }
    ],
    "materials": [
        {
            "type": "flooring|countertop|backsplash|cabinetry|wall_finish",
            "material": "specific material",
            "color_finish": "description",
            "condition": "excellent|good|fair|poor"
        }
    ],
    "notable_features": ["feature1", "feature2"]
}

Be thorough and identify as many items as possible."""

    COMPREHENSIVE_PROMPT = """Provide a comprehensive analysis of this room image.

Include:
1. Room type and purpose
2. Estimated dimensions (length, width, height in feet)
3. Style and aesthetic classification
4. All visible products and materials
5. Condition assessment
6. Improvement opportunities
7. Estimated age/era of the space

Provide detailed JSON output with all relevant information."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize Vision Analysis Agent.
        
        Args:
            gemini_client: Optional Gemini client
        """
        config = AgentConfig(
            name="vision_analysis_agent",
            role=AgentRole.VISION,
            description="Image analysis and understanding using Gemini Vision",
            model_name="gemini-2.0-flash",  # Use gemini-2.0-flash for vision analysis
            temperature=0.3,  # Lower temperature for factual analysis
            enable_memory=False  # Vision analysis is stateless
        )
        super().__init__(config)
        
        self.gemini = gemini_client or GeminiClient()
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process image and return analysis.
        
        Args:
            input_data: {
                "image": str | Path | Image.Image | bytes,  # Image to analyze
                "analysis_type": str,  # Type of analysis (optional, defaults to comprehensive)
                "additional_context": Optional[str],  # Additional context for analysis
            }
            
        Returns:
            AgentResponse with analysis results
        """
        try:
            image = input_data.get("image")
            if not image:
                return AgentResponse(
                    agent_name=self.name,
                    agent_role=self.role,
                    success=False,
                    error="No image provided"
                )
            
            analysis_type = input_data.get("analysis_type", AnalysisType.COMPREHENSIVE)
            if isinstance(analysis_type, str):
                try:
                    analysis_type = AnalysisType(analysis_type)
                except ValueError:
                    analysis_type = AnalysisType.COMPREHENSIVE
            
            additional_context = input_data.get("additional_context", "")
            
            # Select appropriate prompt
            prompt = self._get_prompt(analysis_type, additional_context)
            
            # Analyze image
            analysis_text = await self.gemini.analyze_image(
                image=image,
                prompt=prompt,
                temperature=0.3
            )
            
            # Parse JSON response
            analysis_data = self._parse_analysis(analysis_text)
            
            return AgentResponse(
                agent_name=self.name,
                agent_role=self.role,
                success=True,
                data={
                    "analysis_type": analysis_type.value,
                    "analysis": analysis_data,
                    "raw_response": analysis_text
                },
                metadata={
                    "model": self.config.model_name
                }
            )
            
        except Exception as e:
            logger.error(f"Error in vision analysis: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.name,
                agent_role=self.role,
                success=False,
                error=str(e)
            )
    
    def _get_prompt(self, analysis_type: AnalysisType, additional_context: str) -> str:
        """
        Get the appropriate prompt for the analysis type.
        
        Args:
            analysis_type: Type of analysis to perform
            additional_context: Additional context to include
            
        Returns:
            Prompt string
        """
        prompt_map = {
            AnalysisType.DIMENSIONS: self.DIMENSION_PROMPT,
            AnalysisType.STYLE_CLASSIFICATION: self.STYLE_PROMPT,
            AnalysisType.PRODUCT_IDENTIFICATION: self.PRODUCT_IDENTIFICATION_PROMPT,
            AnalysisType.COMPREHENSIVE: self.COMPREHENSIVE_PROMPT,
        }
        
        base_prompt = prompt_map.get(analysis_type, self.COMPREHENSIVE_PROMPT)
        
        if additional_context:
            base_prompt += f"\n\nAdditional context: {additional_context}"
        
        return base_prompt
    
    def _parse_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """
        Parse JSON from analysis response.
        
        Args:
            analysis_text: Raw analysis text from Gemini
            
        Returns:
            Parsed analysis data
        """
        try:
            # Try to find JSON in the response
            # Gemini might wrap JSON in markdown code blocks
            if "```json" in analysis_text:
                # Extract JSON from code block
                start = analysis_text.find("```json") + 7
                end = analysis_text.find("```", start)
                json_str = analysis_text[start:end].strip()
            elif "```" in analysis_text:
                # Generic code block
                start = analysis_text.find("```") + 3
                end = analysis_text.find("```", start)
                json_str = analysis_text[start:end].strip()
            else:
                # Assume entire response is JSON
                json_str = analysis_text.strip()
            
            # Parse JSON
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from analysis: {str(e)}")
            # Return raw text if JSON parsing fails
            return {
                "raw_analysis": analysis_text,
                "parse_error": str(e)
            }
    
    async def analyze_multiple_images(
        self,
        images: List[Union[str, Path, Image.Image, bytes]],
        analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE
    ) -> List[AgentResponse]:
        """
        Analyze multiple images.
        
        Args:
            images: List of images to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            List of analysis responses
        """
        results = []
        for i, image in enumerate(images):
            logger.info(f"Analyzing image {i+1}/{len(images)}")
            result = await self.execute({
                "image": image,
                "analysis_type": analysis_type
            })
            results.append(result)
        
        return results
    
    async def compare_images(
        self,
        image1: Union[str, Path, Image.Image, bytes],
        image2: Union[str, Path, Image.Image, bytes],
        comparison_focus: str = "overall changes"
    ) -> AgentResponse:
        """
        Compare two images (e.g., before/after).
        
        Args:
            image1: First image
            image2: Second image
            comparison_focus: What to focus on in comparison
            
        Returns:
            Comparison analysis
        """
        # Note: This would require a different approach with Gemini
        # For now, analyze both separately and compare results
        
        result1 = await self.execute({
            "image": image1,
            "analysis_type": AnalysisType.COMPREHENSIVE
        })
        
        result2 = await self.execute({
            "image": image2,
            "analysis_type": AnalysisType.COMPREHENSIVE
        })
        
        if not (result1.success and result2.success):
            return AgentResponse(
                agent_name=self.name,
                agent_role=self.role,
                success=False,
                error="Failed to analyze one or both images"
            )
        
        # Create comparison
        comparison = {
            "image1_analysis": result1.data["analysis"],
            "image2_analysis": result2.data["analysis"],
            "comparison_focus": comparison_focus,
            "differences_detected": self._detect_differences(
                result1.data["analysis"],
                result2.data["analysis"]
            )
        }
        
        return AgentResponse(
            agent_name=self.name,
            agent_role=self.role,
            success=True,
            data=comparison
        )
    
    def _detect_differences(self, analysis1: Dict, analysis2: Dict) -> List[str]:
        """
        Detect differences between two analyses.
        
        Args:
            analysis1: First analysis
            analysis2: Second analysis
            
        Returns:
            List of detected differences
        """
        differences = []
        
        # Simple comparison logic
        # This could be made much more sophisticated
        
        if analysis1.get("room_type") != analysis2.get("room_type"):
            differences.append(f"Room type changed: {analysis1.get('room_type')} → {analysis2.get('room_type')}")
        
        if analysis1.get("primary_style") != analysis2.get("primary_style"):
            differences.append(f"Style changed: {analysis1.get('primary_style')} → {analysis2.get('primary_style')}")
        
        # Add more comparison logic as needed
        
        return differences

