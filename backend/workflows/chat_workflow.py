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

logger = logging.getLogger(__name__)


class ChatState(BaseWorkflowState, total=False):
    """State for chat workflow."""
    
    # Input
    user_message: str
    home_id: Optional[str]
    conversation_id: str
    user_id: Optional[str]
    
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
        workflow.add_node("suggest_actions", self._suggest_actions)
        workflow.add_node("save_conversation", self._save_conversation)
        workflow.add_node("finalize", self._finalize)
        
        # Define edges
        workflow.set_entry_point("validate_input")
        workflow.add_edge("validate_input", "classify_intent")
        workflow.add_edge("classify_intent", "retrieve_context")
        workflow.add_edge("retrieve_context", "load_conversation_history")
        workflow.add_edge("load_conversation_history", "generate_response")
        workflow.add_edge("generate_response", "suggest_actions")
        workflow.add_edge("suggest_actions", "save_conversation")
        workflow.add_edge("save_conversation", "finalize")
        workflow.add_edge("finalize", END)
        
        # Compile with checkpointing
        return workflow.compile(checkpointer=MemorySaver())
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the chat workflow."""
        try:
            # Create initial state
            state = self.orchestrator.create_initial_state(
                user_message=input_data.get("user_message"),
                home_id=input_data.get("home_id"),
                conversation_id=input_data.get("conversation_id", str(uuid.uuid4())),
                user_id=input_data.get("user_id"),
                conversation_history=input_data.get("conversation_history", []),
                context_sources=[],
                requires_action=False,
                suggested_actions=[],
                response_metadata={}
            )
            
            # Execute workflow
            config = {"configurable": {"thread_id": state["conversation_id"]}}
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
            home_id = state.get("home_id")
            user_message = state["user_message"]
            
            if home_id:
                # Retrieve context using RAG service
                context = await self.rag_service.assemble_context(
                    db=self.db,
                    query=user_message,
                    home_id=home_id,
                    k=8,
                    include_images=True
                )
                
                state["retrieved_context"] = context
                state["context_sources"] = context.get("metadata", {}).get("sources", [])
                
                logger.info(
                    f"Retrieved {context['metadata']['total_chunks']} context chunks "
                    f"from sources: {', '.join(state['context_sources'])}"
                )
            else:
                logger.info("No home_id provided, skipping context retrieval")
                state["retrieved_context"] = None
                state["context_sources"] = []
            
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
            prompt = self._build_response_prompt(user_message, context, history)

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

    async def _suggest_actions(self, state: ChatState) -> ChatState:
        """Suggest follow-up actions based on intent and response."""
        state = self.orchestrator.mark_node_start(state, "suggest_actions")

        try:
            intent = state.get("intent", "question")
            user_message = state["user_message"]

            suggested_actions = []

            # Suggest actions based on intent
            if intent == "cost_estimate":
                suggested_actions.append({
                    "action": "get_detailed_estimate",
                    "label": "Get Detailed Cost Estimate",
                    "description": "Get a comprehensive cost breakdown for your project",
                    "agent": "cost_estimation"
                })

            elif intent == "product_recommendation":
                suggested_actions.append({
                    "action": "find_products",
                    "label": "Find Matching Products",
                    "description": "Search for products that fit your space and style",
                    "agent": "product_matching"
                })

            elif intent == "design_idea":
                suggested_actions.append({
                    "action": "generate_design",
                    "label": "Generate Design Mockup",
                    "description": "Create AI-generated design visualizations",
                    "agent": "design_studio"
                })

            # Always suggest exploring the digital twin
            if state.get("home_id"):
                suggested_actions.append({
                    "action": "explore_digital_twin",
                    "label": "Explore Your Digital Twin",
                    "description": "View your home's 3D model and room details",
                    "agent": "digital_twin"
                })

            state["suggested_actions"] = suggested_actions
            state["requires_action"] = len(suggested_actions) > 0

            logger.info(f"Suggested {len(suggested_actions)} actions")
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
                metadata=state.get("response_metadata", {}),
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
                "context_sources": state.get("context_sources", []),
                "metadata": {
                    **state.get("response_metadata", {}),
                    "execution_time_seconds": execution_time,
                    "nodes_visited": len(state.get("visited_nodes", [])),
                    "errors": len(state.get("errors", []))
                }
            }

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
        history: List[Dict[str, str]]
    ) -> str:
        """Build comprehensive prompt for response generation."""
        prompt_parts = []

        # System prompt
        prompt_parts.append("""You are HomeView AI, an intelligent home improvement assistant. You help homeowners, DIY enthusiasts, and contractors understand their homes and plan improvements.

Your capabilities:
- Analyze home data including floor plans, rooms, materials, and fixtures
- Answer questions about specific rooms and their features
- Provide improvement suggestions and design recommendations
- Estimate renovation costs
- Explain materials and fixtures in detail
- Help plan home improvement projects

Guidelines:
- Be friendly, helpful, and professional
- Provide specific, data-backed answers when home data is available
- If you don't have specific data, acknowledge it and provide general guidance
- Use emojis sparingly to make responses engaging
- Format responses clearly with bullet points and sections when appropriate
- Always prioritize accuracy over speculation
- Keep responses concise but informative (aim for 150-300 words unless more detail is requested)
""")

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

