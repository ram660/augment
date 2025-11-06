"""
Product API endpoints for HomeView AI.

Provides product catalog, matching, and recommendation endpoints.
"""

import logging
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from backend.api.auth import get_current_user
from backend.models.user import User
from backend.models.product import ProductCatalog, ProductMatch, ProductCategory
from backend.models.home import Room
from backend.models.base import get_async_db
from backend.agents.intelligence.product_matching_agent import ProductMatchingAgent

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/products", tags=["products"])


class ProductCreateRequest(BaseModel):
    """Product creation request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    brand: Optional[str] = None
    category: ProductCategory
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None
    price: Optional[float] = None
    suitable_rooms: List[str] = []
    style_tags: List[str] = []


class ProductResponse(BaseModel):
    """Product response."""
    id: str
    name: str
    description: Optional[str]
    brand: Optional[str]
    category: str
    dimensions: dict
    price: Optional[float]
    in_stock: bool
    suitable_rooms: List[str]
    style_tags: List[str]


class ProductMatchRequest(BaseModel):
    """Product match request."""
    room_id: str
    category: Optional[ProductCategory] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    style_preference: Optional[str] = None


class ProductMatchResponse(BaseModel):
    """Product match response."""
    product_id: str
    product_name: str
    fit_score: float
    style_score: float
    overall_score: float
    will_fit: bool
    is_recommended: bool
    recommendation_reason: Optional[str]


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: ProductCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new product in the catalog.
    
    Args:
        request: Product creation request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created product
    """
    try:
        product = ProductCatalog(
            id=uuid4(),
            name=request.name,
            description=request.description,
            brand=request.brand,
            category=request.category,
            width=request.width,
            height=request.height,
            depth=request.depth,
            price=request.price,
            suitable_rooms=request.suitable_rooms,
            style_tags=request.style_tags,
            in_stock=True
        )
        
        db.add(product)
        await db.commit()
        await db.refresh(product)
        
        return ProductResponse(
            id=str(product.id),
            name=product.name,
            description=product.description,
            brand=product.brand,
            category=product.category.value,
            dimensions={
                "width": product.width,
                "height": product.height,
                "depth": product.depth
            },
            price=product.price,
            in_stock=product.in_stock,
            suitable_rooms=product.suitable_rooms or [],
            style_tags=product.style_tags or []
        )
    
    except Exception as e:
        logger.error(f"Create product error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    category: Optional[ProductCategory] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    style: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db)
):
    """
    List products with optional filters.
    
    Args:
        category: Filter by category
        min_price: Minimum price
        max_price: Maximum price
        style: Filter by style tag
        limit: Maximum number of products
        offset: Offset for pagination
        db: Database session
        
    Returns:
        List of products
    """
    try:
        query = select(ProductCatalog)
        
        if category:
            query = query.where(ProductCatalog.category == category)
        if min_price is not None:
            query = query.where(ProductCatalog.price >= min_price)
        if max_price is not None:
            query = query.where(ProductCatalog.price <= max_price)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        # Filter by style if provided
        if style:
            products = [p for p in products if style.lower() in [s.lower() for s in (p.style_tags or [])]]
        
        return [
            ProductResponse(
                id=str(p.id),
                name=p.name,
                description=p.description,
                brand=p.brand,
                category=p.category.value,
                dimensions={
                    "width": p.width,
                    "height": p.height,
                    "depth": p.depth
                },
                price=p.price,
                in_stock=p.in_stock,
                suitable_rooms=p.suitable_rooms or [],
                style_tags=p.style_tags or []
            )
            for p in products
        ]
    
    except Exception as e:
        logger.error(f"List products error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list products"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get product by ID.
    
    Args:
        product_id: Product ID
        db: Database session
        
    Returns:
        Product details
    """
    try:
        product = await db.get(ProductCatalog, UUID(product_id))
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return ProductResponse(
            id=str(product.id),
            name=product.name,
            description=product.description,
            brand=product.brand,
            category=product.category.value,
            dimensions={
                "width": product.width,
                "height": product.height,
                "depth": product.depth
            },
            price=product.price,
            in_stock=product.in_stock,
            suitable_rooms=product.suitable_rooms or [],
            style_tags=product.style_tags or []
        )
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get product error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get product"
        )


@router.post("/match", response_model=List[ProductMatchResponse])
async def match_products_to_room(
    request: ProductMatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Match products to a room based on dimensions and style.
    
    Args:
        request: Product match request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of matched products with scores
    """
    try:
        # Get room
        room = await db.get(Room, UUID(request.room_id))
        
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found"
            )
        
        # Get products
        query = select(ProductCatalog).where(ProductCatalog.in_stock == True)
        
        if request.category:
            query = query.where(ProductCatalog.category == request.category)
        if request.budget_min:
            query = query.where(ProductCatalog.price >= request.budget_min)
        if request.budget_max:
            query = query.where(ProductCatalog.price <= request.budget_max)
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        # Initialize product matching agent
        agent = ProductMatchingAgent()
        
        # Prepare products for matching
        products_data = [
            {
                "id": str(p.id),
                "name": p.name,
                "category": p.category.value,
                "dimensions": {
                    "width": p.width or 0,
                    "height": p.height or 0,
                    "depth": p.depth or 0
                },
                "price": p.price or 0,
                "style_tags": p.style_tags or [],
                "clearance_required": p.clearance_required or 0
            }
            for p in products
        ]
        
        # Match products
        match_result = await agent.process({
            "action": "match_products",
            "request": {
                "room_id": request.room_id,
                "room_dimensions": {
                    "width": room.width_ft or 10,
                    "length": room.length_ft or 10,
                    "height": room.height_ft or 8
                },
                "room_type": room.room_type.value if room.room_type else "living_room",
                "room_style": request.style_preference,
                "budget_min": request.budget_min,
                "budget_max": request.budget_max
            },
            "products": products_data
        })
        
        if not match_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=match_result.error or "Product matching failed"
            )
        
        matches = match_result.data.get("matches", [])
        
        return [
            ProductMatchResponse(
                product_id=m["product_id"],
                product_name=m["product_name"],
                fit_score=m["fit_analysis"]["dimension_fit_score"],
                style_score=m["style_match_score"],
                overall_score=m["overall_score"],
                will_fit=m["fit_analysis"]["will_fit"],
                is_recommended=m["is_recommended"],
                recommendation_reason=m.get("recommendation_reason")
            )
            for m in matches
        ]
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product matching error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to match products"
        )

