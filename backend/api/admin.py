"""Admin API endpoints for monitoring and management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os

from backend.database import get_async_db
from backend.models.user import User
from backend.models.message_feedback import MessageFeedback
from backend.api.auth import get_current_user, get_current_user_optional
from backend.integrations.agentlightning.store import get_lightning_store
from backend.integrations.agentlightning.tracker import AgentTracker

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# Simple admin check - in production, use proper role-based access control
async def require_admin_optional(current_user: Optional[User] = Depends(get_current_user_optional)) -> Optional[User]:
    """
    Require admin privileges (optional in development).

    In development mode (ENVIRONMENT != 'production'), allows access without authentication.
    In production, requires authentication and admin role.
    """
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "production":
        # In production, require authentication
        if not current_user:
            raise HTTPException(status_code=403, detail="Admin access required")
        # TODO: Add proper admin role check
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Admin privileges required")

    # In development, allow access without authentication
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin privileges.

    In production this enforces that a valid authenticated user is present.
    In development it still requires a user but is less strict about roles (TODO: add role checks).
    """
    environment = os.getenv("ENVIRONMENT", "development")

    if not current_user:
        # No authenticated user provided
        raise HTTPException(status_code=403, detail="Admin access required")

    if environment == "production":
        # TODO: enforce a proper admin role check when roles are implemented on User
        # if not getattr(current_user, "is_admin", False):
        #     raise HTTPException(status_code=403, detail="Admin privileges required")
        pass

    return current_user


