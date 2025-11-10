# Foundation Services Quick Reference

**Quick guide for using the new foundation services**

---

## 1. Error Handling Service

### Basic Usage

```python
from backend.services.error_handling_service import (
    get_error_handling_service,
    ErrorContext,
    ErrorCategory,
    RecoveryStrategy
)

# Get service instance
error_service = get_error_handling_service()

# Handle an error
try:
    # Some operation that might fail
    result = await risky_operation()
except Exception as e:
    # Create error context
    context = ErrorContext(
        error=e,
        operation="risky_operation",
        node_name="process_data",
        workflow_id="workflow-123",
        user_id="user-456",
        metadata={"attempt": 1}
    )
    
    # Get error resolution
    resolution = error_service.handle_error(context)
    
    # Use resolution
    print(f"User message: {resolution.user_message}")
    print(f"Recovery strategy: {resolution.recovery_strategy.value}")
    print(f"Suggested actions: {resolution.suggested_actions}")
    
    # Check if should retry
    if resolution.recovery_strategy == RecoveryStrategy.RETRY:
        if resolution.retry_after_seconds:
            await asyncio.sleep(resolution.retry_after_seconds)
        # Retry the operation
```

### In Workflows

```python
# Already integrated in WorkflowOrchestrator
try:
    # Node logic
    result = await some_operation()
except Exception as e:
    # This automatically uses ErrorHandlingService
    state = self.orchestrator.add_error(
        state,
        error=e,
        node_name="my_node",
        user_id=state.get("user_id")
    )
    
    # Get last error resolution
    resolution = self.orchestrator.get_last_error_resolution(state)
    if resolution:
        # Use recovery strategy
        if resolution["recovery_strategy"] == "retry":
            # Retry logic
            pass
```

### Circuit Breaker

```python
# Check if circuit is open before calling external service
if error_service._is_circuit_open("gemini_api"):
    # Use fallback or skip
    return fallback_result

# Reset circuit manually if needed
error_service.reset_circuit("gemini_api")

# Get error statistics
stats = error_service.get_error_stats()
print(f"Total errors: {stats['total_errors']}")
print(f"Open circuits: {stats['open_circuit_breakers']}")
```

---

## 2. Cost Tracking Service

### Basic Usage

```python
from backend.services.cost_tracking_service import get_cost_tracking_service

# Get service instance
cost_service = get_cost_tracking_service()

# Track a cost
cost = cost_service.track_cost(
    service="gemini",
    operation="generate_text_flash",
    user_id="user-123",
    project_id="home-456",
    metadata={
        "model": "gemini-2.5-flash",
        "tokens": 1500,
        "duration_ms": 234
    }
)
print(f"Cost: ${cost:.4f}")

# Track with explicit cost
cost_service.track_cost(
    service="custom_api",
    operation="special_call",
    cost_usd=0.05,  # Explicit cost
    user_id="user-123"
)
```

### Get Cost Reports

```python
from datetime import datetime, timedelta

# Get costs for last 7 days
report = cost_service.get_costs(
    start_date=datetime.now() - timedelta(days=7),
    service="gemini"  # Optional filter
)

print(f"Total cost: ${report['total_cost_usd']:.2f}")
print(f"By service: {report['by_service']}")
print(f"By operation: {report['by_operation']}")
print(f"By user: {report['by_user']}")

# Get daily costs
daily_costs = cost_service.get_daily_costs(days=7)
for date, cost in daily_costs.items():
    print(f"{date}: ${cost:.2f}")
```

### Budget Alerts

```python
# Get current stats (includes budget status)
stats = cost_service.get_stats()
print(f"Today: ${stats['today_cost_usd']:.2f}")
print(f"This week: ${stats['this_week_cost_usd']:.2f}")
print(f"This month: ${stats['this_month_cost_usd']:.2f}")
print(f"Alerts triggered: {stats['alerts_triggered']}")

# Get optimization recommendations
recommendations = cost_service.get_optimization_recommendations()
for rec in recommendations:
    print(f"{rec['title']}: Save ${rec['potential_savings_usd']:.2f}")
    print(f"  Action: {rec['action']}")
```

### In API Clients

```python
# Already integrated in GeminiClient
gemini = GeminiClient()

# Cost is automatically tracked
response = await gemini.generate_text(
    prompt="Design a kitchen",
    user_id="user-123",      # For cost tracking
    project_id="home-456"    # For cost tracking
)
# Cost tracked automatically!

# Same for other methods
analysis = await gemini.analyze_image(
    image=image_bytes,
    prompt="Analyze this room",
    user_id="user-123",
    project_id="home-456"
)
# Cost tracked: $0.25 per image
```

