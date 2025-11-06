"""
Design Studio Agent for HomeView AI.

Orchestrates design transformations, style transfers, and design variations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.agents.base.agent import BaseAgent, AgentConfig, AgentRole, AgentResponse
from backend.services.imagen_service import ImagenService, DesignTransformationRequest
from backend.workflows.design_transformation_workflow import DesignTransformationWorkflow
from backend.integrations.gemini.client import GeminiClient

logger = logging.getLogger(__name__)


class DesignStudioAgent(BaseAgent):
    """
    Agent for orchestrating design studio operations.
    
    Capabilities:
    - Style transfer (change room style)
    - Room redesign (change specific elements)
    - Color palette changes
    - Furniture swapping
    - Design variation generation
    - Before/after comparisons
    """
    
    def __init__(
        self,
        imagen_service: Optional[ImagenService] = None,
        gemini_client: Optional[GeminiClient] = None
    ):
        """Initialize design studio agent."""
        config = AgentConfig(
            name="DesignStudioAgent",
            role=AgentRole.SPECIALIST,
            description="Orchestrates design transformations and style transfers using AI image generation",
            temperature=0.7,
            max_tokens=2000
        )
        super().__init__(config)
        
        self.imagen_service = imagen_service or ImagenService()
        self.gemini_client = gemini_client or GeminiClient()
        self.workflow = DesignTransformationWorkflow(
            imagen_service=self.imagen_service,
            gemini_client=self.gemini_client
        )
        
        logger.info("Design Studio Agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process design studio request.
        
        Args:
            input_data: {
                "action": str,  # transform, generate_variations, compare
                "home_id": str,
                "room_id": Optional[str],
                "image_path": str,
                "transformation_type": Optional[str],
                "transformation_params": Optional[Dict],
                "num_variations": Optional[int],
                "styles": Optional[List[str]]
            }
            
        Returns:
            AgentResponse with transformation results
        """
        action = input_data.get("action", "transform")
        
        try:
            if action == "transform":
                return await self._handle_transformation(input_data)
            elif action == "generate_variations":
                return await self._handle_variations(input_data)
            elif action == "compare":
                return await self._handle_comparison(input_data)
            elif action == "suggest_styles":
                return await self._suggest_styles(input_data)
            else:
                return AgentResponse(
                    agent_name=self.config.name,
                    agent_role=self.config.role.value,
                    success=False,
                    data={},
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Error processing design studio request: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role.value,
                success=False,
                data={},
                error=str(e)
            )
    
    async def _handle_transformation(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Handle design transformation request."""
        logger.info("Handling design transformation")
        
        try:
            result = await self.workflow.execute(
                home_id=input_data["home_id"],
                original_image_path=input_data["image_path"],
                transformation_type=input_data.get("transformation_type", "style_transfer"),
                transformation_params=input_data.get("transformation_params", {}),
                num_variations=input_data.get("num_variations", 1),
                room_id=input_data.get("room_id")
            )
            
            if result.get("errors"):
                return AgentResponse(
                    agent_name=self.config.name,
                    agent_role=self.config.role.value,
                    success=False,
                    data=result,
                    error="; ".join(result["errors"])
                )
            
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role.value,
                success=True,
                data={
                    "workflow_id": result.get("workflow_id"),
                    "generated_images": result.get("generated_images", []),
                    "image_paths": result.get("image_paths", []),
                    "comparison_path": result.get("comparison_path"),
                    "transformation_type": result.get("transformation_type"),
                    "metadata": result.get("execution_metadata", {})
                },
                metadata={
                    "transformation_type": result.get("transformation_type"),
                    "num_variations": len(result.get("generated_images", []))
                }
            )
            
        except Exception as e:
            logger.error(f"Transformation failed: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role.value,
                success=False,
                data={},
                error=str(e)
            )
    
    async def _handle_variations(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Handle design variation generation."""
        logger.info("Generating design variations")
        
        try:
            styles = input_data.get("styles", ["modern", "traditional", "minimalist"])
            num_per_style = input_data.get("num_variations", 1)
            
            results = await self.imagen_service.generate_design_variations(
                original_image_path=input_data["image_path"],
                variation_styles=styles,
                num_variations_per_style=num_per_style
            )
            
            # Compile results
            all_images = []
            all_paths = []
            style_results = {}
            
            for style, result in results.items():
                if result.success:
                    all_images.extend(result.images)
                    all_paths.extend(result.image_paths)
                    style_results[style] = {
                        "images": result.images,
                        "paths": result.image_paths,
                        "metadata": result.metadata
                    }
            
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role.value,
                success=True,
                data={
                    "all_images": all_images,
                    "all_paths": all_paths,
                    "by_style": style_results,
                    "total_variations": len(all_images)
                },
                metadata={
                    "styles": styles,
                    "num_per_style": num_per_style
                }
            )
            
        except Exception as e:
            logger.error(f"Variation generation failed: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role.value,
                success=False,
                data={},
                error=str(e)
            )
    
    async def _handle_comparison(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Handle before/after comparison creation."""
        logger.info("Creating before/after comparison")
        
        try:
            comparison_path = await self.imagen_service.create_before_after_comparison(
                before_image_path=input_data["before_image"],
                after_image_path=input_data["after_image"]
            )
            
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role.value,
                success=True,
                data={
                    "comparison_path": comparison_path,
                    "before_image": input_data["before_image"],
                    "after_image": input_data["after_image"]
                }
            )
            
        except Exception as e:
            logger.error(f"Comparison creation failed: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role.value,
                success=False,
                data={},
                error=str(e)
            )
    
    async def _suggest_styles(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Suggest design styles based on current room."""
        logger.info("Suggesting design styles")
        
        try:
            # Analyze current image
            analysis_prompt = """Analyze this interior design image and suggest 5 design styles that would work well for this space.
For each style, explain why it would be a good fit.

Consider:
- Current room layout and size
- Natural lighting
- Existing architectural features
- Room function

Provide suggestions in this format:
1. [Style Name]: [Brief explanation]
2. [Style Name]: [Brief explanation]
etc."""
            
            suggestions = await self.gemini_client.generate_content(
                prompt=analysis_prompt,
                image_path=input_data["image_path"]
            )
            
            # Parse suggestions (simple parsing)
            style_list = []
            for line in suggestions.split('\n'):
                if line.strip() and line[0].isdigit():
                    style_list.append(line.strip())
            
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role.value,
                success=True,
                data={
                    "suggestions": suggestions,
                    "style_list": style_list,
                    "image_analyzed": input_data["image_path"]
                },
                metadata={
                    "num_suggestions": len(style_list)
                }
            )
            
        except Exception as e:
            logger.error(f"Style suggestion failed: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role.value,
                success=False,
                data={},
                error=str(e)
            )

