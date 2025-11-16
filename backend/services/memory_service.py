"""Service for storing and retrieving long-lived user memories.

This is a minimal key-value store on top of the UserMemory model. It is
purposely generic so both ChatWorkflow and Design Studio can reuse it.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.memory import UserMemory

logger = logging.getLogger(__name__)


class MemoryService:
    """Simple CRUD-style API for user and conversation memories.

    For this initial Phase 2 slice we keep the API intentionally small:
    - add_or_update_memory: upsert a single fact
    - get_memories_for_user: fetch memories scoped to a user (optionally a home)
    - get_memories_for_conversation: fetch memories tied to a specific conversation

    Higher-level LLM-based extraction will be added in later slices.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_or_update_memory(
        self,
        *,
        user_id: Optional[str] = None,
        home_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        topic: str,
        key: str,
        value: Dict[str, Any],
        source: str = "chat",
        confidence: float = 0.9,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UserMemory:
        """Insert or update a memory.

        Upsert semantics are:
        - If a memory exists for (user_id, home_id, topic, key) we update its
          value/confidence/metadata.
        - Otherwise we insert a new row.
        """

        if not user_id and not conversation_id:
            # We allow purely conversation-scoped memories, but if neither is
            # set this is almost certainly a bug.
            logger.warning(
                "MemoryService.add_or_update_memory called without user_id or conversation_id; "
                "the memory will be stored but may be hard to retrieve."
            )

        # Normalise IDs to UUID objects where possible
        def _to_uuid(val: Optional[str]) -> Optional[uuid.UUID]:
            if not val:
                return None
            if isinstance(val, uuid.UUID):
                return val
            return uuid.UUID(str(val))

        user_uuid = _to_uuid(user_id)
        home_uuid = _to_uuid(home_id)
        conv_uuid = _to_uuid(conversation_id)

        stmt = select(UserMemory).where(
            UserMemory.user_id == user_uuid,
            UserMemory.home_id == home_uuid,
            UserMemory.topic == topic,
            UserMemory.key == key,
        )

        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.value = value
            existing.source = source
            existing.confidence = confidence
            if metadata is not None:
                existing.metadata = metadata
            existing.conversation_id = conv_uuid or existing.conversation_id
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        memory = UserMemory(
            user_id=user_uuid,
            home_id=home_uuid,
            conversation_id=conv_uuid,
            topic=topic,
            key=key,
            value=value,
            source=source,
            confidence=confidence,
            metadata=metadata or {},
        )

        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def get_memories_for_user(
        self,
        *,
        user_id: str,
        home_id: Optional[str] = None,
        topics: Optional[Iterable[str]] = None,
        limit: int = 20,
    ) -> List[UserMemory]:
        """Return recent memories for a user, optionally filtered by topic/home."""

        if not user_id:
            return []

        def _to_uuid(val: Optional[str]) -> Optional[uuid.UUID]:
            if not val:
                return None
            if isinstance(val, uuid.UUID):
                return val
            return uuid.UUID(str(val))

        user_uuid = _to_uuid(user_id)
        home_uuid = _to_uuid(home_id)

        stmt = select(UserMemory).where(UserMemory.user_id == user_uuid)

        if home_uuid is not None:
            stmt = stmt.where(UserMemory.home_id == home_uuid)

        if topics:
            stmt = stmt.where(UserMemory.topic.in_(list(topics)))

        stmt = stmt.order_by(UserMemory.created_at.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_memories_for_conversation(
        self,
        *,
        conversation_id: str,
        limit: int = 20,
    ) -> List[UserMemory]:
        """Return memories associated with a given conversation."""

        if not conversation_id:
            return []

        conv_uuid = uuid.UUID(str(conversation_id))

        stmt = (
            select(UserMemory)
            .where(UserMemory.conversation_id == conv_uuid)
            .order_by(UserMemory.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())


    async def extract_memories_from_conversation(
        self,
        *,
        conversation_id: str,
        user_id: str,
        home_id: Optional[str] = None,
        message_limit: int = 30,
    ) -> List[UserMemory]:
        """Use Gemini to extract structured long-lived memories from a conversation.

        This is best-effort and safe to call periodically (e.g. every N messages).
        Failures are logged but never raised.
        """
        if not conversation_id or not user_id:
            return []

        try:
            # Local imports to avoid circular dependencies at module import time.
            from backend.services.conversation_service import ConversationService
            from backend.integrations.gemini.client import GeminiClient
            import json
            import re

            conv_service = ConversationService(self.db)
            messages = await conv_service.get_messages(conversation_id, limit=message_limit)
            if not messages:
                return []

            # Build plain-text transcript with roles for the LLM.
            conversation_text = "\n".join(
                f"{m.role.upper()}: {m.content}"
                for m in messages
                if getattr(m, "content", None)
            )

            extraction_prompt = f"""You are helping a home improvement assistant remember important long-term facts about a homeowner.

From the conversation below, extract ONLY facts that are useful as persistent memories about the user, their home, budget, and design preferences.

Conversation:
{conversation_text}

Return a JSON array of memory objects in this exact format:

[
  {{
    "topic": "design_preferences",
    "key": "style",
    "value": {{"description": "Modern coastal with light wood"}},
    "confidence": 0.9
  }},
  {{
    "topic": "budget",
    "key": "max_budget_cad",
    "value": {{"amount": 50000, "currency": "CAD"}},
    "confidence": 0.85
  }},
  {{
    "topic": "home_constraints",
    "key": "condo_rules",
    "value": {{"description": "No changes to exterior windows or balcony"}},
    "confidence": 0.8
  }}
]

Rules:
- Only include facts that are explicitly stated or strongly implied.
- Use topics only from this set: ["design_preferences", "budget", "home_constraints", "project_info"].
- Use confidence 0.9 for explicit facts, 0.7–0.8 for inferred ones.
- If there are no useful memories, return [].

Return ONLY the JSON array, with no extra text.
"""

            gemini = GeminiClient()
            llm_response = await gemini.generate_text(
                prompt=extraction_prompt,
                temperature=0.1,
                max_tokens=700,
            )

            match = re.search(r"\[.*\]", llm_response, re.DOTALL)
            if not match:
                logger.warning(
                    "Memory extraction: no JSON array found in LLM response for conversation %s",
                    conversation_id,
                )
                return []

            try:
                items = json.loads(match.group(0))
            except Exception as parse_err:
                logger.warning(
                    "Memory extraction: failed to parse JSON for conversation %s: %s",
                    conversation_id,
                    parse_err,
                )
                return []

            stored: List[UserMemory] = []
            for item in items:
                if not isinstance(item, dict):
                    continue

                topic = item.get("topic")
                key = item.get("key")
                value = item.get("value")
                if not topic or not key or value is None:
                    continue

                confidence_val = item.get("confidence", 0.8)
                try:
                    confidence_float = float(confidence_val)
                except Exception:
                    confidence_float = 0.8

                try:
                    mem = await self.add_or_update_memory(
                        user_id=user_id,
                        home_id=home_id,
                        conversation_id=conversation_id,
                        topic=str(topic),
                        key=str(key),
                        value=value,
                        source="chat_extraction",
                        confidence=confidence_float,
                    )
                    stored.append(mem)
                except Exception as store_err:
                    logger.warning(
                        "Failed to store extracted memory %s/%s for conversation %s: %s",
                        topic,
                        key,
                        conversation_id,
                        store_err,
                    )

            if stored:
                logger.info(
                    "Extracted %d memories from conversation %s via LLM",
                    len(stored),
                    conversation_id,
                )

            return stored

        except Exception as e:
            logger.error(
                "Memory extraction failed for conversation %s: %s",
                conversation_id,
                e,
                exc_info=True,
            )
            return []

    @staticmethod
    def to_prompt_rows(memories: Iterable[UserMemory]) -> List[Dict[str, Any]]:
        """Convert memories to a compact list of dicts for prompt injection."""

        rows: List[Dict[str, Any]] = []
        for m in memories:
            row = {
                "topic": m.topic,
                "key": m.key,
                "value": m.value,
                "source": m.source,
                "confidence": float(m.confidence) if m.confidence is not None else None,
            }
            rows.append(row)
        return rows

