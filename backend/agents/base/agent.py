"""Base agent class for all HomeVision AI agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Agent role types."""
    CONVERSATION = "conversation"
    VISION = "vision"
    DESIGN = "design"
    PRODUCT_DISCOVERY = "product_discovery"
    COST_INTELLIGENCE = "cost_intelligence"
    RENDERING = "rendering"
    HOME_PROFILE = "home_profile"
    MAINTENANCE = "maintenance"
    COMPLIANCE = "compliance"
    CONTRACTOR_MATCHING = "contractor_matching"
    RFP_GENERATION = "rfp_generation"
    QUOTE_OPTIMIZATION = "quote_optimization"
    PROJECT_MANAGEMENT = "project_management"
    PAYMENT = "payment"
    SYNC = "sync"
    NOTIFICATION = "notification"
    VERIFICATION = "verification"
    REPUTATION = "reputation"


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    name: str
    role: AgentRole
    description: str
    model_name: Optional[str] = "gemini-2.0-flash-exp"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout_seconds: int = 30
    retry_attempts: int = 3
    enable_memory: bool = True
    memory_window: int = 10  # Number of previous interactions to remember
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Standard response format from agents."""
    agent_name: str
    agent_role: AgentRole
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: Optional[float] = None


class BaseAgent(ABC):
    """
    Base class for all agents in the HomeVision AI system.
    
    All agents should inherit from this class and implement the required methods.
    Provides common functionality for:
    - Configuration management
    - Memory/context handling
    - Error handling and retries
    - Logging and monitoring
    - Response formatting
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.name = config.name
        self.role = config.role
        self.logger = logging.getLogger(f"agent.{self.name}")
        self.memory: Optional[Any] = None
        
        if config.enable_memory:
            from .memory import AgentMemory
            self.memory = AgentMemory(window_size=config.memory_window)
        
        self.logger.info(f"Initialized agent: {self.name} (role: {self.role})")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process input and return a response.
        
        This is the main method that each agent must implement.
        
        Args:
            input_data: Input data for the agent to process
            
        Returns:
            AgentResponse with the result
        """
        pass
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Execute the agent with error handling and retries.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            AgentResponse with the result
        """
        start_time = datetime.utcnow()
        
        for attempt in range(self.config.retry_attempts):
            try:
                self.logger.info(f"Executing {self.name} (attempt {attempt + 1}/{self.config.retry_attempts})")
                
                # Add to memory if enabled
                if self.memory:
                    self.memory.add_interaction(input_data, None)
                
                # Process the input
                response = await self.process(input_data)
                
                # Calculate execution time
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                response.execution_time_ms = execution_time
                
                # Update memory with response
                if self.memory and response.success:
                    self.memory.update_last_response(response.data)
                
                self.logger.info(f"{self.name} completed in {execution_time:.2f}ms")
                return response
                
            except Exception as e:
                self.logger.error(f"{self.name} error (attempt {attempt + 1}): {str(e)}", exc_info=True)
                
                if attempt == self.config.retry_attempts - 1:
                    # Last attempt failed
                    execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    return AgentResponse(
                        agent_name=self.name,
                        agent_role=self.role,
                        success=False,
                        error=str(e),
                        execution_time_ms=execution_time
                    )
                
                # Wait before retry (exponential backoff)
                import asyncio
                await asyncio.sleep(2 ** attempt)
        
        # Should never reach here, but just in case
        return AgentResponse(
            agent_name=self.name,
            agent_role=self.role,
            success=False,
            error="Max retries exceeded"
        )
    
    def get_context(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get the current context/memory for this agent.
        
        Returns:
            List of previous interactions or None if memory is disabled
        """
        if self.memory:
            return self.memory.get_context()
        return None
    
    def clear_memory(self):
        """Clear the agent's memory."""
        if self.memory:
            self.memory.clear()
            self.logger.info(f"Cleared memory for {self.name}")
    
    def update_config(self, **kwargs):
        """
        Update agent configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"Updated {self.name} config: {key}={value}")
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' role='{self.role}'>"

