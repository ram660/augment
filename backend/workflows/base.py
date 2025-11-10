"""Base workflow infrastructure for LangGraph orchestration."""

import logging
from typing import Any, Dict, List, Optional, TypedDict, Literal
from datetime import datetime
from enum import Enum
import uuid

from backend.services.error_handling_service import (
    get_error_handling_service,
    ErrorContext,
    ErrorResolution,
    RecoveryStrategy
)

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"  # Some steps succeeded, some failed


class WorkflowError(Exception):
    """Custom exception for workflow errors."""
    
    def __init__(
        self,
        message: str,
        node_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
        recoverable: bool = False
    ):
        super().__init__(message)
        self.node_name = node_name
        self.original_error = original_error
        self.recoverable = recoverable
        self.timestamp = datetime.utcnow()


class BaseWorkflowState(TypedDict, total=False):
    """Base state for all workflows with common fields."""
    
    # Workflow metadata
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    started_at: str
    completed_at: Optional[str]
    
    # Execution tracking
    current_node: Optional[str]
    visited_nodes: List[str]
    retry_count: int
    max_retries: int
    
    # Error handling
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    
    # Results
    result: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]


class WorkflowOrchestrator:
    """
    Base orchestrator for LangGraph workflows.
    Provides common functionality for workflow execution, error handling, and monitoring.
    """

    def __init__(
        self,
        workflow_name: str,
        max_retries: int = 3,
        timeout_seconds: int = 300
    ):
        self.workflow_name = workflow_name
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(f"workflow.{workflow_name}")
        self.error_service = get_error_handling_service()
    
    def create_initial_state(
        self,
        **kwargs
    ) -> BaseWorkflowState:
        """Create initial workflow state with common fields."""
        return BaseWorkflowState(
            workflow_id=str(uuid.uuid4()),
            workflow_name=self.workflow_name,
            status=WorkflowStatus.PENDING,
            started_at=datetime.utcnow().isoformat(),
            completed_at=None,
            current_node=None,
            visited_nodes=[],
            retry_count=0,
            max_retries=self.max_retries,
            errors=[],
            warnings=[],
            result=None,
            metadata=kwargs
        )
    
    def mark_node_start(
        self,
        state: BaseWorkflowState,
        node_name: str
    ) -> BaseWorkflowState:
        """Mark the start of a node execution."""
        state["current_node"] = node_name
        if node_name not in state.get("visited_nodes", []):
            state.setdefault("visited_nodes", []).append(node_name)
        
        self.logger.info(
            f"[{state['workflow_id']}] Starting node: {node_name} "
            f"(visited: {len(state.get('visited_nodes', []))})"
        )
        return state
    
    def mark_node_complete(
        self,
        state: BaseWorkflowState,
        node_name: str,
        result: Optional[Dict[str, Any]] = None
    ) -> BaseWorkflowState:
        """Mark the completion of a node execution."""
        self.logger.info(
            f"[{state['workflow_id']}] Completed node: {node_name}"
        )
        
        if result:
            state.setdefault("metadata", {}).setdefault("node_results", {})[node_name] = result
        
        return state
    
    def add_error(
        self,
        state: BaseWorkflowState,
        error: Exception,
        node_name: Optional[str] = None,
        recoverable: bool = False,
        user_id: Optional[str] = None
    ) -> BaseWorkflowState:
        """
        Add an error to the workflow state with intelligent error handling.

        Uses ErrorHandlingService to:
        - Classify the error
        - Determine recovery strategy
        - Generate user-friendly messages
        - Track circuit breakers
        """
        # Create error context
        context = ErrorContext(
            error=error,
            operation=node_name or state.get("current_node", "unknown"),
            node_name=node_name,
            workflow_id=state.get("workflow_id"),
            user_id=user_id or state.get("metadata", {}).get("user_id"),
            metadata=state.get("metadata", {})
        )

        # Get error resolution from service
        resolution = self.error_service.handle_error(context)

        # Create enhanced error entry
        error_entry = {
            "node": node_name or state.get("current_node"),
            "error": str(error),
            "error_type": type(error).__name__,
            "recoverable": recoverable or (resolution.recovery_strategy in [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.FALLBACK,
                RecoveryStrategy.SKIP
            ]),
            "timestamp": datetime.utcnow().isoformat(),
            # Enhanced fields from error service
            "category": resolution.category.value,
            "recovery_strategy": resolution.recovery_strategy.value,
            "user_message": resolution.user_message,
            "suggested_actions": resolution.suggested_actions,
            "retry_after_seconds": resolution.retry_after_seconds,
            "circuit_breaker_open": resolution.metadata.get("circuit_breaker_open", False)
        }

        state.setdefault("errors", []).append(error_entry)

        self.logger.error(
            f"[{state['workflow_id']}] Error in {node_name}: {str(error)} | "
            f"Category: {resolution.category.value} | "
            f"Strategy: {resolution.recovery_strategy.value}",
            exc_info=error
        )

        return state
    
    def add_warning(
        self,
        state: BaseWorkflowState,
        message: str,
        node_name: Optional[str] = None
    ) -> BaseWorkflowState:
        """Add a warning to the workflow state."""
        warning_entry = {
            "node": node_name or state.get("current_node"),
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        state.setdefault("warnings", []).append(warning_entry)
        
        self.logger.warning(
            f"[{state['workflow_id']}] Warning in {node_name}: {message}"
        )
        
        return state
    
    def should_retry(self, state: BaseWorkflowState) -> bool:
        """Determine if the workflow should retry."""
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", self.max_retries)
        
        # Check if we have recoverable errors
        errors = state.get("errors", [])
        has_recoverable = any(e.get("recoverable", False) for e in errors)
        
        return retry_count < max_retries and has_recoverable
    
    def increment_retry(self, state: BaseWorkflowState) -> BaseWorkflowState:
        """Increment the retry counter."""
        state["retry_count"] = state.get("retry_count", 0) + 1
        self.logger.info(
            f"[{state['workflow_id']}] Retry attempt {state['retry_count']}/{state.get('max_retries', self.max_retries)}"
        )
        return state
    
    def mark_completed(
        self,
        state: BaseWorkflowState,
        result: Optional[Dict[str, Any]] = None
    ) -> BaseWorkflowState:
        """Mark the workflow as completed."""
        state["status"] = WorkflowStatus.COMPLETED
        state["completed_at"] = datetime.utcnow().isoformat()
        state["current_node"] = None
        
        if result:
            state["result"] = result
        
        duration = (
            datetime.fromisoformat(state["completed_at"]) -
            datetime.fromisoformat(state["started_at"])
        ).total_seconds()
        
        self.logger.info(
            f"[{state['workflow_id']}] Workflow completed successfully "
            f"(duration: {duration:.2f}s, nodes: {len(state.get('visited_nodes', []))})"
        )
        
        return state
    
    def mark_failed(
        self,
        state: BaseWorkflowState,
        error: Optional[Exception] = None
    ) -> BaseWorkflowState:
        """Mark the workflow as failed."""
        state["status"] = WorkflowStatus.FAILED
        state["completed_at"] = datetime.utcnow().isoformat()
        state["current_node"] = None
        
        if error:
            self.add_error(state, error, recoverable=False)
        
        self.logger.error(
            f"[{state['workflow_id']}] Workflow failed "
            f"(errors: {len(state.get('errors', []))})"
        )
        
        return state
    
    def mark_partial(
        self,
        state: BaseWorkflowState,
        result: Optional[Dict[str, Any]] = None
    ) -> BaseWorkflowState:
        """Mark the workflow as partially completed."""
        state["status"] = WorkflowStatus.PARTIAL
        state["completed_at"] = datetime.utcnow().isoformat()
        state["current_node"] = None
        
        if result:
            state["result"] = result
        
        self.logger.warning(
            f"[{state['workflow_id']}] Workflow partially completed "
            f"(errors: {len(state.get('errors', []))}, warnings: {len(state.get('warnings', []))})"
        )
        
        return state
    
    def get_last_error_resolution(self, state: BaseWorkflowState) -> Optional[Dict[str, Any]]:
        """
        Get the last error resolution with recovery strategy.

        Returns:
            Dictionary with error details and suggested actions, or None if no errors
        """
        errors = state.get("errors", [])
        if not errors:
            return None

        last_error = errors[-1]
        return {
            "error_message": last_error.get("user_message", last_error.get("error")),
            "category": last_error.get("category"),
            "recovery_strategy": last_error.get("recovery_strategy"),
            "suggested_actions": last_error.get("suggested_actions", []),
            "retry_after_seconds": last_error.get("retry_after_seconds"),
            "circuit_breaker_open": last_error.get("circuit_breaker_open", False)
        }

    def get_execution_summary(self, state: BaseWorkflowState) -> Dict[str, Any]:
        """Get a summary of the workflow execution."""
        duration = None
        if state.get("completed_at") and state.get("started_at"):
            duration = (
                datetime.fromisoformat(state["completed_at"]) -
                datetime.fromisoformat(state["started_at"])
            ).total_seconds()

        return {
            "workflow_id": state.get("workflow_id"),
            "workflow_name": state.get("workflow_name"),
            "status": state.get("status"),
            "duration_seconds": duration,
            "nodes_visited": len(state.get("visited_nodes", [])),
            "errors_count": len(state.get("errors", [])),
            "warnings_count": len(state.get("warnings", [])),
            "retry_count": state.get("retry_count", 0),
            "has_result": state.get("result") is not None,
            "last_error_resolution": self.get_last_error_resolution(state)
        }

