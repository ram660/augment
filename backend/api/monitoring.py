"""
Monitoring and health check endpoints.

Provides:
- Health check for all services
- Analytics dashboard data
- Cost monitoring data
- System metrics
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.services.cache_service import get_cache_service
from backend.services.analytics_service import get_analytics_service
from backend.services.cost_tracking_service import get_cost_tracking_service
from backend.services.event_bus import get_event_bus
from backend.services.feature_flags import get_feature_flag_service
from backend.services.journey_manager import get_journey_manager
from backend.services.persona_service import get_persona_service
from backend.services.template_service import get_template_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for all services.
    
    Returns:
        Health status for each service
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    overall_healthy = True
    
    # Check cache service
    try:
        cache_service = get_cache_service()
        stats = cache_service.get_stats()
        health_status["services"]["cache"] = {
            "status": "healthy",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Cache service health check failed: {e}")
        health_status["services"]["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check analytics service
    try:
        analytics_service = get_analytics_service()
        metrics = analytics_service.get_metrics_summary()
        health_status["services"]["analytics"] = {
            "status": "healthy",
            "metrics_count": len(metrics)
        }
    except Exception as e:
        logger.error(f"Analytics service health check failed: {e}")
        health_status["services"]["analytics"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check cost tracking service
    try:
        cost_service = get_cost_tracking_service()
        daily_cost = cost_service.get_aggregated_costs("daily")
        health_status["services"]["cost_tracking"] = {
            "status": "healthy",
            "daily_cost": daily_cost
        }
    except Exception as e:
        logger.error(f"Cost tracking service health check failed: {e}")
        health_status["services"]["cost_tracking"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check event bus
    try:
        event_bus = get_event_bus()
        event_count = len(event_bus.get_event_history())
        health_status["services"]["event_bus"] = {
            "status": "healthy",
            "event_count": event_count
        }
    except Exception as e:
        logger.error(f"Event bus health check failed: {e}")
        health_status["services"]["event_bus"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check feature flags
    try:
        feature_flag_service = get_feature_flag_service()
        flags = feature_flag_service.get_all_flags()
        health_status["services"]["feature_flags"] = {
            "status": "healthy",
            "flag_count": len(flags)
        }
    except Exception as e:
        logger.error(f"Feature flag service health check failed: {e}")
        health_status["services"]["feature_flags"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check journey manager
    try:
        journey_manager = get_journey_manager()
        templates = journey_manager.get_all_templates()
        health_status["services"]["journey_manager"] = {
            "status": "healthy",
            "template_count": len(templates)
        }
    except Exception as e:
        logger.error(f"Journey manager health check failed: {e}")
        health_status["services"]["journey_manager"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check persona service
    try:
        persona_service = get_persona_service()
        personas = persona_service.get_all_personas()
        health_status["services"]["persona"] = {
            "status": "healthy",
            "persona_count": len(personas)
        }
    except Exception as e:
        logger.error(f"Persona service health check failed: {e}")
        health_status["services"]["persona"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check template service
    try:
        template_service = get_template_service()
        templates = template_service.get_all_templates()
        health_status["services"]["template"] = {
            "status": "healthy",
            "template_count": len(templates)
        }
    except Exception as e:
        logger.error(f"Template service health check failed: {e}")
        health_status["services"]["template"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Set overall status
    health_status["status"] = "healthy" if overall_healthy else "degraded"
    
    return health_status


@router.get("/analytics/dashboard")
async def get_analytics_dashboard() -> Dict[str, Any]:
    """
    Get analytics dashboard data.
    
    Returns:
        Analytics metrics for dashboard visualization
    """
    try:
        analytics_service = get_analytics_service()
        
        # Get metrics summary
        metrics_summary = analytics_service.get_metrics_summary()
        
        # Get user journey metrics
        journey_metrics = analytics_service.get_journey_metrics()
        
        # Get feature usage
        feature_usage = analytics_service.get_feature_usage()
        
        # Get performance metrics
        performance_metrics = analytics_service.get_performance_metrics()
        
        # Get conversion funnels
        funnels = []
        for funnel_name in ["kitchen_renovation", "diy_project", "contractor_brief"]:
            funnel_data = analytics_service.get_conversion_funnel(funnel_name)
            if funnel_data:
                funnels.append({
                    "name": funnel_name,
                    "data": funnel_data
                })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_summary": metrics_summary,
            "journey_metrics": journey_metrics,
            "feature_usage": feature_usage,
            "performance_metrics": performance_metrics,
            "conversion_funnels": funnels
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics dashboard: {str(e)}"
        )


@router.get("/cost/dashboard")
async def get_cost_dashboard() -> Dict[str, Any]:
    """
    Get cost monitoring dashboard data.
    
    Returns:
        Cost metrics for dashboard visualization
    """
    try:
        cost_service = get_cost_tracking_service()
        
        # Get aggregated costs
        daily_cost = cost_service.get_aggregated_costs("daily")
        weekly_cost = cost_service.get_aggregated_costs("weekly")
        monthly_cost = cost_service.get_aggregated_costs("monthly")
        
        # Get budget status
        budget_status = cost_service.check_budget_alerts()
        
        # Get cost optimization recommendations
        recommendations = cost_service.get_cost_optimization_recommendations()
        
        # Get recent cost entries (last 100)
        recent_costs = cost_service.get_recent_costs(limit=100)
        
        # Calculate cost breakdown by operation type
        cost_by_operation = {}
        for cost_entry in recent_costs:
            op_type = cost_entry.get("operation_type", "unknown")
            cost = cost_entry.get("cost", 0)
            cost_by_operation[op_type] = cost_by_operation.get(op_type, 0) + cost
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "aggregated_costs": {
                "daily": daily_cost,
                "weekly": weekly_cost,
                "monthly": monthly_cost
            },
            "budget_status": budget_status,
            "cost_by_operation": cost_by_operation,
            "recommendations": recommendations,
            "recent_costs": recent_costs[:20]  # Return only last 20 for dashboard
        }
        
    except Exception as e:
        logger.error(f"Failed to get cost dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cost dashboard: {str(e)}"
        )


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Cache hit/miss rates and other metrics
    """
    try:
        cache_service = get_cache_service()
        stats = cache_service.get_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )

