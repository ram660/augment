"""
Comprehensive tests for Week 1 implementation.

Tests:
- LangGraph workflow foundation
- Digital Twin workflow
- RAG service with Gemini embeddings
- Cost Estimation agent
- Product Matching agent
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

# Import components to test
from backend.workflows.base import WorkflowOrchestrator, WorkflowStatus, WorkflowError, BaseWorkflowState
from backend.workflows.digital_twin_workflow import DigitalTwinWorkflow, DigitalTwinState
from backend.services.rag_service import RAGService
from backend.agents.intelligence.cost_estimation_agent import CostEstimationAgent
from backend.agents.intelligence.product_matching_agent import ProductMatchingAgent


class TestWorkflowFoundation:
    """Test base workflow infrastructure."""
    
    def test_workflow_orchestrator_initialization(self):
        """Test WorkflowOrchestrator initialization."""
        orchestrator = WorkflowOrchestrator(
            workflow_name="test_workflow",
            max_retries=3
        )
        
        assert orchestrator.workflow_name == "test_workflow"
        assert orchestrator.max_retries == 3
    
    def test_workflow_state_initialization(self):
        """Test workflow state initialization."""
        orchestrator = WorkflowOrchestrator(workflow_name="test")
        state = orchestrator.create_initial_state()

        assert state["workflow_name"] == "test"
        assert state["status"] == WorkflowStatus.PENDING
        assert state["retry_count"] == 0
        assert state["visited_nodes"] == []
        assert state["errors"] == []

    def test_mark_node_start(self):
        """Test marking node start."""
        orchestrator = WorkflowOrchestrator(workflow_name="test")
        state = orchestrator.create_initial_state()

        updated_state = orchestrator.mark_node_start(state, "test_node")

        assert updated_state["current_node"] == "test_node"
        assert "test_node" in updated_state["visited_nodes"]

    def test_mark_node_complete(self):
        """Test marking node complete."""
        orchestrator = WorkflowOrchestrator(workflow_name="test")
        state = orchestrator.create_initial_state()
        state = orchestrator.mark_node_start(state, "test_node")

        result = {"data": "test"}
        updated_state = orchestrator.mark_node_complete(state, "test_node", result)

        # Node complete doesn't clear current_node, just logs completion
        assert "node_results" in updated_state.get("metadata", {})

    def test_add_error_recoverable(self):
        """Test adding recoverable error."""
        orchestrator = WorkflowOrchestrator(workflow_name="test")
        state = orchestrator.create_initial_state()

        error = Exception("Test error")
        updated_state = orchestrator.add_error(state, error, "test_node", recoverable=True)

        assert len(updated_state["errors"]) == 1
        assert updated_state["errors"][0]["recoverable"] is True
        assert updated_state["errors"][0]["node"] == "test_node"

    def test_should_retry(self):
        """Test retry logic."""
        orchestrator = WorkflowOrchestrator(workflow_name="test", max_retries=3)
        state = orchestrator.create_initial_state()

        # Should NOT retry when no recoverable errors
        assert orchestrator.should_retry(state) is False

        # Add a recoverable error
        error = Exception("Test error")
        state = orchestrator.add_error(state, error, "test_node", recoverable=True)

        # Should retry when under max with recoverable error
        assert orchestrator.should_retry(state) is True

        # Should not retry when at max
        state["retry_count"] = 3
        assert orchestrator.should_retry(state) is False


class TestDigitalTwinWorkflow:
    """Test Digital Twin workflow."""
    
    @pytest.mark.asyncio
    async def test_workflow_initialization(self):
        """Test workflow initialization."""
        mock_db = AsyncMock()
        workflow = DigitalTwinWorkflow(db_session=mock_db)
        
        assert workflow.db == mock_db
        assert workflow.orchestrator is not None
        assert workflow.graph is not None
    
    @pytest.mark.asyncio
    async def test_validate_inputs_success(self):
        """Test input validation with valid data."""
        import uuid

        mock_db = AsyncMock()
        workflow = DigitalTwinWorkflow(db_session=mock_db)

        # Create valid UUID
        home_uuid = str(uuid.uuid4())

        # Mock home exists
        mock_db.execute = AsyncMock(return_value=Mock(scalar_one_or_none=Mock(return_value=Mock(id=home_uuid))))

        state: DigitalTwinState = {
            "workflow_id": str(uuid.uuid4()),
            "workflow_name": "digital_twin",
            "status": WorkflowStatus.PENDING,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "current_node": None,
            "visited_nodes": [],
            "retry_count": 0,
            "max_retries": 3,
            "errors": [],
            "warnings": [],
            "result": None,
            "metadata": {},
            "home_id": home_uuid,
            "floor_plan_url": "https://example.com/floor_plan.jpg",
            "room_images": [{"url": "https://example.com/room1.jpg", "room_type": "kitchen"}]
        }

        result = await workflow._validate_inputs(state)

        # Validation doesn't change status, just validates
        assert len(result["errors"]) == 0
        assert result["home_id"] == home_uuid


class TestRAGService:
    """Test RAG service with Gemini embeddings."""
    
    def test_rag_service_initialization_gemini(self):
        """Test RAG service initialization with Gemini."""
        rag = RAGService(use_gemini=True)
        
        assert rag.use_gemini is True
        assert rag.dim == 768  # Gemini embedding dimension
        assert rag.model_name == "text-embedding-004"
    
    def test_rag_service_initialization_fallback(self):
        """Test RAG service initialization with fallback."""
        rag = RAGService(use_gemini=False)
        
        assert rag.use_gemini is False
    
    @pytest.mark.asyncio
    async def test_embed_with_gemini(self):
        """Test embedding generation with Gemini."""
        rag = RAGService(use_gemini=True)
        
        with patch.object(rag._gemini_client, 'get_embeddings', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.1] * 768]  # Mock 768-dim embedding
            
            embedding = await rag._embed("test text")
            
            assert len(embedding) == 768
            mock_embed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_embed_fallback_on_error(self):
        """Test embedding fallback when Gemini fails."""
        rag = RAGService(use_gemini=True)
        
        with patch.object(rag._gemini_client, 'get_embeddings', new_callable=AsyncMock) as mock_embed:
            mock_embed.side_effect = Exception("API error")
            
            embedding = await rag._embed("test text")
            
            # Should fallback to hash-based embedding
            assert len(embedding) > 0
    
    def test_cache_functionality(self):
        """Test query cache."""
        rag = RAGService(use_gemini=False)
        
        # Cache should be empty initially
        assert len(rag._query_cache) == 0
        
        # Clear cache
        rag.clear_cache()
        assert len(rag._query_cache) == 0


class TestCostEstimationAgent:
    """Test Cost Estimation agent."""
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = CostEstimationAgent()
        
        assert agent.config.name == "cost_estimation_agent"
        assert agent.gemini_client is not None
    
    @pytest.mark.asyncio
    async def test_process_missing_description(self):
        """Test process with missing project description."""
        agent = CostEstimationAgent()
        
        result = await agent.process({})
        
        assert result.success is False
        assert "project_description is required" in result.error
    
    @pytest.mark.asyncio
    async def test_process_with_valid_input(self):
        """Test process with valid input."""
        agent = CostEstimationAgent()
        
        with patch.object(agent, '_analyze_project_scope', new_callable=AsyncMock) as mock_scope:
            mock_scope.return_value = {
                "project_type": "kitchen_remodel",
                "estimated_duration_days": 14,
                "complexity": "medium",
                "required_materials": [
                    {"material": "granite_countertop", "quantity": 25, "unit": "sqft"}
                ],
                "required_labor": [
                    {"trade": "carpenter", "estimated_hours": 40}
                ],
                "special_considerations": [],
                "permits_required": []
            }
            
            input_data = {
                "project_description": "Remodel kitchen with new countertops",
                "room_type": "kitchen",
                "room_dimensions": {"length_ft": 12, "width_ft": 10, "height_ft": 8},
                "quality_tier": "mid",
                "region": "national"
            }
            
            result = await agent.process(input_data)
            
            assert result.success is True
            assert "summary" in result.data
            assert result.data["summary"]["total_cost"] > 0
    
    def test_material_cost_estimation(self):
        """Test material cost estimation."""
        agent = CostEstimationAgent()
        
        scope = {
            "required_materials": [
                {"material": "hardwood_flooring", "quantity": 100, "unit": "sqft"}
            ]
        }
        
        costs = agent._estimate_material_costs(scope, [], "mid", "national")
        
        assert "hardwood_flooring" in costs
        assert costs["hardwood_flooring"]["total_cost"] > 0
    
    def test_labor_cost_estimation(self):
        """Test labor cost estimation."""
        agent = CostEstimationAgent()
        
        scope = {
            "required_labor": [
                {"trade": "carpenter", "estimated_hours": 20}
            ]
        }
        
        costs = agent._estimate_labor_costs(scope, "national")
        
        assert "carpenter" in costs
        assert costs["carpenter"]["total_cost"] > 0


class TestProductMatchingAgent:
    """Test Product Matching agent."""
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = ProductMatchingAgent()
        
        assert agent.config.name == "product_matching_agent"
        assert agent.gemini_client is not None
    
    @pytest.mark.asyncio
    async def test_process_missing_product_type(self):
        """Test process with missing product type."""
        agent = ProductMatchingAgent()
        
        result = await agent.process({})
        
        assert result.success is False
        assert "product_type is required" in result.error
    
    @pytest.mark.asyncio
    async def test_process_missing_dimensions(self):
        """Test process with missing room dimensions."""
        agent = ProductMatchingAgent()
        
        result = await agent.process({"product_type": "sofa"})
        
        assert result.success is False
        assert "room_dimensions are required" in result.error

    @pytest.mark.asyncio
    async def test_process_with_valid_input(self):
        """Test process with valid input."""
        agent = ProductMatchingAgent()

        with patch.object(agent, '_analyze_style_compatibility', new_callable=AsyncMock) as mock_style:
            mock_style.return_value = {
                "style_match_score": 0.85,
                "recommended_styles": ["modern", "contemporary"],
                "color_recommendations": ["gray", "white"],
                "material_recommendations": ["fabric", "leather"],
                "design_notes": "Good match"
            }

            input_data = {
                "product_type": "sofa",
                "room_type": "living_room",
                "room_dimensions": {"length_ft": 15, "width_ft": 12, "height_ft": 8},
                "style_preference": "modern"
            }

            result = await agent.process(input_data)

            assert result.success is True
            assert "fit_validation" in result.data
            assert "recommendations" in result.data

    def test_get_product_dimensions(self):
        """Test getting product dimensions."""
        agent = ProductMatchingAgent()

        dims = agent._get_product_dimensions("sofa")

        assert "width_in" in dims
        assert "depth_in" in dims
        assert "height_in" in dims

    def test_validate_fit_success(self):
        """Test fit validation when product fits."""
        agent = ProductMatchingAgent()

        product_dims = {
            "width_in": {"min": 72, "max": 84},
            "depth_in": {"min": 32, "max": 36},
            "height_in": {"min": 30, "max": 34}
        }

        room_dimensions = {
            "length_ft": 15,
            "width_ft": 12,
            "height_ft": 8
        }

        validation = agent._validate_fit("sofa", product_dims, room_dimensions, [])

        assert validation["will_fit"] is True
        assert validation["fits_width"] is True
        assert validation["fits_depth"] is True
        assert validation["fits_height"] is True

    def test_validate_fit_failure(self):
        """Test fit validation when product doesn't fit."""
        agent = ProductMatchingAgent()

        product_dims = {
            "width_in": {"min": 120, "max": 144},  # 10-12 feet wide
            "depth_in": {"min": 48, "max": 60},
            "height_in": {"min": 30, "max": 34}
        }

        room_dimensions = {
            "length_ft": 10,  # Too small
            "width_ft": 8,    # Too small
            "height_ft": 8
        }

        validation = agent._validate_fit("sofa", product_dims, room_dimensions, [])

        assert validation["will_fit"] is False
        assert len(validation["warnings"]) > 0

    def test_calculate_occupied_space(self):
        """Test occupied space calculation."""
        agent = ProductMatchingAgent()

        existing_products = [
            {"dimensions": {"width_in": 60, "depth_in": 30}},  # 1800 sq in
            {"dimensions": {"width_in": 40, "depth_in": 20}}   # 800 sq in
        ]

        occupied = agent._calculate_occupied_space(existing_products)

        assert occupied == 2600  # 1800 + 800

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        agent = ProductMatchingAgent()

        product_dims = {"width_in": {"min": 72, "max": 84}}
        fit_validation = {"will_fit": True}
        style_analysis = {"recommended_styles": ["modern", "contemporary"]}
        budget_range = {"min": 500, "max": 1500}
        must_have_features = ["reclining", "USB ports"]

        recommendations = agent._generate_recommendations(
            "sofa",
            product_dims,
            fit_validation,
            style_analysis,
            budget_range,
            must_have_features
        )

        assert len(recommendations) > 0
        assert any(r["recommendation_type"] == "style_match" for r in recommendations)


