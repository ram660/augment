"""Chat Orchestration Workflow - Production-ready conversational AI with context retrieval."""

import logging
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime
import uuid
from pathlib import Path

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.ext.asyncio import AsyncSession

from backend.workflows.base import (
    BaseWorkflowState,
    WorkflowOrchestrator,
    WorkflowStatus,
    WorkflowError
)
from backend.services.rag_service import RAGService
from backend.services.conversation_service import ConversationService
from backend.services.memory_service import MemoryService
from backend.integrations.gemini.client import GeminiClient
from backend.integrations.agentlightning.tracker import AgentTracker
from backend.integrations.agentlightning.rewards import RewardCalculator
from backend.services.event_bus import (
    get_event_bus,
    publish_workflow_started,
    publish_workflow_completed,
    publish_workflow_failed,
    publish_chat_message_received,
    publish_chat_response_generated
)
from backend.services.persona_service import get_persona_service, SafetyLevel
from backend.services.cache_service import get_cache_service
from backend.services.journey_manager import get_journey_manager, JourneyStatus
from backend.services.journey_persistence_service import JourneyPersistenceService
from backend.agents.tools.runtime import ToolRuntimeContext
from backend.agents.tools import gemini_tools
from backend.models.user import User
import hashlib

logger = logging.getLogger(__name__)


class ChatState(BaseWorkflowState, total=False):
    """State for chat workflow."""

    # Input
    user_message: str
    home_id: Optional[str]
    conversation_id: str
    user_id: Optional[str]
    persona: Optional[str]
    scenario: Optional[str]
    mode: Optional[str]  # 'chat' | 'agent'
    uploaded_image_path: Optional[str]  # NEW: Path to uploaded image for multi-modal search

    # Context retrieval
    retrieved_context: Optional[Dict[str, Any]]
    context_sources: List[str]

    # Conversation history
    conversation_history: List[Dict[str, Any]]

    # Long-term memory (per-user / per-home)
    user_memories: List[Dict[str, Any]]

    # Response generation
    ai_response: Optional[str]
    response_metadata: Dict[str, Any]

    # Intent classification
    intent: Optional[str]
    requires_action: bool
    suggested_actions: List[Dict[str, Any]]
    suggested_questions: List[str]

    # Multimodal features (Agent mode only)
    web_search_results: Optional[List[Dict[str, Any]]]
    web_sources: Optional[List[str]]
    youtube_videos: Optional[List[Dict[str, Any]]]
    contractors: Optional[List[Dict[str, Any]]]  # Google Maps contractor search
    generated_images: Optional[List[str]]
    visual_aids: Optional[List[Dict[str, Any]]]
    image_analysis: Optional[Dict[str, Any]]  # NEW: Image analysis results from multi-modal search

    # Journey tracking
    journey_id: Optional[str]
    journey_status: Optional[str]
    current_step: Optional[Dict[str, Any]]
    next_steps: Optional[List[Dict[str, Any]]]


