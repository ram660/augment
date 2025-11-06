"""
Conversation Agent - Natural language interface for HomeVision AI.

This agent handles all conversational interactions with homeowners:
- Intent classification and routing
- Context retention across sessions
- Proactive suggestions
- Multi-turn conversations
- Voice command support
"""

import logging
from typing import Any, Dict, List, Optional
from enum import Enum

from backend.agents.base import BaseAgent, AgentConfig, AgentRole, AgentResponse
from backend.agents.base.memory import ConversationMemory
from backend.integrations.gemini import GeminiClient

logger = logging.getLogger(__name__)


class ConversationIntent(str, Enum):
    """Types of user intents."""
    DESIGN_REQUEST = "design_request"
    PRODUCT_SEARCH = "product_search"
    COST_ESTIMATE = "cost_estimate"
    CONTRACTOR_SEARCH = "contractor_search"
    PROJECT_STATUS = "project_status"
    HOME_INFO = "home_info"
    MAINTENANCE_QUERY = "maintenance_query"
    GENERAL_QUESTION = "general_question"
    CLARIFICATION_NEEDED = "clarification_needed"


class ConversationAgent(BaseAgent):
    """
    Conversation Agent for natural language interactions.
    
    Capabilities:
    - Understand user intent from natural language
    - Maintain conversation context
    - Route to specialist agents
    - Provide helpful responses
    - Ask clarifying questions when needed
    """
    
    SYSTEM_INSTRUCTION = """You are the AI assistant for HomeVision AI, a platform that helps homeowners plan and execute home improvement projects.

Your role is to:
1. Understand what the homeowner wants to accomplish
2. Ask clarifying questions when needed
3. Provide helpful, actionable responses
4. Guide users through the platform's capabilities
5. Be friendly, professional, and concise

Platform capabilities:
- Design visualization and planning
- Product search and recommendations
- Cost estimation and budgeting
- Contractor matching and quotes
- Project management and tracking
- Home profile and maintenance tracking

When responding:
- Be conversational but professional
- Ask ONE clarifying question at a time if needed
- Suggest specific next steps
- Reference the user's home profile when relevant
- Keep responses under 150 words unless detailed explanation is needed
"""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize Conversation Agent.
        
        Args:
            gemini_client: Optional Gemini client (creates new one if not provided)
        """
        config = AgentConfig(
            name="conversation_agent",
            role=AgentRole.CONVERSATION,
            description="Natural language interface for homeowner interactions",
            temperature=0.7,
            enable_memory=True,
            memory_window=20  # Remember last 20 interactions
        )
        super().__init__(config)
        
        # Use provided client or create new one
        self.gemini = gemini_client or GeminiClient()
        
        # Use ConversationMemory for chat history
        self.memory = ConversationMemory(window_size=20)
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process user message and generate response.
        
        Args:
            input_data: {
                "message": str,  # User's message
                "user_id": str,  # User identifier
                "context": Optional[Dict],  # Additional context (home profile, current project, etc.)
            }
            
        Returns:
            AgentResponse with conversation result
        """
        try:
            message = input_data.get("message", "")
            user_id = input_data.get("user_id", "unknown")
            context = input_data.get("context", {})
            
            if not message:
                return AgentResponse(
                    agent_name=self.name,
                    agent_role=self.role,
                    success=False,
                    error="No message provided"
                )
            
            # Add user message to memory
            self.memory.add_message("user", message)
            
            # Classify intent
            intent = await self._classify_intent(message, context)
            
            # Generate response
            response_text = await self._generate_response(message, context, intent)
            
            # Add assistant response to memory
            self.memory.add_message("assistant", response_text)
            
            # Determine if we need to route to specialist agent
            specialist_agent = self._get_specialist_agent(intent)
            
            return AgentResponse(
                agent_name=self.name,
                agent_role=self.role,
                success=True,
                data={
                    "response": response_text,
                    "intent": intent,
                    "specialist_agent": specialist_agent,
                    "conversation_history": self.memory.get_messages(include_system=False)
                },
                metadata={
                    "user_id": user_id,
                    "message_count": len(self.memory)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in conversation processing: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.name,
                agent_role=self.role,
                success=False,
                error=str(e)
            )
    
    async def _classify_intent(self, message: str, context: Dict[str, Any]) -> ConversationIntent:
        """
        Classify user intent from message.
        
        Args:
            message: User's message
            context: Additional context
            
        Returns:
            Classified intent
        """
        # Build classification prompt
        classification_prompt = f"""Classify the user's intent from this message.

User message: "{message}"

Context: {context if context else "No additional context"}

Possible intents:
- design_request: User wants to design/visualize a room or project
- product_search: User is looking for specific products or materials
- cost_estimate: User wants cost information or budget planning
- contractor_search: User wants to find contractors or get quotes
- project_status: User asking about current project status
- home_info: User asking about their home profile or specifications
- maintenance_query: User asking about maintenance or repairs
- general_question: General questions about home improvement
- clarification_needed: Message is unclear or needs more information

Respond with ONLY the intent name, nothing else."""
        
        try:
            intent_str = await self.gemini.generate_text(
                classification_prompt,
                temperature=0.3  # Lower temperature for classification
            )
            
            # Parse intent
            intent_str = intent_str.strip().lower()
            
            # Try to match to enum
            for intent in ConversationIntent:
                if intent.value in intent_str:
                    return intent
            
            # Default to general question
            return ConversationIntent.GENERAL_QUESTION
            
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            return ConversationIntent.GENERAL_QUESTION
    
    async def _generate_response(
        self,
        message: str,
        context: Dict[str, Any],
        intent: ConversationIntent
    ) -> str:
        """
        Generate response to user message.
        
        Args:
            message: User's message
            context: Additional context
            intent: Classified intent
            
        Returns:
            Response text
        """
        # Build context string
        context_str = ""
        if context:
            if "home_profile" in context:
                home = context["home_profile"]
                context_str += f"\nUser's home: {home.get('home_type', 'unknown')} in {home.get('city', 'unknown')}"
            if "current_project" in context:
                project = context["current_project"]
                context_str += f"\nCurrent project: {project.get('name', 'unknown')} ({project.get('status', 'unknown')})"
        
        # Get conversation history
        history = self.memory.get_messages(include_system=False)
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-5:]])  # Last 5 messages
        
        # Build prompt
        prompt = f"""User message: "{message}"

Intent: {intent.value}

{context_str}

Recent conversation:
{history_str if history_str else "No previous conversation"}

Generate a helpful, conversational response. If you need more information, ask ONE specific clarifying question."""
        
        try:
            response = await self.gemini.generate_text(
                prompt,
                temperature=0.7,
                system_instruction=self.SYSTEM_INSTRUCTION
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Could you please try again?"
    
    def _get_specialist_agent(self, intent: ConversationIntent) -> Optional[str]:
        """
        Determine which specialist agent should handle this intent.
        
        Args:
            intent: Classified intent
            
        Returns:
            Specialist agent name or None
        """
        routing_map = {
            ConversationIntent.DESIGN_REQUEST: "design_orchestrator",
            ConversationIntent.PRODUCT_SEARCH: "product_discovery",
            ConversationIntent.COST_ESTIMATE: "cost_intelligence",
            ConversationIntent.CONTRACTOR_SEARCH: "contractor_matching",
            ConversationIntent.PROJECT_STATUS: "project_management",
            ConversationIntent.HOME_INFO: "home_profile_manager",
            ConversationIntent.MAINTENANCE_QUERY: "predictive_maintenance",
        }
        
        return routing_map.get(intent)
    
    def get_conversation_summary(self) -> str:
        """
        Get a summary of the current conversation.
        
        Returns:
            Summary text
        """
        return self.memory.summarize_context()
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.memory.clear()
        logger.info(f"Conversation reset for {self.name}")

