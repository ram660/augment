"""
Chat Orchestrator Agent - Main controller for multimodal chat workflow.

LEGACY: This agent and its API endpoints are maintained for backward
compatibility and experimentation only. The canonical chat path for
HomeView AI is now the LangGraph-based ChatWorkflow exposed via
`backend/api/chat.py` at `/api/v1/chat/message`.

This agent:
1. Understands user intent
2. Determines what type of response is needed (text/image/video/products)
3. Routes to specialized agents
4. Aggregates multimodal responses
5. Maintains conversation context
6. Tracks renovation workflow progress
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum

from backend.agents.base.agent import BaseAgent, AgentRole, AgentConfig, AgentResponse
from backend.integrations.gemini.client import GeminiClient

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of user intents."""
    VISUAL_EXPLORATION = "visual_exploration"  # "show me designs"
    DIY_INSTRUCTIONS = "diy_instructions"      # "how do I..."
    COST_ESTIMATION = "cost_estimation"        # "what will it cost"
    PRODUCT_SEARCH = "product_search"          # "find me a sofa"
    RENOVATION_WORKFLOW = "renovation_workflow" # "I want to renovate"
    GENERAL_QUESTION = "general_question"      # General queries
    SAFETY_CHECK = "safety_check"              # "is this safe"
    TROUBLESHOOTING = "troubleshooting"        # "paint is dripping"


class ResponseType(Enum):
    """Types of responses to generate."""
    TEXT_ONLY = "text_only"
    TEXT_WITH_IMAGES = "text_with_images"
    TEXT_WITH_VIDEO = "text_with_video"
    TEXT_WITH_PRODUCTS = "text_with_products"
    MULTIMODAL_FULL = "multimodal_full"  # Text + Images + Video + Products