class ChatWorkflow:
    """
    Production-ready chat orchestration workflow.

    Features:
    - Context retrieval from RAG service
    - Conversation history management
    - Intent classification
    - Multi-turn conversation support
    - Action suggestions (cost estimation, product matching, etc.)
    - Comprehensive error handling
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.orchestrator = WorkflowOrchestrator(
            workflow_name="chat_orchestration",
            max_retries=2,
            timeout_seconds=60
        )
        self.rag_service = RAGService(use_gemini=True)
        self.conversation_service = ConversationService(db_session)
        self.memory_service = MemoryService(db_session)
        self.gemini_client = GeminiClient()

        # Initialize Agent Lightning tracker
        self.tracker = AgentTracker(agent_name="chat_agent")
        self.reward_calculator = RewardCalculator()

        # Initialize event bus
        self.event_bus = get_event_bus()

        # Initialize persona service
        self.persona_service = get_persona_service()

        # Initialize cache service
        self.cache_service = get_cache_service()

        # Initialize journey manager (in-memory)
        self.journey_manager = get_journey_manager()

        # Initialize journey persistence service (database)
        self.journey_persistence_service = JourneyPersistenceService(db_session)

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(ChatState)

        # Add nodes
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("manage_journey", self._manage_journey)  # NEW: Journey management
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("load_conversation_history", self._load_conversation_history)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("enrich_with_multimodal", self._enrich_with_multimodal)  # NEW: Multimodal enrichment
        workflow.add_node("suggest_actions", self._suggest_actions)
        workflow.add_node("save_conversation", self._save_conversation)
        workflow.add_node("finalize", self._finalize)

        # Define edges
        workflow.set_entry_point("validate_input")
        workflow.add_edge("validate_input", "classify_intent")
        workflow.add_edge("classify_intent", "manage_journey")  # NEW: Journey management after intent
        workflow.add_edge("manage_journey", "retrieve_context")
        workflow.add_edge("retrieve_context", "load_conversation_history")
        workflow.add_edge("load_conversation_history", "generate_response")
        workflow.add_edge("generate_response", "enrich_with_multimodal")  # NEW: Add multimodal content
        workflow.add_edge("enrich_with_multimodal", "suggest_actions")
        workflow.add_edge("suggest_actions", "save_conversation")
        workflow.add_edge("save_conversation", "finalize")
        workflow.add_edge("finalize", END)

        # Compile with checkpointing
        return workflow.compile(checkpointer=MemorySaver())

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the chat workflow."""
        workflow_id = str(uuid.uuid4())
        conversation_id = input_data.get("conversation_id", str(uuid.uuid4()))
        start_time = datetime.utcnow()

        try:
            # Publish workflow started event
            await publish_workflow_started(
                workflow_id=workflow_id,
                workflow_name=self.orchestrator.workflow_name,
                metadata={
                    "conversation_id": conversation_id,
                    "user_id": input_data.get("user_id"),
                    "mode": input_data.get("mode", "agent")
                }
            )

            # Publish chat message received event
            await publish_chat_message_received(
                conversation_id=conversation_id,
                message=input_data.get("user_message", ""),
                user_id=input_data.get("user_id", "anonymous"),
                metadata={
                    "workflow_id": workflow_id,
                    "persona": input_data.get("persona"),
                    "scenario": input_data.get("scenario")
                }
            )

            # Create initial state as ChatState TypedDict
            state: ChatState = {
                # Workflow metadata
                "workflow_id": workflow_id,
                "workflow_name": self.orchestrator.workflow_name,
                "status": WorkflowStatus.PENDING,
                "started_at": start_time.isoformat(),
                "completed_at": None,
                "current_node": None,
                "visited_nodes": [],
                "retry_count": 0,
                "max_retries": self.orchestrator.max_retries,
                "errors": [],
                "warnings": [],
                "result": None,
                "metadata": {},
                # Chat-specific fields
                "user_message": input_data.get("user_message", ""),
                "home_id": input_data.get("home_id"),
                "conversation_id": conversation_id,
                "user_id": input_data.get("user_id"),
                "persona": input_data.get("persona"),
                "scenario": input_data.get("scenario"),
                "mode": input_data.get("mode", "agent"),  # Default to agent mode
                "conversation_history": input_data.get("conversation_history", []),
                "context_sources": [],
                "requires_action": False,
                "suggested_actions": [],
                "suggested_questions": [],
                "response_metadata": {},
                "retrieved_context": None,
                "ai_response": None,
                "intent": None,
                # Multimodal fields
                "web_search_results": None,
                "web_sources": None,
                "youtube_videos": None,
                "contractors": None,
                "generated_images": None,
                "visual_aids": None
            }

            # Execute workflow
            config = {"configurable": {"thread_id": conversation_id}}
            final_state = await self.graph.ainvoke(state, config=config)

            # Publish chat response generated event
            if final_state.get("ai_response"):
                await publish_chat_response_generated(
                    conversation_id=conversation_id,
                    response=final_state["ai_response"],
                    metadata={
                        "workflow_id": workflow_id,
                        "intent": final_state.get("intent"),
                        "suggested_actions": final_state.get("suggested_actions", []),
                        "context_sources": final_state.get("context_sources", [])
                    }
                )

            # Publish workflow completed event
            duration = (datetime.utcnow() - start_time).total_seconds()
            await publish_workflow_completed(
                workflow_id=workflow_id,
                workflow_name=self.orchestrator.workflow_name,
                duration_seconds=duration,
                metadata={
                    "conversation_id": conversation_id,
                    "nodes_visited": len(final_state.get("visited_nodes", [])),
                    "errors_count": len(final_state.get("errors", []))
                }
            )

            return final_state

        except Exception as e:
            logger.error(f"Chat workflow execution failed: {e}", exc_info=True)

            # Publish workflow failed event
            await publish_workflow_failed(
                workflow_id=workflow_id,
                workflow_name=self.orchestrator.workflow_name,
                error=str(e),
                metadata={
                    "conversation_id": conversation_id,
                    "user_id": input_data.get("user_id")
                }
            )

            raise WorkflowError(
                f"Chat workflow failed: {str(e)}",
                original_error=e,
                recoverable=False
            )

    async def _validate_input(self, state: ChatState) -> ChatState:
        """Validate input parameters."""
        state = self.orchestrator.mark_node_start(state, "validate_input")

        try:
            user_message = state.get("user_message")

            if not user_message or not user_message.strip():
                raise WorkflowError(
                    "user_message is required and cannot be empty",
                    node_name="validate_input",
                    recoverable=False
                )

            # Validate message length
            if len(user_message) > 5000:
                self.orchestrator.add_warning(
                    state,
                    "User message exceeds 5000 characters, truncating",
                    "validate_input"
                )
                state["user_message"] = user_message[:5000]

            logger.info(f"Input validated for conversation: {state['conversation_id']}")
            state = self.orchestrator.mark_node_complete(state, "validate_input")

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "validate_input", recoverable=False)
            raise

        return state

    async def _classify_intent(self, state: ChatState) -> ChatState:
        """Classify user intent to determine workflow path."""
        state = self.orchestrator.mark_node_start(state, "classify_intent")

        try:
            user_message = state["user_message"]

            # Use Gemini to classify intent
            classification_prompt = f"""Classify the user's intent from this message. Return ONLY a JSON object.

User message: "{user_message}"

Classify into ONE of these intents:
- "question": User is asking a question about their home
- "cost_estimate": User wants cost estimation for a project
- "product_recommendation": User wants product recommendations
- "design_idea": User wants design or style suggestions
- "design_visualization": User wants to SEE/VISUALIZE design options (keywords: "show me", "visualize", "what would it look like", "generate", "create mockup")
- "design_transformation": User requests transforming an image (paint, flooring, cabinets, furniture, staging)
- "before_after": User wants to see before/after comparisons or transformations
- "material_comparison": User wants to compare materials or finishes visually
- "diy_guide": User wants a step-by-step DIY guide with materials/tools/safety
- "pdf_request": User wants a PDF export of a plan/guide or the conversation
- "general_chat": General conversation or greeting

Return JSON:
{{
    "intent": "<intent>",
    "confidence": <0.0-1.0>,
    "requires_home_data": <true/false>
}}"""

            try:
                response = await self.gemini_client.generate_text(
                    prompt=classification_prompt,
                    temperature=0.1
                )

                # Parse JSON response
                import json
                classification = self._parse_json_response(response)

                state["intent"] = classification.get("intent", "question")
                state["response_metadata"]["intent_confidence"] = classification.get("confidence", 0.5)

                logger.info(f"Intent classified: {state['intent']}")

            except Exception as e:
                logger.warning(f"Intent classification failed, defaulting to 'question': {e}")
                state["intent"] = "question"
                state["response_metadata"]["intent_confidence"] = 0.5

            state = self.orchestrator.mark_node_complete(state, "classify_intent")

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "classify_intent", recoverable=True)
            # Default to question intent on error
            state["intent"] = "question"

        return state

    async def _manage_journey(self, state: ChatState) -> ChatState:
        """Manage user journey - detect start, track progress, suggest next steps."""
        state = self.orchestrator.mark_node_start(state, "manage_journey")

        try:
            user_id = state.get("user_id")
            intent = state.get("intent")
            user_message = state.get("user_message", "").lower()
            conversation_id = state.get("conversation_id")
            home_id = state.get("home_id")

            # Initialize journey fields
            state["journey_id"] = None
            state["journey_status"] = None
            state["current_step"] = None
            state["next_steps"] = []

            if not user_id:
                logger.debug("No user_id provided, skipping journey management")
                state = self.orchestrator.mark_node_complete(state, "manage_journey")
                return state

            # Detect journey start from intent and keywords
            journey_template_id = None

            # Kitchen renovation journey
            if ("kitchen" in user_message and any(word in user_message for word in ["renovate", "remodel", "upgrade", "renovation"])):
                journey_template_id = "kitchen_renovation"

            # DIY project journey
            elif intent == "diy_guide" or ("diy" in user_message and "project" in user_message):
                journey_template_id = "diy_project"

            # Bathroom upgrade journey
            elif ("bathroom" in user_message and any(word in user_message for word in ["renovate", "remodel", "upgrade", "renovation"])):
                journey_template_id = "bathroom_upgrade"

            # Check if user has an active journey (from database)
            active_journeys = await self.journey_persistence_service.get_user_journeys(
                user_id=user_id,
                status="in_progress"
            )
            active_journey = active_journeys[0] if active_journeys else None

            # Start new journey if detected and no active journey
            if journey_template_id and not active_journey:
                try:
                    # Create journey in database (also creates in-memory)
                    journey = await self.journey_persistence_service.create_journey(
                        user_id=user_id,
                        template_id=journey_template_id,
                        home_id=home_id,
                        conversation_id=conversation_id
                    )

                    state["journey_id"] = str(journey.id)
                    state["journey_status"] = journey.status.value

                    # Get current step from database
                    if journey.steps:
                        # Find the first in-progress step
                        current_step = next(
                            (step for step in journey.steps if step.status == "in_progress"),
                            journey.steps[0] if journey.steps else None
                        )

                        if current_step:
                            state["current_step"] = {
                                "step_id": current_step.step_id,
                                "name": current_step.name,
                                "description": current_step.description,
                                "required_actions": current_step.required_actions or []
                            }

                            # Get next steps (steps after current)
                            current_index = next(
                                (i for i, s in enumerate(journey.steps) if s.id == current_step.id),
                                0
                            )
                            next_steps = journey.steps[current_index + 1:current_index + 4]
                            state["next_steps"] = [
                                {
                                    "step_id": step.step_id,
                                    "name": step.name,
                                    "description": step.description
                                }
                                for step in next_steps
                            ]

                    logger.info(f"Started journey '{journey_template_id}' for user {user_id} (ID: {journey.id})")

                except Exception as e:
                    logger.warning(f"Failed to start journey: {e}", exc_info=True)

            # Track progress for active journey
            elif active_journey:
                state["journey_id"] = str(active_journey.id)
                state["journey_status"] = active_journey.status.value

                # Get journey with steps from database
                journey = await self.journey_persistence_service.get_journey(str(active_journey.id))

                if journey and journey.steps:
                    # Find the current in-progress step
                    current_step = next(
                        (step for step in journey.steps if step.status == "in_progress"),
                        None
                    )

                    if current_step:
                        state["current_step"] = {
                            "step_id": current_step.step_id,
                            "name": current_step.name,
                            "description": current_step.description,
                            "required_actions": current_step.required_actions or []
                        }

                        # Auto-complete step based on intent
                        # For example, if user asks for product recommendations and that's a required action
                        if intent and current_step.required_actions and intent in current_step.required_actions:
                            try:
                                await self.journey_persistence_service.update_step(
                                    journey_id=str(journey.id),
                                    step_id=str(current_step.id),
                                    status="completed",
                                    progress=100.0,
                                    data={"completed_via": intent, "message": user_message}
                                )
                                logger.info(f"Auto-completed step '{current_step.step_id}' via intent '{intent}'")
                            except Exception as e:
                                logger.warning(f"Failed to auto-complete step: {e}", exc_info=True)

                        # Get next steps (steps after current)
                        current_index = next(
                            (i for i, s in enumerate(journey.steps) if s.id == current_step.id),
                            0
                        )
                        next_steps = journey.steps[current_index + 1:current_index + 4]
                        state["next_steps"] = [
                            {
                                "step_id": step.step_id,
                                "name": step.name,
                                "description": step.description
                            }
                            for step in next_steps
                        ]

                        # Attach uploaded images to current journey step
                        attachments = state.get("attachments", [])
                        if attachments and current_step:
                            image_attachments = [att for att in attachments if att.get("type") == "image"]

                            for att in image_attachments:
                                try:
                                    await self.journey_persistence_service.add_image(
                                        journey_id=str(journey.id),
                                        step_id=str(current_step.id),
                                        filename=att.get("filename", "uploaded_image.jpg"),
                                        file_path=att.get("path", ""),
                                        url=att.get("url", ""),
                                        content_type=att.get("content_type", "image/jpeg"),
                                        file_size=att.get("file_size", 0),
                                        is_generated=False,
                                        image_type="user_upload",
                                        label=att.get("label", "User uploaded image"),
                                        metadata=att.get("analysis", {})
                                    )
                                    logger.info(f"Attached image {att.get('filename')} to journey step {current_step.step_id}")
                                except Exception as e:
                                    logger.warning(f"Failed to attach image to journey step: {e}")

                logger.debug(f"Tracking journey '{journey.id}' for user {user_id}")

            state = self.orchestrator.mark_node_complete(state, "manage_journey")

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "manage_journey", recoverable=True)
            logger.warning(f"Journey management failed: {e}")

        return state

    async def _retrieve_context(self, state: ChatState) -> ChatState:
        """Retrieve relevant context from RAG service."""
        state = self.orchestrator.mark_node_start(state, "retrieve_context")

        try:
            # Digital Twin context temporarily disabled; proceed without RAG retrieval
            state["retrieved_context"] = None
            state["context_sources"] = []
            logger.info("Digital Twin context disabled for chat; skipping context retrieval")

            state = self.orchestrator.mark_node_complete(state, "retrieve_context")

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "retrieve_context", recoverable=True)
            # Continue without context
            state["retrieved_context"] = None
            state["context_sources"] = []

        return state

    async def _load_conversation_history(self, state: ChatState) -> ChatState:
        """Load conversation history from database."""
        state = self.orchestrator.mark_node_start(state, "load_conversation_history")

        try:
            conversation_id = state["conversation_id"]

            # Try to build a compact context window that includes both
            # recent turns and any stored summaries for older parts of
            # the conversation. This keeps prompts within budget while
            # preserving long-term context.
            history = await self.conversation_service.build_context_window(
                conversation_id=conversation_id,
                max_messages=10,
                include_summaries=True,
                max_summaries=2,
            )

            # If no history in DB (e.g., brand new conversation), fall
            # back to any history provided directly in the state.
            if not history:
                history = state.get("conversation_history", [])
                history = history[-10:] if len(history) > 10 else history

            state["conversation_history"] = history

            # Load any long-lived user memories (preferences, budget, etc.).
            user_memories: List[Dict[str, Any]] = []
            user_id = state.get("user_id")
            home_id = state.get("home_id")
            if user_id:
                try:
                    mem_rows = await self.memory_service.get_memories_for_user(
                        user_id=user_id,
                        home_id=home_id,
                        topics=None,
                        limit=20,
                    )
                    user_memories = MemoryService.to_prompt_rows(mem_rows)
                except Exception as mem_err:
                    logger.warning(
                        "Failed to load user memories for user %s: %s",
                        user_id,
                        mem_err,
                    )

            state["user_memories"] = user_memories

            logger.info(
                "Loaded %d items into conversation history (including summaries, if any)",
                len(state["conversation_history"]),
            )
            state = self.orchestrator.mark_node_complete(state, "load_conversation_history")

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "load_conversation_history", recoverable=True)
            # Fallback to provided history
            history = state.get("conversation_history", [])
            state["conversation_history"] = history[-10:] if len(history) > 10 else history

        return state

    async def _generate_response(self, state: ChatState) -> ChatState:
        '''Generate AI response using Gemini, with tool-calling when helpful.'''
        state = self.orchestrator.mark_node_start(state, 'generate_response')

        try:
            user_message = state['user_message']
            context = state.get('retrieved_context')
            history = state.get('conversation_history', [])

            # Build comprehensive prompt
            prompt = self._build_response_prompt(
                user_message,
                context,
                history,
                state.get('persona'),
                state.get('scenario'),
                state.get('intent'),
                state.get('user_memories', []),
            )

            # Prepare metadata
            response_metadata = state.get('response_metadata', {})
            tool_invocations = []

            # Try function calling; fall back to plain text on any error
            use_tools = True
            try:
                from google import genai as google_genai  # type: ignore
                from google.genai import types as genai_types  # type: ignore
            except Exception:
                use_tools = False

            ai_text = None

            if use_tools:
                try:
                    client = google_genai.Client(api_key=self.gemini_client.config.api_key)
                    tools = gemini_tools.get_all_function_declarations()

                    gen_config = genai_types.GenerateContentConfig(
                        tools=[genai_types.Tool(function_declarations=tools)],
                        tool_config=genai_types.ToolConfig(
                            function_calling_config=genai_types.FunctionCallingConfig(
                                mode='AUTO'
                            )
                        ),
                        temperature=0.7,
                    )

                    resp = client.models.generate_content(
                        model=self.gemini_client.config.default_text_model,
                        contents=prompt,
                        config=gen_config,
                    )

                    # Parse tool calls and any direct text
                    tool_calls = []
                    text_parts = []
                    try:
                        candidate = (resp.candidates or [None])[0]
                        if candidate:
                            content = getattr(candidate, 'content', None)
                            if content:
                                for part in getattr(content, 'parts', []) or []:
                                    fn = getattr(part, 'function_call', None)
                                    if fn:
                                        tool_calls.append(
                                            {
                                                'name': getattr(fn, 'name', '') or '',
                                                'args': getattr(fn, 'args', {}) or {},
                                            }
                                        )
                                    else:
                                        txt = getattr(part, 'text', None)
                                        if txt:
                                            text_parts.append(txt)
                    except Exception:
                        tool_calls = []
                        text_parts = []

                    if tool_calls:
                        # Resolve current user if available for tools that need auth
                        current_user = None
                        user_id = state.get('user_id')
                        if user_id:
                            try:
                                current_user = await self.db.get(User, user_id)
                            except Exception:
                                current_user = None

                        ctx = ToolRuntimeContext(
                            db=self.db,
                            gemini_client=self.gemini_client,
                            current_user=current_user,
                            home_id=state.get('home_id'),
                            conversation_id=state.get('conversation_id'),
                            location_hint=state.get('location_hint') or 'Vancouver, Canada',
                            extras={'intent': state.get('intent')},
                        )

                        for call in tool_calls:
                            try:
                                tool_name = call['name']
                                tool_args = call.get('args') or {}
                                tool_response = await gemini_tools.execute_tool_call(
                                    tool_name,
                                    tool_args,
                                    ctx,
                                )

                                # Normalize the tool response to a plain dict for
                                # both logging and metadata. ToolResponse already
                                # exposes latency_ms and success for observability.
                                result_payload = (
                                    tool_response.to_dict()
                                    if hasattr(tool_response, 'to_dict')
                                    else tool_response
                                )

                                record = {
                                    'tool': tool_name,
                                    'args': tool_args,
                                    'result': result_payload,
                                }
                                tool_invocations.append(record)

                                # Lightweight structured log for each tool call.
                                if isinstance(result_payload, dict):
                                    logger.info(
                                        'Tool %s executed (success=%s, latency_ms=%s)',
                                        tool_name,
                                        result_payload.get('success'),
                                        result_payload.get('latency_ms'),
                                    )
                                else:
                                    logger.info('Tool %s executed', tool_name)
                            except Exception as tool_err:
                                logger.error(
                                    'Error executing tool %s: %s',
                                    call.get('name'),
                                    tool_err,
                                    exc_info=True,
                                )
                                tool_invocations.append(
                                    {
                                        'tool': call.get('name'),
                                        'args': call.get('args'),
                                        'error': str(tool_err),
                                    }
                                )

                        if tool_invocations:
                            logger.info(
                                'Executed %d tools via Gemini function calling: %s',
                                len(tool_invocations),
                                [t.get('tool') for t in tool_invocations],
                            )

                        # Ask Gemini for final user-facing answer with tool results
                        try:
                            import json  # local import

                            tools_summary = json.dumps(tool_invocations, default=str)
                        except Exception:
                            tools_summary = str(tool_invocations)

                        final_prompt = (
                            f'{prompt}\n\n'
                            'You have access to structured tool results (JSON below). '
                            'Use them to answer the user clearly and helpfully. '
                            'Do not mention internal tool names unless it helps the user.\n\n'
                            f'TOOL_RESULTS_JSON: {tools_summary}'
                        )

                        ai_text = await self.gemini_client.generate_text(
                            prompt=final_prompt,
                            temperature=0.7,
                            max_tokens=2048,
                        )
                    else:
                        direct_text = '\n'.join(text_parts).strip()
                        if direct_text:
                            ai_text = direct_text
                        else:
                            ai_text = await self.gemini_client.generate_text(
                                prompt=prompt,
                                temperature=0.7,
                                max_tokens=2048,
                            )
                except Exception as tool_e:
                    logger.error(
                        'Error during Gemini tool-calling flow: %s',
                        tool_e,
                        exc_info=True,
                    )
                    ai_text = None

            # Fallback to plain text generation
            if ai_text is None:
                ai_text = await self.gemini_client.generate_text(
                    prompt=prompt,
                    temperature=0.7,
                    max_tokens=2048,
                )

            state['ai_response'] = ai_text
            response_metadata['generated_at'] = datetime.utcnow().isoformat()
            response_metadata['model'] = getattr(
                self.gemini_client.config,
                'default_text_model',
                'gemini-2.5-flash',
            )
            if tool_invocations:
                response_metadata['tool_invocations'] = tool_invocations
            state['response_metadata'] = response_metadata

            logger.info(f'Generated response ({len(ai_text)} chars)')
            state = self.orchestrator.mark_node_complete(state, 'generate_response')

        except Exception as e:
            state = self.orchestrator.add_error(
                state,
                e,
                'generate_response',
                recoverable=False,
            )
            # Provide fallback response
            state['ai_response'] = (
                'I apologize, but I am having trouble generating a response right now. '
                'Please try rephrasing your question or try again in a moment.'
            )

        return state

    async def _enrich_with_multimodal(self, state: ChatState) -> ChatState:
        """
        Enrich response with multimodal content (Agent mode only).

        Adds:
        - Web search results (Google Grounding) for products/costs
        - YouTube tutorial videos for DIY tasks
        - Generated images for visual aids
        """
        state = self.orchestrator.mark_node_start(state, "enrich_with_multimodal")

        try:
            # Skip if in chat mode (simple conversational responses only)
            mode = state.get("mode", "agent")
            if mode == "chat":
                logger.info("Chat mode: Skipping multimodal enrichment")
                state = self.orchestrator.mark_node_complete(state, "enrich_with_multimodal", {
                    "skipped": True,
                    "reason": "chat_mode"
                })
                return state

            intent = state.get("intent", "question")
            user_message = state.get("user_message", "")
            ai_response = state.get("ai_response", "")
            uploaded_image_path = state.get("uploaded_image_path")

            # Initialize multimodal content
            web_search_results = []
            web_sources = []
            youtube_videos = []
            generated_images = []
            image_analysis = None

            # 1. Multi-Modal Search (NEW): If user uploaded image + asking about products
            if uploaded_image_path and intent in ["product_recommendation", "design_inspiration", "material_selection", "question"]:
                try:
                    logger.info(f"[MultiModal] Using multi-modal search with uploaded image: {uploaded_image_path}")

                    # Check if user is asking about products/shopping
                    product_keywords = ["find", "buy", "purchase", "shop", "where", "similar", "like this", "match", "product"]
                    is_product_query = any(keyword in user_message.lower() for keyword in product_keywords)

                    if is_product_query or intent == "product_recommendation":
                        # Use new multi-modal search (image + text)
                        from pathlib import Path

                        # Read image file
                        image_path = Path(uploaded_image_path)
                        if image_path.exists():
                            # Use analyze_image_and_suggest_products for multi-modal search
                            multimodal_result = await self.gemini_client.analyze_image_and_suggest_products(
                                image=uploaded_image_path,
                                user_prompt=user_message,
                                room_hint=None,  # Could extract from context
                                max_items=5,
                                location_hint="Canada",
                                user_id=state.get("user_id"),
                                project_id=state.get("conversation_id")
                            )

                            if multimodal_result.success:
                                # Extract products and image analysis
                                data = multimodal_result.data if isinstance(multimodal_result.data, dict) else {}
                                web_search_results = data.get("products", [])
                                web_sources = data.get("sources", [])
                                image_analysis = data.get("image_analysis", {})

                                logger.info(f"[MultiModal] Found {len(web_search_results)} products via multi-modal search")
                                logger.info(f"[MultiModal] Image analysis: {image_analysis}")

                                # Store image analysis in state
                                state["image_analysis"] = image_analysis
                            else:
                                logger.warning(f"[MultiModal] Multi-modal search failed: {multimodal_result.error}")
                        else:
                            logger.warning(f"[MultiModal] Image file not found: {uploaded_image_path}")

                except Exception as e:
                    logger.error(f"[MultiModal] Multi-modal search failed: {e}", exc_info=True)
                    # Fall back to regular grounding search

            # 2. Regular Web Search (Google Grounding) for product recommendations without images
            # NEW: Detect if user is asking for multiple items (batch search)
            if not web_search_results and intent in ["product_recommendation", "cost_estimate", "material_selection"]:
                try:
                    # Detect multiple items in user message
                    multiple_item_indicators = [" and ", ", ", " & ", " plus ", " also "]
                    is_multiple_items = any(indicator in user_message.lower() for indicator in multiple_item_indicators)

                    # Extract individual items if multiple
                    if is_multiple_items:
                        logger.info(f"[BatchSearch] Detected multiple items in query")

                        # Simple extraction: split by common separators
                        items = []
                        for separator in [" and ", ", ", " & ", " plus ", " also "]:
                            if separator in user_message.lower():
                                items = [item.strip() for item in user_message.lower().split(separator)]
                                break

                        # Limit to 5 items for performance
                        items = items[:5]

                        if len(items) >= 2:
                            logger.info(f"[BatchSearch] Searching for {len(items)} items: {items}")

                            # Build batch queries
                            batch_queries = [
                                {
                                    "user_prompt": item,
                                    "requested_changes": [intent],
                                    "location_hint": "Canada"
                                }
                                for item in items
                            ]

                            # Use batch grounding
                            batch_results = await self.gemini_client.batch_grounding_queries(
                                queries=batch_queries,
                                max_items=3  # 3 items per query to avoid overwhelming
                            )

                            # Aggregate results from all queries
                            all_products = []
                            all_sources = []

                            for result in batch_results:
                                if result.success:
                                    data = result.data if isinstance(result.data, dict) else {}
                                    all_products.extend(data.get("products", []))
                                    all_sources.extend(data.get("sources", []))

                            web_search_results = all_products
                            web_sources = list(set(all_sources))  # Deduplicate sources

                            logger.info(f"[BatchSearch] Found {len(web_search_results)} products from {len(items)} queries")
                        else:
                            is_multiple_items = False

                    # Single item search (fallback or default)
                    if not is_multiple_items:
                        logger.info(f"Adding web search for intent: {intent}")

                        # Build grounding query from user message and AI response
                        grounding_input = {
                            "user_prompt": user_message,
                            "requested_changes": [intent],
                            "location_hint": "Canada",  # Prefer Canadian sources
                        }

                        # Check cache first
                        cache_key = f"product_search:{hashlib.md5(user_message.encode()).hexdigest()[:16]}:{intent}"
                        cached_result = await self.cache_service.get(cache_key, cache_type="product_search")

                        if cached_result:
                            logger.info(f"Product search cache hit for intent: {intent}")
                            web_search_results = cached_result.get("products", [])
                            web_sources = cached_result.get("sources", [])
                        else:
                            # Use existing Gemini grounding capability
                            grounding_result = await self.gemini_client.suggest_products_with_grounding(
                                grounding_input,
                                max_items=5
                            )

                            web_search_results = grounding_result.get("products", [])
                            web_sources = grounding_result.get("sources", [])

                            # Cache the result
                            await self.cache_service.set(
                                cache_key,
                                {"products": web_search_results, "sources": web_sources},
                                cache_type="product_search"
                            )

                        logger.info(f"Found {len(web_search_results)} products, {len(web_sources)} sources")

                except Exception as e:
                    logger.warning(f"Web search failed: {e}")
                    # Continue without web search

            # 2. YouTube Videos for DIY guides and tutorials (using Google Grounding)
            if intent in ["diy_guide", "how_to", "installation_guide"]:
                try:
                    logger.info(f"Adding YouTube videos for intent: {intent}")

                    # Use Google Grounding to search for YouTube tutorials
                    # This is better than YouTube API because:
                    # 1. No API key required
                    # 2. Already integrated
                    # 3. Returns real results

                    # Build search query for YouTube tutorials
                    search_query = f"{user_message} tutorial site:youtube.com"

                    grounding_input = {
                        "user_prompt": search_query,
                        "requested_changes": ["youtube_tutorial"],
                        "location_hint": "Canada",  # Prefer Canadian creators
                    }

                    # Use Gemini grounding to search YouTube
                    grounding_result = await self.gemini_client.suggest_products_with_grounding(
                        grounding_input,
                        max_items=5
                    )

                    # Parse grounding results into YouTube video format
                    raw_results = grounding_result.get("products", [])
                    youtube_videos = []

                    for result in raw_results:
                        url = result.get("url", "")
                        # Only include YouTube URLs
                        if "youtube.com" in url or "youtu.be" in url:
                            # Extract video ID from URL
                            video_id = None
                            if "watch?v=" in url:
                                video_id = url.split("watch?v=")[1].split("&")[0]
                            elif "youtu.be/" in url:
                                video_id = url.split("youtu.be/")[1].split("?")[0]

                            video = {
                                "video_id": video_id or url,
                                "title": result.get("name") or result.get("title", "YouTube Tutorial"),
                                "url": url,
                                "description": result.get("description", ""),
                                "channel": result.get("vendor", "YouTube"),
                                # Grounding doesn't provide these, but we can add placeholders
                                "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg" if video_id else None,
                                "is_trusted_channel": False,  # Can't determine from grounding
                            }
                            youtube_videos.append(video)

                    logger.info(f"Found {len(youtube_videos)} YouTube tutorials via Google Grounding")

                except Exception as e:
                    logger.warning(f"YouTube search via grounding failed: {e}")
                    # Continue without YouTube videos

            # 3. Contractor Search (Google Maps Grounding) for contractor quotes
            # NEW: Also trigger on natural language contractor queries
            contractor_keywords = ["contractor", "hire", "find someone", "professional", "quote", "estimate", "installer", "specialist"]
            is_contractor_query = any(keyword in user_message.lower() for keyword in contractor_keywords)

            if intent in ["contractor_quotes", "find_contractor", "get_quote"] or is_contractor_query:
                try:
                    logger.info(f"[ContractorSearch] Triggering contractor search for intent: {intent}, is_contractor_query: {is_contractor_query}")

                    # Use Google Maps Grounding to find contractors
                    # Vancouver, BC coordinates (default location)
                    vancouver_lat = 49.2827
                    vancouver_lng = -123.1207

                    # Build search query for contractors
                    # Extract job type from user message
                    job_type = "home renovation contractor"
                    if "paint" in user_message.lower():
                        job_type = "painting contractor"
                    elif "plumb" in user_message.lower():
                        job_type = "plumber"
                    elif "electric" in user_message.lower():
                        job_type = "electrician"
                    elif "roof" in user_message.lower():
                        job_type = "roofing contractor"
                    elif "floor" in user_message.lower():
                        job_type = "flooring contractor"
                    elif "kitchen" in user_message.lower() or "bathroom" in user_message.lower():
                        job_type = "kitchen and bathroom contractor"
                    elif "hvac" in user_message.lower() or "heating" in user_message.lower() or "cooling" in user_message.lower():
                        job_type = "HVAC contractor"

                    search_query = f"{job_type} near Vancouver BC"

                    # Check cache first
                    cache_key = f"contractor_search:{job_type}:vancouver"
                    cached_contractors = await self.cache_service.get(cache_key, cache_type="contractor_search")

                    if cached_contractors:
                        logger.info(f"[ContractorSearch] Cache hit for job type: {job_type}")
                        contractors = cached_contractors
                    else:
                        # NEW: Use the dedicated find_local_contractors_with_maps method
                        logger.info(f"[ContractorSearch] Searching for {job_type} in Vancouver, BC")

                        contractor_result = await self.gemini_client.find_local_contractors_with_maps(
                            service_type=job_type,
                            location="Vancouver, BC",
                            radius_miles=25,
                            max_results=5
                        )

                        if contractor_result.success:
                            data = contractor_result.data if isinstance(contractor_result.data, dict) else {}
                            contractors = data.get("contractors", [])
                            logger.info(f"[ContractorSearch] Found {len(contractors)} contractors")
                        else:
                            logger.warning(f"[ContractorSearch] Search failed: {contractor_result.error}")
                            contractors = []

                        # Cache the result
                        if contractors:
                            await self.cache_service.set(cache_key, contractors, cache_type="contractor_search")

                    # Store in state
                    state["response_metadata"]["contractors"] = contractors

                    logger.info(f"Found {len(contractors)} contractors via Google Maps Grounding")

                except Exception as e:
                    logger.warning(f"Contractor search via Maps grounding failed: {e}")
                    # Continue without contractor results

            # 4. Image Generation for design concepts and visual aids
            if intent in ["design_idea", "design_visualization", "before_after", "design_transformation", "material_comparison"]:
                try:
                    logger.info(f"Generating images for intent: {intent}")

                    # Check if user uploaded an image
                    uploaded_image = state.get("uploaded_image_path")

                    if uploaded_image:
                        # Transform existing image
                        logger.info(f"Transforming uploaded image: {uploaded_image}")
                        from backend.services.design_transformation_service import DesignTransformationService

                        design_service = DesignTransformationService()
                        style = self._extract_style_from_message(user_message)

                        # Use transform_room_style method
                        try:
                            images = await design_service.transform_room_style(
                                image=uploaded_image,
                                target_style=style,
                                num_variations=3
                            )

                            generated_images = [
                                {
                                    "type": "transformation",
                                    "url": img_path,
                                    "style": style,
                                    "caption": f"{style.title()} style transformation"
                                }
                                for img_path in images
                            ]

                            logger.info(f"Successfully transformed image into {len(generated_images)} variations")
                        except Exception as transform_error:
                            logger.warning(f"Image transformation failed: {transform_error}")
                            # Fall back to text-only response
                    else:
                        # Generate from description
                        logger.info("Generating images from description")
                        from backend.services.imagen_service import ImagenService, ImageGenerationRequest

                        imagen_service = ImagenService()
                        prompt = self._build_image_generation_prompt(user_message, ai_response)

                        logger.info(f"Image generation prompt: {prompt}")

                        request = ImageGenerationRequest(
                            prompt=prompt,
                            num_images=3,
                            aspect_ratio="16:9"
                        )

                        result = await imagen_service.generate_images(request)

                        if result.success:
                            generated_images = [
                                {
                                    "type": "generated",
                                    "url": img_path,
                                    "caption": "AI-generated design concept",
                                    "prompt": prompt
                                }
                                for img_path in result.image_paths
                            ]

                            logger.info(f"Successfully generated {len(generated_images)} images")
                        else:
                            logger.warning(f"Image generation failed: {result.error}")

                    logger.info(f"Total generated images: {len(generated_images)}")

                except Exception as e:
                    logger.warning(f"Image generation failed: {e}", exc_info=True)
                    # Continue without images

            # Store multimodal content in state
            state["web_search_results"] = web_search_results
            state["web_sources"] = web_sources
            state["youtube_videos"] = youtube_videos
            state["generated_images"] = generated_images

            # Add to response metadata for frontend display
            if web_search_results or web_sources:
                state["response_metadata"]["web_search_results"] = web_search_results
                state["response_metadata"]["web_sources"] = web_sources

            if youtube_videos:
                state["response_metadata"]["youtube_videos"] = youtube_videos

            if generated_images:
                state["response_metadata"]["generated_images"] = generated_images

            state = self.orchestrator.mark_node_complete(state, "enrich_with_multimodal", {
                "web_results": len(web_search_results),
                "web_sources": len(web_sources),
                "youtube_videos": len(youtube_videos),
                "generated_images": len(generated_images)
            })

        except Exception as e:
            logger.error(f"Multimodal enrichment failed: {e}", exc_info=True)
            state = self.orchestrator.add_error(state, e, "enrich_with_multimodal", recoverable=True)
            # Continue without multimodal content

        return state

    async def _suggest_actions(self, state: ChatState) -> ChatState:
        """Suggest follow-up actions based on intent and response."""
        state = self.orchestrator.mark_node_start(state, "suggest_actions")

        try:
            intent = state.get("intent", "question")
            user_message = state["user_message"]

            suggested_actions = []

            # Suggest actions based on intent
            suggested_questions: List[str] = []

            if intent == "cost_estimate":
                suggested_actions.append({
                    "action": "get_detailed_estimate",
                    "label": "Get Detailed Cost Estimate",
                    "description": "Get a comprehensive cost breakdown for your project",
                    "agent": "cost_estimation"
                })
                suggested_questions.extend([
                    "What are the room dimensions (L x W x H)?",
                    "Include labor or materials only?",
                    "What material quality/tier and budget range?",
                    "What is your location (for Canada pricing)?",
                ])

            elif intent == "product_recommendation":
                suggested_actions.append({
                    "action": "find_products",
                    "label": "Find Matching Products",
                    "description": "Search for products that fit your space and style",
                    "agent": "product_matching"
                })
                suggested_questions.extend([
                    "Which room and its dimensions?",
                    "What budget range and style preference?",
                    "Any must-have materials or brands (.ca vendors preferred)?",
                    "Do you need eco-friendly or low-VOC options?",
                ])

            elif intent == "design_idea":
                suggested_actions.append({
                    "action": "generate_design",
                    "label": "Generate Design Mockup",
                    "description": "Create AI-generated design visualizations",
                    "agent": "design_studio"
                })
                suggested_questions.extend([
                    "Which room photo should I reference?",
                    "What styles or color palettes do you like?",
                    "Any elements to keep (flooring, cabinets, furniture)?",
                ])

            elif intent == "design_transformation":
                suggested_actions.append({
                    "action": "open_design_studio",
                    "label": "Open Design Studio",
                    "description": "Apply AI transformations (paint, flooring, cabinets, staging)",
                    "agent": "design_studio"
                })
                suggested_questions.extend([
                    "Which attached photo should I use?",
                    "What exact edits (paint color, flooring type, cabinets)?",
                    "Should I preserve existing furniture and layout?",
                ])

            elif intent == "diy_guide":
                suggested_actions.append({
                    "action": "generate_diy_guide",
                    "label": "Generate DIY Step-by-Step Guide",
                    "description": "Get a structured plan with tools, materials, time, and safety",
                    "agent": "diy_guide"
                })
                suggested_questions.extend([
                    "What is your skill level and available time?",
                    "Do you already have any of the required tools?",
                    "What is your budget and deadline?",
                ])

            elif intent == "pdf_request":
                suggested_actions.append({
                    "action": "export_pdf",
                    "label": "Export as PDF",
                    "description": "Create a PDF document of this plan/guide with images",
                    "agent": "pdf_export"
                })
                suggested_questions.extend([
                    "Include images and a materials checklist?",
                    "What title should I use for the PDF?",
                    "Do you want a Canadian vendor list appended?",
                ])

            # Persona/Scenario specific suggestions
            p = state.get("persona")
            s = state.get("scenario")
            if p == "homeowner" or s == "contractor_quotes":
                suggested_actions.append({
                    "action": "start_contractor_quotes",
                    "label": "Get Contractor Quotes",
                    "description": "Prepare a brief and collect bids from contractors",
                    "agent": "contractor_quotes"
                })
            if p == "diy_worker" or s == "diy_project_plan":
                suggested_actions.append({
                    "action": "create_diy_plan",
                    "label": "Create My DIY Project Plan",
                    "description": "Get a step-by-step plan with tools and materials",
                    "agent": "diy_planner"
                })


            # Add journey next steps as suggested actions
            next_steps = state.get("next_steps", [])
            if next_steps:
                for step in next_steps:
                    suggested_actions.append({
                        "action": "journey_next_step",
                        "label": f"Next: {step['name']}",
                        "description": step['description'],
                        "step_id": step['step_id']
                    })

            # Default suggested questions for general queries
            if not suggested_questions:
                suggested_questions.extend([
                    "Which room or area are we focusing on?",
                    "What are the dimensions and current materials?",
                    "What is your budget and timeline?",
                    "Do you prefer DIY plan or contractor quotes?",
                ])

            # Context-aware refinement of follow-up questions using conversation history
            try:
                hist = state.get("conversation_history", []) or []
                # Build minimal history text (last 6 messages)
                history_lines = []
                for msg in hist[-6:]:
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    content = (msg.get("content") or "")[:400]
                    history_lines.append(f"{role}: {content}")
                history_text = "\n".join(history_lines)
                user_message = state.get("user_message", "")
                intent_label = state.get("intent") or "question"
                persona_label = state.get("persona") or ""
                scenario_label = state.get("scenario") or ""

                gen_prompt = f"""Given the conversation and latest message, propose 3-4 short follow-up questions that move the user forward.
They must be context-aware, <= 80 characters each, and easy to tap as chips.
Return ONLY a JSON array of strings.

Conversation (most recent first):
{history_text}

Latest message: {user_message}
Intent: {intent_label}
Persona: {persona_label}
Scenario: {scenario_label}
"""
                resp = await self.gemini_client.generate_text(
                    prompt=gen_prompt,
                    temperature=0.2,
                    max_tokens=200,
                )
                import json, re
                m = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', resp, re.DOTALL)
                arr_text = m.group(1) if m else resp.strip()
                arr = json.loads(arr_text)
                if isinstance(arr, list):
                    cleaned = []
                    for q in arr:
                        if isinstance(q, str):
                            q = q.strip()
                            if q and len(q) <= 100 and q not in cleaned:
                                cleaned.append(q)
                    if cleaned:
                        # Merge with existing, keep order, cap at 4
                        merged = []
                        for q in cleaned + suggested_questions:
                            if q not in merged:
                                merged.append(q)
                        suggested_questions = merged[:4]
            except Exception as fe:
                logger.debug(f"Contextual follow-up generation skipped: {fe}")

            state["suggested_actions"] = suggested_actions
            state["suggested_questions"] = suggested_questions
            state["requires_action"] = len(suggested_actions) > 0

            logger.info(f"Suggested {len(suggested_actions)} actions and {len(suggested_questions)} questions")
            state = self.orchestrator.mark_node_complete(state, "suggest_actions")

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "suggest_actions", recoverable=True)
            state["suggested_actions"] = []
            state["requires_action"] = False

        return state

    async def _save_conversation(self, state: ChatState) -> ChatState:
        """Save conversation to database."""
        state = self.orchestrator.mark_node_start(state, "save_conversation")

        try:
            conversation_id = state["conversation_id"]
            user_message = state["user_message"]
            ai_response = state.get("ai_response")
            intent = state.get("intent")
            context_sources = state.get("context_sources", [])

            # Ensure conversation exists
            conversation = await self.conversation_service.get_conversation(conversation_id)
            if not conversation:
                # Create new conversation
                user_id = state.get("user_id")
                home_id = state.get("home_id")
                conversation = await self.conversation_service.create_conversation(
                    user_id=user_id,
                    home_id=home_id
                )
                # Update state with actual conversation ID
                state["conversation_id"] = str(conversation.id)
                conversation_id = str(conversation.id)

            # Get journey information
            journey_id = state.get("journey_id")
            journey_status = state.get("journey_status")
            current_step = state.get("current_step")

            # Save user message
            await self.conversation_service.add_message(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                intent=intent,
                metadata={
                    **state.get("response_metadata", {}),
                    "persona": state.get("persona"),
                    "scenario": state.get("scenario"),
                    "journey_id": journey_id,
                    "journey_status": journey_status,
                    "current_step": current_step,
                },
                context_sources=context_sources
            )

            # Save AI response
            if ai_response:
                await self.conversation_service.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=ai_response,
                    metadata={
                        "suggested_actions": state.get("suggested_actions", []),
                        "suggested_questions": state.get("suggested_questions", []),
                        "persona": state.get("persona"),
                        "scenario": state.get("scenario"),
                        "journey_id": journey_id,
                        "journey_status": journey_status,
                        "current_step": current_step,
                        "next_steps": state.get("next_steps", []),
                        **state.get("response_metadata", {})
                    },
                    context_sources=context_sources
                )

            # Update journey's last_activity_at if journey exists
            if journey_id:
                try:
                    journey = await self.journey_persistence_service.get_journey(journey_id)
                    if journey:
                        # Update last activity timestamp
                        from sqlalchemy import update
                        from backend.models.journey import Journey
                        from datetime import datetime

                        stmt = update(Journey).where(
                            Journey.id == journey.id
                        ).values(
                            last_activity_at=datetime.utcnow()
                        )
                        await self.db.execute(stmt)
                        await self.db.commit()
                        logger.debug(f"Updated last_activity_at for journey {journey_id}")
                except Exception as e:
                    logger.warning(f"Failed to update journey last_activity_at: {e}")

            # Optionally generate/update a long-term summary. This is intentionally
            # fire-and-forget so we don't block the main response path.
            try:
                import asyncio

                async def _maybe_summarize(conv_id: str) -> None:
                    try:
                        await self.conversation_service.maybe_generate_summary(conv_id)
                    except Exception as inner_e:  # pragma: no cover - best-effort
                        logger.warning(
                            "Background summary generation failed for %s: %s",
                            conv_id,
                            inner_e,
                        )

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule in the existing event loop
                    loop.create_task(_maybe_summarize(conversation_id))
                else:  # pragma: no cover - defensive
                    loop.run_until_complete(_maybe_summarize(conversation_id))
            except Exception as e:  # pragma: no cover - non-critical
                logger.debug("Skipping summary generation due to error: %s", e)

            # Optionally extract long-term memories from the conversation (best-effort).
            try:
                import asyncio

                async def _maybe_extract_memories(conv_id: str, usr_id: str, hm_id: Optional[str]) -> None:
                    try:
                        # Only run every N messages to avoid unnecessary overhead.
                        conv = await self.conversation_service.get_conversation(conv_id)
                        if not conv:
                            return
                        msg_count = int(getattr(conv, "message_count", 0) or 0)
                        if msg_count <= 0 or msg_count % 10 != 0:
                            return

                        await self.memory_service.extract_memories_from_conversation(
                            conversation_id=conv_id,
                            user_id=usr_id,
                            home_id=hm_id,
                        )
                    except Exception as inner_e:  # pragma: no cover - best-effort
                        logger.warning(
                            "Background memory extraction failed for %s: %s",
                            conv_id,
                            inner_e,
                        )

                user_id_for_mem = state.get("user_id")
                if user_id_for_mem:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(
                            _maybe_extract_memories(
                                conversation_id,
                                user_id_for_mem,
                                state.get("home_id"),
                            )
                        )
                    else:  # pragma: no cover - defensive
                        loop.run_until_complete(
                            _maybe_extract_memories(
                                conversation_id,
                                user_id_for_mem,
                                state.get("home_id"),
                            )
                        )
            except Exception as e:  # pragma: no cover - non-critical
                logger.debug("Skipping memory extraction due to error: %s", e)

            logger.info(f"Saved conversation {conversation_id} to database")
            state = self.orchestrator.mark_node_complete(state, "save_conversation")

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "save_conversation", recoverable=True)
            # Non-critical error, continue
            logger.warning(f"Failed to save conversation, continuing: {e}")

        return state

    async def _finalize(self, state: ChatState) -> ChatState:
        """Finalize the workflow."""
        state = self.orchestrator.mark_node_start(state, "finalize")

        try:
            # Calculate execution metrics
            execution_time = (
                datetime.utcnow() - datetime.fromisoformat(state["started_at"])
            ).total_seconds()

            result = {
                "conversation_id": state["conversation_id"],
                "user_message": state["user_message"],
                "ai_response": state.get("ai_response"),
                "intent": state.get("intent"),
                "suggested_actions": state.get("suggested_actions", []),
                "suggested_questions": state.get("suggested_questions", []),
                "context_sources": state.get("context_sources", []),
                "metadata": {
                    **state.get("response_metadata", {}),
                    "persona": state.get("persona"),
                    "scenario": state.get("scenario"),
                    "execution_time_seconds": execution_time,
                    "nodes_visited": len(state.get("visited_nodes", [])),
                    "errors": len(state.get("errors", []))
                }
            }

            # Track interaction with Agent Lightning
            try:
                # Calculate implicit reward based on response quality
                response_metadata = {
                    "intent": state.get("intent"),
                    "intent_confidence": state.get("response_metadata", {}).get("intent_confidence", 0.5),
                    "context_used": bool(state.get("context_sources")),
                    "suggested_actions": state.get("suggested_actions", []),
                    "response_length": len(state.get("ai_response", "")),
                    "execution_time": execution_time,
                    "errors": len(state.get("errors", []))
                }

                # Calculate implicit reward (will be updated later with explicit feedback)
                implicit_reward = self.reward_calculator.calculate_implicit_reward(
                    response_metadata=response_metadata
                )

                # Track the interaction
                self.tracker.track_chat_message(
                    user_message=state["user_message"],
                    ai_response=state.get("ai_response", ""),
                    conversation_id=state["conversation_id"],
                    intent=state.get("intent"),
                    home_id=state.get("home_id"),
                    persona=state.get("persona"),
                    reward=implicit_reward
                )

                logger.debug(f"Tracked interaction with implicit reward: {implicit_reward:.2f}")

            except Exception as tracking_error:
                # Don't fail the workflow if tracking fails
                logger.warning(f"Failed to track interaction with Agent Lightning: {tracking_error}")

            state = self.orchestrator.mark_completed(state, result)
            logger.info(f"Chat workflow completed in {execution_time:.2f}s")

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "finalize", recoverable=False)
            raise

        return state

    def _build_response_prompt(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]],
        history: List[Dict[str, Any]],
        persona: Optional[str] = None,
        scenario: Optional[str] = None,
        intent: Optional[str] = None,
        user_memories: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Build comprehensive prompt for response generation."""
        prompt_parts = []

        # Load enhanced intelligent assistant system prompt
        prompt_file = Path(__file__).parent.parent / "prompts" / "intelligent_assistant_system_prompt.txt"
        try:
            if prompt_file.exists():
                enhanced_prompt = prompt_file.read_text(encoding="utf-8")
                prompt_parts.append(enhanced_prompt)
                logger.info("Loaded enhanced intelligent assistant system prompt")
            else:
                # Fallback to basic prompt if file not found
                logger.warning(f"Enhanced prompt file not found at {prompt_file}, using fallback")
                prompt_parts.append("""You are HomeView AI, an intelligent home improvement assistant. You help homeowners, DIY enthusiasts, and contractors understand their homes and plan improvements.

