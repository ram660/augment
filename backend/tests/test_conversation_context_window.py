"""Focused tests for ConversationService context window and summarization helpers.

These tests exercise:
- build_context_window: mixing summaries + recent messages
- maybe_generate_summary: threshold logic around when to generate a new summary

They use an in-memory async SQLite database, mirroring other chat workflow tests.
"""

import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.services import conversation_service as cs
from backend.services.conversation_service import ConversationService
from backend.models.conversation import ConversationSummary


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


class DummyGeminiClient:
    """Minimal stub for GeminiClient used by ConversationService in tests."""

    async def generate_text(self, *args, **kwargs) -> str:  # pragma: no cover - not exercised here
        return "dummy"


@pytest_asyncio.fixture
async def test_db(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory test database session and patch GeminiClient.

    Patching cs.GeminiClient ensures ConversationService does not require
    real GOOGLE_API_KEY / GEMINI_API_KEY env vars during tests.
    """

    monkeypatch.setattr(cs, "GeminiClient", DummyGeminiClient)

    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.mark.asyncio
async def test_build_context_window_includes_summaries_and_recent_messages(test_db: AsyncSession) -> None:
    """Context window should prepend summaries then append last N messages."""

    service = ConversationService(test_db)
    conv = await service.create_conversation()
    conv_id = str(conv.id)

    # Create a small message history
    for i in range(6):
        await service.add_message(
            conversation_id=conv_id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i + 1}",
        )

    messages = await service.get_messages(conv_id, limit=6)

    # Two summaries with different created_at timestamps
    summary1 = ConversationSummary(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        summary_text="Summary 1",
        start_message_id=messages[0].id,
        end_message_id=messages[2].id,
        message_count=3,
        key_topics=["kitchen"],
        entities_mentioned={},
    )
    summary1.created_at = datetime.utcnow() - timedelta(minutes=10)

    summary2 = ConversationSummary(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        summary_text="Summary 2",
        start_message_id=messages[3].id,
        end_message_id=messages[5].id,
        message_count=3,
        key_topics=["flooring"],
        entities_mentioned={},
    )
    summary2.created_at = datetime.utcnow()

    test_db.add_all([summary1, summary2])
    await test_db.commit()

    history = await service.build_context_window(
        conversation_id=conv_id,
        max_messages=3,
        include_summaries=True,
        max_summaries=2,
    )

    # Expect 2 summaries (oldest -> newest) then last 3 messages
    assert len(history) == 5
    assert [item.get("type") for item in history[:2]] == ["summary", "summary"]
    assert history[0]["content"] == "Summary 1"
    assert history[1]["content"] == "Summary 2"

    tail_contents = [item["content"] for item in history[2:]]
    assert tail_contents == ["Message 4", "Message 5", "Message 6"]


@pytest.mark.asyncio
async def test_maybe_generate_summary_skips_when_below_threshold(test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    """maybe_generate_summary should no-op when total messages < threshold."""

    service = ConversationService(test_db)
    conv = await service.create_conversation()
    conv_id = str(conv.id)

    # Add fewer messages than the threshold
    for i in range(4):
        await service.add_message(conversation_id=conv_id, role="user", content=f"msg {i}")

    generate_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(service, "generate_summary", generate_mock)

    result = await service.maybe_generate_summary(conversation_id=conv_id, message_threshold=5)

    assert result is None
    generate_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_maybe_generate_summary_triggers_when_above_threshold(test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    """maybe_generate_summary should call generate_summary once when threshold met."""

    service = ConversationService(test_db)
    conv = await service.create_conversation()
    conv_id = str(conv.id)

    # Add more messages than the threshold
    for i in range(6):
        await service.add_message(conversation_id=conv_id, role="user", content=f"msg {i}")

    sentinel_summary = object()
    generate_mock = AsyncMock(return_value=sentinel_summary)
    monkeypatch.setattr(service, "generate_summary", generate_mock)

    result = await service.maybe_generate_summary(conversation_id=conv_id, message_threshold=5)

    assert result is sentinel_summary
    generate_mock.assert_awaited_once()
    args, kwargs = generate_mock.await_args
    assert kwargs["conversation_id"] == conv_id
    assert kwargs["message_count"] == 6

