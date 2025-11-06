"""
Intelligence API - Smart recommendations and estimations based on home data.

Endpoints:
- POST /api/intelligence/material-quantity - Calculate material quantities
- POST /api/intelligence/product-fit - Check if product fits in room
- POST /api/intelligence/cost-estimate - Estimate renovation costs
- POST /api/intelligence/style-suggestions - Get style-consistent suggestions
- POST /api/intelligence/comprehensive - Get all recommendations
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_async_db
from backend.models import Room, Material, Fixture, Product
from backend.agents.intelligence.smart_recommendations_agent import SmartRecommendationsAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


# Request/Response Models
class MaterialQuantityRequest(BaseModel):
    """Request for material quantity calculation."""
    room_id: UUID
    material_type: str = Field(..., description="Type of material (paint, flooring, tile, etc.)")
    include_cost_estimate: bool = Field(default=True, description="Include cost estimates")


class ProductFitRequest(BaseModel):
    """Request for product fit check."""
    room_id: UUID
    product_type: str = Field(..., description="Type of product (sofa, table, bed, etc.)")
    product_dimensions: dict = Field(..., description="Product dimensions {length, width, height} in feet")
    product_description: Optional[str] = Field(None, description="Additional product details")


class CostEstimateRequest(BaseModel):
    """Request for renovation cost estimate."""
    room_id: UUID
    renovation_scope: str = Field(
        default="refresh",
        description="Scope: refresh, moderate, full_renovation, luxury"
    )
    include_labor: bool = Field(default=True, description="Include labor costs")
    include_timeline: bool = Field(default=True, description="Include timeline estimate")


class StyleSuggestionsRequest(BaseModel):
    """Request for style-consistent suggestions."""
    room_id: UUID
    target_style: Optional[str] = Field(None, description="Desired style (modern, traditional, etc.)")
    focus_area: Optional[str] = Field(None, description="Focus area (walls, flooring, fixtures, etc.)")


class ComprehensiveAnalysisRequest(BaseModel):
    """Request for comprehensive room analysis."""
    room_id: UUID
    include_all: bool = Field(default=True, description="Include all analysis types")


# Helper function to load room data
async def load_room_data(room_id: UUID, db: AsyncSession) -> dict:
    """Load complete room data including materials, fixtures, and products."""
    
    # Load room
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    
    # Load materials
    result = await db.execute(select(Material).where(Material.room_id == room_id))
    materials = result.scalars().all()
    
    # Load fixtures
    result = await db.execute(select(Fixture).where(Fixture.room_id == room_id))
    fixtures = result.scalars().all()
    
    # Load products
    result = await db.execute(select(Product).where(Product.room_id == room_id))
    products = result.scalars().all()
    
    return {
        "id": str(room.id),
        "name": room.name,
        "room_type": room.room_type,
        "floor_level": room.floor_level,
        "length": room.length,
        "width": room.width,
        "height": room.height or 8.0,  # Default ceiling height
        "area": room.area,
        "materials": [
            {
                "id": str(m.id),
                "category": m.category.value if hasattr(m.category, 'value') else str(m.category),
                "material_type": m.material_type,
                "brand": m.brand,
                "color": m.color,
                "finish": m.finish,
                "condition": m.condition
            }
            for m in materials
        ],
        "fixtures": [
            {
                "id": str(f.id),
                "fixture_type": f.fixture_type,
                "brand": f.brand,
                "style": f.style,
                "finish": f.finish,
                "location": f.location,
                "condition": f.condition
            }
            for f in fixtures
        ],
        "products": [
            {
                "id": str(p.id),
                "product_type": p.product_type,
                "product_category": p.product_category,
                "brand": p.brand,
                "style": p.style,
                "color": p.color,
                "dimensions": p.dimensions,
                "condition": p.condition
            }
            for p in products
        ]
    }


# Endpoints
@router.post("/material-quantity")
async def calculate_material_quantity(
    request: MaterialQuantityRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Calculate material quantities needed for a room.
    
    Returns:
    - Total quantity needed (with waste factor)
    - Number of units to purchase
    - Cost estimate (if requested)
    - Special considerations
    """
    try:
        # Load room data
        room_data = await load_room_data(request.room_id, db)
        
        # Initialize agent
        agent = SmartRecommendationsAgent()
        
        # Get recommendations
        response = await agent.process({
            "recommendation_type": "material_quantity",
            "room_data": room_data,
            "target_material": request.material_type
        })
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        
        return {
            "room_id": str(request.room_id),
            "room_name": room_data["name"],
            "room_type": room_data["room_type"],
            "material_type": request.material_type,
            "calculations": response.data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating material quantity: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/product-fit")
async def check_product_fit(
    request: ProductFitRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Check if a product will fit in the room.
    
    Returns:
    - Fit analysis (yes/no with reasoning)
    - Recommended placement locations
    - Clearance requirements
    - Alternative sizes if needed
    """
    try:
        # Load room data
        room_data = await load_room_data(request.room_id, db)
        
        # Initialize agent
        agent = SmartRecommendationsAgent()
        
        # Get recommendations
        response = await agent.process({
            "recommendation_type": "product_fit",
            "room_data": room_data,
            "target_product": {
                "product_type": request.product_type,
                "dimensions": request.product_dimensions,
                "description": request.product_description
            }
        })
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        
        return {
            "room_id": str(request.room_id),
            "room_name": room_data["name"],
            "room_dimensions": {
                "length": room_data["length"],
                "width": room_data["width"],
                "area": room_data["area"]
            },
            "product": {
                "type": request.product_type,
                "dimensions": request.product_dimensions
            },
            "fit_analysis": response.data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking product fit: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cost-estimate")
async def estimate_renovation_cost(
    request: CostEstimateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Estimate renovation costs for a room.
    
    Returns:
    - Cost breakdown (materials, labor, fixtures, etc.)
    - Total cost range (low, mid, high)
    - Timeline estimate
    - Itemized list
    """
    try:
        # Load room data
        room_data = await load_room_data(request.room_id, db)
        
        # Initialize agent
        agent = SmartRecommendationsAgent()
        
        # Get recommendations
        response = await agent.process({
            "recommendation_type": "cost_estimate",
            "room_data": room_data,
            "renovation_scope": request.renovation_scope
        })
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        
        return {
            "room_id": str(request.room_id),
            "room_name": room_data["name"],
            "room_type": room_data["room_type"],
            "room_area": room_data["area"],
            "renovation_scope": request.renovation_scope,
            "cost_estimate": response.data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating cost: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/style-suggestions")
async def get_style_suggestions(
    request: StyleSuggestionsRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get style-consistent material and product suggestions.
    
    Returns:
    - Suggested materials that match the style
    - Suggested products
    - Color palette recommendations
    - Style consistency analysis
    """
    try:
        # Load room data
        room_data = await load_room_data(request.room_id, db)
        
        # Initialize agent
        agent = SmartRecommendationsAgent()
        
        # Get recommendations
        response = await agent.process({
            "recommendation_type": "style_match",
            "room_data": room_data,
            "style_preference": request.target_style,
            "focus_area": request.focus_area
        })
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        
        return {
            "room_id": str(request.room_id),
            "room_name": room_data["name"],
            "current_style": room_data.get("style", "unknown"),
            "target_style": request.target_style,
            "suggestions": response.data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting style suggestions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comprehensive")
async def comprehensive_analysis(
    request: ComprehensiveAnalysisRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get comprehensive analysis and recommendations for a room.
    
    Returns all available intelligence:
    - Material quantity calculations
    - Product fit analysis
    - Cost estimates
    - Style suggestions
    - Maintenance recommendations
    """
    try:
        # Load room data
        room_data = await load_room_data(request.room_id, db)
        
        # Initialize agent
        agent = SmartRecommendationsAgent()
        
        # Get comprehensive recommendations
        response = await agent.process({
            "recommendation_type": "comprehensive",
            "room_data": room_data
        })
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        
        return {
            "room_id": str(request.room_id),
            "room_name": room_data["name"],
            "room_type": room_data["room_type"],
            "room_dimensions": {
                "length": room_data["length"],
                "width": room_data["width"],
                "height": room_data["height"],
                "area": room_data["area"]
            },
            "analysis": response.data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