Your capabilities (available platform actions you can guide to):
- Estimate renovation costs (detailed cost breakdowns)
- Create DIY project plans with tools, materials, safety, and effort
- Generate a shopping list from a DIY plan
- Open the Design Studio to generate/edit visuals (paint, flooring, cabinets, furniture, staging) from user photos
- Recommend products (prefer Canadian/.ca vendors when possible)
- Prepare a contractor-quote brief
- Export DIY plans or summaries as downloadable PDFs

Guidelines:
- Be concise, clear, and professional; avoid fluff.
- Ground answers in the conversation history; don't repeat long lists already given.
- Prefer 3–6 short bullets or 1–3 short paragraphs; aim for 60–120 words unless the user asks for more.
- If critical info is missing, ask 1–2 specific clarifying questions in a friendly tone (e.g., “I can run that — could you share X and Y?”).
- End with one decisive next step (A/B style), matching the user’s goal.
- Keep Canadian context in mind; prefer .ca vendors when mentioning products.
- Do not reference any Digital Twin or home_id unless explicitly provided by the user.
- CRITICAL: You CAN create and export PDFs. Never say "I cannot create PDF documents" or similar. When asked for a PDF, confirm you can do it and guide the user to provide any missing content (e.g., create a DIY plan first if needed).
- Avoid repeating the same suggestion chips every message. If an action was just offered, propose the next logical step instead.
""")
        except Exception as e:
            logger.error(f"Error loading enhanced prompt: {e}, using minimal fallback")
            prompt_parts.append("""You are HomeView AI, an intelligent home improvement assistant.""")

        # Universal guidance (persona-agnostic - respond based on user's actual questions)
        prompt_parts.append("""
