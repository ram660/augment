"""
Centralized error handling service with categorization and recovery strategies.

This service provides:
- Error classification into categories (transient, permanent, user input, etc.)
- User-friendly error message generation
- Recovery strategy selection (retry, fallback, ask user, etc.)
- Circuit breaker pattern for external services
- Error rate tracking and monitoring
"""
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
import logging
import time

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Error categories for classification."""
    TRANSIENT = "transient"  # Temporary, retry likely to succeed
    PERMANENT = "permanent"  # Permanent, retry won't help
    USER_INPUT = "user_input"  # User needs to provide more/different input
    EXTERNAL_SERVICE = "external_service"  # 3rd party service issue
    CONFIGURATION = "configuration"  # Missing config/credentials
    RATE_LIMIT = "rate_limit"  # Rate limit exceeded
    VALIDATION = "validation"  # Input validation failed
    UNKNOWN = "unknown"  # Unclassified error


class RecoveryStrategy(Enum):
    """Recovery strategies for errors."""
    RETRY = "retry"  # Retry the operation
    FALLBACK = "fallback"  # Use alternative method
    ASK_USER = "ask_user"  # Request clarification from user
    SKIP = "skip"  # Skip this step and continue
    ABORT = "abort"  # Stop the workflow
    DEGRADE = "degrade"  # Continue with reduced functionality


@dataclass
class ErrorContext:
    """Context information for an error."""
    error: Exception
    operation: str  # What was being attempted
    node_name: Optional[str] = None
    workflow_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorResolution:
    """Resolution plan for an error."""
    category: ErrorCategory
    recovery_strategy: RecoveryStrategy
    user_message: str  # User-friendly explanation
    technical_message: str  # Technical details for logging
    suggested_actions: List[Dict[str, Any]]  # Actions user can take
    retry_after_seconds: Optional[int] = None
    fallback_function: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ErrorHandlingService:
    """
    Centralized error handling with categorization and recovery.
    
    Features:
    - Error classification
    - User-friendly message generation
    - Recovery strategy selection
    - Circuit breaker pattern
    - Error rate tracking
    """
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}  # Track errors per operation
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}  # Circuit breaker state
        self.error_history: List[Dict[str, Any]] = []  # Recent errors for analytics
        
    def handle_error(self, context: ErrorContext) -> ErrorResolution:
        """
        Handle an error and determine recovery strategy.
        
        Args:
            context: Error context with operation details
            
        Returns:
            ErrorResolution with recovery plan
        """
        # Classify the error
        category = self._classify_error(context.error)
        
        # Select recovery strategy
        strategy = self._select_recovery_strategy(category, context)
        
        # Generate user-friendly message
        user_message = self._generate_user_message(category, context)
        
        # Generate suggested actions
        suggested_actions = self._generate_suggested_actions(category, strategy, context)
        
        # Track error for circuit breaker
        self._track_error(context.operation)
        
        # Calculate retry delay if applicable
        retry_after = self._calculate_retry_delay(category, context.operation)
        
        resolution = ErrorResolution(
            category=category,
            recovery_strategy=strategy,
            user_message=user_message,
            technical_message=str(context.error),
            suggested_actions=suggested_actions,
            retry_after_seconds=retry_after,
            metadata={
                "error_type": type(context.error).__name__,
                "operation": context.operation,
                "node_name": context.node_name,
                "circuit_breaker_open": self._is_circuit_open(context.operation)
            }
        )
        
        # Log the error
        logger.info(
            f"Error handled: {context.operation} | "
            f"Category: {category.value} | "
            f"Strategy: {strategy.value} | "
            f"User: {context.user_id}"
        )
        
        # Store in history for analytics
        self._store_error_history(context, resolution)
        
        return resolution
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error into category."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Transient errors (network, timeout)
        if any(keyword in error_message for keyword in ["timeout", "connection", "temporary", "unavailable"]):
            return ErrorCategory.TRANSIENT
        
        # Rate limit errors
        if any(keyword in error_message for keyword in ["rate limit", "quota", "too many requests", "429"]):
            return ErrorCategory.RATE_LIMIT
        
        # Configuration errors
        if any(keyword in error_message for keyword in ["not configured", "missing", "api key", "credentials", "environment"]):
            return ErrorCategory.CONFIGURATION
        
        # Validation errors
        if "validation" in error_message or error_type in ["ValidationError", "ValueError", "TypeError"]:
            return ErrorCategory.VALIDATION
        
        # External service errors
        if any(keyword in error_message for keyword in ["gemini", "google", "deepseek", "api", "service", "external"]):
            return ErrorCategory.EXTERNAL_SERVICE
        
        # User input errors
        if any(keyword in error_message for keyword in ["invalid input", "required", "missing field", "empty"]):
            return ErrorCategory.USER_INPUT
        
        # Permanent errors
        if any(keyword in error_message for keyword in ["not found", "forbidden", "unauthorized", "404", "403", "401"]):
            return ErrorCategory.PERMANENT
        
        return ErrorCategory.UNKNOWN
    
    def _select_recovery_strategy(self, category: ErrorCategory, context: ErrorContext) -> RecoveryStrategy:
        """Select appropriate recovery strategy based on error category."""
        strategy_map = {
            ErrorCategory.TRANSIENT: RecoveryStrategy.RETRY,
            ErrorCategory.RATE_LIMIT: RecoveryStrategy.RETRY,
            ErrorCategory.USER_INPUT: RecoveryStrategy.ASK_USER,
            ErrorCategory.VALIDATION: RecoveryStrategy.ASK_USER,
            ErrorCategory.CONFIGURATION: RecoveryStrategy.FALLBACK,
            ErrorCategory.EXTERNAL_SERVICE: RecoveryStrategy.FALLBACK,
            ErrorCategory.PERMANENT: RecoveryStrategy.ABORT,
            ErrorCategory.UNKNOWN: RecoveryStrategy.DEGRADE,
        }
        
        strategy = strategy_map.get(category, RecoveryStrategy.ABORT)
        
        # Check circuit breaker - force fallback if open
        if self._is_circuit_open(context.operation):
            logger.warning(f"Circuit breaker open for {context.operation}, forcing fallback")
            return RecoveryStrategy.FALLBACK
        
        return strategy
    
    def _generate_user_message(self, category: ErrorCategory, context: ErrorContext) -> str:
        """Generate user-friendly error message."""
        messages = {
            ErrorCategory.TRANSIENT: (
                "We're experiencing a temporary issue. "
                "Please try again in a moment."
            ),
            ErrorCategory.RATE_LIMIT: (
                "We've reached our request limit for this service. "
                "Please wait a moment and try again."
            ),
            ErrorCategory.USER_INPUT: (
                "I need a bit more information to help you. "
                "Could you provide more details or rephrase your request?"
            ),
            ErrorCategory.VALIDATION: (
                "There seems to be an issue with the information provided. "
                "Please check your input and try again."
            ),
            ErrorCategory.CONFIGURATION: (
                "This feature is temporarily unavailable due to a configuration issue. "
                "We're working on it!"
            ),
            ErrorCategory.EXTERNAL_SERVICE: (
                "We're having trouble connecting to an external service. "
                "Let me try an alternative approach."
            ),
            ErrorCategory.PERMANENT: (
                "I'm unable to complete this request. "
                "Please try a different approach or contact support if the issue persists."
            ),
            ErrorCategory.UNKNOWN: (
                "Something unexpected happened. "
                "I'll do my best to continue with what I can."
            ),
        }
        
        base_message = messages.get(category, messages[ErrorCategory.UNKNOWN])
        
        # Add operation-specific context if available
        if context.operation:
            operation_friendly = context.operation.replace("_", " ").title()
            return f"{base_message}\n\n(While attempting: {operation_friendly})"
        
        return base_message
    
    def _generate_suggested_actions(
        self, 
        category: ErrorCategory, 
        strategy: RecoveryStrategy,
        context: ErrorContext
    ) -> List[Dict[str, Any]]:
        """Generate suggested actions for user."""
        actions = []
        
        if strategy == RecoveryStrategy.RETRY:
            actions.append({
                "action": "retry",
                "label": "Try Again",
                "description": "Retry the operation",
                "icon": "refresh"
            })
        
        if strategy == RecoveryStrategy.ASK_USER:
            actions.append({
                "action": "provide_more_info",
                "label": "Provide More Details",
                "description": "Give me more information to help",
                "icon": "edit"
            })
        
        if strategy == RecoveryStrategy.FALLBACK:
            actions.append({
                "action": "use_alternative",
                "label": "Use Alternative Method",
                "description": "Try a different approach",
                "icon": "swap"
            })
        
        if strategy == RecoveryStrategy.SKIP:
            actions.append({
                "action": "skip_step",
                "label": "Skip This Step",
                "description": "Continue without this feature",
                "icon": "forward"
            })
        
        if strategy == RecoveryStrategy.DEGRADE:
            actions.append({
                "action": "continue_limited",
                "label": "Continue with Limited Features",
                "description": "Proceed with reduced functionality",
                "icon": "warning"
            })
        
        # Always offer to contact support
        actions.append({
            "action": "contact_support",
            "label": "Contact Support",
            "description": "Get help from our team",
            "icon": "help"
        })
        
        return actions
    
    def _track_error(self, operation: str):
        """Track error for circuit breaker."""
        self.error_counts[operation] = self.error_counts.get(operation, 0) + 1
        
        # Open circuit breaker if too many errors (5 in recent history)
        if self.error_counts[operation] >= 5:
            self._open_circuit(operation)
    
    def _open_circuit(self, operation: str):
        """Open circuit breaker for operation."""
        self.circuit_breakers[operation] = {
            "open": True,
            "opened_at": time.time(),
            "retry_after": 60  # seconds
        }
        logger.warning(f"Circuit breaker opened for {operation} after {self.error_counts[operation]} errors")
    
    def _is_circuit_open(self, operation: str) -> bool:
        """Check if circuit breaker is open."""
        if operation not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[operation]
        if not breaker["open"]:
            return False
        
        # Check if retry period has passed
        if time.time() - breaker["opened_at"] > breaker["retry_after"]:
            # Close circuit and reset
            breaker["open"] = False
            self.error_counts[operation] = 0
            logger.info(f"Circuit breaker closed for {operation} after cooldown period")
            return False
        
        return True
    
    def _calculate_retry_delay(self, category: ErrorCategory, operation: str) -> Optional[int]:
        """Calculate retry delay in seconds."""
        if category == ErrorCategory.RATE_LIMIT:
            return 60  # Wait 1 minute for rate limits
        elif category == ErrorCategory.TRANSIENT:
            # Exponential backoff based on error count
            error_count = self.error_counts.get(operation, 0)
            return min(2 ** error_count, 30)  # Max 30 seconds
        return None
    
    def _store_error_history(self, context: ErrorContext, resolution: ErrorResolution):
        """Store error in history for analytics."""
        self.error_history.append({
            "timestamp": time.time(),
            "operation": context.operation,
            "category": resolution.category.value,
            "strategy": resolution.recovery_strategy.value,
            "user_id": context.user_id,
            "error_type": type(context.error).__name__
        })
        
        # Keep only last 1000 errors
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def reset_circuit(self, operation: str):
        """Manually reset circuit breaker."""
        if operation in self.circuit_breakers:
            self.circuit_breakers[operation]["open"] = False
            self.error_counts[operation] = 0
            logger.info(f"Circuit breaker manually reset for {operation}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "errors_by_operation": dict(self.error_counts),
            "open_circuit_breakers": [
                op for op, breaker in self.circuit_breakers.items() 
                if breaker.get("open", False)
            ],
            "recent_errors": self.error_history[-100:]  # Last 100 errors
        }


# Singleton instance
_error_handling_service = None

def get_error_handling_service() -> ErrorHandlingService:
    """Get singleton error handling service."""
    global _error_handling_service
    if _error_handling_service is None:
        _error_handling_service = ErrorHandlingService()
    return _error_handling_service