# Integration tests
class TestIntegration:
    """Integration tests for all components."""

    @pytest.mark.asyncio
    async def test_end_to_end_cost_estimation(self):
        """Test end-to-end cost estimation flow."""
        agent = CostEstimationAgent()

        with patch.object(agent.gemini_client, 'generate_text', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = """{
                "project_type": "bathroom_remodel",
                "estimated_duration_days": 10,
                "complexity": "medium",
                "required_materials": [
                    {"material": "tile_flooring", "quantity": 50, "unit": "sqft"}
                ],
                "required_labor": [
                    {"trade": "tile_installer", "estimated_hours": 30}
                ],
                "special_considerations": ["waterproofing"],
                "permits_required": ["plumbing"]
            }"""

            input_data = {
                "project_description": "Remodel bathroom with new tile",
                "room_type": "bathroom",
                "room_dimensions": {"length_ft": 8, "width_ft": 6, "height_ft": 8},
                "quality_tier": "mid",
                "region": "national",
                "include_labor": True
            }

            result = await agent.process(input_data)

            assert result.success is True
            assert result.data["summary"]["total_cost"] > 0
            assert result.data["summary"]["total_material_cost"] > 0
            assert result.data["summary"]["total_labor_cost"] > 0

    @pytest.mark.asyncio
    async def test_end_to_end_product_matching(self):
        """Test end-to-end product matching flow."""
        agent = ProductMatchingAgent()

        with patch.object(agent.gemini_client, 'generate_text', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = """{
                "style_match_score": 0.9,
                "recommended_styles": ["modern", "minimalist"],
                "color_recommendations": ["white", "gray"],
                "material_recommendations": ["wood", "metal"],
                "design_notes": "Perfect for modern living room"
            }"""

            input_data = {
                "product_type": "coffee_table",
                "room_type": "living_room",
                "room_dimensions": {"length_ft": 15, "width_ft": 12, "height_ft": 8},
                "style_preference": "modern",
                "budget_range": {"min": 200, "max": 800}
            }

            result = await agent.process(input_data)

            assert result.success is True
            assert result.data["fit_validation"]["will_fit"] is True
            assert len(result.data["recommendations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])

