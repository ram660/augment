"""Conversation Manager - Handle multi-turn conversations with context and clarifications."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.conversation_service import ConversationService
from backend.integrations.gemini.client import GeminiClient

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manage multi-turn conversations with context tracking and clarification handling.
    
    Features:
    - Track conversation state across turns
    - Detect when clarification is needed
    - Handle follow-up questions
    - Maintain conversation context
    - Detect topic changes
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversation_service = ConversationService(db)
        self.gemini_client = GeminiClient()
    
    async def analyze_conversation_turn(
        self,
        conversation_id: str,
        current_message: str,
        previous_messages: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a conversation turn to determine context and needs.
        
        Returns:
            {
                "is_follow_up": bool,
                "needs_clarification": bool,
                "clarification_questions": List[str],
                "topic_changed": bool,
                "current_topic": str,
                "referenced_entities": List[str],
                "confidence": float
            }
        """
        try:
            # Load previous messages if not provided
            if previous_messages is None:
                previous_messages = await self.conversation_service.get_recent_messages(
                    conversation_id=conversation_id,
                    count=6
                )
            
            # Analyze the turn
            analysis = await self._analyze_turn(current_message, previous_messages)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze conversation turn: {e}", exc_info=True)
            return {
                "is_follow_up": False,
                "needs_clarification": False,
                "clarification_questions": [],
                "topic_changed": False,
                "current_topic": "general",
                "referenced_entities": [],
                "confidence": 0.5
            }
    
    async def _analyze_turn(
        self,
        current_message: str,
        previous_messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Analyze conversation turn using AI."""
        try:
            # Build context from previous messages
            context_text = "\n".join([
                f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
                for msg in previous_messages[-4:]  # Last 4 messages (2 exchanges)
            ])
            
            analysis_prompt = f"""Analyze this conversation turn. Return ONLY a JSON object.

Previous conversation:
{context_text}

Current user message: "{current_message}"

Analyze:
1. Is this a follow-up to the previous conversation?
2. Does the user's message need clarification?
3. What is the current topic?
4. Did the topic change from the previous conversation?
5. What entities (rooms, materials, products) are referenced?

Return JSON:
{{
    "is_follow_up": <true/false>,
    "needs_clarification": <true/false>,
    "clarification_questions": ["question1", "question2"],
    "topic_changed": <true/false>,
    "current_topic": "<topic>",
    "referenced_entities": ["entity1", "entity2"],
    "confidence": <0.0-1.0>
}}"""
            
            response = await self.gemini_client.generate_text(
                prompt=analysis_prompt,
                temperature=0.2,
                max_tokens=500
            )
            
            # Parse JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(0))
                return analysis
            
            # Fallback
            return {
                "is_follow_up": len(previous_messages) > 0,
                "needs_clarification": False,
                "clarification_questions": [],
                "topic_changed": False,
                "current_topic": "general",
                "referenced_entities": [],
                "confidence": 0.5
            }
            
        except Exception as e:
            logger.warning(f"Turn analysis failed: {e}")
            return {
                "is_follow_up": len(previous_messages) > 0,
                "needs_clarification": False,
                "clarification_questions": [],
                "topic_changed": False,
                "current_topic": "general",
                "referenced_entities": [],
                "confidence": 0.5
            }
    
    async def generate_clarification_response(
        self,
        user_message: str,
        clarification_questions: List[str],
        context: Optional[str] = None
    ) -> str:
        """Generate a response that asks for clarification."""
        try:
            clarification_prompt = f"""The user said: "{user_message}"

We need clarification on these points:
{chr(10).join(f"- {q}" for q in clarification_questions)}

{f"Context: {context}" if context else ""}

Generate a friendly response that:
1. Acknowledges what the user said
2. Asks for the needed clarifications
3. Explains why the information is helpful
4. Keeps it conversational and helpful

Response:"""
            
            response = await self.gemini_client.generate_text(
                prompt=clarification_prompt,
                temperature=0.7,
                max_tokens=300
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate clarification: {e}")
            # Fallback to simple clarification
            questions_text = "\n".join(f"{i+1}. {q}" for i, q in enumerate(clarification_questions))
            return f"I'd be happy to help! To give you the best answer, could you clarify:\n\n{questions_text}"
    
    async def detect_ambiguity(
        self,
        user_message: str,
        home_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect ambiguity in user message that needs clarification.
        
        Returns:
            {
                "is_ambiguous": bool,
                "ambiguity_type": str,  # "missing_info", "multiple_options", "unclear_intent"
                "suggestions": List[str],
                "confidence": float
            }
        """
        try:
            # Build context string
            context_str = ""
            if home_context:
                rooms = home_context.get("rooms", [])
                if rooms:
                    room_names = [r.get("name", r.get("room_type", "")) for r in rooms[:10]]
                    context_str = f"\nAvailable rooms: {', '.join(room_names)}"
            
            ambiguity_prompt = f"""Analyze this user message for ambiguity. Return ONLY a JSON object.

User message: "{user_message}"
{context_str}

Check for:
1. Missing critical information (which room? what size? what style?)
2. Multiple possible interpretations
3. Unclear intent

Return JSON:
{{
    "is_ambiguous": <true/false>,
    "ambiguity_type": "<missing_info|multiple_options|unclear_intent|none>",
    "suggestions": ["suggestion1", "suggestion2"],
    "confidence": <0.0-1.0>
}}"""
            
            response = await self.gemini_client.generate_text(
                prompt=ambiguity_prompt,
                temperature=0.1,
                max_tokens=300
            )
            
            # Parse JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            return {
                "is_ambiguous": False,
                "ambiguity_type": "none",
                "suggestions": [],
                "confidence": 0.5
            }
            
        except Exception as e:
            logger.warning(f"Ambiguity detection failed: {e}")
            return {
                "is_ambiguous": False,
                "ambiguity_type": "none",
                "suggestions": [],
                "confidence": 0.5
            }
    
    async def resolve_references(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Resolve pronouns and references in user message.
        
        Examples:
        - "it" -> "the kitchen"
        - "that room" -> "the master bedroom"
        - "the same one" -> "hardwood flooring"
        
        Returns:
            {
                "resolved_message": str,
                "references_found": List[Dict[str, str]],
                "confidence": float
            }
        """
        try:
            # Build conversation context
            context_text = "\n".join([
                f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
                for msg in conversation_history[-6:]
            ])
            
            resolution_prompt = f"""Resolve pronouns and references in the current message based on conversation history.

Conversation history:
{context_text}

Current message: "{user_message}"

Identify pronouns/references like "it", "that", "the same", "there" and what they refer to.

Return JSON:
{{
    "resolved_message": "<message with references replaced>",
    "references_found": [
        {{"pronoun": "it", "refers_to": "the kitchen"}},
        {{"pronoun": "that", "refers_to": "hardwood flooring"}}
    ],
    "confidence": <0.0-1.0>
}}"""
            
            response = await self.gemini_client.generate_text(
                prompt=resolution_prompt,
                temperature=0.2,
                max_tokens=400
            )
            
            # Parse JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            return {
                "resolved_message": user_message,
                "references_found": [],
                "confidence": 0.5
            }
            
        except Exception as e:
            logger.warning(f"Reference resolution failed: {e}")
            return {
                "resolved_message": user_message,
                "references_found": [],
                "confidence": 0.5
            }
    
    async def should_summarize_conversation(
        self,
        conversation_id: str
    ) -> bool:
        """Determine if conversation should be summarized."""
        try:
            conversation = await self.conversation_service.get_conversation(conversation_id)
            
            if not conversation:
                return False
            
            # Summarize every 20 messages
            return conversation.message_count > 0 and conversation.message_count % 20 == 0
            
        except Exception as e:
            logger.error(f"Failed to check summarization need: {e}")
            return False

