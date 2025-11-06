"""
Smart Recommendations Agent - Provides intelligent suggestions based on home data.

This agent analyzes the digital twin data to provide:
- Material and product recommendations based on room dimensions
- Cost estimates for renovations
- Product dimension compatibility checks
- Style consistency suggestions
- Maintenance recommendations
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.agents.base import BaseAgent, AgentConfig, AgentRole, AgentResponse
from backend.integrations.gemini import GeminiClient

logger = logging.getLogger(__name__)


class SmartRecommendationsAgent(BaseAgent):
    """
    Smart Recommendations Agent for intelligent home improvement suggestions.
    
    Capabilities:
    - Calculate material quantities based on room dimensions
    - Recommend products that fit room dimensions
    - Estimate renovation costs
    - Suggest style-consistent materials
    - Identify maintenance needs
    """
    
    SYSTEM_INSTRUCTION = """You are an expert home improvement consultant with deep knowledge of:
- Material quantities and coverage calculations
- Product dimensions and compatibility
- Cost estimation for renovations
- Interior design and style consistency
- Building codes and best practices

When providing recommendations:
1. Always base calculations on actual room dimensions
2. Include material waste factors (typically 10-15%)
3. Suggest products that physically fit the space
4. Consider style consistency across rooms
5. Provide cost ranges (low, mid, high)
6. Explain your reasoning clearly
"""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """Initialize Smart Recommendations Agent."""
        config = AgentConfig(
            name="smart_recommendations_agent",
            role=AgentRole.PLANNER,
            description="Intelligent recommendations based on home data",
            model_name="gemini-2.0-flash-exp",
            temperature=0.3,  # Lower for factual recommendations
            enable_memory=False
        )
        super().__init__(config)
        
        self.gemini = gemini_client or GeminiClient()
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process recommendation request.
        
        Args:
            input_data: {
                "recommendation_type": str,  # 'material_quantity', 'product_fit', 'cost_estimate', 'style_match'
                "room_data": dict,  # Room dimensions and current materials
                "target_material": Optional[str],  # Material to calculate
                "target_product": Optional[dict],  # Product to check fit
                "renovation_scope": Optional[str],  # Scope for cost estimate
                "style_preference": Optional[str]  # Desired style
            }
        
        Returns:
            AgentResponse with recommendations
        """
        try:
            recommendation_type = input_data.get("recommendation_type")
            
            if recommendation_type == "material_quantity":
                return await self._calculate_material_quantity(input_data)
            elif recommendation_type == "product_fit":
                return await self._check_product_fit(input_data)
            elif recommendation_type == "cost_estimate":
                return await self._estimate_renovation_cost(input_data)
            elif recommendation_type == "style_match":
                return await self._suggest_style_match(input_data)
            elif recommendation_type == "comprehensive":
                return await self._comprehensive_analysis(input_data)
            else:
                return AgentResponse(
                    agent_name=self.name,
                    agent_role=self.role,
                    success=False,
                    error=f"Unknown recommendation type: {recommendation_type}"
                )
        
        except Exception as e:
            logger.error(f"Error in smart recommendations: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.name,
                agent_role=self.role,
                success=False,
                error=str(e)
            )
    
    async def _calculate_material_quantity(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Calculate material quantities needed for a room."""
        room_data = input_data.get("room_data", {})
        target_material = input_data.get("target_material", "paint")
        
        prompt = f"""Calculate the material quantities needed for this room:

Room Details:
- Type: {room_data.get('room_type', 'unknown')}
- Dimensions: {room_data.get('length', 0)}ft x {room_data.get('width', 0)}ft
- Area: {room_data.get('area', 0)} sq ft
- Height: {room_data.get('height', 8)}ft (assumed if not provided)

Target Material: {target_material}

Current Materials:
{self._format_materials(room_data.get('materials', []))}

Current Fixtures:
{self._format_fixtures(room_data.get('fixtures', []))}

Please calculate:
1. Total quantity needed (with 10-15% waste factor)
2. Number of units to purchase (e.g., gallons of paint, boxes of flooring)
3. Estimated coverage per unit
4. Special considerations (doors, windows, built-ins to exclude)

Provide response as JSON:
{{
  "material_type": "{target_material}",
  "calculations": {{
    "gross_area": 0,
    "deductions": 0,
    "net_area": 0,
    "waste_factor": 0.15,
    "total_area_with_waste": 0
  }},
  "quantities": {{
    "amount": 0,
    "unit": "gallons|sq_ft|boxes",
    "units_to_purchase": 0
  }},
  "coverage_per_unit": 0,
  "special_considerations": [],
  "cost_estimate": {{
    "low": 0,
    "mid": 0,
    "high": 0,
    "currency": "CAD"
  }},
  "recommendations": []
}}
"""
        
        response_text = await self.gemini.generate_text(
            prompt=prompt,
            temperature=0.3
        )
        
        # Parse JSON response
        import json
        try:
            result = json.loads(response_text)
        except:
            # If not valid JSON, wrap in structure
            result = {
                "material_type": target_material,
                "raw_response": response_text
            }
        
        return AgentResponse(
            agent_name=self.name,
            agent_role=self.role,
            success=True,
            data=result,
            metadata={
                "room_id": room_data.get('id'),
                "calculation_type": "material_quantity"
            }
        )
    
    async def _check_product_fit(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Check if a product fits in the room dimensions."""
        room_data = input_data.get("room_data", {})
        target_product = input_data.get("target_product", {})
        
        prompt = f"""Check if this product will fit in the room:

Room Details:
- Type: {room_data.get('room_type', 'unknown')}
- Dimensions: {room_data.get('length', 0)}ft x {room_data.get('width', 0)}ft
- Area: {room_data.get('area', 0)} sq ft

Product Details:
- Type: {target_product.get('product_type', 'unknown')}
- Dimensions: {target_product.get('dimensions', {})}
- Description: {target_product.get('description', '')}

Current Products in Room:
{self._format_products(room_data.get('products', []))}

Please analyze:
1. Will the product physically fit?
2. Recommended placement locations
3. Clearance requirements
4. Traffic flow considerations
5. Alternative sizes if needed

Provide response as JSON:
{{
  "fits": true|false,
  "fit_analysis": {{
    "product_footprint": {{"length": 0, "width": 0, "unit": "ft"}},
    "available_space": {{"length": 0, "width": 0, "unit": "ft"}},
    "clearance_needed": {{"front": 0, "sides": 0, "back": 0, "unit": "ft"}},
    "total_space_required": 0
  }},
  "recommended_placements": [],
  "traffic_flow_impact": "minimal|moderate|significant",
  "alternative_sizes": [],
  "warnings": [],
  "recommendations": []
}}
"""
        
        response_text = await self.gemini.generate_text(
            prompt=prompt,
            temperature=0.3
        )
        
        import json
        try:
            result = json.loads(response_text)
        except:
            result = {"raw_response": response_text}
        
        return AgentResponse(
            agent_name=self.name,
            agent_role=self.role,
            success=True,
            data=result,
            metadata={
                "room_id": room_data.get('id'),
                "product_type": target_product.get('product_type')
            }
        )
    
    async def _estimate_renovation_cost(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Estimate renovation costs based on room data and scope."""
        room_data = input_data.get("room_data", {})
        renovation_scope = input_data.get("renovation_scope", "refresh")
        
        prompt = f"""Estimate renovation costs for this room:

Room Details:
- Type: {room_data.get('room_type', 'unknown')}
- Dimensions: {room_data.get('length', 0)}ft x {room_data.get('width', 0)}ft
- Area: {room_data.get('area', 0)} sq ft
- Height: {room_data.get('height', 8)}ft

Current Condition:
- Materials: {self._format_materials(room_data.get('materials', []))}
- Fixtures: {self._format_fixtures(room_data.get('fixtures', []))}
- Products: {self._format_products(room_data.get('products', []))}

Renovation Scope: {renovation_scope}
(Options: refresh, moderate, full_renovation, luxury)

Please provide detailed cost estimate including:
1. Materials costs
2. Labor costs
3. Fixtures and products
4. Permits and fees (if applicable)
5. Contingency (10-20%)

Provide response as JSON with CAD pricing:
{{
  "scope": "{renovation_scope}",
  "breakdown": {{
    "materials": {{"low": 0, "mid": 0, "high": 0}},
    "labor": {{"low": 0, "mid": 0, "high": 0}},
    "fixtures": {{"low": 0, "mid": 0, "high": 0}},
    "products": {{"low": 0, "mid": 0, "high": 0}},
    "permits_fees": {{"low": 0, "mid": 0, "high": 0}},
    "contingency": {{"low": 0, "mid": 0, "high": 0}}
  }},
  "total": {{"low": 0, "mid": 0, "high": 0, "currency": "CAD"}},
  "timeline": {{"min_weeks": 0, "max_weeks": 0}},
  "itemized_list": [],
  "assumptions": [],
  "recommendations": []
}}
"""
        
        response_text = await self.gemini.generate_text(
            prompt=prompt,
            temperature=0.3
        )
        
        import json
        try:
            result = json.loads(response_text)
        except:
            result = {"raw_response": response_text}
        
        return AgentResponse(
            agent_name=self.name,
            agent_role=self.role,
            success=True,
            data=result,
            metadata={
                "room_id": room_data.get('id'),
                "scope": renovation_scope
            }
        )
    
    def _format_materials(self, materials: List[Dict]) -> str:
        """Format materials list for prompt."""
        if not materials:
            return "No materials data available"
        
        lines = []
        for mat in materials:
            lines.append(f"- {mat.get('category', 'unknown')}: {mat.get('material_type', 'unknown')} "
                        f"({mat.get('color', 'unknown')} {mat.get('finish', '')})")
        return "\n".join(lines)
    
    def _format_fixtures(self, fixtures: List[Dict]) -> str:
        """Format fixtures list for prompt."""
        if not fixtures:
            return "No fixtures data available"
        
        lines = []
        for fix in fixtures:
            lines.append(f"- {fix.get('fixture_type', 'unknown')}: {fix.get('style', 'unknown')} "
                        f"({fix.get('finish', 'unknown')})")
        return "\n".join(lines)
    
    def _format_products(self, products: List[Dict]) -> str:
        """Format products list for prompt."""
        if not products:
            return "No products data available"

        lines = []
        for prod in products:
            dims = prod.get('dimensions', {})
            dim_str = f"{dims.get('length', '?')}x{dims.get('width', '?')}x{dims.get('height', '?')}" if dims else "unknown"
            lines.append(f"- {prod.get('product_type', 'unknown')}: {dim_str} "
                        f"({prod.get('style', 'unknown')})")
        return "\n".join(lines)

    async def _comprehensive_analysis(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Provide comprehensive analysis and recommendations for a room."""
        room_data = input_data.get("room_data", {})

        prompt = f"""Provide a comprehensive analysis and recommendations for this room:

Room Details:
- Name: {room_data.get('name', 'Unknown')}
- Type: {room_data.get('room_type', 'unknown')}
- Dimensions: {room_data.get('length', 0)}ft x {room_data.get('width', 0)}ft
- Area: {room_data.get('area', 0)} sq ft
- Height: {room_data.get('height', 8)}ft

Current Materials:
{self._format_materials(room_data.get('materials', []))}

Current Fixtures:
{self._format_fixtures(room_data.get('fixtures', []))}

Current Products:
{self._format_products(room_data.get('products', []))}

Please provide:
1. Overall room assessment (condition, style, functionality)
2. Top 3 improvement recommendations with priorities
3. Material quantity estimates for common updates (paint, flooring)
4. Cost estimates for recommended improvements (low, mid, high)
5. Product recommendations that fit the space
6. Style consistency analysis
7. Maintenance recommendations

Provide response as JSON:
{{
  "overall_assessment": {{
    "condition_score": 0-100,
    "style_consistency": "excellent|good|fair|poor",
    "functionality_score": 0-100,
    "summary": "text"
  }},
  "top_recommendations": [
    {{
      "priority": 1,
      "category": "paint|flooring|fixtures|products",
      "recommendation": "text",
      "estimated_cost": {{"low": 0, "mid": 0, "high": 0, "currency": "CAD"}},
      "estimated_timeline": "text",
      "impact": "high|medium|low"
    }}
  ],
  "material_estimates": {{
    "paint": {{
      "quantity": 0,
      "unit": "gallons",
      "cost_range": {{"low": 0, "mid": 0, "high": 0}}
    }},
    "flooring": {{
      "quantity": 0,
      "unit": "sq_ft",
      "cost_range": {{"low": 0, "mid": 0, "high": 0}}
    }}
  }},
  "product_recommendations": [
    {{
      "product_type": "text",
      "recommended_dimensions": {{"length": 0, "width": 0, "height": 0}},
      "placement_suggestions": [],
      "style_match": "excellent|good|fair|poor",
      "estimated_cost": {{"low": 0, "mid": 0, "high": 0}}
    }}
  ],
  "style_analysis": {{
    "current_style": "text",
    "consistency_issues": [],
    "style_recommendations": []
  }},
  "maintenance_recommendations": [
    {{
      "item": "text",
      "frequency": "text",
      "priority": "high|medium|low",
      "estimated_cost": 0
    }}
  ]
}}
"""

        response_text = await self.gemini.generate_text(
            prompt=prompt,
            temperature=0.3
        )

        import json
        try:
            result = json.loads(response_text)
        except:
            result = {"raw_response": response_text}

        return AgentResponse(
            agent_name=self.name,
            agent_role=self.role,
            success=True,
            data=result,
            metadata={
                "room_id": room_data.get('id'),
                "analysis_type": "comprehensive"
            }
        )

    async def _suggest_style_match(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Suggest style-consistent materials and products."""
        room_data = input_data.get("room_data", {})
        style_preference = input_data.get("style_preference", "modern")
        focus_area = input_data.get("focus_area", "all")

        prompt = f"""Suggest style-consistent materials and products for this room:

Room Details:
- Type: {room_data.get('room_type', 'unknown')}
- Current Style: {room_data.get('style', 'unknown')}
- Target Style: {style_preference}
- Focus Area: {focus_area}

Current Materials:
{self._format_materials(room_data.get('materials', []))}

Current Fixtures:
{self._format_fixtures(room_data.get('fixtures', []))}

Please suggest:
1. Materials that match the target style
2. Fixtures that complement the style
3. Color palette recommendations
4. Products that fit the aesthetic
5. Style consistency tips

Provide response as JSON:
{{
  "target_style": "{style_preference}",
  "material_suggestions": [
    {{
      "category": "flooring|wall|ceiling|countertop|cabinetry|backsplash",
      "material_type": "text",
      "color": "text",
      "finish": "text",
      "why_it_works": "text",
      "estimated_cost_per_unit": 0
    }}
  ],
  "fixture_suggestions": [
    {{
      "fixture_type": "text",
      "style": "text",
      "finish": "text",
      "why_it_works": "text",
      "estimated_cost": {{"low": 0, "mid": 0, "high": 0}}
    }}
  ],
  "color_palette": {{
    "primary": [],
    "secondary": [],
    "accent": [],
    "rationale": "text"
  }},
  "product_suggestions": [
    {{
      "product_type": "text",
      "style_characteristics": [],
      "why_it_works": "text"
    }}
  ],
  "style_tips": []
}}
"""

        response_text = await self.gemini.generate_text(
            prompt=prompt,
            temperature=0.4  # Slightly higher for creative suggestions
        )

        import json
        try:
            result = json.loads(response_text)
        except:
            result = {"raw_response": response_text}

        return AgentResponse(
            agent_name=self.name,
            agent_role=self.role,
            success=True,
            data=result,
            metadata={
                "room_id": room_data.get('id'),
                "target_style": style_preference,
                "focus_area": focus_area
            }
        )

