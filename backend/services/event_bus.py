"""
Event bus for decoupled communication between services.

Provides:
- Publish/subscribe pattern
- Event filtering by type and metadata
- Async event handlers
- Event history for debugging
- Event replay capability

Events:
- workflow.started
- workflow.completed
- workflow.failed
- chat.message_received
- chat.response_generated
- vision.analysis_completed
- rag.context_retrieved
- cost.threshold_exceeded
- error.occurred
"""
import logging
from typing import Dict, Any, List, Callable, Awaitable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Event data structure."""
    event_type: str  # e.g., "workflow.started", "chat.message_received"
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: str = field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    source: Optional[str] = None  # Service/component that emitted the event
    metadata: Dict[str, Any] = field(default_factory=dict)


EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    """
    Event bus for decoupled service communication.
    
    Features:
    - Publish/subscribe pattern
    - Async event handlers
    - Event filtering
    - Event history
    - Error handling for handlers
    """
    
    def __init__(self, max_history: int = 1000):
        self.subscribers: Dict[str, List[EventHandler]] = defaultdict(list)
        self.event_history: List[Event] = []
        self.max_history = max_history
        self.handler_errors: List[Dict[str, Any]] = []
        
    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Event:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: Type of event (e.g., "workflow.started")
            data: Event data
            source: Source service/component
            metadata: Additional metadata
            
        Returns:
            The published event
        """
        event = Event(
            event_type=event_type,
            data=data,
            source=source,
            metadata=metadata or {}
        )
        
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        logger.debug(f"Event published: {event_type} from {source}")
        
        # Notify subscribers
        await self._notify_subscribers(event)
        
        return event
    
    async def _notify_subscribers(self, event: Event):
        """Notify all subscribers of an event."""
        # Get exact match subscribers
        handlers = self.subscribers.get(event.event_type, [])
        
        # Get wildcard subscribers (e.g., "workflow.*")
        wildcard_pattern = event.event_type.split(".")[0] + ".*"
        handlers.extend(self.subscribers.get(wildcard_pattern, []))
        
        # Get global subscribers ("*")
        handlers.extend(self.subscribers.get("*", []))
        
        if not handlers:
            return
        
        # Call all handlers concurrently
        tasks = []
        for handler in handlers:
            tasks.append(self._call_handler_safely(handler, event))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _call_handler_safely(self, handler: EventHandler, event: Event):
        """Call a handler with error handling."""
        try:
            await handler(event)
        except Exception as e:
            error_entry = {
                "handler": handler.__name__,
                "event_type": event.event_type,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.handler_errors.append(error_entry)
            
            logger.error(
                f"Error in event handler {handler.__name__} for {event.event_type}: {e}",
                exc_info=e
            )
    
    def subscribe(
        self,
        event_type: str,
        handler: EventHandler
    ):
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of event to subscribe to (supports wildcards: "workflow.*", "*")
            handler: Async function to call when event is published
            
        Example:
            async def on_workflow_started(event: Event):
                print(f"Workflow {event.data['workflow_id']} started")
            
            event_bus.subscribe("workflow.started", on_workflow_started)
        """
        self.subscribers[event_type].append(handler)
        logger.info(f"Subscribed {handler.__name__} to {event_type}")
    
    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler
    ):
        """Unsubscribe a handler from an event type."""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(handler)
                logger.info(f"Unsubscribed {handler.__name__} from {event_type}")
            except ValueError:
                pass
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get events from history with filters.
        
        Args:
            event_type: Filter by event type
            source: Filter by source
            since: Filter by timestamp (events after this time)
            limit: Maximum number of events to return
            
        Returns:
            List of matching events
        """
        events = self.event_history
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if source:
            events = [e for e in events if e.source == source]
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        # Return most recent events up to limit
        return events[-limit:]
    
    async def replay_events(
        self,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None
    ):
        """
        Replay events from history.
        
        Useful for:
        - Debugging
        - Rebuilding state
        - Testing event handlers
        
        Args:
            event_type: Only replay events of this type
            since: Only replay events after this time
        """
        events = self.get_events(event_type=event_type, since=since, limit=10000)
        
        logger.info(f"Replaying {len(events)} events")
        
        for event in events:
            await self._notify_subscribers(event)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        # Count events by type
        event_counts = defaultdict(int)
        for event in self.event_history:
            event_counts[event.event_type] += 1
        
        # Count subscribers by type
        subscriber_counts = {
            event_type: len(handlers)
            for event_type, handlers in self.subscribers.items()
        }
        
        return {
            "total_events": len(self.event_history),
            "events_by_type": dict(event_counts),
            "subscribers_by_type": subscriber_counts,
            "handler_errors": len(self.handler_errors),
            "recent_errors": self.handler_errors[-10:]  # Last 10 errors
        }
    
    def clear_history(self):
        """Clear event history (useful for testing)."""
        self.event_history.clear()
        logger.info("Event history cleared")


# Singleton instance
_event_bus = None

def get_event_bus() -> EventBus:
    """Get singleton event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Convenience functions for common events

async def publish_workflow_started(workflow_id: str, workflow_name: str, metadata: Optional[Dict[str, Any]] = None):
    """Publish workflow.started event."""
    bus = get_event_bus()
    await bus.publish(
        "workflow.started",
        {"workflow_id": workflow_id, "workflow_name": workflow_name},
        source="workflow_orchestrator",
        metadata=metadata
    )


async def publish_workflow_completed(workflow_id: str, workflow_name: str, duration_seconds: float, metadata: Optional[Dict[str, Any]] = None):
    """Publish workflow.completed event."""
    bus = get_event_bus()
    await bus.publish(
        "workflow.completed",
        {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "duration_seconds": duration_seconds
        },
        source="workflow_orchestrator",
        metadata=metadata
    )


async def publish_workflow_failed(workflow_id: str, workflow_name: str, error: str, metadata: Optional[Dict[str, Any]] = None):
    """Publish workflow.failed event."""
    bus = get_event_bus()
    await bus.publish(
        "workflow.failed",
        {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "error": error
        },
        source="workflow_orchestrator",
        metadata=metadata
    )


async def publish_chat_message_received(conversation_id: str, message: str, user_id: str, metadata: Optional[Dict[str, Any]] = None):
    """Publish chat.message_received event."""
    bus = get_event_bus()
    await bus.publish(
        "chat.message_received",
        {
            "conversation_id": conversation_id,
            "message": message,
            "user_id": user_id
        },
        source="chat_api",
        metadata=metadata
    )


async def publish_chat_response_generated(conversation_id: str, response: str, metadata: Optional[Dict[str, Any]] = None):
    """Publish chat.response_generated event."""
    bus = get_event_bus()
    await bus.publish(
        "chat.response_generated",
        {
            "conversation_id": conversation_id,
            "response": response
        },
        source="chat_workflow",
        metadata=metadata
    )


async def publish_cost_threshold_exceeded(threshold_name: str, current_spend: float, threshold: float, metadata: Optional[Dict[str, Any]] = None):
    """Publish cost.threshold_exceeded event."""
    bus = get_event_bus()
    await bus.publish(
        "cost.threshold_exceeded",
        {
            "threshold_name": threshold_name,
            "current_spend_usd": current_spend,
            "threshold_usd": threshold
        },
        source="cost_tracking_service",
        metadata=metadata
    )


async def publish_error_occurred(error_category: str, error_message: str, recovery_strategy: str, metadata: Optional[Dict[str, Any]] = None):
    """Publish error.occurred event."""
    bus = get_event_bus()
    await bus.publish(
        "error.occurred",
        {
            "category": error_category,
            "message": error_message,
            "recovery_strategy": recovery_strategy
        },
        source="error_handling_service",
        metadata=metadata
    )

