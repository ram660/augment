"""Tests for ChatWorkflow tool invocation tracking and metadata.

This focuses on the S-1 slice: ensuring that when Gemini function calling
is used, tool invocations are executed via gemini_tools and recorded in
response_metadata['tool_invocations'].
"""

import types
import sys
from typing import Any, Dict, List

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.workflows.chat_workflow import ChatWorkflow
from backend.types.tool_responses import ToolResponse


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db() -> AsyncSession:
    """Create an in-memory test database session.

    This mirrors the pattern used in other chat workflow integration tests
    but is kept local to this file to avoid cross-test coupling.
    """

    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def patched_google(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide a minimal stub for google.genai and google.genai.types.

    ChatWorkflow._generate_response imports these modules directly when
    function calling is enabled. We stub just enough surface area for the
    test to exercise the tool-calling path without hitting the real SDK.
    """

    # Create module hierarchy: google, google.genai, google.genai.types
    google_mod = types.ModuleType("google")
    genai_mod = types.ModuleType("google.genai")
    types_mod = types.ModuleType("google.genai.types")

    class FakeFunctionCall:
        def __init__(self, name: str, args: Dict[str, Any]):
            self.name = name
            self.args = args

    class FakePart:
        def __init__(self, function_call: FakeFunctionCall | None = None, text: str | None = None):
            self.function_call = function_call
            self.text = text

    class FakeContent:
        def __init__(self, parts: List[FakePart]):
            self.parts = parts

    class FakeCandidate:
        def __init__(self, content: FakeContent):
            self.content = content

    class FakeResponse:
        def __init__(self, candidates: List[FakeCandidate]):
            self.candidates = candidates

    class FakeModels:
        def generate_content(self, model: str, contents: str, config: Any) -> FakeResponse:  # type: ignore[override]
            # Always return a single function call to a known tool.
            fn = FakeFunctionCall(
                name="test_tool",
                args={"foo": "bar"},
            )
            part = FakePart(function_call=fn)
            content = FakeContent(parts=[part])
            return FakeResponse(candidates=[FakeCandidate(content)])

    class FakeClient:
        def __init__(self, api_key: str | None = None):  # match usage pattern
            self.api_key = api_key
            self.models = FakeModels()

    class GenerateContentConfig:
        def __init__(self, tools: Any, tool_config: Any, temperature: float = 0.7):
            self.tools = tools
            self.tool_config = tool_config
            self.temperature = temperature

    class FunctionCallingConfig:
        def __init__(self, mode: str = "AUTO"):
            self.mode = mode

    class ToolConfig:
        def __init__(self, function_calling_config: FunctionCallingConfig):
            self.function_calling_config = function_calling_config

    class Tool:
        def __init__(self, function_declarations: List[Any]):
            self.function_declarations = function_declarations

    # Wire classes into the stub modules
    genai_mod.Client = FakeClient
    types_mod.GenerateContentConfig = GenerateContentConfig
    types_mod.ToolConfig = ToolConfig
    types_mod.FunctionCallingConfig = FunctionCallingConfig
    types_mod.Tool = Tool

    # Register modules in sys.modules via monkeypatch so imports succeed
    monkeypatch.setitem(sys.modules, "google", google_mod)
    monkeypatch.setitem(sys.modules, "google.genai", genai_mod)
    monkeypatch.setitem(sys.modules, "google.genai.types", types_mod)


@pytest.mark.asyncio
async def test_generate_response_records_tool_invocations(test_db: AsyncSession, patched_google: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """ChatWorkflow should execute tools and record tool_invocations metadata.

    This is a focused regression-style test to ensure S-1 behavior is wired:
    - Gemini function calling is used (via our stubbed google.genai modules)
    - gemini_tools.execute_tool_call is invoked once
    - The returned ToolResponse is serialized into response_metadata
    """

    # Patch gemini_tools so we can control tool behavior
    from backend.agents.tools import gemini_tools

    async def fake_execute_tool_call(name: str, args: Dict[str, Any], ctx: Any) -> ToolResponse:
        assert name == "test_tool"
        assert args == {"foo": "bar"}
        return ToolResponse(success=True, data={"ok": True}, latency_ms=42)

    def fake_get_function_declarations() -> list[Any]:
        # We don't care about the exact declaration objects in this test.
        return []

    monkeypatch.setattr(gemini_tools, "execute_tool_call", fake_execute_tool_call)
    monkeypatch.setattr(gemini_tools, "get_all_function_declarations", fake_get_function_declarations)

    # Create workflow instance
    workflow = ChatWorkflow(test_db)

    # Minimal state required by _generate_response
    state: Dict[str, Any] = {
        "workflow_id": "wf-test",
        "visited_nodes": [],
        "user_message": "Please use tools to help me.",
        "retrieved_context": None,
        "conversation_history": [],
        "persona": None,
        "scenario": None,
        "intent": None,
        "response_metadata": {},
        "user_id": None,
        "home_id": None,
        "conversation_id": "conv-test",
    }

    new_state = await workflow._generate_response(state)

    metadata = new_state.get("response_metadata", {})
    tool_invocations = metadata.get("tool_invocations")

    assert tool_invocations, "Expected at least one tool invocation recorded"
    first = tool_invocations[0]

    assert first["tool"] == "test_tool"
    assert first["args"] == {"foo": "bar"}
    assert first["result"]["success"] is True
    assert first["result"]["latency_ms"] == 42