class ChatOrchestrator(BaseAgent):
    """
    Main orchestrator for chat-based agentic workflow.

    Coordinates multiple specialized agents to provide comprehensive
    multimodal responses to user queries.
    """

    def __init__(
        self,
        gemini_client: GeminiClient,
        mcp_client: Optional[Any] = None
    ):
        """
        Initialize Chat Orchestrator.

        Args:
            gemini_client: Gemini AI client
            mcp_client: Optional MCP client for tool access
        """
        config = AgentConfig(
            name="Chat Orchestrator",
            role=AgentRole.CHAT_ORCHESTRATOR,
            description="Multimodal chat orchestrator for home improvement assistance",
            enable_mcp=True if mcp_client else False
        )
        super().__init__(
            config=config,
            gemini_client=gemini_client,
            mcp_client=mcp_client
        )
        
        # Conversation context
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        
        # Workflow state tracking
        self.workflow_states: Dict[str, Dict[str, Any]] = {}


    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process input (required by BaseAgent).

        This is a wrapper around process_message for BaseAgent compatibility.
        """
        message = input_data.get("message", "")
        conversation_id = input_data.get("conversation_id", "default")
        user_id = input_data.get("user_id")
        context = input_data.get("context")

        result = await self.process_message(message, conversation_id, user_id, context)

        return AgentResponse(
            agent_name=self.name,
            agent_role=self.role,
            success=result.get("success", False),
            data=result,
            message="Processed chat message"
        )

    async def process_message(
        self,
        message: str,
        conversation_id: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user message and generate multimodal response.
        
        Args:
            message: User's message
            conversation_id: Conversation ID
            user_id: Optional user ID
            context: Optional additional context
            
        Returns:
            Multimodal response with text, images, videos, products
        """
        try:
            logger.info(f"Processing message: {message[:100]}...")
            
            # Step 1: Detect intent
            intent = await self._detect_intent(message, conversation_id)
            logger.info(f"Detected intent: {intent}")
            
            # Step 2: Determine response type
            response_type = self._determine_response_type(intent)
            logger.info(f"Response type: {response_type}")
            
            # Step 3: Generate response components
            response = await self._generate_response(
                message=message,
                intent=intent,
                response_type=response_type,
                conversation_id=conversation_id,
                user_id=user_id,
                context=context
            )
            
            # Step 4: Save to conversation history
            self._save_to_history(conversation_id, message, response)
            
            # Step 5: Update workflow state if applicable
            if intent == IntentType.RENOVATION_WORKFLOW:
                self._update_workflow_state(conversation_id, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": {
                    "text": {
                        "content": "I apologize, but I encountered an error processing your request. Please try again.",
                        "format": "markdown"
                    }
                }
            }
    
    async def _detect_intent(
        self,
        message: str,
        conversation_id: str
    ) -> IntentType:
        """
        Detect user intent from message.
        
        Uses keyword matching and Gemini for complex cases.
        """
        message_lower = message.lower()
        
        # Keyword-based detection (fast path)
        if any(word in message_lower for word in ["show me", "design", "ideas", "look like", "example"]):
            return IntentType.VISUAL_EXPLORATION
        
        if any(word in message_lower for word in ["how do i", "how to", "steps", "guide", "tutorial"]):
            return IntentType.DIY_INSTRUCTIONS
        
        if any(word in message_lower for word in ["cost", "price", "budget", "expensive", "how much"]):
            return IntentType.COST_ESTIMATION
        
        if any(word in message_lower for word in ["find", "search", "buy", "purchase", "where can i get"]):
            return IntentType.PRODUCT_SEARCH
        
        if any(word in message_lower for word in ["renovate", "remodel", "redo", "complete overhaul"]):
            return IntentType.RENOVATION_WORKFLOW
        
        if any(word in message_lower for word in ["safe", "danger", "risk", "hazard"]):
            return IntentType.SAFETY_CHECK
        
        if any(word in message_lower for word in ["problem", "issue", "wrong", "not working", "help"]):
            return IntentType.TROUBLESHOOTING
        
        # Use Gemini for complex intent detection
        return await self._detect_intent_with_ai(message, conversation_id)

    async def _detect_intent_with_ai(
        self,
        message: str,
        conversation_id: str
    ) -> IntentType:
        """Use Gemini to detect intent for complex messages."""
        try:
            # Get conversation history for context
            history = self.conversations.get(conversation_id, [])
            history_text = "\n".join([
                f"User: {msg['user']}\nAI: {msg['ai'][:100]}..."
                for msg in history[-3:]  # Last 3 messages
            ])

            prompt = f"""Analyze this user message and determine their intent.

Conversation history:
{history_text}

Current message: "{message}"

Intent options:
1. visual_exploration - User wants to see designs, images, examples
2. diy_instructions - User wants step-by-step how-to instructions
3. cost_estimation - User wants to know costs, prices, budget
4. product_search - User wants to find/buy specific products
5. renovation_workflow - User wants complete renovation planning
6. safety_check - User has safety concerns
7. troubleshooting - User has a problem that needs fixing
8. general_question - General question or conversation

Return ONLY the intent name, nothing else."""

            result = await self.gemini_client.generate_text(prompt)
            intent_str = result.strip().lower()

            # Map to IntentType
            intent_map = {
                "visual_exploration": IntentType.VISUAL_EXPLORATION,
                "diy_instructions": IntentType.DIY_INSTRUCTIONS,
                "cost_estimation": IntentType.COST_ESTIMATION,
                "product_search": IntentType.PRODUCT_SEARCH,
                "renovation_workflow": IntentType.RENOVATION_WORKFLOW,
                "safety_check": IntentType.SAFETY_CHECK,
                "troubleshooting": IntentType.TROUBLESHOOTING,
                "general_question": IntentType.GENERAL_QUESTION
            }

            return intent_map.get(intent_str, IntentType.GENERAL_QUESTION)

        except Exception as e:
            logger.error(f"Error detecting intent with AI: {e}")
            return IntentType.GENERAL_QUESTION

    def _determine_response_type(self, intent: IntentType) -> ResponseType:
        """Determine what type of response to generate based on intent."""
        response_map = {
            IntentType.VISUAL_EXPLORATION: ResponseType.TEXT_WITH_IMAGES,
            IntentType.DIY_INSTRUCTIONS: ResponseType.MULTIMODAL_FULL,
            IntentType.COST_ESTIMATION: ResponseType.TEXT_WITH_PRODUCTS,
            IntentType.PRODUCT_SEARCH: ResponseType.TEXT_WITH_PRODUCTS,
            IntentType.RENOVATION_WORKFLOW: ResponseType.MULTIMODAL_FULL,
            IntentType.SAFETY_CHECK: ResponseType.TEXT_WITH_IMAGES,
            IntentType.TROUBLESHOOTING: ResponseType.TEXT_WITH_VIDEO,
            IntentType.GENERAL_QUESTION: ResponseType.TEXT_ONLY
        }
        return response_map.get(intent, ResponseType.TEXT_ONLY)

    async def _generate_response(
        self,
        message: str,
        intent: IntentType,
        response_type: ResponseType,
        conversation_id: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate multimodal response based on intent and response type."""

        response = {
            "success": True,
            "message_id": f"msg_{conversation_id}_{len(self.conversations.get(conversation_id, []))}",
            "conversation_id": conversation_id,
            "intent": intent.value,
            "response": {},
            "metadata": {
                "agents_used": [],
                "processing_time_ms": 0,
                "cost_usd": 0.0
            }
        }

        # Always generate text response
        text_response = await self._generate_text_response(message, intent, conversation_id)
        response["response"]["text"] = text_response
        response["metadata"]["agents_used"].append("text_agent")

        # Generate additional components based on response type
        if response_type in [ResponseType.TEXT_WITH_IMAGES, ResponseType.MULTIMODAL_FULL]:
            images = await self._generate_images(message, intent, context)
            if images:
                response["response"]["images"] = images
                response["metadata"]["agents_used"].append("visual_agent")

        if response_type in [ResponseType.TEXT_WITH_VIDEO, ResponseType.MULTIMODAL_FULL]:
            videos = await self._find_relevant_videos(message, intent)
            if videos:
                response["response"]["videos"] = videos
                response["metadata"]["agents_used"].append("video_agent")

        if response_type in [ResponseType.TEXT_WITH_PRODUCTS, ResponseType.MULTIMODAL_FULL]:
            products = await self._search_products(message, intent, context)
            if products:
                response["response"]["products"] = products
                response["metadata"]["agents_used"].append("product_agent")

        # Add workflow tracking for renovation workflows
        if intent == IntentType.RENOVATION_WORKFLOW:
            workflow = self._get_workflow_status(conversation_id)
            response["response"]["workflow"] = workflow

        # Add interactive elements
        interactive = self._generate_interactive_elements(intent, response_type)
        if interactive:
            response["response"]["interactive_elements"] = interactive

        return response

    async def _generate_text_response(
        self,
        message: str,
        intent: IntentType,
        conversation_id: str
    ) -> Dict[str, str]:
        """Generate text response using Gemini."""
        try:
            # Get conversation history
            history = self.conversations.get(conversation_id, [])
            history_text = "\n".join([
                f"User: {msg['user']}\nAI: {msg['ai']}"
                for msg in history[-5:]  # Last 5 messages
            ])

            # Build prompt based on intent
            system_prompt = self._get_system_prompt_for_intent(intent)

            prompt = f"""{system_prompt}

Conversation history:
{history_text}

User message: {message}

Provide a helpful, detailed response. Use markdown formatting for better readability."""

            content = await self.gemini_client.generate_text(prompt)

            return {
                "content": content,
                "format": "markdown"
            }

        except Exception as e:
            logger.error(f"Error generating text response: {e}")
            return {
                "content": "I apologize, but I'm having trouble generating a response. Please try again.",
                "format": "markdown"
            }

    def _get_system_prompt_for_intent(self, intent: IntentType) -> str:
        """Get system prompt based on intent."""
        prompts = {
            IntentType.VISUAL_EXPLORATION: """You are a home design expert helping users explore design ideas.
Provide inspiring, detailed descriptions of design options. Be enthusiastic and creative.""",

            IntentType.DIY_INSTRUCTIONS: """You are a DIY expert helping beginners and experienced DIYers.
Provide clear, step-by-step instructions with safety warnings. Be encouraging and practical.""",

            IntentType.COST_ESTIMATION: """You are a cost estimation expert for home improvement projects.
Provide realistic cost ranges, explain factors that affect cost, and suggest budget-friendly alternatives.""",

            IntentType.PRODUCT_SEARCH: """You are a product recommendation expert for home improvement.
Help users find the right products for their needs, considering quality, price, and availability.""",

            IntentType.RENOVATION_WORKFLOW: """You are a renovation planning expert guiding users through complete projects.
Break down the process into manageable stages and provide comprehensive guidance.""",

            IntentType.SAFETY_CHECK: """You are a safety expert for home improvement projects.
Prioritize safety, provide clear warnings, and explain proper safety procedures.""",

            IntentType.TROUBLESHOOTING: """You are a troubleshooting expert for home improvement problems.
Diagnose issues, provide multiple solution approaches, and explain root causes.""",

            IntentType.GENERAL_QUESTION: """You are a helpful home improvement assistant.
Answer questions clearly and provide useful information."""
        }
        return prompts.get(intent, prompts[IntentType.GENERAL_QUESTION])

    async def _generate_images(
        self,
        message: str,
        intent: IntentType,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate relevant images based on message and intent."""
        try:
            # Extract design requirements from message
            prompt = await self._create_image_generation_prompt(message, intent)

            # Generate 3 design variations
            images = []
            for i in range(3):
                variation_prompt = f"{prompt} - Variation {i+1}"

                generated_images = await self.gemini_client.generate_image(
                    prompt=variation_prompt,
                    aspect_ratio="16:9",
                    num_images=1
                )

                if generated_images:
                    # Save image
                    import os
                    from datetime import datetime

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"chat_generated_{timestamp}_{i}.png"
                    filepath = os.path.join("uploads", "chat", filename)

                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    generated_images[0].save(filepath)

                    images.append({
                        "url": f"/uploads/chat/{filename}",
                        "caption": f"Design variation {i+1}",
                        "type": "generated"
                    })

            return images

        except Exception as e:
            logger.error(f"Error generating images: {e}")
            return []

    async def _create_image_generation_prompt(
        self,
        message: str,
        intent: IntentType
    ) -> str:
        """Create optimized prompt for image generation."""
        prompt = f"""Based on this user request: "{message}"

Generate a high-quality, photorealistic home improvement design image.
Include proper lighting, realistic materials, and professional styling.
Make it inspiring and achievable."""

        result = await self.gemini_client.generate_text(prompt)
        return result.strip()

    async def _find_relevant_videos(
        self,
        message: str,
        intent: IntentType
    ) -> List[Dict[str, Any]]:
        """Find relevant tutorial videos (placeholder - would integrate with YouTube API)."""
        # For now, return placeholder
        # In production, integrate with YouTube Data API

        if intent == IntentType.DIY_INSTRUCTIONS:
            return [{
                "url": "https://www.youtube.com/watch?v=example",
                "title": "Step-by-Step Tutorial",
                "duration": "10:30",
                "thumbnail": "/static/video_placeholder.jpg",
                "source": "youtube"
            }]

        return []

    async def _search_products(
        self,
        message: str,
        intent: IntentType,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant products using Google Grounding."""
        try:
            # Extract product search query from message
            query = await self._extract_product_query(message)

            # Use Google Grounding to find products
            grounding_query = {
                "user_prompt": query,
                "requested_changes": [],
                "location_hint": "Vancouver, Canada"
            }

            result = await self.gemini_client.suggest_products_with_grounding(
                summary_or_grounding=grounding_query,
                max_items=8
            )

            # Format products
            products = []
            if hasattr(result, 'grounding_metadata') and result.grounding_metadata:
                for chunk in result.grounding_metadata.grounding_chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        products.append({
                            "title": chunk.web.title or "Product",
                            "url": chunk.web.uri,
                            "source": "google_grounding"
                        })

            return products[:8]  # Limit to 8 products

        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []

    async def _extract_product_query(self, message: str) -> str:
        """Extract product search query from user message."""
        prompt = f"""Extract the product search query from this message: "{message}"

Return ONLY the search query, nothing else. Make it specific and searchable.

Examples:
- "I need paint for my bedroom" → "interior wall paint"
- "Find me a grey sofa" → "grey sofa"
- "What tools do I need?" → "home improvement tools"

Message: {message}
Query:"""

        result = await self.gemini_client.generate_text(prompt)
        return result.strip()

    def _get_workflow_status(self, conversation_id: str) -> Dict[str, Any]:
        """Get current workflow status for conversation."""
        workflow = self.workflow_states.get(conversation_id, {
            "stage": "initial_consultation",
            "stage_number": 1,
            "total_stages": 7,
            "progress": 0.14,
            "next_steps": [
                "Tell me about your project vision",
                "Share your budget range",
                "Provide room dimensions"
            ]
        })
        return workflow

    def _generate_interactive_elements(
        self,
        intent: IntentType,
        response_type: ResponseType
    ) -> List[Dict[str, str]]:
        """Generate interactive UI elements based on intent."""
        elements = []

        if intent == IntentType.VISUAL_EXPLORATION:
            elements.extend([
                {"type": "button", "label": "Generate more designs", "action": "generate_variations"},
                {"type": "button", "label": "Customize this design", "action": "customize_design"}
            ])

        if intent == IntentType.DIY_INSTRUCTIONS:
            elements.extend([
                {"type": "button", "label": "Calculate materials", "action": "calculate_materials"},
                {"type": "button", "label": "Get step-by-step checklist", "action": "get_checklist"},
                {"type": "button", "label": "Show safety tips", "action": "show_safety"}
            ])

        if intent == IntentType.PRODUCT_SEARCH:
            elements.extend([
                {"type": "button", "label": "Show more options", "action": "show_more_products"},
                {"type": "button", "label": "Compare selected", "action": "compare_products"}
            ])

        if intent == IntentType.RENOVATION_WORKFLOW:
            elements.extend([
                {"type": "button", "label": "Continue to next stage", "action": "next_stage"},
                {"type": "button", "label": "Save progress", "action": "save_progress"}
            ])

        return elements

    def _save_to_history(
        self,
        conversation_id: str,
        user_message: str,
        ai_response: Dict[str, Any]
    ):
        """Save message exchange to conversation history."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        # Extract text content from response
        ai_text = ai_response.get("response", {}).get("text", {}).get("content", "")

        self.conversations[conversation_id].append({
            "user": user_message,
            "ai": ai_text,
            "full_response": ai_response
        })

        # Keep only last 20 messages
        if len(self.conversations[conversation_id]) > 20:
            self.conversations[conversation_id] = self.conversations[conversation_id][-20:]

    def _update_workflow_state(
        self,
        conversation_id: str,
        response: Dict[str, Any]
    ):
        """Update workflow state based on conversation progress."""
        if conversation_id not in self.workflow_states:
            self.workflow_states[conversation_id] = {
                "stage": "initial_consultation",
                "stage_number": 1,
                "total_stages": 7,
                "progress": 0.14,
                "next_steps": []
            }

        # Workflow progression logic would go here
        # For now, just maintain current state

    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get conversation history."""
        history = self.conversations.get(conversation_id, [])
        return history[-limit:]

    def get_workflow_status(self, conversation_id: str) -> Dict[str, Any]:
        """Get workflow status for a conversation."""
        return self._get_workflow_status(conversation_id)

