"""Conversation Service - Manage conversation history and memory."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func, text
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import OperationalError

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
        title: Optional[str] = None,
        persona: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> Conversation:
        """Create a new conversation thread."""
        try:
            conversation = Conversation(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id) if user_id else None,
                home_id=uuid.UUID(home_id) if home_id else None,
                title=title,
                persona=persona,
                scenario=scenario,
                is_active=True,
                message_count=0
            )

            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)

            logger.info(f"Created conversation: {conversation.id}")
            return conversation

        except OperationalError as e:
            # Fallback for dev DBs without new columns: insert only core columns via raw SQL
            await self.db.rollback()
            try:
                conv_id = uuid.uuid4()
                now = datetime.utcnow()
                sql = text(
                    """
                    INSERT INTO conversations (
                        id, user_id, home_id, title, is_active, message_count, created_at, updated_at, last_message_at
                    ) VALUES (
                        :id, :user_id, :home_id, :title, :is_active, :message_count, :created_at, :updated_at, :last_message_at
                    )
                    """
                )
                await self.db.execute(sql, {
                    "id": str(conv_id),
                    "user_id": str(uuid.UUID(user_id)) if user_id else None,
                    "home_id": str(uuid.UUID(home_id)) if home_id else None,
                    "title": title or "New Conversation",
                    "is_active": True,
                    "message_count": 0,
                    "created_at": now,
                    "updated_at": now,
                    "last_message_at": None,
                })
                await self.db.commit()

                # Construct a Conversation instance without touching ORM persistence (avoid SELECT *)
                conversation = Conversation(
                    id=conv_id,
                    user_id=uuid.UUID(user_id) if user_id else None,
                    home_id=uuid.UUID(home_id) if home_id else None,
                    title=title or "New Conversation",
                    is_active=True,
                    message_count=0,
                )
                setattr(conversation, "created_at", now)
                setattr(conversation, "updated_at", now)
                setattr(conversation, "last_message_at", None)
                setattr(conversation, "summary", None)
                setattr(conversation, "persona", None)
                setattr(conversation, "scenario", None)

                logger.warning(
                    "Created conversation via raw SQL without persona/scenario (columns missing). "
                    "Run migrations to add them when ready."
                )
                return conversation
            except Exception as e2:
                await self.db.rollback()
                logger.error(f"Failed to create conversation (raw SQL fallback): {e2}", exc_info=True)
                raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create conversation: {e}", exc_info=True)
            raise

    async def update_conversation_attributes(
        self,
        conversation_id: str,
        *,
        persona: Optional[str] = None,
        scenario: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Optional[Conversation]:
        """Update mutable conversation attributes like persona, scenario, title."""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return None

            updated = False
            if persona is not None and conversation.persona != persona:
                conversation.persona = persona
                updated = True
            if scenario is not None and conversation.scenario != scenario:
                conversation.scenario = scenario
                updated = True
            if title is not None and conversation.title != title:
                conversation.title = title
                updated = True

            if updated:
                conversation.updated_at = datetime.utcnow()
                await self.db.commit()
                await self.db.refresh(conversation)
            return conversation
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update conversation attributes: {e}", exc_info=True)
            return None

    async def update_conversation_title(self, conversation_id: str, user_message: str) -> Optional[Conversation]:
        """Set a conversation title, generating one from the first user message if needed."""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return None
            if not conversation.title:
                conversation.title = await self._generate_title(user_message)
                conversation.updated_at = datetime.utcnow()
                await self.db.commit()
                await self.db.refresh(conversation)
            return conversation
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update conversation title: {e}", exc_info=True)
            return None

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

            try:
                result = await self.db.execute(query)
                conversation = result.scalar_one_or_none()
                return conversation
            except OperationalError:
                # Fallback: query minimal columns to avoid missing new columns in older DBs
                sql = text(
                    """
                    SELECT id, user_id, home_id, title, is_active, message_count, created_at, updated_at, last_message_at
                    FROM conversations
                    WHERE id = :id
                    LIMIT 1
                    """
                )
                res = await self.db.execute(sql, {"id": str(uuid.UUID(conversation_id))})
                row = res.mappings().first()
                if not row:
                    return None
                conv = Conversation(
                    id=uuid.UUID(str(row["id"])),
                    user_id=uuid.UUID(str(row["user_id"])) if row.get("user_id") else None,
                    home_id=uuid.UUID(str(row["home_id"])) if row.get("home_id") else None,
                    title=row.get("title"),
                    is_active=bool(row.get("is_active")) if row.get("is_active") is not None else True,
                    message_count=int(row.get("message_count") or 0),
                )
                setattr(conv, "created_at", row.get("created_at"))
                setattr(conv, "updated_at", row.get("updated_at"))
                setattr(conv, "last_message_at", row.get("last_message_at"))
                setattr(conv, "summary", None)
                setattr(conv, "persona", None)
                setattr(conv, "scenario", None)
                return conv

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
            else:
                # Fallback for older DB schemas: raw SQL increment without touching new columns
                try:
                    now = datetime.utcnow()
                    await self.db.execute(
                        text("""
                            UPDATE conversations
                            SET message_count = COALESCE(message_count, 0) + 1,
                                last_message_at = :now,
                                updated_at = :now
                            WHERE id = :id
                        """),
                        {"now": now, "id": str(uuid.UUID(conversation_id))}
                    )
                except Exception as ue:
                    logger.debug(f"Fallback update of conversation counters failed: {ue}")

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

    async def build_context_window(
        self,
        conversation_id: str,
        max_messages: int = 10,
        include_summaries: bool = True,
        max_summaries: int = 2,
    ) -> List[Dict[str, Any]]:
        """Build a compact context window for chat.

        Returns a list of message dicts suitable for ChatWorkflow.conversation_history.
        When summaries exist (and include_summaries is True), they are injected as
        special entries with type="summary" before the recent turn messages.
        """
        try:
            # Start with the most recent messages
            recent_messages = await self.get_recent_messages(
                conversation_id=conversation_id,
                count=max_messages,
            )

            history: List[Dict[str, Any]] = []

            if include_summaries:
                # Fetch up to max_summaries most recent summaries
                summaries = await self.get_summaries_for_conversation(
                    conversation_id=conversation_id,
                    limit=max_summaries,
                )

                # Order oldest -> newest so the prompt reads chronologically
                for summary in reversed(summaries):
                    history.append(
                        {
                            "role": "system",
                            "type": "summary",
                            "content": summary.summary_text,
                            "key_topics": summary.key_topics,
                            "created_at": summary.created_at.isoformat()
                            if getattr(summary, "created_at", None)
                            else None,
                        }
                    )

            # Then append the most recent conversation turns
            if recent_messages:
                history.extend(recent_messages[-max_messages:])

            return history

        except Exception as e:
            logger.error(
                f"Failed to build context window for conversation {conversation_id}: {e}",
                exc_info=True,
            )
            # Fall back to a simple recent-message window
            return await self.get_recent_messages(conversation_id=conversation_id, count=max_messages)

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

            try:
                result = await self.db.execute(query)
                conversations = result.scalars().all()
                return list(conversations)
            except OperationalError as oe:
                logger.warning(
                    "List conversations failed due to schema mismatch (likely missing columns). "
                    "Falling back to minimal column query.")
                # Fallback: query only core columns present in older schemas
                uid = str(uuid.UUID(user_id)) if user_id else None
                hid = str(uuid.UUID(home_id)) if home_id else None
                sql = text(
                    """
                    SELECT id, user_id, home_id, title, is_active, message_count, created_at, updated_at, last_message_at
                    FROM conversations
                    WHERE (:uid IS NULL OR user_id = :uid)
                      AND (:hid IS NULL OR home_id = :hid)
                      AND (:active IS NULL OR is_active = :active)
                    ORDER BY updated_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                )
                result = await self.db.execute(sql, {
                    "uid": uid,
                    "hid": hid,
                    "active": is_active,
                    "limit": limit,
                    "offset": offset,
                })
                rows = result.mappings().all()
                # Build lightweight Conversation objects (detached)
                conversations: List[Conversation] = []
                for r in rows:
                    try:
                        conv = Conversation(
                            id=uuid.UUID(str(r["id"])) if r.get("id") else uuid.uuid4(),
                            user_id=uuid.UUID(str(r["user_id"])) if r.get("user_id") else None,
                            home_id=uuid.UUID(str(r["home_id"])) if r.get("home_id") else None,
                            title=r.get("title"),
                            is_active=bool(r.get("is_active")) if r.get("is_active") is not None else True,
                            message_count=int(r.get("message_count") or 0),
                        )
                        # Set timestamps if present
                        setattr(conv, "created_at", r.get("created_at"))
                        setattr(conv, "updated_at", r.get("updated_at"))
                        setattr(conv, "last_message_at", r.get("last_message_at"))
                        # Ensure missing new fields are None
                        setattr(conv, "summary", None)
                        setattr(conv, "persona", None)
                        setattr(conv, "scenario", None)
                        conversations.append(conv)
                    except Exception as be:
                        logger.debug(f"Skipping row in fallback mapping: {be}")
                return conversations
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}", exc_info=True)
            return []

    async def get_summaries_for_conversation(
        self,
        conversation_id: str,
        limit: int = 3,
    ) -> List[ConversationSummary]:
        """Return up to `limit` most recent summaries for a conversation.

        Results are ordered from newest to oldest. This is used by the chat
        workflow to inject concise summaries before the recent turn history.
        """
        try:
            query = (
                select(ConversationSummary)
                .where(ConversationSummary.conversation_id == uuid.UUID(conversation_id))
                .order_by(desc(ConversationSummary.created_at))
                .limit(limit)
            )

            result = await self.db.execute(query)
            summaries = result.scalars().all()
            return list(summaries)

        except Exception as e:
            logger.error(
                f"Failed to load conversation summaries for {conversation_id}: {e}",
                exc_info=True,
            )
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
            logger.error(
                f"Failed to delete conversation {conversation_id}: {e}",
                exc_info=True,
            )
            return False

    async def maybe_generate_summary(
        self,
        conversation_id: str,
        message_threshold: int = 20,
    ) -> Optional[ConversationSummary]:
        """Generate a new summary if enough new messages have accumulated.

        This is a lightweight wrapper around `generate_summary` that:
        - Checks total message_count on the conversation
        - Looks at the most recent existing summary (if any)
        - Only generates a new summary when at least `message_threshold` new
          messages have been added since the last summary.

        It is safe to call this on every turn; most calls will no-op once
        summaries are up to date.
        """
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return None

            total_messages = int(getattr(conversation, "message_count", 0) or 0)

            # Not enough messages overall to justify a summary
            if total_messages < max(5, message_threshold):
                return None

            # Find the most recent summary, if any
            try:
                query = (
                    select(ConversationSummary)
                    .where(ConversationSummary.conversation_id == conversation.id)
                    .order_by(desc(ConversationSummary.created_at))
                    .limit(1)
                )
                result = await self.db.execute(query)
                last_summary = result.scalar_one_or_none()
            except Exception as e:
                logger.warning(
                    f"Failed to load last summary for {conversation_id}: {e}",
                    exc_info=True,
                )
                last_summary = None

            if last_summary is not None:
                summarized_count = int(getattr(last_summary, "message_count", 0) or 0)
                if total_messages - summarized_count < message_threshold:
                    # Fewer than message_threshold new messages since last summary
                    return None

            # Generate and persist a new summary over the most recent messages
            return await self.generate_summary(
                conversation_id=conversation_id,
                message_count=min(total_messages, 50),
            )

        except Exception as e:
            logger.error(
                f"Failed to maybe generate summary for conversation {conversation_id}: {e}",
                exc_info=True,
            )
            return None

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