Respond universally to all users based on their questions and needs, not their persona label:
- If they ask about costs or budgets → provide estimates and offer contractor quotes if they want professional help
- If they ask "how to" or want to DIY → provide step-by-step guidance and offer to create a detailed DIY plan
- If they ask about products → recommend products with Canadian/.ca vendors preferred
- If they ask about design/visuals → offer to generate mockups in the Design Studio
- If they want to hire help → guide them to prepare a contractor brief
- Always offer BOTH pathways (DIY and contractor) neutrally unless the user has clearly chosen one

Adapt your tone and detail level to match what the user is asking for, not what their persona label says.
""")

        # Add persona-specific tone/detail guidance (subtle, not restrictive)
        if persona:
            persona_prefix = self.persona_service.get_prompt_prefix(persona, scenario)
            if persona_prefix:
                prompt_parts.append(f"\n**Tone & Detail Guidance:** {persona_prefix}")

        # Scenario-specific guidance (only if explicitly set)
        if scenario == "contractor_quotes":
            prompt_parts.append(
                "\nCurrent focus: Contractor Quotes. Gather key project details (scope, dimensions, materials, constraints), propose a concise brief the user can send to contractors."
            )
        elif scenario == "diy_project_plan":
            prompt_parts.append(
                "\nCurrent focus: DIY Project Plan. Produce a concise, ordered plan with tools, materials, estimated effort, safety notes, and dependencies."
            )

        # Add safety warnings for DIY tasks if applicable
        if persona in ["diy_worker", "homeowner"] and scenario == "diy_project_plan":
            # Check if message contains hazardous keywords
            message_lower = user_message.lower()
            safety_warnings = []

            if any(word in message_lower for word in ["electrical", "wiring", "outlet", "circuit"]):
                warning = self.persona_service.get_safety_warning("electrical")
                if warning:
                    safety_warnings.append(f"⚠️ {warning.title}: {warning.description}")

            if any(word in message_lower for word in ["gas", "gas line"]):
                warning = self.persona_service.get_safety_warning("gas")
                if warning:
                    safety_warnings.append(f"⚠️ {warning.title}: {warning.description}")

            if any(word in message_lower for word in ["load bearing", "wall removal", "structural"]):
                warning = self.persona_service.get_safety_warning("structural")
                if warning:
                    safety_warnings.append(f"⚠️ {warning.title}: {warning.description}")

            if any(word in message_lower for word in ["roof", "roofing"]):
                warning = self.persona_service.get_safety_warning("roof")
                if warning:
                    safety_warnings.append(f"⚠️ {warning.title}: {warning.description}")

            if any(word in message_lower for word in ["asbestos"]):
                warning = self.persona_service.get_safety_warning("asbestos")
                if warning:
                    safety_warnings.append(f"⚠️ {warning.title}: {warning.description}")

            if safety_warnings:
                prompt_parts.append("\n**SAFETY WARNINGS - Include these in your response:**")
                for warning in safety_warnings:
                    prompt_parts.append(warning)

        # Inject Skills context (concise)
        try:
            from backend.services.skill_manager import SkillManager  # local import
            sm = SkillManager()
            skill_context = sm.get_context(intent, persona, scenario, user_message)
            if skill_context:
                prompt_parts.append(skill_context)
        except Exception:
            # Non-fatal if skills are unavailable
            pass

        # Add context if available
        if context and context.get("context_text"):
            prompt_parts.append("\n**CURRENT HOME DATA:**\n")
            prompt_parts.append(context["context_text"])

            # Add image URLs if available
            if context.get("image_urls"):
                prompt_parts.append("\n**Available Images:**")
                for img_url in context["image_urls"][:5]:  # Limit to 5
                    prompt_parts.append(f"- {img_url}")

            prompt_parts.append("\nUse this home data to provide accurate, specific answers.")

        # Add long-lived user memory (preferences, constraints, etc.)
        if user_memories:
            prompt_parts.append("\n**USER MEMORY & PREFERENCES (long-term):**\n")
            for mem in user_memories[:8]:  # keep this concise
                topic = (mem.get("topic") or "general").replace("_", " ").title()
                key = mem.get("key") or ""
                value = mem.get("value")
                if isinstance(value, dict) and "description" in value:
                    description = str(value.get("description"))
                else:
                    description = str(value)

                if key:
                    prompt_parts.append(f"- [{topic}] {key}: {description}")
                else:
                    prompt_parts.append(f"- [{topic}] {description}")

        # Add conversation summaries and recent history
        if history:
            # Separate summaries from regular turns
            summaries = [msg for msg in history if msg.get("type") == "summary"]
            turns = [msg for msg in history if msg.get("type") != "summary"]

            if summaries:
                prompt_parts.append("\n**CONVERSATION SUMMARY (older turns):**\n")
                for idx, summary in enumerate(summaries[-3:], start=1):
                    content = summary.get("content", "")
                    if not content:
                        continue
                    prefix = f"Summary {idx}: " if len(summaries) > 1 else "Summary: "
                    prompt_parts.append(f"{prefix}{content}")

            if turns:
                prompt_parts.append("\n**CONVERSATION HISTORY (recent messages):**\n")
                for msg in turns[-6:]:  # Last 6 messages (3 exchanges)
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    prompt_parts.append(f"{role}: {msg.get('content', '')}")

        # Add current user message
        prompt_parts.append(f"\n**CURRENT USER MESSAGE:**\n{user_message}")

        prompt_parts.append("\n**YOUR RESPONSE:**")

        return "\n".join(prompt_parts)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        import json
        import re

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)

        # Remove any leading/trailing whitespace
        response = response.strip()

        # Try to parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise

    def _extract_style_from_message(self, message: str) -> str:
        """Extract design style from user message."""
        message_lower = message.lower()

        styles = {
            "modern": ["modern", "contemporary", "minimalist", "sleek", "clean"],
            "traditional": ["traditional", "classic", "timeless", "elegant"],
            "rustic": ["rustic", "farmhouse", "country", "cottage"],
            "industrial": ["industrial", "loft", "urban", "warehouse"],
            "scandinavian": ["scandinavian", "nordic", "scandi", "hygge"],
            "bohemian": ["bohemian", "boho", "eclectic", "artistic"],
            "coastal": ["coastal", "beach", "nautical", "seaside"],
            "transitional": ["transitional", "blend", "mixed"]
        }

        for style, keywords in styles.items():
            if any(keyword in message_lower for keyword in keywords):
                return style

        return "modern"  # Default

    def _build_image_generation_prompt(self, user_message: str, ai_response: str) -> str:
        """Build image generation prompt from conversation context."""
        message_lower = user_message.lower()

        # Extract room type
        room_type = "room"
        if "bathroom" in message_lower:
            room_type = "bathroom"
        elif "kitchen" in message_lower:
            room_type = "kitchen"
        elif "bedroom" in message_lower:
            room_type = "bedroom"
        elif "living" in message_lower or "living room" in message_lower:
            room_type = "living room"
        elif "dining" in message_lower:
            room_type = "dining room"
        elif "office" in message_lower:
            room_type = "home office"
        elif "basement" in message_lower:
            room_type = "basement"

        # Extract style
        style = self._extract_style_from_message(user_message)

        # Build detailed prompt
        prompt = f"A beautiful {style} {room_type} interior design. "
        prompt += "Professional interior photography, well-lit, realistic, high quality, "
        prompt += "interior design magazine style, 8K resolution. "

        # Add specific details from user message
        if "small" in message_lower or "compact" in message_lower:
            prompt += "Compact and space-efficient layout. "
        if "budget" in message_lower or "affordable" in message_lower:
            prompt += "Cost-effective materials and finishes. "
        if "luxury" in message_lower or "high-end" in message_lower or "premium" in message_lower:
            prompt += "Premium materials and luxury finishes. "
        if "bright" in message_lower or "light" in message_lower:
            prompt += "Bright and airy with natural light. "
        if "cozy" in message_lower or "warm" in message_lower:
            prompt += "Warm and cozy atmosphere. "
        if "open" in message_lower or "spacious" in message_lower:
            prompt += "Open and spacious layout. "

        # Add color preferences
        colors = ["white", "gray", "grey", "blue", "green", "beige", "black", "navy"]
        for color in colors:
            if color in message_lower:
                prompt += f"Featuring {color} tones. "
                break

        return prompt

