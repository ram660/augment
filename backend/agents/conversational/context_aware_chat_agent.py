"""Context-Aware Chat Agent - Intelligent chat with full home context and agent orchestration."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.base.agent import BaseAgent, AgentResponse, AgentConfig, AgentRole
from backend.services.rag_service import RAGService
from backend.services.conversation_service import ConversationService
from backend.agents.intelligence.cost_estimation_agent import CostEstimationAgent
from backend.agents.intelligence.product_matching_agent import ProductMatchingAgent
from backend.integrations.gemini.client import GeminiClient

logger = logging.getLogger(__name__)


class ContextAwareChatAgent(BaseAgent):
    """
    Context-aware chat agent with intelligence agent orchestration.
    
    Features:
    - Full home context awareness via RAG
    - Conversation history management
    - Intent-based agent routing
    - Cost estimation integration
    - Product matching integration
    - Multi-turn conversation support
    """
    
    def __init__(self, db_session: AsyncSession):
        config = AgentConfig(
            name="context_aware_chat",
            role=AgentRole.CONVERSATION,
            description="Intelligent chat agent with full home context awareness",
            temperature=0.7,
            max_tokens=2048
        )
        super().__init__(config)
        self.db = db_session
        self.rag_service = RAGService(use_gemini=True)
        self.conversation_service = ConversationService(db_session)
        self.cost_agent = CostEstimationAgent()
        self.product_agent = ProductMatchingAgent()
        self.gemini_client = GeminiClient()
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process a chat message with full context awareness.
        
        Args:
            input_data: {
                "user_message": str,
                "home_id": Optional[str],
                "conversation_id": Optional[str],
                "user_id": Optional[str]
            }
        
        Returns:
            AgentResponse with AI response and suggested actions
        """
        try:
            user_message = input_data.get("user_message")
            if not user_message:
                return AgentResponse(
                    agent_name=self.name,
                    agent_role=self.role,
                    success=False,
                    data={},
                    error="user_message is required",
                    metadata={}
                )
            
            home_id = input_data.get("home_id")
            conversation_id = input_data.get("conversation_id")
            
            # Step 1: Classify intent
            intent = await self._classify_intent(user_message)
            logger.info(f"Classified intent: {intent['intent']}")
            
            # Step 2: Retrieve context if home_id provided
            context = None
            if home_id:
                context = await self.rag_service.assemble_context(
                    db=self.db,
                    query=user_message,
                    home_id=home_id,
                    k=8,
                    include_images=True
                )
            
            # Step 3: Load conversation history
            conversation_history = []
            if conversation_id:
                conversation_history = await self.conversation_service.get_recent_messages(
                    conversation_id=conversation_id,
                    count=10
                )
            
            # Step 4: Route to specialized agent if needed
            specialized_response = None
            if intent["intent"] == "cost_estimate":
                specialized_response = await self._handle_cost_estimation(
                    user_message,
                    context
                )
            elif intent["intent"] == "product_recommendation":
                specialized_response = await self._handle_product_matching(
                    user_message,
                    context
                )
            
            # Step 5: Generate response
            if specialized_response:
                ai_response = specialized_response
            else:
                ai_response = await self._generate_response(
                    user_message,
                    context,
                    conversation_history,
                    intent
                )
            
            # Step 6: Suggest follow-up actions
            suggested_actions = self._suggest_actions(intent["intent"], home_id)

            return AgentResponse(
                agent_name=self.name,
                agent_role=self.role,
                success=True,
                data={
                    "ai_response": ai_response,
                    "intent": intent["intent"],
                    "suggested_actions": suggested_actions,
                    "context_sources": context.get("metadata", {}).get("sources", []) if context else []
                },
                metadata={
                    "intent_confidence": intent.get("confidence", 0.5),
                    "context_chunks": context.get("metadata", {}).get("total_chunks", 0) if context else 0,
                    "conversation_length": len(conversation_history)
                }
            )
            
        except Exception as e:
            logger.error(f"Context-aware chat failed: {e}", exc_info=True)
            return AgentResponse(
                agent_name=self.name,
                agent_role=self.role,
                success=False,
                data={},
                error=str(e),
                metadata={}
            )
    
    async def _classify_intent(self, user_message: str) -> Dict[str, Any]:
        """Classify user intent."""
        try:
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
            
            response = await self.gemini_client.generate_text(
                prompt=classification_prompt,
                temperature=0.1
            )
            
            # Parse JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            return {"intent": "question", "confidence": 0.5, "requires_home_data": False}
            
        except Exception as e:
            logger.warning(f"Intent classification failed: {e}")
            return {"intent": "question", "confidence": 0.5, "requires_home_data": False}
    
    async def _handle_cost_estimation(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Handle cost estimation requests."""
        try:
            # Extract project description from message and context
            project_description = user_message
            if context and context.get("context_text"):
                project_description += f"\n\nHome Context:\n{context['context_text'][:500]}"
            
            # Call cost estimation agent
            cost_response = await self.cost_agent.process({
                "project_description": project_description,
                "region": "national"  # TODO: Get from user profile
            })
            
            if cost_response.success:
                cost_data = cost_response.data
                
                # Format response
                response_parts = [
                    "Based on your project, here's a cost estimate:\n",
                    f"**Total Estimated Cost:** ${cost_data['summary']['total_cost']:,.2f}",
                    f"(Range: ${cost_data['summary']['min_cost']:,.2f} - ${cost_data['summary']['max_cost']:,.2f})\n",
                    "**Breakdown:**"
                ]
                
                # Material costs
                if cost_data.get("material_costs"):
                    response_parts.append("\n*Materials:*")
                    for material in cost_data["material_costs"][:5]:
                        response_parts.append(
                            f"- {material['material_type']}: ${material['total_cost']:,.2f}"
                        )
                
                # Labor costs
                if cost_data.get("labor_costs"):
                    response_parts.append("\n*Labor:*")
                    for labor in cost_data["labor_costs"][:5]:
                        response_parts.append(
                            f"- {labor['trade']}: ${labor['total_cost']:,.2f}"
                        )
                
                response_parts.append(
                    f"\n*Confidence:* {cost_data['summary']['confidence_score']*100:.0f}%"
                )
                response_parts.append(
                    "\nNote: This is an estimate. Actual costs may vary based on your location, "
                    "material choices, and contractor rates."
                )
                
                return "\n".join(response_parts)
            
            return "I couldn't generate a cost estimate. Could you provide more details about your project?"
            
        except Exception as e:
            logger.error(f"Cost estimation failed: {e}", exc_info=True)
            return "I encountered an error while estimating costs. Please try again."
    
    async def _handle_product_matching(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Handle product recommendation requests."""
        try:
            # Extract product type and room dimensions from context
            # This is simplified - in production, you'd parse the message more carefully
            
            # For now, return a helpful message
            return (
                "I can help you find products that fit your space! To give you the best recommendations, "
                "I need to know:\n"
                "1. What type of product are you looking for? (e.g., sofa, dining table, refrigerator)\n"
                "2. Which room is it for?\n"
                "3. Any style preferences?\n\n"
                "Once you provide these details, I can check if products will fit and suggest alternatives!"
            )
            
        except Exception as e:
            logger.error(f"Product matching failed: {e}", exc_info=True)
            return "I encountered an error while finding products. Please try again."
    
    async def _generate_response(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]],
        conversation_history: List[Dict[str, str]],
        intent: Dict[str, Any]
    ) -> str:
        """Generate AI response using Gemini."""
        try:
            prompt = self._build_prompt(user_message, context, conversation_history)
            
            response = await self.gemini_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2048
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}", exc_info=True)
            return (
                "I apologize, but I'm having trouble generating a response right now. "
                "Please try rephrasing your question or try again in a moment."
            )
    
    def _build_prompt(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Build comprehensive prompt."""
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
        
        # Add context
        if context and context.get("context_text"):
            prompt_parts.append("\n**CURRENT HOME DATA:**\n")
            prompt_parts.append(context["context_text"])
            prompt_parts.append("\nUse this home data to provide accurate, specific answers.")
        
        # Add conversation history
        if conversation_history:
            prompt_parts.append("\n**CONVERSATION HISTORY:**\n")
            for msg in conversation_history[-6:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg.get('content', '')}")
        
        # Add current message
        prompt_parts.append(f"\n**CURRENT USER MESSAGE:**\n{user_message}")
        prompt_parts.append("\n**YOUR RESPONSE:**")
        
        return "\n".join(prompt_parts)
    
    def _suggest_actions(self, intent: str, home_id: Optional[str]) -> List[Dict[str, Any]]:
        """Suggest follow-up actions."""
        actions = []
        
        if intent == "cost_estimate":
            actions.append({
                "action": "get_detailed_estimate",
                "label": "Get Detailed Cost Estimate",
                "description": "Get a comprehensive cost breakdown for your project",
                "agent": "cost_estimation"
            })
        
        elif intent == "product_recommendation":
            actions.append({
                "action": "find_products",
                "label": "Find Matching Products",
                "description": "Search for products that fit your space and style",
                "agent": "product_matching"
            })
        
        elif intent == "design_idea":
            actions.append({
                "action": "generate_design",
                "label": "Generate Design Mockup",
                "description": "Create AI-generated design visualizations",
                "agent": "design_studio"
            })
        
        if home_id:
            actions.append({
                "action": "explore_digital_twin",
                "label": "Explore Your Digital Twin",
                "description": "View your home's 3D model and room details",
                "agent": "digital_twin"
            })
        
        return actions

