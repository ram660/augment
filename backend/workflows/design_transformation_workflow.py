"""
Design Transformation Workflow for HomeView AI.

LangGraph workflow for orchestrating design transformations using Gemini Imagen.
Handles style transfer, room redesign, and design variations.
"""

import logging
from typing import TypedDict, List, Optional, Dict, Any, Annotated
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.workflows.base import WorkflowOrchestrator
from backend.services.imagen_service import (
    ImagenService,
    ImageGenerationRequest,
    DesignTransformationRequest,
    ImageGenerationResult
)
from backend.integrations.gemini.client import GeminiClient

logger = logging.getLogger(__name__)


class DesignTransformationState(TypedDict, total=False):
    """State for design transformation workflow."""
    # Input
    workflow_id: str
    home_id: str
    room_id: Optional[str]
    original_image_path: str
    transformation_type: str  # style_transfer, room_redesign, color_change, furniture_swap
    transformation_params: Dict[str, Any]
    num_variations: int
    user_preferences: Dict[str, Any]
    
    # Processing
    validated_image: bool
    image_metadata: Dict[str, Any]
    transformation_prompt: str
    generated_images: List[str]
    image_paths: List[str]
    comparison_path: Optional[str]
    
    # Output
    transformation_result: Optional[ImageGenerationResult]
    selected_variation: Optional[int]
    user_feedback: Optional[str]
    
    # Workflow management
    current_node: str
    errors: Annotated[List[str], operator.add]
    execution_metadata: Dict[str, Any]


