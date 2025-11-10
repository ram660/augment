"""Chat Orchestration Workflow - Production-ready conversational AI with context retrieval."""

import logging
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime
import uuid

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
from backend.integrations.gemini.client import GeminiClient
from backend.integrations.agentlightning.tracker import AgentTracker
from backend.integrations.agentlightning.rewards import RewardCalculator

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

    # Context retrieval
    retrieved_context: Optional[Dict[str, Any]]
    context_sources: List[str]

    # Conversation history
    conversation_history: List[Dict[str, str]]

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
        self.gemini_client = GeminiClient()

        # Initialize Agent Lightning tracker
        self.tracker = AgentTracker(agent_name="chat_agent")
        self.reward_calculator = RewardCalculator()

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(ChatState)

        # Add nodes
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("classify_intent", self._classify_intent)
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
        workflow.add_edge("classify_intent", "retrieve_context")
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
        try:
            # Create initial state as ChatState TypedDict
            conversation_id = input_data.get("conversation_id", str(uuid.uuid4()))
            state: ChatState = {
                # Workflow metadata
                "workflow_id": str(uuid.uuid4()),
                "workflow_name": self.orchestrator.workflow_name,
                "status": WorkflowStatus.PENDING,
                "started_at": datetime.utcnow().isoformat(),
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

            return final_state

        except Exception as e:
            logger.error(f"Chat workflow execution failed: {e}", exc_info=True)
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
- "design_transformation": User requests transforming an image (paint, flooring, cabinets, furniture, staging)
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

            # Try to load from database
            history = await self.conversation_service.get_recent_messages(
                conversation_id=conversation_id,
                count=10
            )

            # If no history in DB, use provided history
            if not history:
                history = state.get("conversation_history", [])
                history = history[-10:] if len(history) > 10 else history

            state["conversation_history"] = history

            logger.info(f"Loaded {len(state['conversation_history'])} messages from history")
            state = self.orchestrator.mark_node_complete(state, "load_conversation_history")

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "load_conversation_history", recoverable=True)
            # Fallback to provided history
            history = state.get("conversation_history", [])
            state["conversation_history"] = history[-10:] if len(history) > 10 else history

        return state

    async def _generate_response(self, state: ChatState) -> ChatState:
        """Generate AI response using Gemini."""
        state = self.orchestrator.mark_node_start(state, "generate_response")

        try:
            user_message = state["user_message"]
            context = state.get("retrieved_context")
            history = state.get("conversation_history", [])

            # Build comprehensive prompt
            prompt = self._build_response_prompt(
                user_message,
                context,
                history,
                state.get("persona"),
                state.get("scenario"),
                state.get("intent")
            )

            # Generate response
            response = await self.gemini_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2048
            )

            state["ai_response"] = response
            state["response_metadata"]["generated_at"] = datetime.utcnow().isoformat()
            state["response_metadata"]["model"] = "gemini-2.0-flash-exp"

            logger.info(f"Generated response ({len(response)} chars)")
            state = self.orchestrator.mark_node_complete(state, "generate_response")

        except Exception as e:
            state = self.orchestrator.add_error(state, e, "generate_response", recoverable=False)
            # Provide fallback response
            state["ai_response"] = (
                "I apologize, but I'm having trouble generating a response right now. "
                "Please try rephrasing your question or try again in a moment."
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

            # Initialize multimodal content
            web_search_results = []
            web_sources = []
            youtube_videos = []
            generated_images = []

            # 1. Web Search (Google Grounding) for product recommendations and cost estimates
            if intent in ["product_recommendation", "cost_estimate", "material_selection"]:
                try:
                    logger.info(f"Adding web search for intent: {intent}")

                    # Build grounding query from user message and AI response
                    grounding_input = {
                        "user_prompt": user_message,
                        "requested_changes": [intent],
                        "location_hint": "Canada",  # Prefer Canadian sources
                    }

                    # Use existing Gemini grounding capability
                    grounding_result = await self.gemini_client.suggest_products_with_grounding(
                        grounding_input,
                        max_items=5
                    )

                    web_search_results = grounding_result.get("products", [])
                    web_sources = grounding_result.get("sources", [])

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
            if intent in ["contractor_quotes", "find_contractor", "get_quote"]:
                try:
                    logger.info(f"Adding contractor search for intent: {intent}")

                    # Use Google Maps Grounding to find contractors
                    # Vancouver, BC coordinates
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

                    # Use Gemini with Google Maps grounding
                    from google import genai as google_genai
                    from google.genai import types

                    # Create a separate client for Maps grounding
                    maps_client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

                    maps_response = await maps_client.aio.models.generate_content(
                        model='gemini-2.0-flash-exp',
                        contents=f"Find the top 5 {job_type} in Vancouver, BC and surrounding areas (Burnaby, Richmond, Surrey). Include their ratings, specialties, and contact information.",
                        config=types.GenerateContentConfig(
                            tools=[types.Tool(google_maps=types.GoogleMaps())],
                            tool_config=types.ToolConfig(
                                retrieval_config=types.RetrievalConfig(
                                    lat_lng=types.LatLng(
                                        latitude=vancouver_lat,
                                        longitude=vancouver_lng
                                    )
                                )
                            )
                        )
                    )

                    # Parse Maps grounding results
                    contractors = []
                    if hasattr(maps_response.candidates[0], 'grounding_metadata'):
                        grounding = maps_response.candidates[0].grounding_metadata
                        if grounding.grounding_chunks:
                            for chunk in grounding.grounding_chunks[:5]:  # Top 5 contractors
                                if hasattr(chunk, 'maps'):
                                    contractor = {
                                        "name": chunk.maps.title,
                                        "place_id": chunk.maps.place_id,
                                        "url": chunk.maps.uri,
                                        "type": job_type,
                                        "location": "Vancouver, BC area",
                                    }
                                    contractors.append(contractor)

                    # Store in state
                    state["response_metadata"]["contractors"] = contractors

                    logger.info(f"Found {len(contractors)} contractors via Google Maps Grounding")

                except Exception as e:
                    logger.warning(f"Contractor search via Maps grounding failed: {e}")
                    # Continue without contractor results

            # 4. Image Generation for design concepts and visual aids
            # Note: We'll add this in a future iteration to avoid overloading the response
            # For now, we'll focus on web search, YouTube videos, and contractor search

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
                        **state.get("response_metadata", {})
                    },
                    context_sources=context_sources
                )

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
        history: List[Dict[str, str]],
        persona: Optional[str] = None,
        scenario: Optional[str] = None,
        intent: Optional[str] = None,
    ) -> str:
        """Build comprehensive prompt for response generation."""
        prompt_parts = []

        # System prompt
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

        # Scenario-specific guidance (only if explicitly set)
        if scenario == "contractor_quotes":
            prompt_parts.append(
                "\nCurrent focus: Contractor Quotes. Gather key project details (scope, dimensions, materials, constraints), propose a concise brief the user can send to contractors."
            )
        elif scenario == "diy_project_plan":
            prompt_parts.append(
                "\nCurrent focus: DIY Project Plan. Produce a concise, ordered plan with tools, materials, estimated effort, safety notes, and dependencies."
            )

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

        # Add conversation history
        if history:
            prompt_parts.append("\n**CONVERSATION HISTORY:**\n")
            for msg in history[-6:]:  # Last 6 messages (3 exchanges)
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

