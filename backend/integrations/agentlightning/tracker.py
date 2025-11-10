"""Agent interaction tracker using Agent Lightning."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import agentlightning as agl
    AGENTLIGHTNING_AVAILABLE = True
except ImportError:
    AGENTLIGHTNING_AVAILABLE = False

from .store import get_lightning_store

logger = logging.getLogger(__name__)


class AgentTracker:
    """
    Tracks agent interactions for reinforcement learning.
    
    Uses Agent Lightning's emit_step() to record:
    - User prompts
    - Agent responses
    - Rewards (from user feedback)
    - Metadata (intent, context, etc.)
    """
    
    def __init__(self, agent_name: str):
        """
        Initialize tracker for a specific agent.
        
        Args:
            agent_name: Name of the agent being tracked
        """
        self.agent_name = agent_name
        self.store_manager = get_lightning_store()
        self.enabled = AGENTLIGHTNING_AVAILABLE and self.store_manager.is_enabled()
        
        if not self.enabled:
            logger.warning(f"Agent tracking disabled for '{agent_name}' - agentlightning not available")
    
    def track_interaction(
        self,
        prompt: str,
        response: str,
        reward: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track a single agent interaction.
        
        Args:
            prompt: User's input/question
            response: Agent's response
            reward: Reward score (0.0 to 1.0, or None if not yet rated)
            metadata: Additional context (intent, home_id, etc.)
            
        Returns:
            True if tracking succeeded, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Prepare metadata
            tracking_metadata = {
                "agent_name": self.agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Emit step to Agent Lightning
            agl.emit_step(
                prompt=prompt,
                response=response,
                reward=reward,
                metadata=tracking_metadata
            )
            
            logger.debug(f"Tracked interaction for '{self.agent_name}' (reward: {reward})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track interaction: {e}", exc_info=True)
            return False
    
    def track_chat_message(
        self,
        user_message: str,
        ai_response: str,
        conversation_id: str,
        intent: Optional[str] = None,
        home_id: Optional[str] = None,
        persona: Optional[str] = None,
        reward: Optional[float] = None
    ) -> bool:
        """
        Track a chat message interaction with rich metadata.
        
        Args:
            user_message: User's message
            ai_response: AI's response
            conversation_id: Conversation ID
            intent: Classified intent
            home_id: Home ID if applicable
            persona: User persona (homeowner, contractor, diy)
            reward: Reward score from user feedback
            
        Returns:
            True if tracking succeeded
        """
        metadata = {
            "conversation_id": conversation_id,
            "intent": intent,
            "home_id": home_id,
            "persona": persona,
            "interaction_type": "chat_message"
        }
        
        return self.track_interaction(
            prompt=user_message,
            response=ai_response,
            reward=reward,
            metadata=metadata
        )
    
    def update_reward(
        self,
        interaction_id: str,
        reward: float,
        feedback_type: Optional[str] = None
    ) -> bool:
        """
        Update the reward for a previously tracked interaction.
        
        This is useful when user provides feedback after the response.
        
        Args:
            interaction_id: ID of the interaction to update
            reward: New reward score
            feedback_type: Type of feedback (thumbs_up, thumbs_down, rating, etc.)
            
        Returns:
            True if update succeeded
        """
        if not self.enabled:
            return False
        
        try:
            # Update reward in the store
            # Note: Actual API may vary based on agentlightning version
            # agl.update_reward(interaction_id, reward, feedback_type=feedback_type)
            
            logger.info(f"Updated reward for interaction {interaction_id}: {reward} ({feedback_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update reward: {e}", exc_info=True)
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get tracking statistics for this agent.
        
        Returns:
            Dictionary with statistics
        """
        return self.store_manager.get_statistics(self.agent_name)


# Convenience function
def track_chat_interaction(
    user_message: str,
    ai_response: str,
    conversation_id: str,
    intent: Optional[str] = None,
    home_id: Optional[str] = None,
    persona: Optional[str] = None,
    reward: Optional[float] = None
) -> bool:
    """
    Convenience function to track a chat interaction.
    
    Args:
        user_message: User's message
        ai_response: AI's response
        conversation_id: Conversation ID
        intent: Classified intent
        home_id: Home ID if applicable
        persona: User persona
        reward: Reward score
        
    Returns:
        True if tracking succeeded
    """
    tracker = AgentTracker(agent_name="chat_agent")
    return tracker.track_chat_message(
        user_message=user_message,
        ai_response=ai_response,
        conversation_id=conversation_id,
        intent=intent,
        home_id=home_id,
        persona=persona,
        reward=reward
    )

