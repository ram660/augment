"""Digital Twin Creation Workflow using LangGraph."""

import logging
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.workflows.base import (
    BaseWorkflowState,
    WorkflowOrchestrator,
    WorkflowStatus,
    WorkflowError
)
from backend.agents.digital_twin import FloorPlanAnalysisAgent, RoomAnalysisAgent
from backend.models import Home, Room, FloorPlan, RoomImage, Material, Fixture, Product
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DigitalTwinState(BaseWorkflowState, total=False):
    """State for Digital Twin creation workflow."""
    
    # Input data
    home_id: str
    floor_plan_url: str
    room_images: List[Dict[str, str]]  # [{"url": str, "room_hint": Optional[str]}]
    
    # Analysis results
    floor_plan_analysis: Optional[Dict[str, Any]]
    detected_rooms: List[Dict[str, Any]]
    room_analyses: List[Dict[str, Any]]
    
    # Database IDs
    floor_plan_ids: List[str]
    room_ids: List[str]
    material_ids: List[str]
    fixture_ids: List[str]
    product_ids: List[str]
    
    # Metrics
    completeness_score: float
    confidence_score: float
    rooms_created: int
    images_analyzed: int


class DigitalTwinWorkflow:
    """
    Production-ready workflow for creating digital twins from floor plans and room images.
    
    Workflow Steps:
    1. Validate inputs
    2. Analyze floor plan (detect rooms, dimensions, layout)
    3. Create room records in database
    4. Analyze room images (materials, fixtures, products)
    5. Extract and persist entities (materials, fixtures, products)
    6. Calculate completeness score
    7. Return results
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.orchestrator = WorkflowOrchestrator(
            workflow_name="digital_twin_creation",
            max_retries=3,
            timeout_seconds=300
        )
        
        # Initialize agents
        self.floor_plan_agent = FloorPlanAnalysisAgent()
        self.room_analysis_agent = RoomAnalysisAgent()
        
        # Build the workflow graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(DigitalTwinState)
        
        # Add nodes
        workflow.add_node("validate_inputs", self._validate_inputs)
        workflow.add_node("analyze_floor_plan", self._analyze_floor_plan)
        workflow.add_node("create_rooms", self._create_rooms)
        workflow.add_node("analyze_room_images", self._analyze_room_images)
        workflow.add_node("extract_entities", self._extract_entities)
        workflow.add_node("calculate_completeness", self._calculate_completeness)
        workflow.add_node("finalize", self._finalize)
        
        # Add edges
        workflow.set_entry_point("validate_inputs")
        workflow.add_edge("validate_inputs", "analyze_floor_plan")
        workflow.add_edge("analyze_floor_plan", "create_rooms")
        workflow.add_edge("create_rooms", "analyze_room_images")
        workflow.add_edge("analyze_room_images", "extract_entities")
        workflow.add_edge("extract_entities", "calculate_completeness")
        workflow.add_edge("calculate_completeness", "finalize")
        workflow.add_edge("finalize", END)
        
        # Compile with checkpointing for resilience
        return workflow.compile(checkpointer=MemorySaver())
    
    async def execute(
        self,
        home_id: str,
        floor_plan_url: str,
        room_images: List[Dict[str, str]],
        **kwargs
    ) -> DigitalTwinState:
        """
        Execute the digital twin creation workflow.
        
        Args:
            home_id: UUID of the home
            floor_plan_url: URL/path to floor plan image
            room_images: List of room image dicts with 'url' and optional 'room_hint'
            **kwargs: Additional metadata
        
        Returns:
            Final workflow state with results
        """
        # Create initial state
        initial_state = DigitalTwinState(
            **self.orchestrator.create_initial_state(**kwargs),
            home_id=home_id,
            floor_plan_url=floor_plan_url,
            room_images=room_images,
            floor_plan_analysis=None,
            detected_rooms=[],
            room_analyses=[],
            floor_plan_ids=[],
            room_ids=[],
            material_ids=[],
            fixture_ids=[],
            product_ids=[],
            completeness_score=0.0,
            confidence_score=0.0,
            rooms_created=0,
            images_analyzed=0
        )
        
        initial_state["status"] = WorkflowStatus.RUNNING
        
        try:
            # Execute the workflow
            config = {"configurable": {"thread_id": initial_state["workflow_id"]}}
            final_state = await self.graph.ainvoke(initial_state, config)
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            initial_state = self.orchestrator.mark_failed(initial_state, e)
            return initial_state
    
    async def _validate_inputs(self, state: DigitalTwinState) -> DigitalTwinState:
        """Validate input data."""
        state = self.orchestrator.mark_node_start(state, "validate_inputs")
        
        try:
            # Validate home_id
            if not state.get("home_id"):
                raise WorkflowError("home_id is required", node_name="validate_inputs")
            
            # Validate floor_plan_url
            if not state.get("floor_plan_url"):
                raise WorkflowError("floor_plan_url is required", node_name="validate_inputs")
            
            # Validate room_images (optional but warn if empty)
            room_images = state.get("room_images", [])
            if not room_images:
                state = self.orchestrator.add_warning(
                    state,
                    "No room images provided - digital twin will be incomplete",
                    "validate_inputs"
                )
            
            # Verify home exists in database
            from sqlalchemy import select
            result = await self.db.execute(
                select(Home).where(Home.id == uuid.UUID(state["home_id"]))
            )
            home = result.scalar_one_or_none()
            
            if not home:
                raise WorkflowError(
                    f"Home {state['home_id']} not found in database",
                    node_name="validate_inputs"
                )
            
            state = self.orchestrator.mark_node_complete(state, "validate_inputs", {
                "home_exists": True,
                "room_images_count": len(room_images)
            })
            
        except WorkflowError:
            raise
        except Exception as e:
            state = self.orchestrator.add_error(state, e, "validate_inputs", recoverable=False)
            raise WorkflowError(
                f"Input validation failed: {str(e)}",
                node_name="validate_inputs",
                original_error=e
            )
        
        return state
    
    async def _analyze_floor_plan(self, state: DigitalTwinState) -> DigitalTwinState:
        """Analyze floor plan to detect rooms and layout."""
        state = self.orchestrator.mark_node_start(state, "analyze_floor_plan")
        
        try:
            logger.info(f"Analyzing floor plan: {state['floor_plan_url']}")
            
            # Execute floor plan analysis
            result = await self.floor_plan_agent.execute({
                "image": state["floor_plan_url"],
                "analysis_depth": "comprehensive"
            })
            
            if not result.success:
                raise WorkflowError(
                    f"Floor plan analysis failed: {result.error}",
                    node_name="analyze_floor_plan",
                    recoverable=True
                )
            
            # Store analysis results
            state["floor_plan_analysis"] = result.data
            
            # Extract detected rooms
            detected_rooms = result.data.get("detected_rooms", [])
            if not detected_rooms:
                state = self.orchestrator.add_warning(
                    state,
                    "No rooms detected in floor plan",
                    "analyze_floor_plan"
                )
            
            state["detected_rooms"] = detected_rooms
            state["confidence_score"] = result.data.get("confidence_score", 0.0)
            
            state = self.orchestrator.mark_node_complete(state, "analyze_floor_plan", {
                "rooms_detected": len(detected_rooms),
                "confidence": state["confidence_score"]
            })
            
        except WorkflowError:
            raise
        except Exception as e:
            state = self.orchestrator.add_error(state, e, "analyze_floor_plan", recoverable=True)
            raise WorkflowError(
                f"Floor plan analysis error: {str(e)}",
                node_name="analyze_floor_plan",
                original_error=e,
                recoverable=True
            )
        
        return state

    async def _create_rooms(self, state: DigitalTwinState) -> DigitalTwinState:
        """Create room records in database from detected rooms."""
        state = self.orchestrator.mark_node_start(state, "create_rooms")

        try:
            detected_rooms = state.get("detected_rooms", [])
            if not detected_rooms:
                state = self.orchestrator.add_warning(
                    state,
                    "No rooms to create - skipping room creation",
                    "create_rooms"
                )
                return state

            home_id = uuid.UUID(state["home_id"])
            room_ids = []

            # Create FloorPlan record first
            floor_plan_analysis = state.get("floor_plan_analysis", {})
            floor_plan = FloorPlan(
                home_id=home_id,
                name=floor_plan_analysis.get("metadata", {}).get("name", "Main Floor"),
                floor_level=1,
                image_url=state["floor_plan_url"],
                scale=floor_plan_analysis.get("units", {}).get("scale_text"),
                is_analyzed=True,
                total_area_sqft=floor_plan_analysis.get("total_area", 0.0)
            )

            self.db.add(floor_plan)
            await self.db.flush()

            state.setdefault("floor_plan_ids", []).append(str(floor_plan.id))

            # Create Room records
            for room_data in detected_rooms:
                room = Room(
                    home_id=home_id,
                    floor_plan_id=floor_plan.id,
                    name=room_data.get("name", "Unknown Room"),
                    room_type=room_data.get("type", "unknown"),
                    area_sqft=room_data.get("area_sqft", 0.0),
                    dimensions_ft=room_data.get("dimensions", {}),
                    is_analyzed=False  # Will be analyzed in next step
                )

                self.db.add(room)
                await self.db.flush()
                room_ids.append(str(room.id))

            await self.db.commit()

            state["room_ids"] = room_ids
            state["rooms_created"] = len(room_ids)

            state = self.orchestrator.mark_node_complete(state, "create_rooms", {
                "rooms_created": len(room_ids),
                "floor_plan_id": str(floor_plan.id)
            })

        except Exception as e:
            await self.db.rollback()
            state = self.orchestrator.add_error(state, e, "create_rooms", recoverable=True)
            raise WorkflowError(
                f"Room creation failed: {str(e)}",
                node_name="create_rooms",
                original_error=e,
                recoverable=True
            )

        return state

    async def _analyze_room_images(self, state: DigitalTwinState) -> DigitalTwinState:
        """Analyze room images to extract materials, fixtures, and products."""
        state = self.orchestrator.mark_node_start(state, "analyze_room_images")

        try:
            room_images = state.get("room_images", [])
            if not room_images:
                state = self.orchestrator.add_warning(
                    state,
                    "No room images to analyze",
                    "analyze_room_images"
                )
                return state

            room_analyses = []
            images_analyzed = 0

            for img_data in room_images:
                try:
                    image_url = img_data.get("url")
                    room_hint = img_data.get("room_hint")

                    if not image_url:
                        state = self.orchestrator.add_warning(
                            state,
                            f"Skipping image with no URL: {img_data}",
                            "analyze_room_images"
                        )
                        continue

                    # Analyze room image
                    result = await self.room_analysis_agent.execute({
                        "image": image_url,
                        "room_type": room_hint,
                        "analysis_type": "comprehensive"
                    })

                    if result.success:
                        analysis_data = result.data
                        analysis_data["image_url"] = image_url
                        room_analyses.append(analysis_data)
                        images_analyzed += 1
                    else:
                        state = self.orchestrator.add_warning(
                            state,
                            f"Failed to analyze image {image_url}: {result.error}",
                            "analyze_room_images"
                        )

                except Exception as e:
                    state = self.orchestrator.add_warning(
                        state,
                        f"Error analyzing image {img_data.get('url', 'unknown')}: {str(e)}",
                        "analyze_room_images"
                    )
                    continue

            state["room_analyses"] = room_analyses
            state["images_analyzed"] = images_analyzed

            state = self.orchestrator.mark_node_complete(state, "analyze_room_images", {
                "images_analyzed": images_analyzed,
                "total_images": len(room_images)
            })

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "analyze_room_images", recoverable=True)
            # Don't raise - partial analysis is acceptable

        return state

    async def _extract_entities(self, state: DigitalTwinState) -> DigitalTwinState:
        """Extract and persist materials, fixtures, and products from room analyses."""
        state = self.orchestrator.mark_node_start(state, "extract_entities")

        try:
            room_analyses = state.get("room_analyses", [])
            if not room_analyses:
                state = self.orchestrator.add_warning(
                    state,
                    "No room analyses to extract entities from",
                    "extract_entities"
                )
                return state

            home_id = uuid.UUID(state["home_id"])
            room_ids = [uuid.UUID(rid) for rid in state.get("room_ids", [])]

            material_ids = []
            fixture_ids = []
            product_ids = []

            for analysis in room_analyses:
                # Match analysis to room (simple matching by room type for now)
                room_type = analysis.get("room_type", "unknown")
                matched_room_id = room_ids[0] if room_ids else None  # TODO: Better matching

                # Extract materials
                for mat_data in analysis.get("detected_materials", []):
                    material = Material(
                        home_id=home_id,
                        room_id=matched_room_id,
                        material_type=mat_data.get("type", "unknown"),
                        location=mat_data.get("location", "unknown"),
                        material_name=mat_data.get("material", "unknown"),
                        color=mat_data.get("color"),
                        condition=mat_data.get("condition", "unknown"),
                        estimated_age_years=mat_data.get("estimated_age"),
                        confidence_score=mat_data.get("confidence", 0.0)
                    )
                    self.db.add(material)
                    await self.db.flush()
                    material_ids.append(str(material.id))

                # Extract fixtures
                for fix_data in analysis.get("detected_fixtures", []):
                    fixture = Fixture(
                        home_id=home_id,
                        room_id=matched_room_id,
                        fixture_type=fix_data.get("type", "unknown"),
                        brand=fix_data.get("brand"),
                        model=fix_data.get("model"),
                        condition=fix_data.get("condition", "unknown"),
                        estimated_age_years=fix_data.get("estimated_age"),
                        confidence_score=fix_data.get("confidence", 0.0)
                    )
                    self.db.add(fixture)
                    await self.db.flush()
                    fixture_ids.append(str(fixture.id))

                # Extract products
                for prod_data in analysis.get("detected_products", []):
                    product = Product(
                        home_id=home_id,
                        room_id=matched_room_id,
                        product_type=prod_data.get("type", "unknown"),
                        name=prod_data.get("name", "Unknown Product"),
                        brand=prod_data.get("brand"),
                        estimated_value=prod_data.get("estimated_value"),
                        confidence_score=prod_data.get("confidence", 0.0)
                    )
                    self.db.add(product)
                    await self.db.flush()
                    product_ids.append(str(product.id))

            await self.db.commit()

            state["material_ids"] = material_ids
            state["fixture_ids"] = fixture_ids
            state["product_ids"] = product_ids

            state = self.orchestrator.mark_node_complete(state, "extract_entities", {
                "materials_extracted": len(material_ids),
                "fixtures_extracted": len(fixture_ids),
                "products_extracted": len(product_ids)
            })

        except Exception as e:
            await self.db.rollback()
            state = self.orchestrator.add_error(state, e, "extract_entities", recoverable=True)
            # Don't raise - partial extraction is acceptable

        return state

    async def _calculate_completeness(self, state: DigitalTwinState) -> DigitalTwinState:
        """Calculate completeness score for the digital twin."""
        state = self.orchestrator.mark_node_start(state, "calculate_completeness")

        try:
            # Scoring factors
            has_floor_plan = bool(state.get("floor_plan_analysis"))
            rooms_detected = len(state.get("detected_rooms", []))
            rooms_created = state.get("rooms_created", 0)
            images_analyzed = state.get("images_analyzed", 0)
            materials_count = len(state.get("material_ids", []))
            fixtures_count = len(state.get("fixture_ids", []))
            products_count = len(state.get("product_ids", []))

            # Calculate completeness (0-100)
            score = 0.0

            if has_floor_plan:
                score += 30.0  # Floor plan analyzed

            if rooms_created > 0:
                score += 20.0  # Rooms created

            if images_analyzed > 0:
                score += 20.0  # Room images analyzed

                # Bonus for comprehensive analysis
                if materials_count > 0:
                    score += 10.0
                if fixtures_count > 0:
                    score += 10.0
                if products_count > 0:
                    score += 10.0

            state["completeness_score"] = min(score, 100.0)

            state = self.orchestrator.mark_node_complete(state, "calculate_completeness", {
                "completeness_score": state["completeness_score"]
            })

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "calculate_completeness", recoverable=True)
            state["completeness_score"] = 0.0

        return state

    async def _finalize(self, state: DigitalTwinState) -> DigitalTwinState:
        """Finalize the workflow and prepare results."""
        state = self.orchestrator.mark_node_start(state, "finalize")

        try:
            # Prepare result summary
            result = {
                "home_id": state["home_id"],
                "floor_plan_ids": state.get("floor_plan_ids", []),
                "room_ids": state.get("room_ids", []),
                "material_ids": state.get("material_ids", []),
                "fixture_ids": state.get("fixture_ids", []),
                "product_ids": state.get("product_ids", []),
                "completeness_score": state.get("completeness_score", 0.0),
                "confidence_score": state.get("confidence_score", 0.0),
                "rooms_created": state.get("rooms_created", 0),
                "images_analyzed": state.get("images_analyzed", 0),
                "summary": {
                    "total_rooms": len(state.get("room_ids", [])),
                    "total_materials": len(state.get("material_ids", [])),
                    "total_fixtures": len(state.get("fixture_ids", [])),
                    "total_products": len(state.get("product_ids", []))
                }
            }

            # Determine final status
            errors = state.get("errors", [])
            if not errors:
                state = self.orchestrator.mark_completed(state, result)
            elif state.get("completeness_score", 0) > 50:
                state = self.orchestrator.mark_partial(state, result)
            else:
                state = self.orchestrator.mark_failed(state)

            state = self.orchestrator.mark_node_complete(state, "finalize", result)

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "finalize", recoverable=False)
            state = self.orchestrator.mark_failed(state, e)

        return state