---

## 3. Event Bus

### Basic Usage

```python
from backend.services.event_bus import get_event_bus, Event

# Get service instance
event_bus = get_event_bus()

# Subscribe to events
async def on_workflow_completed(event: Event):
    print(f"Workflow {event.data['workflow_id']} completed!")
    print(f"Duration: {event.data['duration_seconds']}s")

event_bus.subscribe("workflow.completed", on_workflow_completed)

# Subscribe to all workflow events (wildcard)
async def on_any_workflow_event(event: Event):
    print(f"Workflow event: {event.event_type}")

event_bus.subscribe("workflow.*", on_any_workflow_event)

# Subscribe to all events
async def on_any_event(event: Event):
    print(f"Event: {event.event_type} from {event.source}")

event_bus.subscribe("*", on_any_event)
```

### Publish Events

```python
# Publish custom event
await event_bus.publish(
    event_type="custom.event",
    data={"key": "value"},
    source="my_service",
    metadata={"extra": "info"}
)

# Use convenience functions
from backend.services.event_bus import (
    publish_workflow_started,
    publish_workflow_completed,
    publish_chat_message_received,
    publish_cost_threshold_exceeded
)

await publish_workflow_started(
    workflow_id="wf-123",
    workflow_name="chat_workflow",
    metadata={"user_id": "user-456"}
)

await publish_chat_message_received(
    conversation_id="conv-789",
    message="Hello!",
    user_id="user-456"
)
```

### Query Event History

```python
from datetime import datetime, timedelta

# Get recent events
recent = event_bus.get_events(limit=50)

# Get events by type
workflow_events = event_bus.get_events(
    event_type="workflow.completed",
    limit=100
)

# Get events by source
chat_events = event_bus.get_events(
    source="chat_workflow",
    limit=100
)

# Get events since timestamp
recent_errors = event_bus.get_events(
    event_type="error.occurred",
    since=datetime.now() - timedelta(hours=1),
    limit=50
)

# Get statistics
stats = event_bus.get_stats()
print(f"Total events: {stats['total_events']}")
print(f"Events by type: {stats['events_by_type']}")
print(f"Subscribers: {stats['subscribers_by_type']}")
```

### Event Replay (Debugging)

```python
# Replay all workflow failures from last hour
await event_bus.replay_events(
    event_type="workflow.failed",
    since=datetime.now() - timedelta(hours=1)
)

# Replay all events (careful!)
await event_bus.replay_events()

# Clear history (testing only)
event_bus.clear_history()
```

---

## 4. Integration Examples

### Complete Chat Flow with All Services

```python
from backend.workflows.chat_workflow import ChatWorkflow
from backend.services.event_bus import get_event_bus

# Setup
workflow = ChatWorkflow(db_session)
event_bus = get_event_bus()

# Subscribe to events
async def log_all_events(event: Event):
    print(f"[{event.timestamp}] {event.event_type}: {event.data}")

event_bus.subscribe("*", log_all_events)

# Execute workflow (all services integrated automatically)
result = await workflow.execute({
    "user_message": "I want to renovate my kitchen",
    "user_id": "user-123",
    "home_id": "home-456",
    "conversation_id": "conv-789",
    "mode": "agent"
})

# Events published automatically:
# 1. workflow.started
# 2. chat.message_received
# 3. chat.response_generated
# 4. workflow.completed (or workflow.failed)

# Costs tracked automatically for:
# - Gemini text generation
# - Gemini vision analysis
# - Gemini embeddings

# Errors handled automatically with:
# - User-friendly messages
# - Recovery strategies
# - Circuit breakers
```

### Custom Service with All Features

```python
from backend.services.error_handling_service import get_error_handling_service, ErrorContext
from backend.services.cost_tracking_service import get_cost_tracking_service
from backend.services.event_bus import get_event_bus

class MyCustomService:
    def __init__(self):
        self.error_service = get_error_handling_service()
        self.cost_service = get_cost_tracking_service()
        self.event_bus = get_event_bus()
    
    async def process_data(self, data: dict, user_id: str):
        start_time = time.time()
        
        try:
            # Publish start event
            await self.event_bus.publish(
                "custom.process_started",
                {"user_id": user_id},
                source="my_custom_service"
            )
            
            # Do work
            result = await self._do_work(data)
            
            # Track cost
            duration = time.time() - start_time
            self.cost_service.track_cost(
                service="custom",
                operation="process_data",
                cost_usd=0.01,
                user_id=user_id,
                metadata={"duration_ms": int(duration * 1000)}
            )
            
            # Publish success event
            await self.event_bus.publish(
                "custom.process_completed",
                {"user_id": user_id, "result": result},
                source="my_custom_service"
            )
            
            return result
            
        except Exception as e:
            # Handle error
            context = ErrorContext(
                error=e,
                operation="process_data",
                user_id=user_id
            )
            resolution = self.error_service.handle_error(context)
            
            # Publish error event
            await self.event_bus.publish(
                "custom.process_failed",
                {
                    "user_id": user_id,
                    "error": resolution.user_message,
                    "recovery_strategy": resolution.recovery_strategy.value
                },
                source="my_custom_service"
            )
            
            # Return error to user
            raise Exception(resolution.user_message)
```

