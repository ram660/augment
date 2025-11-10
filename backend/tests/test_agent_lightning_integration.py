"""Tests for Agent Lightning integration."""

import pytest
from backend.integrations.agentlightning.store import LightningStoreManager, get_lightning_store
from backend.integrations.agentlightning.tracker import AgentTracker
from backend.integrations.agentlightning.rewards import RewardCalculator, FeedbackType


class TestLightningStore:
    """Test LightningStore manager."""
    
    def test_store_initialization(self):
        """Test that LightningStore initializes correctly."""
        store = LightningStoreManager()
        
        # Should initialize even if agentlightning is not available
        assert store is not None
        
        # Check if enabled
        if store.is_enabled():
            assert store.store is not None
            assert store.db_url is not None
    
    def test_singleton_pattern(self):
        """Test that get_lightning_store returns singleton."""
        store1 = get_lightning_store()
        store2 = get_lightning_store()
        
        assert store1 is store2
    
    def test_get_statistics(self):
        """Test getting statistics."""
        store = get_lightning_store()
        stats = store.get_statistics("chat_agent")
        
        assert "enabled" in stats
        assert "total_interactions" in stats
        assert "avg_reward" in stats


class TestAgentTracker:
    """Test AgentTracker."""
    
    def test_tracker_initialization(self):
        """Test tracker initialization."""
        tracker = AgentTracker(agent_name="test_agent")
        
        assert tracker.agent_name == "test_agent"
        assert tracker.store_manager is not None
    
    def test_track_interaction(self):
        """Test tracking a simple interaction."""
        tracker = AgentTracker(agent_name="test_agent")
        
        result = tracker.track_interaction(
            prompt="Test question",
            response="Test answer",
            reward=0.8,
            metadata={"test": True}
        )
        
        # Should return True if tracking succeeded, False if disabled
        assert isinstance(result, bool)
    
    def test_track_chat_message(self):
        """Test tracking a chat message."""
        tracker = AgentTracker(agent_name="chat_agent")
        
        result = tracker.track_chat_message(
            user_message="How much to paint my room?",
            ai_response="Based on a 12x15 room, approximately $500-800.",
            conversation_id="test-conv-123",
            intent="cost_estimate",
            home_id="test-home-456",
            persona="homeowner",
            reward=0.85
        )
        
        assert isinstance(result, bool)
    
    def test_get_statistics(self):
        """Test getting tracker statistics."""
        tracker = AgentTracker(agent_name="chat_agent")
        stats = tracker.get_statistics()
        
        assert "enabled" in stats
        assert "total_interactions" in stats


