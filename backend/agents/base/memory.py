"""Memory management for agents."""

from typing import Any, Dict, List, Optional
from collections import deque
from datetime import datetime
from pydantic import BaseModel


class Interaction(BaseModel):
    """Represents a single interaction in agent memory."""
    timestamp: datetime
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}


class AgentMemory:
    """
    Simple memory system for agents to maintain context.
    
    Uses a sliding window approach to keep recent interactions.
    """
    
    def __init__(self, window_size: int = 10):
        """
        Initialize agent memory.
        
        Args:
            window_size: Number of interactions to remember
        """
        self.window_size = window_size
        self.interactions: deque = deque(maxlen=window_size)
    
    def add_interaction(self, input_data: Dict[str, Any], output_data: Optional[Dict[str, Any]] = None):
        """
        Add a new interaction to memory.
        
        Args:
            input_data: Input data for the interaction
            output_data: Output data from the interaction (can be added later)
        """
        interaction = Interaction(
            timestamp=datetime.utcnow(),
            input_data=input_data,
            output_data=output_data
        )
        self.interactions.append(interaction)
    
    def update_last_response(self, output_data: Dict[str, Any]):
        """
        Update the output data of the most recent interaction.
        
        Args:
            output_data: Output data to add
        """
        if self.interactions:
            self.interactions[-1].output_data = output_data
    
    def get_context(self) -> List[Dict[str, Any]]:
        """
        Get all interactions as context.
        
        Returns:
            List of interaction dictionaries
        """
        return [interaction.model_dump() for interaction in self.interactions]
    
    def get_recent(self, n: int = 5) -> List[Interaction]:
        """
        Get the n most recent interactions.
        
        Args:
            n: Number of recent interactions to retrieve
            
        Returns:
            List of recent interactions
        """
        return list(self.interactions)[-n:]
    
    def clear(self):
        """Clear all interactions from memory."""
        self.interactions.clear()
    
    def __len__(self) -> int:
        return len(self.interactions)


class ConversationMemory(AgentMemory):
    """
    Extended memory for conversation agents.
    
    Maintains conversation history with role-based messages.
    """
    
    def __init__(self, window_size: int = 20):
        super().__init__(window_size)
        self.messages: deque = deque(maxlen=window_size)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a message to conversation history.
        
        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
    
    def get_messages(self, include_system: bool = True) -> List[Dict[str, Any]]:
        """
        Get conversation messages.
        
        Args:
            include_system: Whether to include system messages
            
        Returns:
            List of messages
        """
        if include_system:
            return list(self.messages)
        return [msg for msg in self.messages if msg["role"] != "system"]
    
    def get_langchain_format(self) -> List[tuple]:
        """
        Get messages in LangChain format.
        
        Returns:
            List of (role, content) tuples
        """
        return [(msg["role"], msg["content"]) for msg in self.messages]
    
    def summarize_context(self) -> str:
        """
        Create a text summary of the conversation.
        
        Returns:
            Summary string
        """
        if not self.messages:
            return "No conversation history."
        
        summary_parts = []
        for msg in self.messages:
            role = msg["role"].upper()
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            summary_parts.append(f"{role}: {content}")
        
        return "\n".join(summary_parts)

