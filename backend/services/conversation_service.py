"""Conversation Service - Manage conversation history and memory."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload

from backend.models.conversation import Conversation, ConversationMessage, ConversationSummary
from backend.integrations.gemini.client import GeminiClient

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Service for managing conversations and message history.
    
    Features:
    - Create and manage conversation threads
    - Store and retrieve messages
    - Generate conversation summaries
    - Extract key topics and entities
    - Manage conversation context window
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.gemini_client = GeminiClient()
    
    async def create_conversation(
        self,
        user_id: Optional[str] = None,
        home_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation thread."""
        try:
            conversation = Conversation(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id) if user_id else None,
                home_id=uuid.UUID(home_id) if home_id else None,
                title=title,
                is_active=True,
                message_count=0
            )
            
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)
            
            logger.info(f"Created conversation: {conversation.id}")
            return conversation
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create conversation: {e}", exc_info=True)
            raise
    
    async def get_conversation(
        self,
        conversation_id: str,
        include_messages: bool = False
    ) -> Optional[Conversation]:
        """Get a conversation by ID."""
        try:
            query = select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
            
            if include_messages:
                query = query.options(selectinload(Conversation.messages))
            
            result = await self.db.execute(query)
            conversation = result.scalar_one_or_none()
            
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}", exc_info=True)
            return None
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        intent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        context_sources: Optional[List[str]] = None
    ) -> ConversationMessage:
        """Add a message to a conversation."""
        try:
            # Create message
            message = ConversationMessage(
                id=uuid.uuid4(),
                conversation_id=uuid.UUID(conversation_id),
                role=role,
                content=content,
                intent=intent,
                message_metadata=metadata or {},
                context_sources=context_sources or []
            )
            
            self.db.add(message)
            
            # Update conversation
            conversation = await self.get_conversation(conversation_id)
            if conversation:
                conversation.message_count += 1
                conversation.last_message_at = datetime.utcnow()
                conversation.updated_at = datetime.utcnow()
                
                # Auto-generate title from first user message
                if not conversation.title and role == "user" and conversation.message_count == 1:
                    conversation.title = await self._generate_title(content)
            
            await self.db.commit()
            await self.db.refresh(message)
            
            logger.info(f"Added {role} message to conversation {conversation_id}")
            return message
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to add message: {e}", exc_info=True)
            raise
    
    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ConversationMessage]:
        """Get messages from a conversation."""
        try:
            query = (
                select(ConversationMessage)
                .where(ConversationMessage.conversation_id == uuid.UUID(conversation_id))
                .order_by(ConversationMessage.created_at.asc())
                .limit(limit)
                .offset(offset)
            )
            
            result = await self.db.execute(query)
            messages = result.scalars().all()
            
            return list(messages)
            
        except Exception as e:
            logger.error(f"Failed to get messages: {e}", exc_info=True)
            return []
    
    async def get_recent_messages(
        self,
        conversation_id: str,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent messages formatted for chat context."""
        try:
            messages = await self.get_messages(conversation_id, limit=count)
            
            # Format for chat context
            formatted = []
            for msg in messages[-count:]:  # Last N messages
                formatted.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None
                })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}", exc_info=True)
            return []
    
    async def list_conversations(
        self,
        user_id: Optional[str] = None,
        home_id: Optional[str] = None,
        is_active: bool = True,
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """List conversations with filters."""
        try:
            query = select(Conversation)
            
            # Apply filters
            filters = []
            if user_id:
                filters.append(Conversation.user_id == uuid.UUID(user_id))
            if home_id:
                filters.append(Conversation.home_id == uuid.UUID(home_id))
            if is_active is not None:
                filters.append(Conversation.is_active == is_active)
            
            if filters:
                query = query.where(and_(*filters))
            
            # Order by most recent
            query = query.order_by(desc(Conversation.updated_at)).limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            conversations = result.scalars().all()
            
            return list(conversations)
            
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}", exc_info=True)
            return []
    
    async def archive_conversation(self, conversation_id: str) -> bool:
        """Archive a conversation (mark as inactive)."""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return False
            
            conversation.is_active = False
            conversation.updated_at = datetime.utcnow()
            
            await self.db.commit()
            logger.info(f"Archived conversation: {conversation_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to archive conversation: {e}", exc_info=True)
            return False
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages."""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return False
            
            await self.db.delete(conversation)
            await self.db.commit()
            
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete conversation: {e}", exc_info=True)
            return False
    
    async def generate_summary(
        self,
        conversation_id: str,
        message_count: int = 20
    ) -> Optional[ConversationSummary]:
        """Generate a summary of recent messages."""
        try:
            messages = await self.get_messages(conversation_id, limit=message_count)
            
            if len(messages) < 5:  # Need at least 5 messages to summarize
                logger.info("Not enough messages to summarize")
                return None
            
            # Build conversation text
            conversation_text = "\n".join([
                f"{msg.role.upper()}: {msg.content}"
                for msg in messages
            ])
            
            # Generate summary using Gemini
            summary_prompt = f"""Summarize this conversation concisely. Focus on:
1. Main topics discussed
2. Key decisions or conclusions
3. Important details about the home or project

Conversation:
{conversation_text}

Provide a concise summary (2-3 paragraphs max)."""
            
            summary_text = await self.gemini_client.generate_text(
                prompt=summary_prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Extract key topics
            topics_prompt = f"""From this conversation, extract the main topics as a JSON array of strings.

Conversation:
{conversation_text}

Return ONLY a JSON array like: ["topic1", "topic2", "topic3"]"""
            
            topics_response = await self.gemini_client.generate_text(
                prompt=topics_prompt,
                temperature=0.1,
                max_tokens=200
            )
            
            # Parse topics
            import json
            import re
            try:
                topics_match = re.search(r'\[.*\]', topics_response, re.DOTALL)
                key_topics = json.loads(topics_match.group(0)) if topics_match else []
            except:
                key_topics = []
            
            # Create summary record
            summary = ConversationSummary(
                id=uuid.uuid4(),
                conversation_id=uuid.UUID(conversation_id),
                summary_text=summary_text,
                start_message_id=messages[0].id,
                end_message_id=messages[-1].id,
                message_count=len(messages),
                key_topics=key_topics,
                entities_mentioned={}  # TODO: Extract entities
            )
            
            self.db.add(summary)
            await self.db.commit()
            await self.db.refresh(summary)
            
            logger.info(f"Generated summary for conversation {conversation_id}")
            return summary
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to generate summary: {e}", exc_info=True)
            return None
    
    async def _generate_title(self, first_message: str) -> str:
        """Generate a title from the first message."""
        try:
            # Use first 50 chars or generate with AI
            if len(first_message) <= 50:
                return first_message
            
            # Generate concise title
            title_prompt = f"""Generate a short, concise title (max 50 characters) for a conversation that starts with:

"{first_message}"

Return ONLY the title, nothing else."""
            
            title = await self.gemini_client.generate_text(
                prompt=title_prompt,
                temperature=0.3,
                max_tokens=20
            )
            
            # Clean and truncate
            title = title.strip().strip('"').strip("'")
            return title[:50]
            
        except Exception as e:
            logger.warning(f"Failed to generate title: {e}")
            return first_message[:50]

