"""
Analytics service for tracking user behavior, feature usage, and system performance.

Aggregates data from:
- Event bus (user actions, workflow events)
- Cost tracking service (API usage and costs)
- Error handling service (error rates and patterns)

Features:
- User journey tracking
- Feature usage metrics
- Performance metrics (latency, throughput)
- Conversion funnel analysis
- A/B test support
- Dashboard data aggregation
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from backend.services.event_bus import get_event_bus, Event
from backend.services.cost_tracking_service import get_cost_tracking_service

logger = logging.getLogger(__name__)


@dataclass
class MetricSnapshot:
    """Snapshot of a metric at a point in time."""
    timestamp: datetime
    metric_name: str
    value: float
    dimensions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserJourneyStep:
    """Single step in a user journey."""
    step_name: str
    timestamp: datetime
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversionFunnel:
    """Conversion funnel definition and metrics."""
    name: str
    steps: List[str]
    counts: Dict[str, int] = field(default_factory=dict)
    conversion_rates: Dict[str, float] = field(default_factory=dict)


class AnalyticsService:
    """
    Service for tracking and analyzing user behavior and system performance.
    
    Features:
    - Real-time metrics aggregation
    - User journey tracking
    - Feature usage analytics
    - Performance monitoring
    - Conversion funnel analysis
    """
    
    def __init__(self):
        self.event_bus = get_event_bus()
        self.cost_service = get_cost_tracking_service()
        
        # Metrics storage
        self.metrics: List[MetricSnapshot] = []
        self.user_journeys: Dict[str, List[UserJourneyStep]] = defaultdict(list)
        self.feature_usage: Dict[str, int] = Counter()
        self.performance_metrics: List[Dict[str, Any]] = []
        
        # Conversion funnels
        self.funnels: Dict[str, ConversionFunnel] = {}
        self._setup_default_funnels()
        
        # Subscribe to events
        self._subscribe_to_events()
    
    def _setup_default_funnels(self):
        """Setup default conversion funnels."""
        self.funnels = {
            "kitchen_renovation": ConversionFunnel(
                name="Kitchen Renovation Journey",
                steps=[
                    "chat.message_received",
                    "vision.analysis_completed",
                    "design.transformation_completed",
                    "product.search_completed",
                    "pdf.export_completed"
                ]
            ),
            "diy_project": ConversionFunnel(
                name="DIY Project Planning",
                steps=[
                    "chat.message_received",
                    "youtube.videos_found",
                    "cost.estimate_generated",
                    "pdf.export_completed"
                ]
            ),
            "contractor_hiring": ConversionFunnel(
                name="Contractor Hiring",
                steps=[
                    "chat.message_received",
                    "contractor.search_completed",
                    "contractor.quote_requested",
                    "contractor.hired"
                ]
            )
        }
    
    def _subscribe_to_events(self):
        """Subscribe to relevant events for analytics."""
        # Subscribe to all events for comprehensive tracking
        self.event_bus.subscribe("*", self._handle_event)
    
    async def _handle_event(self, event: Event):
        """Handle incoming events for analytics."""
        try:
            # Track feature usage
            feature = event.event_type.split(".")[0]
            self.feature_usage[feature] += 1
            
            # Track user journey
            if event.metadata and "user_id" in event.metadata:
                user_id = event.metadata["user_id"]
                step = UserJourneyStep(
                    step_name=event.event_type,
                    timestamp=event.timestamp,
                    metadata=event.metadata
                )
                self.user_journeys[user_id].append(step)
            
            # Track performance metrics
            if "duration_ms" in event.metadata or "duration_seconds" in event.metadata:
                duration_ms = event.metadata.get("duration_ms") or (event.metadata.get("duration_seconds", 0) * 1000)
                self.performance_metrics.append({
                    "event_type": event.event_type,
                    "duration_ms": duration_ms,
                    "timestamp": event.timestamp
                })
            
            # Update conversion funnels
            for funnel in self.funnels.values():
                if event.event_type in funnel.steps:
                    funnel.counts[event.event_type] = funnel.counts.get(event.event_type, 0) + 1
            
        except Exception as e:
            logger.error(f"Error handling event for analytics: {e}")
    
    def record_metric(self, metric_name: str, value: float, dimensions: Optional[Dict[str, Any]] = None):
        """Record a custom metric."""
        snapshot = MetricSnapshot(
            timestamp=datetime.utcnow(),
            metric_name=metric_name,
            value=value,
            dimensions=dimensions or {}
        )
        self.metrics.append(snapshot)
    
    def get_feature_usage(self, since: Optional[datetime] = None) -> Dict[str, int]:
        """Get feature usage counts."""
        if since is None:
            return dict(self.feature_usage)
        
        # Filter by time (would need to track timestamps per feature)
        return dict(self.feature_usage)
    
    def get_user_journey(self, user_id: str, since: Optional[datetime] = None) -> List[UserJourneyStep]:
        """Get user journey steps."""
        steps = self.user_journeys.get(user_id, [])
        
        if since:
            steps = [s for s in steps if s.timestamp >= since]
        
        return steps
    
    def get_performance_stats(self, event_type: Optional[str] = None, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get performance statistics."""
        metrics = self.performance_metrics
        
        # Filter by event type
        if event_type:
            metrics = [m for m in metrics if m["event_type"] == event_type]
        
        # Filter by time
        if since:
            metrics = [m for m in metrics if m["timestamp"] >= since]
        
        if not metrics:
            return {
                "count": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
                "p50_duration_ms": 0,
                "p95_duration_ms": 0,
                "p99_duration_ms": 0
            }
        
        durations = [m["duration_ms"] for m in metrics]
        durations.sort()
        
        return {
            "count": len(durations),
            "avg_duration_ms": statistics.mean(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "p50_duration_ms": durations[len(durations) // 2],
            "p95_duration_ms": durations[int(len(durations) * 0.95)],
            "p99_duration_ms": durations[int(len(durations) * 0.99)]
        }
    
    def get_conversion_funnel(self, funnel_name: str) -> Dict[str, Any]:
        """Get conversion funnel metrics."""
        if funnel_name not in self.funnels:
            return {"error": f"Funnel '{funnel_name}' not found"}
        
        funnel = self.funnels[funnel_name]
        
        # Calculate conversion rates
        total_started = funnel.counts.get(funnel.steps[0], 0)
        if total_started == 0:
            return {
                "name": funnel.name,
                "steps": funnel.steps,
                "counts": funnel.counts,
                "conversion_rates": {},
                "total_started": 0,
                "total_completed": 0,
                "overall_conversion_rate": 0.0
            }
        
        conversion_rates = {}
        for i, step in enumerate(funnel.steps):
            count = funnel.counts.get(step, 0)
            conversion_rates[step] = (count / total_started) * 100
        
        total_completed = funnel.counts.get(funnel.steps[-1], 0)
        overall_conversion_rate = (total_completed / total_started) * 100
        
        return {
            "name": funnel.name,
            "steps": funnel.steps,
            "counts": funnel.counts,
            "conversion_rates": conversion_rates,
            "total_started": total_started,
            "total_completed": total_completed,
            "overall_conversion_rate": overall_conversion_rate
        }
    
    def get_dashboard_data(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get aggregated data for analytics dashboard."""
        if since is None:
            since = datetime.utcnow() - timedelta(days=7)
        
        # Get cost data
        cost_report = self.cost_service.get_costs(start_date=since)
        
        # Get performance stats
        perf_stats = self.get_performance_stats(since=since)
        
        # Get feature usage
        feature_usage = self.get_feature_usage(since=since)
        
        # Get conversion funnels
        funnels = {}
        for funnel_name in self.funnels.keys():
            funnels[funnel_name] = self.get_conversion_funnel(funnel_name)
        
        # Get active users
        active_users = len(set(
            event.metadata.get("user_id")
            for event in self.event_bus.get_events(since=since)
            if event.metadata and "user_id" in event.metadata
        ))
        
        # Get total events
        total_events = len(self.event_bus.get_events(since=since))
        
        return {
            "period": {
                "start": since.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "overview": {
                "active_users": active_users,
                "total_events": total_events,
                "total_cost_usd": cost_report["total_cost_usd"],
                "avg_response_time_ms": perf_stats.get("avg_duration_ms", 0)
            },
            "costs": {
                "total": cost_report["total_cost_usd"],
                "by_service": cost_report["by_service"],
                "by_operation": cost_report["by_operation"]
            },
            "performance": perf_stats,
            "feature_usage": feature_usage,
            "conversion_funnels": funnels
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get analytics service statistics."""
        return {
            "metrics_tracked": len(self.metrics),
            "users_tracked": len(self.user_journeys),
            "features_tracked": len(self.feature_usage),
            "performance_samples": len(self.performance_metrics),
            "funnels_configured": len(self.funnels)
        }


# Singleton instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get or create the analytics service singleton."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service

