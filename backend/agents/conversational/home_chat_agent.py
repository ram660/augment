"""
Home Chat Agent
Conversational AI agent for answering questions about home data using LangChain and Gemini
"""

import os
import logging
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)


class HomeChatAgent:
    """
    Conversational agent for answering questions about home data.
    Uses LangChain with Gemini for natural language understanding and generation.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the chat agent."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        # Initialize Gemini model (lazily import to handle version mismatches)
        self.llm = None
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI as _ChatGoogleGenerativeAI
            self.llm = _ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=self.api_key,
                temperature=0.7,
                max_output_tokens=2048,
            )
        except Exception as e:
            logger.error(
                "Failed to initialize Gemini LLM. Ensure compatible versions of google-generativeai and langchain-google-genai are installed.",
                exc_info=True,
            )
        
        # Try to import message classes from langchain core; optional
        self._msg_classes = None
        try:
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage  # type: ignore
            self._msg_classes = (HumanMessage, AIMessage, SystemMessage)
        except Exception:
            # If unavailable, we'll fall back to plain string prompts
            self._msg_classes = None
        
        # Create system prompt
        self.system_prompt = self._create_system_prompt()
        
        logger.info("HomeChatAgent initialized successfully")
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the agent."""
        return """You are HomeVision AI, an intelligent home improvement assistant. You help homeowners, DIY enthusiasts, and contractors understand their homes and plan improvements.

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

When answering questions:
1. First check if relevant home data is provided in the context
2. Use specific details from the home data when available
3. Provide actionable insights and recommendations
4. Suggest follow-up questions or actions when appropriate
"""
    
    async def chat(
        self,
        user_message: str,
        home_data: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Process a user message and generate a response.
        
        Args:
            user_message: The user's question or message
            home_data: Complete home data from the digital twin
            conversation_history: Previous conversation messages
            
        Returns:
            AI-generated response
        """
        try:
            # Build context from home data
            context = self._build_context(home_data) if home_data else ""
            
            # Create the prompt
            prompt = self._create_prompt(user_message, context, conversation_history)
            
            # If LLM failed to initialize, provide a graceful fallback
            if self.llm is None:
                return self._local_fallback(user_message, home_data, context)

            # Generate response (async)
            response = await self.llm.ainvoke(prompt)
            
            # Extract text from response
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            logger.info(f"Generated response for query: {user_message[:50]}...")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            return f"I apologize, but I encountered an error processing your request. Please try rephrasing your question."

    def _local_fallback(self, user_message: str, home_data: Optional[Dict[str, Any]], context: str) -> str:
        """Simple local fallback when LLM isn't available (dependency issue)."""
        parts = []
        parts.append("(Temporary fallback: LLM provider unavailable; using a simple response.)")
        if context:
            parts.append("I do have some context about your home:")
            # Keep it short
            ctx_lines = context.splitlines()[:10]
            parts.append("\n".join(ctx_lines))
        parts.append("")
        parts.append(f"You asked: {user_message}")
        parts.append("")
        parts.append("Here's how I can help right now:")
        parts.append("- Summarize rooms, floors, and basic stats from available data")
        parts.append("- Suggest general improvement ideas and next steps")
        parts.append("- If you provide a specific room or floor, I can tailor the guidance")
        parts.append("")
        parts.append("Tip: Once the AI provider is available again, you'll get richer, conversational answers.")
        return "\n".join(parts)
    
    def _build_context(self, home_data: Dict[str, Any]) -> str:
        """Build context string from home data."""
        if not home_data:
            return ""
        
        context_parts = []
        
        # Basic home info
        basic_info = home_data.get('basic_info', {})
        if basic_info:
            context_parts.append("**Home Information:**")
            context_parts.append(f"- Name: {basic_info.get('name', 'N/A')}")
            # home_type is top-level in our digital twin structure
            context_parts.append(f"- Type: {home_data.get('home_type', 'N/A')}")
            sq_val = basic_info.get('square_footage')
            size_str = f"{sq_val:,} sq ft" if isinstance(sq_val, (int, float)) else "N/A"
            bed_val = basic_info.get('num_bedrooms')
            bed_str = str(bed_val) if isinstance(bed_val, (int, float)) else "N/A"
            bath_val = basic_info.get('num_bathrooms')
            bath_str = str(bath_val) if isinstance(bath_val, (int, float)) else "N/A"
            context_parts.append(f"- Size: {size_str}")
            context_parts.append(f"- Bedrooms: {bed_str}")
            context_parts.append(f"- Bathrooms: {bath_str}")
            context_parts.append(f"- Year Built: {basic_info.get('year_built', 'N/A')}")
            context_parts.append("")
        
        # Rooms summary
        rooms = home_data.get('rooms', [])
        if rooms:
            context_parts.append(f"**Rooms ({len(rooms)} total):**")

            # Per-floor breakdown
            floors: Dict[int, List[Dict[str, Any]]] = {}
            for r in rooms:
                lvl = r.get('floor_level', 1) or 1
                floors.setdefault(lvl, []).append(r)

            def floor_label(n: int) -> str:
                if n == 0:
                    return "Basement"
                if n == 1:
                    return "Main"
                if n == 2:
                    return "Second"
                if n >= 3:
                    return f"Third+ (Floor {n})"
                return f"Floor {n}"

            context_parts.append("\n**By Floor:**")
            for lvl in sorted(floors.keys()):
                context_parts.append(f"- {floor_label(lvl)}: {len(floors[lvl])} rooms")

            # Group rooms by type
            room_types: Dict[str, List[Dict[str, Any]]] = {}
            for room in rooms:
                room_type = room.get('room_type', 'unknown')
                room_types.setdefault(room_type, []).append(room)

            for room_type, room_list in room_types.items():
                context_parts.append(f"\n{room_type.replace('_', ' ').title()} ({len(room_list)}):")
                for room in room_list:
                    name = room.get('name') or room_type.replace('_', ' ').title()
                    lvl = room.get('floor_level', 1) or 1
                    dimensions = room.get('dimensions', {})
                    # Our digital twin returns 'area' key (not area_sqft)
                    area = dimensions.get('area')
                    area_str = f"{area:.1f} sq ft" if isinstance(area, (int, float)) else "N/A"
                    context_parts.append(f"  - {name} — Floor {lvl} — {area_str}")

                    # Add materials, fixtures, and products for this room
                    materials = room.get('materials', [])
                    if materials:
                        context_parts.append(f"    Materials ({len(materials)}):")
                        for mat in materials[:10]:  # Limit to 10 per room
                            mat_type = mat.get('material_type', 'unknown')
                            category = mat.get('category', '')
                            color = mat.get('color', '')
                            finish = mat.get('finish', '')
                            details = []
                            if color:
                                details.append(f"color: {color}")
                            if finish:
                                details.append(f"finish: {finish}")
                            detail_str = f" ({', '.join(details)})" if details else ""
                            context_parts.append(f"      • {category}: {mat_type}{detail_str}")

                    fixtures = room.get('fixtures', [])
                    if fixtures:
                        context_parts.append(f"    Fixtures ({len(fixtures)}):")
                        for fix in fixtures[:10]:  # Limit to 10 per room
                            fix_type = fix.get('fixture_type', 'unknown')
                            style = fix.get('style', '')
                            finish = fix.get('finish', '')
                            details = []
                            if style:
                                details.append(f"style: {style}")
                            if finish:
                                details.append(f"finish: {finish}")
                            detail_str = f" ({', '.join(details)})" if details else ""
                            context_parts.append(f"      • {fix_type}{detail_str}")

                    products = room.get('products', [])
                    if products:
                        context_parts.append(f"    Products ({len(products)}):")
                        for prod in products[:10]:  # Limit to 10 per room
                            prod_type = prod.get('product_type', 'unknown')
                            category = prod.get('product_category', '')
                            style = prod.get('style', '')
                            details = []
                            if category:
                                details.append(f"category: {category}")
                            if style:
                                details.append(f"style: {style}")
                            detail_str = f" ({', '.join(details)})" if details else ""
                            context_parts.append(f"      • {prod_type}{detail_str}")

                # Limit detailed lists if very large
                if len(room_list) > 25:
                    context_parts.append("  …many more rooms omitted for brevity…")
        
        # Digital twin completeness
        completeness = home_data.get('digital_twin_completeness', 0) * 100
        context_parts.append(f"**Digital Twin Completeness:** {completeness:.0f}%")
        return "\n".join(context_parts)
    
    def _create_prompt(
        self,
        user_message: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List:
        """Create the prompt for the LLM."""
        # If we have LC message classes, build a structured chat; otherwise return a single string prompt
        if self._msg_classes is not None:
            HumanMessage, AIMessage, SystemMessage = self._msg_classes  # type: ignore
            messages = []

            # System message MUST be first for Gemini
            system_content = self.system_prompt

            # Include context in system message if available
            if context:
                system_content += f"""

**CURRENT HOME DATA:**

{context}

Use this home data to provide accurate, specific answers to the user's questions."""

            messages.append(SystemMessage(content=system_content))

            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages for context
                    if msg['role'] == 'user':
                        messages.append(HumanMessage(content=msg['content']))
                    elif msg['role'] == 'assistant':
                        messages.append(AIMessage(content=msg['content']))

            # Add current user message
            messages.append(HumanMessage(content=user_message))
            return messages

        # Plain string fallback prompt
        prompt_parts = [self.system_prompt]
        if context:
            prompt_parts.append("\nCURRENT HOME DATA:\n\n" + context)
        if conversation_history:
            prompt_parts.append("\nRECENT HISTORY:\n")
            for msg in conversation_history[-10:]:
                role = msg.get('role', 'user')
                prefix = 'User' if role == 'user' else 'Assistant'
                prompt_parts.append(f"{prefix}: {msg.get('content','')}")
        prompt_parts.append("\nUser: " + user_message)
        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)
    
    def reset_memory(self):
        """Reset conversation memory."""
        # Memory is optional now; nothing to reset
        logger.info("Conversation memory reset (no-op)")


# Singleton instance
_agent_instance: Optional[HomeChatAgent] = None


def get_chat_agent() -> HomeChatAgent:
    """Get or create the chat agent singleton."""
    global _agent_instance
    
    if _agent_instance is None:
        _agent_instance = HomeChatAgent()
    
    return _agent_instance


async def process_chat_message(
    user_message: str,
    home_data: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Convenience function to process a chat message.
    
    Args:
        user_message: The user's question
        home_data: Complete home data from digital twin
        conversation_history: Previous messages
        
    Returns:
        AI-generated response
    """
    agent = get_chat_agent()
    return await agent.chat(user_message, home_data, conversation_history)