@router.get("/agent-lightning/stats")
async def get_agent_lightning_stats(
    agent_name: str = "chat_agent",
    current_user: Optional[User] = Depends(require_admin_optional)
) -> Dict[str, Any]:
    """
    Get Agent Lightning statistics for monitoring.
    
    Returns:
        - Total interactions tracked
        - Average reward score
        - Reward distribution
        - Recent performance trends
    """
    store = get_lightning_store()
    
    # Get basic stats from LightningStore
    stats = store.get_statistics(agent_name)
    
    return {
        "agent_name": agent_name,
        "lightning_store": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/feedback/stats")
async def get_feedback_stats(
    days: int = 7,
    current_user: Optional[User] = Depends(require_admin_optional),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get feedback statistics from the database.
    
    Args:
        days: Number of days to look back (default: 7)
    
    Returns:
        - Total feedback count
        - Feedback type distribution
        - Average reward by type
        - Recent trends
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total feedback count
    total_query = select(func.count(MessageFeedback.id)).where(
        MessageFeedback.created_at >= cutoff_date
    )
    total_result = await db.execute(total_query)
    total_count = total_result.scalar() or 0
    
    # Feedback by type
    type_query = select(
        MessageFeedback.feedback_type,
        func.count(MessageFeedback.id).label('count'),
        func.avg(MessageFeedback.reward_score).label('avg_reward')
    ).where(
        MessageFeedback.created_at >= cutoff_date
    ).group_by(MessageFeedback.feedback_type)
    
    type_result = await db.execute(type_query)
    type_stats = []
    for row in type_result:
        type_stats.append({
            "feedback_type": row.feedback_type,
            "count": row.count,
            "avg_reward": float(row.avg_reward) if row.avg_reward else 0.0
        })
    
    # Overall average reward
    avg_query = select(func.avg(MessageFeedback.reward_score)).where(
        MessageFeedback.created_at >= cutoff_date
    )
    avg_result = await db.execute(avg_query)
    avg_reward = avg_result.scalar() or 0.0
    
    # Daily trends (last 7 days)
    daily_query = select(
        func.date(MessageFeedback.created_at).label('date'),
        func.count(MessageFeedback.id).label('count'),
        func.avg(MessageFeedback.reward_score).label('avg_reward')
    ).where(
        MessageFeedback.created_at >= cutoff_date
    ).group_by(
        func.date(MessageFeedback.created_at)
    ).order_by(desc('date'))
    
    daily_result = await db.execute(daily_query)
    daily_trends = []
    for row in daily_result:
        daily_trends.append({
            "date": row.date.isoformat() if row.date else None,
            "count": row.count,
            "avg_reward": float(row.avg_reward) if row.avg_reward else 0.0
        })
    
    return {
        "period_days": days,
        "total_feedback": total_count,
        "avg_reward": float(avg_reward),
        "by_type": type_stats,
        "daily_trends": daily_trends,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/feedback/recent")
async def get_recent_feedback(
    limit: int = 20,
    current_user: Optional[User] = Depends(require_admin_optional),
    db: AsyncSession = Depends(get_async_db)
) -> List[Dict[str, Any]]:
    """
    Get recent feedback submissions.
    
    Args:
        limit: Maximum number of feedback items to return (default: 20)
    
    Returns:
        List of recent feedback with details
    """
    query = select(MessageFeedback).order_by(
        desc(MessageFeedback.created_at)
    ).limit(limit)
    
    result = await db.execute(query)
    feedback_items = result.scalars().all()
    
    return [
        {
            "id": str(item.id),
            "message_id": str(item.message_id),
            "conversation_id": str(item.conversation_id) if item.conversation_id else None,
            "feedback_type": item.feedback_type,
            "rating": item.rating,
            "reward_score": item.reward_score,
            "helpful": item.helpful,
            "accurate": item.accurate,
            "complete": item.complete,
            "comment": item.comment,
            "created_at": item.created_at.isoformat()
        }
        for item in feedback_items
    ]


@router.get("/dashboard")
async def get_dashboard_summary(
    current_user: Optional[User] = Depends(require_admin_optional),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard summary combining all metrics.
    
    Returns:
        - Agent Lightning stats
        - Feedback stats (last 7 days)
        - Performance indicators
        - Data collection progress
    """
    # Get Agent Lightning stats
    store = get_lightning_store()
    lightning_stats = store.get_statistics("chat_agent")
    
    # Get feedback stats (last 7 days)
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    
    total_query = select(func.count(MessageFeedback.id)).where(
        MessageFeedback.created_at >= cutoff_date
    )
    total_result = await db.execute(total_query)
    total_feedback = total_result.scalar() or 0
    
    avg_query = select(func.avg(MessageFeedback.reward_score)).where(
        MessageFeedback.created_at >= cutoff_date
    )
    avg_result = await db.execute(avg_query)
    avg_reward = avg_result.scalar() or 0.0
    
    # Feedback submission rate (feedback / total interactions)
    total_interactions = lightning_stats.get("total_interactions", 0)
    submission_rate = (total_feedback / total_interactions * 100) if total_interactions > 0 else 0.0
    
    # Reward distribution
    excellent_query = select(func.count(MessageFeedback.id)).where(
        MessageFeedback.created_at >= cutoff_date,
        MessageFeedback.reward_score >= 0.8
    )
    excellent_result = await db.execute(excellent_query)
    excellent_count = excellent_result.scalar() or 0
    
    good_query = select(func.count(MessageFeedback.id)).where(
        MessageFeedback.created_at >= cutoff_date,
        MessageFeedback.reward_score >= 0.5,
        MessageFeedback.reward_score < 0.8
    )
    good_result = await db.execute(good_query)
    good_count = good_result.scalar() or 0
    
    poor_query = select(func.count(MessageFeedback.id)).where(
        MessageFeedback.created_at >= cutoff_date,
        MessageFeedback.reward_score < 0.5
    )
    poor_result = await db.execute(poor_query)
    poor_count = poor_result.scalar() or 0
    
    # Phase 2 progress (goal: 1000 interactions, 200 feedback)
    phase2_progress = {
        "interactions": {
            "current": total_interactions,
            "goal": 1000,
            "progress_pct": min(100, (total_interactions / 1000 * 100)) if total_interactions else 0
        },
        "feedback": {
            "current": total_feedback,
            "goal": 200,
            "progress_pct": min(100, (total_feedback / 200 * 100)) if total_feedback else 0
        },
        "submission_rate": {
            "current": submission_rate,
            "goal": 20.0,
            "on_track": submission_rate >= 20.0
        }
    }
    
    return {
        "agent_lightning": lightning_stats,
        "feedback_summary": {
            "total_feedback_7d": total_feedback,
            "avg_reward_7d": float(avg_reward),
            "submission_rate_pct": submission_rate,
            "distribution": {
                "excellent": excellent_count,  # >= 0.8
                "good": good_count,  # 0.5 - 0.8
                "poor": poor_count  # < 0.5
            }
        },
        "phase2_progress": phase2_progress,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/agent-lightning/clear")
async def clear_agent_lightning_data(
    agent_name: str = "chat_agent",
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """
    Clear Agent Lightning data for an agent (use with caution!).
    
    This is useful for testing or resetting data collection.
    """
    store = get_lightning_store()
    
    if not store.is_enabled():
        raise HTTPException(status_code=503, detail="Agent Lightning is not enabled")
    
    try:
        store.clear_data(agent_name)
        return {
            "status": "success",
            "message": f"Cleared data for agent: {agent_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")