class TestRewardCalculator:
    """Test RewardCalculator."""
    
    def test_thumbs_up_reward(self):
        """Test reward for thumbs up."""
        calculator = RewardCalculator()
        reward = calculator.calculate_from_feedback(FeedbackType.THUMBS_UP)
        
        assert reward == 1.0
    
    def test_thumbs_down_reward(self):
        """Test reward for thumbs down."""
        calculator = RewardCalculator()
        reward = calculator.calculate_from_feedback(FeedbackType.THUMBS_DOWN)
        
        assert reward == 0.0
    
    def test_rating_rewards(self):
        """Test rewards for different ratings."""
        calculator = RewardCalculator()
        
        rating_5 = calculator.calculate_from_feedback(FeedbackType.RATING_5)
        rating_4 = calculator.calculate_from_feedback(FeedbackType.RATING_4)
        rating_3 = calculator.calculate_from_feedback(FeedbackType.RATING_3)
        rating_2 = calculator.calculate_from_feedback(FeedbackType.RATING_2)
        rating_1 = calculator.calculate_from_feedback(FeedbackType.RATING_1)
        
        assert rating_5 == 1.0
        assert rating_4 == 0.8
        assert rating_3 == 0.5
        assert rating_2 == 0.3
        assert rating_1 == 0.0
        
        # Verify ordering
        assert rating_5 > rating_4 > rating_3 > rating_2 > rating_1
    
    def test_reward_with_bonuses(self):
        """Test reward calculation with additional signals."""
        calculator = RewardCalculator()

        # Base reward
        base_reward = calculator.calculate_from_feedback(FeedbackType.RATING_4)
        assert base_reward == 0.8

        # With intent match bonus
        with_bonus = calculator.calculate_from_feedback(
            FeedbackType.RATING_4,
            additional_signals={"intent_match": True, "response_length": 500}
        )
        assert pytest.approx(with_bonus, 0.01) == 0.9  # 0.8 + 0.1

        # With context bonus
        with_context = calculator.calculate_from_feedback(
            FeedbackType.RATING_4,
            additional_signals={"used_context": True, "response_length": 500}
        )
        assert pytest.approx(with_context, 0.01) == 0.85  # 0.8 + 0.05

        # With both bonuses (capped at 1.0)
        with_both = calculator.calculate_from_feedback(
            FeedbackType.RATING_4,
            additional_signals={"intent_match": True, "used_context": True, "response_length": 500}
        )
        assert pytest.approx(with_both, 0.01) == 0.95  # 0.8 + 0.1 + 0.05
    
    def test_reward_with_penalties(self):
        """Test reward calculation with penalties."""
        calculator = RewardCalculator()

        # Too short response
        short_response = calculator.calculate_from_feedback(
            FeedbackType.RATING_4,
            additional_signals={"response_length": 30}
        )
        assert pytest.approx(short_response, 0.01) == 0.7  # 0.8 - 0.1

        # Too long response
        long_response = calculator.calculate_from_feedback(
            FeedbackType.RATING_4,
            additional_signals={"response_length": 2500}
        )
        assert pytest.approx(long_response, 0.01) == 0.75  # 0.8 - 0.05
    
    def test_implicit_reward(self):
        """Test implicit reward calculation."""
        calculator = RewardCalculator()
        
        # Good response metadata
        good_metadata = {
            "intent_confidence": 0.9,
            "context_used": True,
            "suggested_actions": [{"action": "test"}],
            "response_length": 500
        }
        
        reward = calculator.calculate_implicit_reward(good_metadata)
        
        # Should be above neutral (0.5)
        assert reward > 0.5
        assert reward <= 1.0
        
        # Poor response metadata
        poor_metadata = {
            "intent_confidence": 0.3,
            "context_used": False,
            "suggested_actions": [],
            "response_length": 30
        }
        
        poor_reward = calculator.calculate_implicit_reward(poor_metadata)
        
        # Should be below neutral
        assert poor_reward < 0.5
        assert poor_reward >= 0.0
    
    def test_chat_reward_with_explicit_feedback(self):
        """Test chat reward with explicit user feedback."""
        calculator = RewardCalculator()
        
        reward = calculator.calculate_chat_reward(
            user_feedback=FeedbackType.THUMBS_UP,
            response_metadata={"response_length": 500}
        )
        
        assert reward == 1.0
    
    def test_chat_reward_without_feedback(self):
        """Test chat reward falls back to implicit signals."""
        calculator = RewardCalculator()
        
        reward = calculator.calculate_chat_reward(
            user_feedback=None,
            response_metadata={
                "intent_confidence": 0.8,
                "context_used": True,
                "response_length": 500
            }
        )
        
        # Should use implicit calculation
        assert 0.0 <= reward <= 1.0
    
    def test_reward_explanation(self):
        """Test reward explanation strings."""
        calculator = RewardCalculator()
        
        assert "Excellent" in calculator.get_reward_explanation(0.95)
        assert "Good" in calculator.get_reward_explanation(0.75)
        assert "Acceptable" in calculator.get_reward_explanation(0.5)
        assert "Poor" in calculator.get_reward_explanation(0.35)
        assert "Bad" in calculator.get_reward_explanation(0.1)


class TestIntegration:
    """Integration tests."""
    
    def test_end_to_end_tracking(self):
        """Test complete tracking flow."""
        # 1. Track interaction with implicit reward
        tracker = AgentTracker(agent_name="chat_agent")
        calculator = RewardCalculator()
        
        # Calculate implicit reward
        implicit_reward = calculator.calculate_implicit_reward({
            "intent_confidence": 0.8,
            "context_used": True,
            "response_length": 500
        })
        
        # Track interaction
        result = tracker.track_chat_message(
            user_message="Test question",
            ai_response="Test answer",
            conversation_id="test-conv",
            intent="question",
            reward=implicit_reward
        )
        
        # Should succeed or gracefully fail
        assert isinstance(result, bool)
        
        # 2. User provides feedback
        explicit_reward = calculator.calculate_from_feedback(
            FeedbackType.THUMBS_UP,
            additional_signals={"intent_match": True}
        )
        
        # Track updated reward
        result2 = tracker.track_chat_message(
            user_message="Test question",
            ai_response="Test answer",
            conversation_id="test-conv",
            intent="question",
            reward=explicit_reward
        )
        
        assert isinstance(result2, bool)
        
        # Explicit reward should be higher
        assert explicit_reward >= implicit_reward


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

