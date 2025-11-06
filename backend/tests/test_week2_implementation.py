"""Tests for Week 2: Chat Agent & Context Management Implementation."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from backend.workflows.chat_workflow import ChatWorkflow, ChatState
from backend.services.conversation_service import ConversationService
from backend.services.conversation_manager import ConversationManager
from backend.agents.conversational.context_aware_chat_agent import ContextAwareChatAgent
from backend.models.conversation import Conversation, ConversationMessage, ConversationSummary


class TestChatWorkflow:
    """Test chat orchestration workflow."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        db.add = Mock()
        db.delete = AsyncMock()
        return db
    
    @pytest.fixture
    def chat_workflow(self, mock_db):
        """Create chat workflow instance."""
        return ChatWorkflow(mock_db)
    
    def test_workflow_initialization(self, chat_workflow):
        """Test workflow initializes correctly."""
        assert chat_workflow.orchestrator.workflow_name == "chat_orchestration"
        assert chat_workflow.orchestrator.max_retries == 2
        assert chat_workflow.rag_service is not None
        assert chat_workflow.conversation_service is not None
        assert chat_workflow.gemini_client is not None
        assert chat_workflow.graph is not None
    
    @pytest.mark.asyncio
    async def test_validate_input_success(self, chat_workflow):
        """Test input validation with valid data."""
        state = {
            "workflow_id": str(uuid.uuid4()),
            "user_message": "What's in my kitchen?",
            "conversation_id": str(uuid.uuid4()),
            "home_id": str(uuid.uuid4()),
            "errors": [],
            "execution_metadata": {}
        }

        result = await chat_workflow._validate_input(state)

        assert len(result["errors"]) == 0
        assert result["user_message"] == "What's in my kitchen?"
    
    @pytest.mark.asyncio
    async def test_validate_input_empty_message(self, chat_workflow):
        """Test input validation with empty message."""
        state = {
            "user_message": "",
            "conversation_id": str(uuid.uuid4()),
            "errors": [],
            "execution_metadata": {}
        }

        with pytest.raises(Exception):
            await chat_workflow._validate_input(state)
    
    @pytest.mark.asyncio
    async def test_classify_intent(self, chat_workflow):
        """Test intent classification."""
        state = {
            "workflow_id": str(uuid.uuid4()),
            "user_message": "How much would it cost to renovate my kitchen?",
            "conversation_id": str(uuid.uuid4()),
            "errors": [],
            "execution_metadata": {},
            "response_metadata": {}
        }

        with patch.object(chat_workflow.gemini_client, 'generate_text', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = '{"intent": "cost_estimate", "confidence": 0.9, "requires_home_data": true}'

            result = await chat_workflow._classify_intent(state)

            assert result.get("intent") == "cost_estimate"
            assert "intent_confidence" in result.get("response_metadata", {})
    
    @pytest.mark.asyncio
    async def test_retrieve_context(self, chat_workflow):
        """Test context retrieval."""
        home_id = str(uuid.uuid4())
        state = {
            "workflow_id": str(uuid.uuid4()),
            "user_message": "Tell me about my kitchen",
            "conversation_id": str(uuid.uuid4()),
            "home_id": home_id,
            "context_sources": [],
            "errors": [],
            "execution_metadata": {}
        }

        with patch.object(chat_workflow.rag_service, 'assemble_context', new_callable=AsyncMock) as mock_context:
            mock_context.return_value = {
                "context_text": "Kitchen: 200 sq ft, hardwood floors",
                "metadata": {"total_chunks": 3, "sources": ["rooms", "materials"]},
                "image_urls": []
            }

            result = await chat_workflow._retrieve_context(state)

            assert result.get("retrieved_context") is not None
            assert len(result.get("context_sources", [])) > 0


class TestConversationService:
    """Test conversation service."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        db.add = Mock()
        db.delete = AsyncMock()
        return db
    
    @pytest.fixture
    def conversation_service(self, mock_db):
        """Create conversation service instance."""
        return ConversationService(mock_db)
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, conversation_service, mock_db):
        """Test creating a new conversation."""
        user_id = str(uuid.uuid4())
        home_id = str(uuid.uuid4())
        
        conversation = await conversation_service.create_conversation(
            user_id=user_id,
            home_id=home_id,
            title="Test Conversation"
        )
        
        assert conversation.user_id == uuid.UUID(user_id)
        assert conversation.home_id == uuid.UUID(home_id)
        assert conversation.title == "Test Conversation"
        assert conversation.is_active is True
        assert conversation.message_count == 0
    
    @pytest.mark.asyncio
    async def test_add_message(self, conversation_service, mock_db):
        """Test adding a message to conversation."""
        conversation_id = str(uuid.uuid4())
        
        # Mock get_conversation to return a conversation
        mock_conversation = Conversation(
            id=uuid.UUID(conversation_id),
            message_count=0,
            is_active=True
        )
        
        with patch.object(conversation_service, 'get_conversation', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_conversation
            
            message = await conversation_service.add_message(
                conversation_id=conversation_id,
                role="user",
                content="Hello!",
                intent="general_chat"
            )
            
            assert message.role == "user"
            assert message.content == "Hello!"
            assert message.intent == "general_chat"
    
    @pytest.mark.asyncio
    async def test_get_recent_messages(self, conversation_service, mock_db):
        """Test getting recent messages."""
        conversation_id = str(uuid.uuid4())
        
        # Mock messages
        mock_messages = [
            ConversationMessage(
                id=uuid.uuid4(),
                conversation_id=uuid.UUID(conversation_id),
                role="user",
                content="Hello",
                created_at=datetime.utcnow()
            ),
            ConversationMessage(
                id=uuid.uuid4(),
                conversation_id=uuid.UUID(conversation_id),
                role="assistant",
                content="Hi there!",
                created_at=datetime.utcnow()
            )
        ]
        
        with patch.object(conversation_service, 'get_messages', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_messages
            
            messages = await conversation_service.get_recent_messages(conversation_id, count=10)
            
            assert len(messages) == 2
            assert messages[0]["role"] == "user"
            assert messages[1]["role"] == "assistant"


class TestConversationManager:
    """Test conversation manager."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        return db
    
    @pytest.fixture
    def conversation_manager(self, mock_db):
        """Create conversation manager instance."""
        return ConversationManager(mock_db)
    
    @pytest.mark.asyncio
    async def test_analyze_conversation_turn(self, conversation_manager):
        """Test analyzing a conversation turn."""
        conversation_id = str(uuid.uuid4())
        current_message = "What about the bathroom?"
        previous_messages = [
            {"role": "user", "content": "Tell me about my kitchen"},
            {"role": "assistant", "content": "Your kitchen is 200 sq ft with hardwood floors"}
        ]
        
        with patch.object(conversation_manager.gemini_client, 'generate_text', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = '''{
                "is_follow_up": true,
                "needs_clarification": false,
                "clarification_questions": [],
                "topic_changed": true,
                "current_topic": "bathroom",
                "referenced_entities": ["bathroom"],
                "confidence": 0.9
            }'''
            
            analysis = await conversation_manager.analyze_conversation_turn(
                conversation_id=conversation_id,
                current_message=current_message,
                previous_messages=previous_messages
            )
            
            assert analysis["is_follow_up"] is True
            assert analysis["topic_changed"] is True
            assert "bathroom" in analysis["referenced_entities"]
    
    @pytest.mark.asyncio
    async def test_detect_ambiguity(self, conversation_manager):
        """Test detecting ambiguity in user message."""
        user_message = "I want to paint it"
        
        with patch.object(conversation_manager.gemini_client, 'generate_text', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = '''{
                "is_ambiguous": true,
                "ambiguity_type": "missing_info",
                "suggestions": ["Which room?", "What color?"],
                "confidence": 0.85
            }'''
            
            result = await conversation_manager.detect_ambiguity(user_message)
            
            assert result["is_ambiguous"] is True
            assert result["ambiguity_type"] == "missing_info"
            assert len(result["suggestions"]) > 0
    
    @pytest.mark.asyncio
    async def test_resolve_references(self, conversation_manager):
        """Test resolving pronouns and references."""
        user_message = "How much would it cost?"
        conversation_history = [
            {"role": "user", "content": "Tell me about kitchen renovation"},
            {"role": "assistant", "content": "Kitchen renovation typically involves..."}
        ]
        
        with patch.object(conversation_manager.gemini_client, 'generate_text', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = '''{
                "resolved_message": "How much would kitchen renovation cost?",
                "references_found": [{"pronoun": "it", "refers_to": "kitchen renovation"}],
                "confidence": 0.9
            }'''
            
            result = await conversation_manager.resolve_references(user_message, conversation_history)
            
            assert "kitchen renovation" in result["resolved_message"]
            assert len(result["references_found"]) > 0


class TestContextAwareChatAgent:
    """Test context-aware chat agent."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        return db
    
    @pytest.fixture
    def chat_agent(self, mock_db):
        """Create chat agent instance."""
        return ContextAwareChatAgent(mock_db)
    
    def test_agent_initialization(self, chat_agent):
        """Test agent initializes correctly."""
        assert chat_agent.name == "context_aware_chat"
        assert chat_agent.rag_service is not None
        assert chat_agent.conversation_service is not None
        assert chat_agent.cost_agent is not None
        assert chat_agent.product_agent is not None
    
    @pytest.mark.asyncio
    async def test_process_missing_message(self, chat_agent):
        """Test processing with missing user message."""
        response = await chat_agent.process({})
        
        assert response.success is False
        assert "user_message is required" in response.error
    
    @pytest.mark.asyncio
    async def test_process_with_valid_input(self, chat_agent):
        """Test processing with valid input."""
        with patch.object(chat_agent, '_classify_intent', new_callable=AsyncMock) as mock_intent, \
             patch.object(chat_agent, '_generate_response', new_callable=AsyncMock) as mock_response, \
             patch.object(chat_agent.rag_service, 'assemble_context', new_callable=AsyncMock) as mock_context, \
             patch.object(chat_agent.conversation_service, 'get_recent_messages', new_callable=AsyncMock) as mock_history:
            
            mock_intent.return_value = {"intent": "question", "confidence": 0.8}
            mock_response.return_value = "Here's information about your kitchen..."
            mock_context.return_value = {
                "context_text": "Kitchen data",
                "metadata": {"total_chunks": 2, "sources": ["rooms"]},
                "image_urls": []
            }
            mock_history.return_value = []
            
            response = await chat_agent.process({
                "user_message": "Tell me about my kitchen",
                "home_id": str(uuid.uuid4()),
                "conversation_id": str(uuid.uuid4())
            })
            
            assert response.success is True
            assert "ai_response" in response.data
            assert "intent" in response.data
            assert "suggested_actions" in response.data


class TestIntegration:
    """Integration tests for chat system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_chat_flow(self):
        """Test complete chat flow from message to response."""
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.execute = AsyncMock()
        
        chat_agent = ContextAwareChatAgent(mock_db)
        
        with patch.object(chat_agent, '_classify_intent', new_callable=AsyncMock) as mock_intent, \
             patch.object(chat_agent, '_generate_response', new_callable=AsyncMock) as mock_response, \
             patch.object(chat_agent.rag_service, 'assemble_context', new_callable=AsyncMock) as mock_context:
            
            mock_intent.return_value = {"intent": "question", "confidence": 0.9}
            mock_response.return_value = "Your kitchen is 200 sq ft with hardwood floors."
            mock_context.return_value = {
                "context_text": "Kitchen: 200 sq ft",
                "metadata": {"total_chunks": 1, "sources": ["rooms"]},
                "image_urls": []
            }
            
            response = await chat_agent.process({
                "user_message": "What's in my kitchen?",
                "home_id": str(uuid.uuid4())
            })
            
            assert response.success is True
            assert "kitchen" in response.data["ai_response"].lower()

