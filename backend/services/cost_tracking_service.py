"""
Cost tracking service for monitoring API usage and expenses.

Tracks costs for:
- Gemini API (text generation, vision, embeddings, image generation)
- DeepSeek API (vision)
- Google Search Grounding
- Other external services

Features:
- Per-call cost tracking
- Budget alerts
- Cost aggregation by service, user, project
- Cost optimization recommendations
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class CostEntry:
    """Single cost entry for an API call."""
    timestamp: datetime
    service: str  # gemini, deepseek, google_search, etc.
    operation: str  # generate_text, analyze_image, embed, etc.
    cost_usd: float
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetAlert:
    """Budget alert configuration."""
    name: str
    threshold_usd: float
    period: str  # daily, weekly, monthly
    alert_channels: List[str]  # email, slack, webhook
    enabled: bool = True


class CostTrackingService:
    """
    Service for tracking and monitoring API costs.
    
    Features:
    - Real-time cost tracking
    - Budget alerts
    - Cost aggregation and reporting
    - Cost optimization recommendations
    """
    
    # Cost per operation (USD)
    COST_TABLE = {
        # Gemini costs (per 1M tokens for text, per image for vision/generation)
        "gemini_generate_text_flash": 0.000075,  # $0.075 per 1M input tokens
        "gemini_generate_text_pro": 0.00125,     # $1.25 per 1M input tokens
        "gemini_analyze_image": 0.25,            # $0.25 per image
        "gemini_generate_image": 0.04,           # $0.04 per image
        "gemini_embed": 0.00001,                 # $0.01 per 1M tokens
        
        # DeepSeek costs
        "deepseek_analyze_image": 0.03,          # $0.03 per image (85% cheaper)
        
        # Google Search Grounding
        "google_search_grounding": 0.035,        # $35 per 1000 queries
        
        # YouTube search (via grounding)
        "youtube_search": 0.035,                 # Same as grounding
        
        # Contractor search (Google Maps)
        "contractor_search": 0.05,               # $50 per 1000 queries
    }
    
    def __init__(self):
        self.cost_entries: List[CostEntry] = []
        self.budget_alerts: List[BudgetAlert] = []
        self.alert_history: List[Dict[str, Any]] = []
        
        # Aggregated costs cache
        self._daily_costs: Dict[str, float] = defaultdict(float)
        self._weekly_costs: Dict[str, float] = defaultdict(float)
        self._monthly_costs: Dict[str, float] = defaultdict(float)
        
        # Load default budget alerts
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Setup default budget alerts."""
        self.budget_alerts = [
            BudgetAlert(
                name="Daily Budget",
                threshold_usd=50.0,
                period="daily",
                alert_channels=["email", "slack"]
            ),
            BudgetAlert(
                name="Weekly Budget",
                threshold_usd=300.0,
                period="weekly",
                alert_channels=["email"]
            ),
            BudgetAlert(
                name="Monthly Budget",
                threshold_usd=1000.0,
                period="monthly",
                alert_channels=["email", "slack"]
            )
        ]
    
    def track_cost(
        self,
        service: str,
        operation: str,
        cost_usd: Optional[float] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Track cost for an API call.
        
        Args:
            service: Service name (gemini, deepseek, etc.)
            operation: Operation name (generate_text, analyze_image, etc.)
            cost_usd: Explicit cost in USD (if None, uses cost table)
            user_id: User who triggered the call
            project_id: Project/home ID
            metadata: Additional metadata (tokens, model, etc.)
            
        Returns:
            Cost in USD
        """
        # Calculate cost if not provided
        if cost_usd is None:
            cost_key = f"{service}_{operation}"
            cost_usd = self.COST_TABLE.get(cost_key, 0.0)
            
            # Adjust for token count if provided
            if "tokens" in (metadata or {}):
                tokens = metadata["tokens"]
                # Cost table is per 1M tokens, adjust
                cost_usd = cost_usd * (tokens / 1_000_000)
        
        # Create cost entry
        entry = CostEntry(
            timestamp=datetime.utcnow(),
            service=service,
            operation=operation,
            cost_usd=cost_usd,
            user_id=user_id,
            project_id=project_id,
            metadata=metadata or {}
        )
        
        self.cost_entries.append(entry)
        
        # Update aggregated costs
        self._update_aggregated_costs(entry)
        
        # Check budget alerts
        self._check_budget_alerts()
        
        logger.info(
            f"Cost tracked: {service}.{operation} = ${cost_usd:.4f} | "
            f"User: {user_id} | Project: {project_id}"
        )
        
        return cost_usd
    
    def _update_aggregated_costs(self, entry: CostEntry):
        """Update aggregated cost caches."""
        today = entry.timestamp.date().isoformat()
        week = entry.timestamp.isocalendar()[:2]  # (year, week)
        month = entry.timestamp.strftime("%Y-%m")
        
        self._daily_costs[today] += entry.cost_usd
        self._weekly_costs[str(week)] += entry.cost_usd
        self._monthly_costs[month] += entry.cost_usd
    
    def _check_budget_alerts(self):
        """Check if any budget thresholds are exceeded."""
        now = datetime.utcnow()
        
        for alert in self.budget_alerts:
            if not alert.enabled:
                continue
            
            # Get current spend for period
            if alert.period == "daily":
                current_spend = self._daily_costs.get(now.date().isoformat(), 0.0)
            elif alert.period == "weekly":
                week = now.isocalendar()[:2]
                current_spend = self._weekly_costs.get(str(week), 0.0)
            elif alert.period == "monthly":
                month = now.strftime("%Y-%m")
                current_spend = self._monthly_costs.get(month, 0.0)
            else:
                continue
            
            # Check threshold
            if current_spend >= alert.threshold_usd:
                self._trigger_alert(alert, current_spend)
    
    def _trigger_alert(self, alert: BudgetAlert, current_spend: float):
        """Trigger a budget alert."""
        alert_data = {
            "alert_name": alert.name,
            "threshold_usd": alert.threshold_usd,
            "current_spend_usd": current_spend,
            "period": alert.period,
            "timestamp": datetime.utcnow().isoformat(),
            "exceeded_by_usd": current_spend - alert.threshold_usd,
            "exceeded_by_percent": ((current_spend / alert.threshold_usd) - 1) * 100
        }
        
        # Check if we already alerted for this period
        recent_alerts = [
            a for a in self.alert_history
            if a["alert_name"] == alert.name and
            datetime.fromisoformat(a["timestamp"]) > datetime.utcnow() - timedelta(hours=1)
        ]
        
        if recent_alerts:
            return  # Don't spam alerts
        
        self.alert_history.append(alert_data)
        
        logger.warning(
            f"BUDGET ALERT: {alert.name} exceeded! "
            f"Threshold: ${alert.threshold_usd:.2f}, "
            f"Current: ${current_spend:.2f} "
            f"({alert_data['exceeded_by_percent']:.1f}% over)"
        )
        
        # TODO: Send actual alerts via email/Slack
        # For now, just log
    
    def get_costs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        service: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get cost report with filters.
        
        Args:
            start_date: Start date for report
            end_date: End date for report
            service: Filter by service
            user_id: Filter by user
            project_id: Filter by project
            
        Returns:
            Cost report with totals and breakdowns
        """
        # Filter entries
        filtered_entries = self.cost_entries
        
        if start_date:
            filtered_entries = [e for e in filtered_entries if e.timestamp >= start_date]
        if end_date:
            filtered_entries = [e for e in filtered_entries if e.timestamp <= end_date]
        if service:
            filtered_entries = [e for e in filtered_entries if e.service == service]
        if user_id:
            filtered_entries = [e for e in filtered_entries if e.user_id == user_id]
        if project_id:
            filtered_entries = [e for e in filtered_entries if e.project_id == project_id]
        
        # Calculate totals
        total_cost = sum(e.cost_usd for e in filtered_entries)
        
        # Breakdown by service
        by_service = defaultdict(float)
        for entry in filtered_entries:
            by_service[entry.service] += entry.cost_usd
        
        # Breakdown by operation
        by_operation = defaultdict(float)
        for entry in filtered_entries:
            by_operation[f"{entry.service}.{entry.operation}"] += entry.cost_usd
        
        # Breakdown by user
        by_user = defaultdict(float)
        for entry in filtered_entries:
            if entry.user_id:
                by_user[entry.user_id] += entry.cost_usd
        
        return {
            "total_cost_usd": round(total_cost, 4),
            "entry_count": len(filtered_entries),
            "by_service": dict(by_service),
            "by_operation": dict(by_operation),
            "by_user": dict(by_user),
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }
    
    def get_daily_costs(self, days: int = 7) -> Dict[str, float]:
        """Get daily costs for last N days."""
        costs = {}
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).date().isoformat()
            costs[date] = self._daily_costs.get(date, 0.0)
        return costs
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get cost optimization recommendations.
        
        Returns:
            List of recommendations with potential savings
        """
        recommendations = []
        
        # Analyze recent costs
        recent_entries = [
            e for e in self.cost_entries
            if e.timestamp > datetime.utcnow() - timedelta(days=7)
        ]
        
        # Count Gemini vision calls
        gemini_vision_count = sum(
            1 for e in recent_entries
            if e.service == "gemini" and e.operation == "analyze_image"
        )
        
        # Recommend DeepSeek if using Gemini vision heavily
        if gemini_vision_count > 100:
            potential_savings = gemini_vision_count * (0.25 - 0.03)
            recommendations.append({
                "title": "Switch to DeepSeek for Vision Analysis",
                "description": f"You've made {gemini_vision_count} Gemini vision calls in the last 7 days. "
                               f"Switching to DeepSeek could save ${potential_savings:.2f} (85% cost reduction).",
                "potential_savings_usd": potential_savings,
                "action": "Set VISION_PROVIDER=deepseek in environment",
                "priority": "high"
            })
        
        # Check for expensive operations
        by_operation = defaultdict(float)
        for entry in recent_entries:
            by_operation[f"{entry.service}.{entry.operation}"] += entry.cost_usd
        
        # Find most expensive operation
        if by_operation:
            most_expensive = max(by_operation.items(), key=lambda x: x[1])
            if most_expensive[1] > 10.0:  # More than $10 in a week
                recommendations.append({
                    "title": f"High Cost Operation: {most_expensive[0]}",
                    "description": f"This operation cost ${most_expensive[1]:.2f} in the last 7 days. "
                                   f"Consider caching results or reducing frequency.",
                    "potential_savings_usd": most_expensive[1] * 0.3,  # Assume 30% savings
                    "action": "Implement caching or rate limiting",
                    "priority": "medium"
                })
        
        return recommendations
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cost tracking statistics."""
        now = datetime.utcnow()
        today = now.date().isoformat()
        week = now.isocalendar()[:2]
        month = now.strftime("%Y-%m")
        
        return {
            "total_entries": len(self.cost_entries),
            "total_cost_all_time_usd": sum(e.cost_usd for e in self.cost_entries),
            "today_cost_usd": self._daily_costs.get(today, 0.0),
            "this_week_cost_usd": self._weekly_costs.get(str(week), 0.0),
            "this_month_cost_usd": self._monthly_costs.get(month, 0.0),
            "budget_alerts": [
                {
                    "name": alert.name,
                    "threshold_usd": alert.threshold_usd,
                    "period": alert.period,
                    "enabled": alert.enabled
                }
                for alert in self.budget_alerts
            ],
            "alerts_triggered": len(self.alert_history),
            "optimization_recommendations": self.get_optimization_recommendations()
        }


# Singleton instance
_cost_tracking_service = None

def get_cost_tracking_service() -> CostTrackingService:
    """Get singleton cost tracking service."""
    global _cost_tracking_service
    if _cost_tracking_service is None:
        _cost_tracking_service = CostTrackingService()
    return _cost_tracking_service

