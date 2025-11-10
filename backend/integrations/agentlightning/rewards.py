"""Reward calculation for agent optimization."""

import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types of user feedback."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    RATING_1 = "rating_1"
    RATING_2 = "rating_2"
    RATING_3 = "rating_3"
    RATING_4 = "rating_4"
    RATING_5 = "rating_5"
    REGENERATE = "regenerate"  # User asked to regenerate response
    COPY = "copy"  # User copied the response
    FOLLOW_UP = "follow_up"  # User asked a follow-up question


class RewardCalculator:
    """
    Calculates reward scores for agent interactions.
    
    Reward scoring philosophy:
    - 1.0: Excellent response (thumbs up, 5-star rating, user copied response)
    - 0.7-0.9: Good response (4-star rating, follow-up question)
    - 0.5: Neutral (3-star rating, no feedback)
    - 0.2-0.4: Poor response (2-star rating, regenerate request)
    - 0.0: Bad response (thumbs down, 1-star rating)
    
    Additional factors:
    - Response length appropriateness
    - Intent match accuracy
    - Context utilization
    - Action suggestion relevance
    """
    
    @staticmethod
    def calculate_from_feedback(
        feedback_type: FeedbackType,
        additional_signals: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate reward from explicit user feedback.
        
        Args:
            feedback_type: Type of feedback received
            additional_signals: Additional signals (response_length, intent_match, etc.)
            
        Returns:
            Reward score between 0.0 and 1.0
        """
        # Base rewards from feedback type
        base_rewards = {
            FeedbackType.THUMBS_UP: 1.0,
            FeedbackType.THUMBS_DOWN: 0.0,
            FeedbackType.RATING_5: 1.0,
            FeedbackType.RATING_4: 0.8,
            FeedbackType.RATING_3: 0.5,
            FeedbackType.RATING_2: 0.3,
            FeedbackType.RATING_1: 0.0,
            FeedbackType.REGENERATE: 0.2,  # User wasn't satisfied
            FeedbackType.COPY: 0.9,  # User found it useful
            FeedbackType.FOLLOW_UP: 0.7,  # Engaged but not perfect
        }
        
        reward = base_rewards.get(feedback_type, 0.5)
        
        # Adjust based on additional signals
        if additional_signals:
            # Intent match bonus
            if additional_signals.get("intent_match", False):
                reward = min(1.0, reward + 0.1)
            
            # Context utilization bonus
            if additional_signals.get("used_context", False):
                reward = min(1.0, reward + 0.05)
            
            # Response length penalty (too short or too long)
            response_length = additional_signals.get("response_length", 0)
            if response_length < 50:  # Too short
                reward = max(0.0, reward - 0.1)
            elif response_length > 2000:  # Too long
                reward = max(0.0, reward - 0.05)
        
        return max(0.0, min(1.0, reward))
    
    @staticmethod
    def calculate_implicit_reward(
        response_metadata: Dict[str, Any],
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate implicit reward from response quality signals.
        
        Used when explicit feedback is not available.
        
        Args:
            response_metadata: Metadata about the response (intent, context_used, etc.)
            conversation_context: Context about the conversation
            
        Returns:
            Estimated reward score
        """
        # Start with neutral score
        reward = 0.5
        
        # Intent classification confidence
        intent_confidence = response_metadata.get("intent_confidence", 0.5)
        reward += (intent_confidence - 0.5) * 0.2  # ±0.1 based on confidence
        
        # Context utilization
        if response_metadata.get("context_used", False):
            reward += 0.1
        
        # Suggested actions provided
        if response_metadata.get("suggested_actions"):
            reward += 0.05
        
        # Response completeness
        response_length = response_metadata.get("response_length", 0)
        if 100 <= response_length <= 1500:  # Ideal length
            reward += 0.1
        
        # Conversation flow (if available)
        if conversation_context:
            # Penalize if user immediately asks for clarification
            if conversation_context.get("immediate_clarification", False):
                reward -= 0.2
            
            # Bonus if conversation continues naturally
            if conversation_context.get("natural_continuation", False):
                reward += 0.1
        
        return max(0.0, min(1.0, reward))
    
    @staticmethod
    def calculate_chat_reward(
        user_feedback: Optional[FeedbackType] = None,
        response_metadata: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate reward for a chat interaction.
        
        Combines explicit feedback (if available) with implicit signals.
        
        Args:
            user_feedback: Explicit user feedback
            response_metadata: Response quality metadata
            conversation_context: Conversation context
            
        Returns:
            Final reward score
        """
        if user_feedback:
            # Use explicit feedback as primary signal
            return RewardCalculator.calculate_from_feedback(
                feedback_type=user_feedback,
                additional_signals=response_metadata
            )
        else:
            # Fall back to implicit signals
            return RewardCalculator.calculate_implicit_reward(
                response_metadata=response_metadata or {},
                conversation_context=conversation_context
            )
    
    @staticmethod
    def get_reward_explanation(reward: float) -> str:
        """
        Get human-readable explanation of reward score.
        
        Args:
            reward: Reward score
            
        Returns:
            Explanation string
        """
        if reward >= 0.9:
            return "Excellent response - user highly satisfied"
        elif reward >= 0.7:
            return "Good response - user satisfied"
        elif reward >= 0.5:
            return "Acceptable response - neutral feedback"
        elif reward >= 0.3:
            return "Poor response - user somewhat dissatisfied"
        else:
            return "Bad response - user dissatisfied"