class DesignTransformationWorkflow:
    """
    LangGraph workflow for design transformations.
    
    Workflow Steps:
    1. Validate image
    2. Analyze original design
    3. Build transformation prompt
    4. Generate transformed images
    5. Create before/after comparison
    6. Collect user feedback
    7. Finalize transformation
    """
    
    def __init__(
        self,
        imagen_service: Optional[ImagenService] = None,
        gemini_client: Optional[GeminiClient] = None
    ):
        """Initialize workflow."""
        self.imagen_service = imagen_service or ImagenService()
        self.gemini_client = gemini_client or GeminiClient()
        self.checkpointer = MemorySaver()
        
        # Build workflow graph
        self.graph = self._build_graph()
        self.app = self.graph.compile(checkpointer=self.checkpointer)
        
        logger.info("Design transformation workflow initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the workflow graph."""
        workflow = StateGraph(DesignTransformationState)
        
        # Add nodes
        workflow.add_node("validate_image", self._validate_image)
        workflow.add_node("analyze_design", self._analyze_design)
        workflow.add_node("build_prompt", self._build_transformation_prompt)
        workflow.add_node("generate_images", self._generate_transformed_images)
        workflow.add_node("create_comparison", self._create_before_after_comparison)
        workflow.add_node("finalize", self._finalize_transformation)
        
        # Add edges
        workflow.set_entry_point("validate_image")
        workflow.add_edge("validate_image", "analyze_design")
        workflow.add_edge("analyze_design", "build_prompt")
        workflow.add_edge("build_prompt", "generate_images")
        workflow.add_edge("generate_images", "create_comparison")
        workflow.add_edge("create_comparison", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow
    
    async def _validate_image(self, state: DesignTransformationState) -> DesignTransformationState:
        """Validate the input image."""
        logger.info(f"Validating image: {state.get('original_image_path')}")
        
        try:
            from PIL import Image
            import os
            
            image_path = state.get("original_image_path")
            
            # Check file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            # Load and validate image
            img = Image.open(image_path)
            
            # Get metadata
            metadata = {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "size_bytes": os.path.getsize(image_path)
            }
            
            logger.info(f"Image validated: {metadata}")
            
            return {
                **state,
                "validated_image": True,
                "image_metadata": metadata,
                "current_node": "validate_image"
            }
            
        except Exception as e:
            logger.error(f"Image validation failed: {str(e)}")
            return {
                **state,
                "validated_image": False,
                "errors": [f"Image validation failed: {str(e)}"],
                "current_node": "validate_image"
            }
    
    async def _analyze_design(self, state: DesignTransformationState) -> DesignTransformationState:
        """Analyze the original design using Gemini Vision."""
        logger.info("Analyzing original design")
        
        try:
            # Use Gemini Vision to analyze the image
            analysis_prompt = """Analyze this interior design image and provide:
1. Room type (kitchen, bedroom, living room, etc.)
2. Current style (modern, traditional, minimalist, etc.)
3. Key design elements (furniture, colors, materials)
4. Lighting conditions
5. Overall aesthetic

Be concise and specific."""
            
            analysis = await self.gemini_client.generate_content(
                prompt=analysis_prompt,
                image_path=state.get("original_image_path")
            )
            
            logger.info(f"Design analysis complete: {analysis[:200]}...")
            
            return {
                **state,
                "image_metadata": {
                    **state.get("image_metadata", {}),
                    "design_analysis": analysis
                },
                "current_node": "analyze_design"
            }
            
        except Exception as e:
            logger.error(f"Design analysis failed: {str(e)}")
            return {
                **state,
                "errors": [f"Design analysis failed: {str(e)}"],
                "current_node": "analyze_design"
            }
    
    async def _build_transformation_prompt(self, state: DesignTransformationState) -> DesignTransformationState:
        """Build the transformation prompt based on type and parameters."""
        logger.info(f"Building transformation prompt for: {state.get('transformation_type')}")
        
        try:
            transformation_type = state.get("transformation_type")
            params = state.get("transformation_params", {})
            
            # The prompt building is handled by ImagenService
            # We just prepare the request here
            
            return {
                **state,
                "transformation_prompt": f"Transformation: {transformation_type} with params: {params}",
                "current_node": "build_prompt"
            }
            
        except Exception as e:
            logger.error(f"Prompt building failed: {str(e)}")
            return {
                **state,
                "errors": [f"Prompt building failed: {str(e)}"],
                "current_node": "build_prompt"
            }
    
    async def _generate_transformed_images(self, state: DesignTransformationState) -> DesignTransformationState:
        """Generate transformed images using Imagen."""
        logger.info("Generating transformed images")
        
        try:
            request = DesignTransformationRequest(
                original_image_path=state.get("original_image_path"),
                transformation_type=state.get("transformation_type"),
                transformation_params=state.get("transformation_params", {}),
                num_variations=state.get("num_variations", 1)
            )
            
            result = await self.imagen_service.transform_design(request)
            
            if not result.success:
                raise Exception(result.error)
            
            logger.info(f"Generated {len(result.images)} transformed images")
            
            return {
                **state,
                "transformation_result": result,
                "generated_images": result.images,
                "image_paths": result.image_paths,
                "current_node": "generate_images",
                "execution_metadata": {
                    **state.get("execution_metadata", {}),
                    "generation_time_ms": result.generation_time_ms,
                    "num_images_generated": len(result.images)
                }
            }
            
        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            return {
                **state,
                "errors": [f"Image generation failed: {str(e)}"],
                "current_node": "generate_images"
            }
    
    async def _create_before_after_comparison(self, state: DesignTransformationState) -> DesignTransformationState:
        """Create before/after comparison image."""
        logger.info("Creating before/after comparison")
        
        try:
            # Use first generated image for comparison
            if not state.get("image_paths"):
                logger.warning("No generated images to compare")
                return {
                    **state,
                    "current_node": "create_comparison"
                }
            
            comparison_path = await self.imagen_service.create_before_after_comparison(
                before_image_path=state.get("original_image_path"),
                after_image_path=state.get("image_paths")[0]
            )
            
            logger.info(f"Comparison created: {comparison_path}")
            
            return {
                **state,
                "comparison_path": comparison_path,
                "current_node": "create_comparison"
            }
            
        except Exception as e:
            logger.error(f"Comparison creation failed: {str(e)}")
            return {
                **state,
                "errors": [f"Comparison creation failed: {str(e)}"],
                "current_node": "create_comparison"
            }
    
    async def _finalize_transformation(self, state: DesignTransformationState) -> DesignTransformationState:
        """Finalize the transformation."""
        logger.info("Finalizing transformation")
        
        return {
            **state,
            "current_node": "finalize",
            "execution_metadata": {
                **state.get("execution_metadata", {}),
                "completed_at": datetime.now().isoformat(),
                "total_errors": len(state.get("errors", []))
            }
        }
    
    async def execute(
        self,
        home_id: str,
        original_image_path: str,
        transformation_type: str,
        transformation_params: Dict[str, Any],
        num_variations: int = 1,
        room_id: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> DesignTransformationState:
        """
        Execute the design transformation workflow.
        
        Args:
            home_id: Home ID
            original_image_path: Path to original image
            transformation_type: Type of transformation
            transformation_params: Transformation parameters
            num_variations: Number of variations to generate
            room_id: Optional room ID
            user_preferences: Optional user preferences
            
        Returns:
            Final workflow state
        """
        import uuid
        
        workflow_id = str(uuid.uuid4())
        
        initial_state: DesignTransformationState = {
            "workflow_id": workflow_id,
            "home_id": home_id,
            "room_id": room_id,
            "original_image_path": original_image_path,
            "transformation_type": transformation_type,
            "transformation_params": transformation_params,
            "num_variations": num_variations,
            "user_preferences": user_preferences or {},
            "errors": [],
            "execution_metadata": {
                "started_at": datetime.now().isoformat()
            }
        }
        
        logger.info(f"Executing design transformation workflow: {workflow_id}")
        
        config = {"configurable": {"thread_id": workflow_id}}
        final_state = await self.app.ainvoke(initial_state, config)
        
        logger.info(f"Workflow completed: {workflow_id}")
        
        return final_state

