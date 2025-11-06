"""Cost Estimation Agent - Production-ready cost estimation for home improvement projects."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from backend.agents.base.agent import BaseAgent, AgentConfig, AgentResponse, AgentRole
from backend.integrations.gemini.client import GeminiClient

logger = logging.getLogger(__name__)


# Regional cost multipliers (base is 1.0 for national average)
REGIONAL_MULTIPLIERS = {
    "northeast": 1.25,  # NYC, Boston, etc.
    "west_coast": 1.30,  # SF, LA, Seattle
    "midwest": 0.90,    # Chicago, Detroit, etc.
    "south": 0.85,      # Atlanta, Dallas, etc.
    "mountain": 0.95,   # Denver, Phoenix, etc.
    "national": 1.00    # Default
}


# Material cost database (per unit, national average)
MATERIAL_COSTS = {
    # Flooring (per sq ft)
    "hardwood_flooring": {"low": 3.0, "mid": 6.0, "high": 12.0, "unit": "sqft"},
    "laminate_flooring": {"low": 1.5, "mid": 3.0, "high": 5.0, "unit": "sqft"},
    "tile_flooring": {"low": 2.0, "mid": 5.0, "high": 15.0, "unit": "sqft"},
    "carpet": {"low": 1.0, "mid": 3.0, "high": 8.0, "unit": "sqft"},
    "vinyl_flooring": {"low": 1.0, "mid": 2.5, "high": 5.0, "unit": "sqft"},
    
    # Countertops (per sq ft)
    "granite_countertop": {"low": 40.0, "mid": 60.0, "high": 100.0, "unit": "sqft"},
    "quartz_countertop": {"low": 50.0, "mid": 75.0, "high": 120.0, "unit": "sqft"},
    "marble_countertop": {"low": 60.0, "mid": 100.0, "high": 200.0, "unit": "sqft"},
    "laminate_countertop": {"low": 10.0, "mid": 20.0, "high": 40.0, "unit": "sqft"},
    "butcher_block_countertop": {"low": 30.0, "mid": 50.0, "high": 80.0, "unit": "sqft"},
    
    # Paint (per gallon, covers ~350 sqft)
    "interior_paint": {"low": 20.0, "mid": 40.0, "high": 80.0, "unit": "gallon"},
    "exterior_paint": {"low": 30.0, "mid": 50.0, "high": 100.0, "unit": "gallon"},
    
    # Cabinets (per linear foot)
    "stock_cabinets": {"low": 60.0, "mid": 100.0, "high": 150.0, "unit": "linear_ft"},
    "semi_custom_cabinets": {"low": 150.0, "mid": 250.0, "high": 400.0, "unit": "linear_ft"},
    "custom_cabinets": {"low": 500.0, "mid": 800.0, "high": 1500.0, "unit": "linear_ft"},
    
    # Fixtures
    "basic_faucet": {"low": 50.0, "mid": 150.0, "high": 400.0, "unit": "each"},
    "basic_light_fixture": {"low": 30.0, "mid": 100.0, "high": 500.0, "unit": "each"},
    "toilet": {"low": 100.0, "mid": 300.0, "high": 800.0, "unit": "each"},
    "vanity": {"low": 200.0, "mid": 600.0, "high": 2000.0, "unit": "each"},
    
    # Appliances
    "refrigerator": {"low": 500.0, "mid": 1500.0, "high": 5000.0, "unit": "each"},
    "dishwasher": {"low": 300.0, "mid": 700.0, "high": 1500.0, "unit": "each"},
    "range": {"low": 400.0, "mid": 1000.0, "high": 3000.0, "unit": "each"},
    "microwave": {"low": 100.0, "mid": 300.0, "high": 800.0, "unit": "each"},
}


# Labor cost database (per hour or per unit)
LABOR_COSTS = {
    "general_contractor": {"rate": 75.0, "unit": "hour"},
    "electrician": {"rate": 85.0, "unit": "hour"},
    "plumber": {"rate": 90.0, "unit": "hour"},
    "carpenter": {"rate": 70.0, "unit": "hour"},
    "painter": {"rate": 50.0, "unit": "hour"},
    "tile_installer": {"rate": 60.0, "unit": "hour"},
    "flooring_installer": {"rate": 55.0, "unit": "hour"},
    "hvac_technician": {"rate": 95.0, "unit": "hour"},
    "drywall_installer": {"rate": 50.0, "unit": "hour"},
    
    # Per-unit labor costs
    "flooring_installation": {"low": 2.0, "mid": 4.0, "high": 8.0, "unit": "sqft"},
    "tile_installation": {"low": 5.0, "mid": 10.0, "high": 20.0, "unit": "sqft"},
    "painting": {"low": 1.5, "mid": 3.0, "high": 6.0, "unit": "sqft"},
    "cabinet_installation": {"low": 50.0, "mid": 100.0, "high": 200.0, "unit": "linear_ft"},
}


class CostEstimationAgent(BaseAgent):
    """
    Production-ready agent for estimating home improvement project costs.
    
    Features:
    - Material cost estimation with quality tiers (low/mid/high)
    - Labor cost estimation with regional adjustments
    - AI-powered project scope analysis
    - Detailed cost breakdowns
    - Confidence scoring
    """
    
    def __init__(self):
        config = AgentConfig(
            name="cost_estimation_agent",
            role=AgentRole.COST_INTELLIGENCE,
            description="Estimates costs for home improvement projects with material and labor breakdowns",
            model_name="gemini-2.5-flash",
            temperature=0.3,
            enable_memory=False
        )
        super().__init__(config)
        self.gemini_client = GeminiClient()
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Estimate costs for a home improvement project.
        
        Args:
            input_data: {
                "project_description": str,  # Description of the project
                "room_type": Optional[str],  # Type of room
                "room_dimensions": Optional[Dict],  # {"length_ft": float, "width_ft": float, "height_ft": float}
                "materials": Optional[List[str]],  # List of materials needed
                "quality_tier": Optional[str],  # "low", "mid", "high"
                "region": Optional[str],  # Region for cost adjustment
                "include_labor": Optional[bool],  # Whether to include labor costs
                "image_url": Optional[str]  # Optional image for visual analysis
            }
        
        Returns:
            AgentResponse with cost estimation data
        """
        try:
            project_description = input_data.get("project_description")
            if not project_description:
                return AgentResponse(
                    agent_name=self.config.name,
                    agent_role=self.config.role,
                    success=False,
                    error="project_description is required"
                )
            
            room_type = input_data.get("room_type", "unknown")
            room_dimensions = input_data.get("room_dimensions", {})
            materials = input_data.get("materials", [])
            quality_tier = input_data.get("quality_tier", "mid")
            region = input_data.get("region", "national")
            include_labor = input_data.get("include_labor", True)
            image_url = input_data.get("image_url")
            
            logger.info(f"Estimating costs for project: {project_description[:100]}...")
            start_time = datetime.utcnow()
            
            # Step 1: Analyze project scope with AI
            scope_analysis = await self._analyze_project_scope(
                project_description,
                room_type,
                room_dimensions,
                image_url
            )
            
            # Step 2: Estimate material costs
            material_costs = self._estimate_material_costs(
                scope_analysis,
                materials,
                quality_tier,
                region
            )
            
            # Step 3: Estimate labor costs
            labor_costs = {}
            if include_labor:
                labor_costs = self._estimate_labor_costs(
                    scope_analysis,
                    region
                )
            
            # Step 4: Calculate totals
            total_material_cost = sum(item["total_cost"] for item in material_costs.values())
            total_labor_cost = sum(item["total_cost"] for item in labor_costs.values())
            total_cost = total_material_cost + total_labor_cost
            
            # Step 5: Calculate confidence score
            confidence_score = self._calculate_confidence(
                scope_analysis,
                room_dimensions,
                materials
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result = {
                "project_scope": scope_analysis,
                "material_costs": material_costs,
                "labor_costs": labor_costs,
                "summary": {
                    "total_material_cost": round(total_material_cost, 2),
                    "total_labor_cost": round(total_labor_cost, 2),
                    "total_cost": round(total_cost, 2),
                    "cost_range": {
                        "low": round(total_cost * 0.85, 2),
                        "high": round(total_cost * 1.15, 2)
                    },
                    "quality_tier": quality_tier,
                    "region": region,
                    "regional_multiplier": REGIONAL_MULTIPLIERS.get(region, 1.0)
                },
                "confidence_score": confidence_score,
                "metadata": {
                    "processing_time_ms": processing_time,
                    "analyzed_at": datetime.utcnow().isoformat()
                }
            }
            
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role,
                success=True,
                data=result,
                message=f"Cost estimation complete: ${total_cost:,.2f} (±15%)"
            )
        
        except Exception as e:
            logger.error(f"Error in cost estimation: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role,
                success=False,
                error=f"Cost estimation failed: {str(e)}"
            )
    
    async def _analyze_project_scope(
        self,
        project_description: str,
        room_type: str,
        room_dimensions: Dict[str, float],
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze project scope using AI."""
        
        prompt = f"""Analyze this home improvement project and provide a detailed scope breakdown.

Project Description: {project_description}
Room Type: {room_type}
Room Dimensions: {room_dimensions}

Provide a JSON response with the following structure:
{{
    "project_type": "kitchen_remodel|bathroom_remodel|flooring|painting|etc",
    "estimated_duration_days": <int>,
    "complexity": "low|medium|high",
    "required_materials": [
        {{"material": "material_name", "quantity": <float>, "unit": "sqft|linear_ft|each|gallon"}}
    ],
    "required_labor": [
        {{"trade": "electrician|plumber|carpenter|etc", "estimated_hours": <float>}}
    ],
    "special_considerations": ["consideration1", "consideration2"],
    "permits_required": ["permit1", "permit2"]
}}

Return only valid JSON."""
        
        try:
            if image_url:
                # Use vision analysis if image provided
                analysis_result = await self.gemini_client.analyze_image(
                    image=image_url,
                    prompt=prompt,
                    temperature=0.3
                )
            else:
                # Use text-only analysis
                analysis_result = await self.gemini_client.generate_text(
                    prompt=prompt,
                    temperature=0.3
                )
            
            # Parse JSON response
            parsed = self._parse_json_response(analysis_result)
            return parsed
            
        except Exception as e:
            logger.error(f"Error analyzing project scope: {e}")
            # Return minimal scope
            return {
                "project_type": "general_renovation",
                "estimated_duration_days": 7,
                "complexity": "medium",
                "required_materials": [],
                "required_labor": [],
                "special_considerations": [],
                "permits_required": []
            }

    def _estimate_material_costs(
        self,
        scope_analysis: Dict[str, Any],
        additional_materials: List[str],
        quality_tier: str,
        region: str
    ) -> Dict[str, Dict[str, Any]]:
        """Estimate material costs based on scope and quality tier."""

        material_costs = {}
        regional_multiplier = REGIONAL_MULTIPLIERS.get(region, 1.0)

        # Process materials from scope analysis
        for material_item in scope_analysis.get("required_materials", []):
            material_name = material_item.get("material", "").lower().replace(" ", "_")
            quantity = material_item.get("quantity", 0)
            unit = material_item.get("unit", "each")

            # Find matching material in database
            cost_data = None
            for key, value in MATERIAL_COSTS.items():
                if material_name in key or key in material_name:
                    cost_data = value
                    break

            if cost_data:
                unit_cost = cost_data.get(quality_tier, cost_data.get("mid", 0))
                total_cost = unit_cost * quantity * regional_multiplier

                material_costs[material_name] = {
                    "quantity": quantity,
                    "unit": unit,
                    "unit_cost": round(unit_cost, 2),
                    "regional_multiplier": regional_multiplier,
                    "total_cost": round(total_cost, 2),
                    "quality_tier": quality_tier
                }

        # Process additional materials
        for material in additional_materials:
            material_key = material.lower().replace(" ", "_")
            if material_key in MATERIAL_COSTS and material_key not in material_costs:
                cost_data = MATERIAL_COSTS[material_key]
                unit_cost = cost_data.get(quality_tier, cost_data.get("mid", 0))

                material_costs[material_key] = {
                    "quantity": 1,
                    "unit": cost_data.get("unit", "each"),
                    "unit_cost": round(unit_cost, 2),
                    "regional_multiplier": regional_multiplier,
                    "total_cost": round(unit_cost * regional_multiplier, 2),
                    "quality_tier": quality_tier
                }

        return material_costs

    def _estimate_labor_costs(
        self,
        scope_analysis: Dict[str, Any],
        region: str
    ) -> Dict[str, Dict[str, Any]]:
        """Estimate labor costs based on scope."""

        labor_costs = {}
        regional_multiplier = REGIONAL_MULTIPLIERS.get(region, 1.0)

        # Process labor from scope analysis
        for labor_item in scope_analysis.get("required_labor", []):
            trade = labor_item.get("trade", "").lower().replace(" ", "_")
            estimated_hours = labor_item.get("estimated_hours", 0)

            # Find matching labor in database
            labor_data = None
            for key, value in LABOR_COSTS.items():
                if trade in key or key in trade:
                    labor_data = value
                    break

            if labor_data and labor_data.get("unit") == "hour":
                hourly_rate = labor_data.get("rate", 0)
                total_cost = hourly_rate * estimated_hours * regional_multiplier

                labor_costs[trade] = {
                    "hours": estimated_hours,
                    "hourly_rate": round(hourly_rate, 2),
                    "regional_multiplier": regional_multiplier,
                    "total_cost": round(total_cost, 2)
                }

        return labor_costs

    def _calculate_confidence(
        self,
        scope_analysis: Dict[str, Any],
        room_dimensions: Dict[str, float],
        materials: List[str]
    ) -> float:
        """Calculate confidence score for the estimate."""

        confidence = 0.5  # Base confidence

        # Increase confidence if we have room dimensions
        if room_dimensions and all(k in room_dimensions for k in ["length_ft", "width_ft"]):
            confidence += 0.2

        # Increase confidence if we have detailed scope
        if scope_analysis.get("required_materials"):
            confidence += 0.15

        if scope_analysis.get("required_labor"):
            confidence += 0.15

        # Decrease confidence for high complexity
        complexity = scope_analysis.get("complexity", "medium")
        if complexity == "high":
            confidence -= 0.1
        elif complexity == "low":
            confidence += 0.1

        return min(max(confidence, 0.0), 1.0)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from AI response."""
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {}