---

## 5. Monitoring & Debugging

### Real-time Monitoring

```python
# Subscribe to all events for monitoring
async def monitor_all(event: Event):
    if event.event_type.startswith("error."):
        print(f"🔴 ERROR: {event.data}")
    elif event.event_type.startswith("cost."):
        print(f"💰 COST: {event.data}")
    elif event.event_type.startswith("workflow."):
        print(f"⚙️ WORKFLOW: {event.data}")

event_bus.subscribe("*", monitor_all)
```

### Debug Failed Workflows

```python
# Get all failed workflows from last hour
failed = event_bus.get_events(
    event_type="workflow.failed",
    since=datetime.now() - timedelta(hours=1)
)

for event in failed:
    workflow_id = event.data["workflow_id"]
    error = event.data["error"]
    print(f"Workflow {workflow_id} failed: {error}")
    
    # Get all events for this workflow
    workflow_events = [
        e for e in event_bus.event_history
        if e.metadata.get("workflow_id") == workflow_id
    ]
    
    # Analyze the flow
    for e in workflow_events:
        print(f"  {e.timestamp}: {e.event_type}")
```

### Cost Analysis

```python
# Get top spenders
report = cost_service.get_costs(
    start_date=datetime.now() - timedelta(days=7)
)

# Sort users by cost
user_costs = sorted(
    report["by_user"].items(),
    key=lambda x: x[1],
    reverse=True
)

print("Top 10 users by cost:")
for user_id, cost in user_costs[:10]:
    print(f"  {user_id}: ${cost:.2f}")

# Get most expensive operations
op_costs = sorted(
    report["by_operation"].items(),
    key=lambda x: x[1],
    reverse=True
)

print("\nMost expensive operations:")
for operation, cost in op_costs[:10]:
    print(f"  {operation}: ${cost:.2f}")
```

---

## 6. Best Practices

### Error Handling
- ✅ Always provide user_id in ErrorContext
- ✅ Use specific operation names for circuit breakers
- ✅ Check circuit breaker status before expensive operations
- ✅ Return error resolution to users, not raw exceptions

### Cost Tracking
- ✅ Always pass user_id and project_id to API calls
- ✅ Review cost reports weekly
- ✅ Implement optimization recommendations
- ✅ Set appropriate budget alert thresholds

### Event Bus
- ✅ Use descriptive event types (e.g., "service.action")
- ✅ Include rich metadata in events
- ✅ Subscribe to wildcards for monitoring
- ✅ Handle errors in event handlers (they're caught automatically)
- ✅ Use event replay for debugging, not production

### General
- ✅ Services are singletons - use get_*_service() functions
- ✅ All services are async-compatible
- ✅ Services are thread-safe
- ✅ Monitor circuit breakers and error rates

---

## 7. Configuration

### Environment Variables

```bash
# Cost tracking thresholds (optional, defaults shown)
COST_DAILY_THRESHOLD=50.0
COST_WEEKLY_THRESHOLD=300.0
COST_MONTHLY_THRESHOLD=1000.0

# Event bus (optional)
EVENT_BUS_MAX_HISTORY=1000

# Error handling (optional)
ERROR_CIRCUIT_BREAKER_THRESHOLD=5
ERROR_CIRCUIT_BREAKER_TIMEOUT=60
```

### Programmatic Configuration

```python
# Customize budget alerts
cost_service = get_cost_tracking_service()
cost_service.budget_alerts.append(
    BudgetAlert(
        name="Hourly Budget",
        threshold_usd=10.0,
        period="hourly",
        alert_channels=["slack"]
    )
)

# Customize event bus
event_bus = get_event_bus()
event_bus.max_history = 5000  # Store more events
```

---

**For more details, see:**
- `backend/services/error_handling_service.py`
- `backend/services/cost_tracking_service.py`
- `backend/services/event_bus.py`
- `docs/analysis/FOUNDATION_IMPROVEMENTS_PROGRESS.md`

