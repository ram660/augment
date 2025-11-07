"""
Chat API endpoints for HomeView AI.

Provides conversational AI interface with context-aware responses.
"""

import logging
from typing import Optional, List, AsyncGenerator
from uuid import UUID, uuid4
from datetime import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from backend.api.auth import get_current_user
from backend.models.user import User
from backend.models.conversation import Conversation, ConversationMessage
from backend.models.base import get_async_db
from backend.workflows.chat_workflow import ChatWorkflow
from backend.services.conversation_service import ConversationService
from backend.services.rag_service import RAGService
from backend.integrations.gemini.client import GeminiClient

from fastapi import File, UploadFile, Form
from pathlib import Path

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatMessageRequest(BaseModel):
    """Chat message request."""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None
    home_id: Optional[str] = None
    context: Optional[dict] = {}
    persona: Optional[str] = None  # 'homeowner' | 'diy_worker' | 'contractor'
    scenario: Optional[str] = None  # 'contractor_quotes' | 'diy_project_plan'


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    conversation_id: str
    message_id: str
    response: str
    intent: str
    suggested_actions: List[dict] = []
    metadata: dict = {}


class ConversationResponse(BaseModel):
    """Conversation response."""
    id: str
    user_id: str
    home_id: Optional[str]
    title: str
    persona: Optional[str] = None
    scenario: Optional[str] = None
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationHistoryResponse(BaseModel):
    """Conversation history response."""
    conversation_id: str
    messages: List[dict]
    total_messages: int

# Local helpers for file handling and URLs (mirror digital_twin behavior)
def _portable_url(url: str) -> str:
    if not url:
        return url
    url = str(url).replace("\\", "/")
    if url.startswith("uploads/"):
        return "/" + url
    parts = url.split("/")
    if "uploads" in parts:
        idx = parts.index("uploads")
        return "/" + "/".join(parts[idx:])
    return url

async def _save_upload_file(upload_file: UploadFile, destination: Path) -> str:
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "wb") as buffer:
            content = await upload_file.read()
            buffer.write(content)
        return str(destination)
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


class UpdateConversationRequest(BaseModel):
    """Update conversation attributes."""
    title: Optional[str] = None
    persona: Optional[str] = None  # 'homeowner' | 'diy_worker' | 'contractor'
    scenario: Optional[str] = None  # 'contractor_quotes' | 'diy_project_plan'


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send a chat message and get AI response.

    Args:
        request: Chat message request
        current_user: Current authenticated user
        db: Database session

    Returns:
        AI response with conversation context
    """
    try:
        # Initialize services
        conversation_service = ConversationService(db)
        chat_workflow = ChatWorkflow(db)

        # Get or create conversation
        if request.conversation_id:
            conversation = await conversation_service.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            if conversation.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this conversation"
                )
            # Update persona/scenario if provided
            if request.persona or request.scenario:
                await conversation_service.update_conversation_attributes(
                    conversation_id=str(conversation.id),
                    persona=request.persona,
                    scenario=request.scenario,
                )
        else:
            # Create new conversation
            conversation = await conversation_service.create_conversation(
                user_id=str(current_user.id),
                home_id=request.home_id,
                title="New Conversation",  # Will be auto-generated from first message
                persona=request.persona,
                scenario=request.scenario,
            )

        # Resolve effective home_id: prefer request.home_id, else conversation.home_id
        resolved_home_uuid = None
        try:
            if request.home_id:
                resolved_home_uuid = UUID(request.home_id)
            elif conversation.home_id:
                resolved_home_uuid = conversation.home_id
        except Exception:
            resolved_home_uuid = None

        # If a home_id is provided now but the conversation has none, persist it
        if request.home_id and not conversation.home_id:
            try:
                conversation.home_id = UUID(request.home_id)
                await db.commit()
                await db.refresh(conversation)
            except Exception:
                # Non-fatal; continue without persisting
                await db.rollback()

        # Execute chat workflow
        workflow_input = {
            "user_message": request.message,
            "conversation_id": str(conversation.id),
            "user_id": str(current_user.id),
            "home_id": str(resolved_home_uuid) if resolved_home_uuid else "",
            "context": request.context or {},
            "persona": request.persona,
            "scenario": request.scenario,
        }

        result = await chat_workflow.execute(workflow_input)

        # Check if workflow failed
        if result.get("status") == "failed" or result.get("errors"):
            error_msg = result.get("errors", [{}])[0].get("message", "Chat workflow failed") if result.get("errors") else "Chat workflow failed"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

        # Get AI response from workflow result
        ai_response = result.get("ai_response", "")

        # Save messages to database
        user_message = await conversation_service.add_message(
            conversation_id=str(conversation.id),
            role="user",
            content=request.message,
            metadata={
                "intent": result.get("intent", "unknown"),
                "persona": request.persona,
                "scenario": request.scenario,
            }
        )

        assistant_message = await conversation_service.add_message(
            conversation_id=str(conversation.id),
            role="assistant",
            content=ai_response,
            metadata={
                "intent": result.get("intent", "unknown"),
                "suggested_actions": result.get("suggested_actions", []),
                "suggested_questions": result.get("suggested_questions", []),
                "persona": request.persona,
                "scenario": request.scenario,
            }
        )

        # Update conversation title if it's the first message
        if conversation.message_count == 0:
            await conversation_service.update_conversation_title(
                conversation_id=str(conversation.id),
                user_message=request.message
            )

        return ChatMessageResponse(
            conversation_id=str(conversation.id),
            message_id=str(assistant_message.id),
            response=ai_response,
            intent=result.get("intent", "unknown"),
            suggested_actions=result.get("suggested_actions", []),
            metadata=result.get("response_metadata", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat message error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )


@router.post("/stream")
async def stream_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Stream a chat message with real-time AI response.

    Args:
        request: Chat message request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Server-Sent Events stream with AI response tokens
    """
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            # Initialize services
            conversation_service = ConversationService(db)
            chat_workflow = ChatWorkflow(db)

            # Get or create conversation
            if request.conversation_id:
                conversation = await conversation_service.get_conversation(request.conversation_id)
                if not conversation or conversation.user_id != current_user.id:
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid conversation'})}\n\n"
                    return
                # Update persona/scenario if provided
                if request.persona or request.scenario:
                    await conversation_service.update_conversation_attributes(
                        conversation_id=str(conversation.id),
                        persona=request.persona,
                        scenario=request.scenario,
                    )
            else:
                conversation = await conversation_service.create_conversation(
                    user_id=str(current_user.id),
                    home_id=request.home_id,
                    title="New Conversation",
                    persona=request.persona,
                    scenario=request.scenario,
                )

            # Resolve effective home_id: prefer request.home_id, else conversation.home_id
            resolved_home_uuid = None
            try:
                if request.home_id:
                    resolved_home_uuid = UUID(request.home_id)
                elif conversation.home_id:
                    resolved_home_uuid = conversation.home_id
            except Exception:
                resolved_home_uuid = None

            # If a home_id is provided now but the conversation has none, persist it
            if request.home_id and not conversation.home_id:
                try:
                    conversation.home_id = UUID(request.home_id)
                    await db.commit()
                    await db.refresh(conversation)
                except Exception:
                    await db.rollback()

            # Build context and history, then stream via Gemini
            rag_service = RAGService(use_gemini=True)
            gemini_client = GeminiClient()

            # Digital Twin context temporarily disabled; proceed without RAG context
            context = None
            context_sources: List[str] = []

            # Save user message immediately (enables title auto-gen on first message)
            await conversation_service.add_message(
                conversation_id=str(conversation.id),
                role="user",
                content=request.message,
                metadata={
                    "persona": request.persona,
                    "scenario": request.scenario,
                },
                context_sources=context_sources,
            )

            # Load recent history (now includes the just-saved user message)
            history = await conversation_service.get_recent_messages(
                conversation_id=str(conversation.id),
                count=10,
            )

            # Build prompt using the same helper as the workflow for consistency
            prompt = chat_workflow._build_response_prompt(
                request.message,
                context,
                history,
                request.persona,
                request.scenario,
            )

            full_text = ""
            try:
                async for token in gemini_client.generate_text_stream(
                    prompt=prompt,
                    temperature=0.7,
                    max_tokens=2048,
                ):
                    full_text += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            except Exception as e:
                logger.error(f"Streaming from Gemini failed: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': 'Streaming failed'})}\n\n"
                return

            # Classify intent (post-stream) for metadata/suggestions
            intent = "question"
            try:
                classification_prompt = f"""Classify the user's intent from this message. Return ONLY a JSON object.

User message: "{request.message}"

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
                classification_resp = await gemini_client.generate_text(
                    prompt=classification_prompt,
                    temperature=0.1,
                )
                classification = chat_workflow._parse_json_response(classification_resp)
                intent = classification.get("intent", "question")
            except Exception as e:

	            # Heuristic nudge based on phrasing in the user's message
	            try:
	                um = (request.message or "").lower()
	                if intent == "question":
	                    if "pdf" in um:
	                        intent = "pdf_request"
	                    elif "guide" in um or "step-by-step" in um:
	                        intent = "diy_guide"
	                    elif "image" in um or "mockup" in um or "visual" in um:
	                        intent = "design_idea"
	            except Exception:
	                pass

	            # Initialize suggested questions list
	            suggested_questions: List[str] = []

                logger.warning(f"Intent classification failed, defaulting to 'question': {e}")
                intent = "question"


	            # Heuristic nudge based on phrasing in the user's message (post-classification)
	            try:
	                um = (request.message or "").lower()
	                if intent == "question":
	                    if "pdf" in um:
	                        intent = "pdf_request"
	                    elif "guide" in um or "step-by-step" in um:
	                        intent = "diy_guide"
	                    elif "image" in um or "mockup" in um or "visual" in um:
	                        intent = "design_idea"
	            except Exception:
	                pass

	            # Initialize suggested questions list (ensure defined)
	            suggested_questions: List[str] = []

            # Build suggested actions (mirrors workflow logic)
            suggested_actions: List[dict] = []
            if intent == "cost_estimate":
                suggested_actions.append({
                    "action": "get_detailed_estimate",
                    "label": "Get Detailed Cost Estimate",
                    "description": "Get a comprehensive cost breakdown for your project",
                    "agent": "cost_estimation",
                })
            elif intent == "product_recommendation":
                suggested_actions.append({
                    "action": "find_products",
                    "label": "Find Matching Products",
                    "description": "Search for products that fit your space and style",
                    "agent": "product_matching",
                })
            elif intent == "design_idea":
                suggested_actions.append({
                    "action": "generate_design",
                    "label": "Generate Design Mockup",
                    "description": "Create AI-generated design visualizations",
                    "agent": "design_studio",
                })

            p = request.persona
            s = request.scenario
            if p == "homeowner" or s == "contractor_quotes":
                suggested_actions.append({
                    "action": "start_contractor_quotes",
                    "label": "Get Contractor Quotes",
                    "description": "Prepare a brief and collect bids from contractors",
                    "agent": "contractor_quotes",
                })
            if p == "diy_worker" or s == "diy_project_plan":
                suggested_actions.append({
                    "action": "create_diy_plan",
                    "label": "Create My DIY Project Plan",
                    "description": "Get a step-by-step plan with tools and materials",
                    "agent": "diy_planner",
                })

                # Suggested follow-up questions
                suggested_questions: List[str] = []
                if intent == "cost_estimate":
                    suggested_questions.extend([
                        "What are the room dimensions (L x W x H)?",
                        "Include labor or materials only?",
                        "What material quality/tier and budget range?",
                        "What is your location (for Canada pricing)?",
                    ])
                elif intent == "product_recommendation":


                    suggested_questions.extend([
                        "Which room and its dimensions?",
                        "What budget range and style preference?",
                        "Any must-have materials or brands (.ca vendors preferred)?",
                        "Do you need eco-friendly or low-VOC options?",
                    ])
                elif intent == "design_idea":
                    suggested_questions.extend([
                        "Which room photo should I reference?",
                        "What styles or color palettes do you like?",
                        "Any elements to keep (flooring, cabinets, furniture)?",
                    ])
                elif intent == "design_transformation":
                    suggested_questions.extend([
                        "Which attached photo should I use?",
                        "What exact edits (paint color, flooring type, cabinets)?",
                        "Should I preserve existing furniture and layout?",
                    ])
                elif intent == "diy_guide":
                    suggested_questions.extend([
                        "What is your skill level and available time?",
                        "Do you already have any of the required tools?",
                        "What is your budget and deadline?",
                    ])
                elif intent == "pdf_request":
                    suggested_questions.extend([
                        "Include images and a materials checklist?",
                        "What title should I use for the PDF?",
                        "Do you want a Canadian vendor list appended?",
                    ])
                if not suggested_questions:
                    suggested_questions.extend([
                        "Which room or area are we focusing on?",
                        "What are the dimensions and current materials?",
                        "What is your budget and timeline?",
                        "Do you prefer DIY plan or contractor quotes?",
                    ])


            # Save assistant message
            await conversation_service.add_message(
                conversation_id=str(conversation.id),
                role="assistant",
                content=full_text,
                metadata={
                    "intent": intent,
                    "suggested_actions": suggested_actions,
                    "suggested_questions": suggested_questions,
                    "persona": request.persona,
                    "scenario": request.scenario,
                    "model": "gemini-2.5-flash",
                    "generated_at": datetime.utcnow().isoformat(),
                },
                context_sources=context_sources,
            )

            # Send completion event; frontend will refetch messages
            yield f"data: {json.dumps({'type': 'complete', 'message': {'conversation_id': str(conversation.id)}})}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Stream chat error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    home_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List user's conversations.

    Args:
        home_id: Optional filter by home ID
        limit: Maximum number of conversations to return
        offset: Offset for pagination
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of conversations
    """
    try:
        conversation_service = ConversationService(db)

        conversations = await conversation_service.list_conversations(
            user_id=str(current_user.id),
            home_id=home_id,
            limit=limit,
            offset=offset
        )

        return [
            ConversationResponse(
                id=str(conv.id),
                user_id=str(conv.user_id),
                home_id=str(conv.home_id) if conv.home_id else None,
                title=conv.title,
                persona=getattr(conv, 'persona', None),
                scenario=getattr(conv, 'scenario', None),
                message_count=conv.message_count,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
            for conv in conversations
        ]

    except Exception as e:
        logger.error(f"List conversations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations"
        )




@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update conversation title/persona/scenario."""
    try:
        conversation_service = ConversationService(db)
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        if conversation.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation")

        updated = await conversation_service.update_conversation_attributes(
            conversation_id=conversation_id,
            persona=request.persona,
            scenario=request.scenario,
            title=request.title,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update conversation attributes. If persona/scenario were recently added, run DB migrations."
            )

        conv = updated
        return ConversationResponse(
            id=str(conv.id),
            user_id=str(conv.user_id),
            home_id=str(conv.home_id) if conv.home_id else None,
            title=conv.title,
            persona=getattr(conv, 'persona', None),
            scenario=getattr(conv, 'scenario', None),
            message_count=conv.message_count,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update conversation error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update conversation")

@router.get("/conversations/{conversation_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get conversation history.

    Args:
        conversation_id: Conversation ID
        limit: Maximum number of messages to return
        offset: Offset for pagination
        current_user: Current authenticated user
        db: Database session

    Returns:
        Conversation history with messages
    """
    try:
        conversation_service = ConversationService(db)

        # Get conversation
        conversation = await conversation_service.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
            )

        # Get messages
        messages = await conversation_service.get_conversation_history(
            conversation_id=conversation_id,
            limit=limit
        )

        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            messages=[
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "metadata": msg.metadata or {},
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ],
            total_messages=conversation.message_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation history"
        )


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all messages for a conversation.

    Args:
        conversation_id: Conversation ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of messages in the conversation
    """
    try:
        conversation_service = ConversationService(db)

        # Get conversation
        conversation = await conversation_service.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
            )

        # Get messages
        messages = await conversation_service.get_messages(conversation_id)

        # Return plain list of messages to match frontend typings
        return [
            {
                "id": str(msg.id),
                "conversation_id": conversation_id,
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.message_metadata or {},
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation messages error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation messages"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a conversation.

    Args:
        conversation_id: Conversation ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    try:
        conversation_service = ConversationService(db)
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
            )
        await conversation_service.delete_conversation(conversation_id)
        return {
            "message": "Conversation deleted successfully",
            "conversation_id": conversation_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


@router.post("/stream-multipart")
@router.post("/stream_multipart")
async def stream_message_multipart(
    message: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    home_id: Optional[str] = Form(None),
    persona: Optional[str] = Form(None),
    scenario: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Stream a chat message with optional file uploads (images, PDFs) using multipart/form-data.
    Saves attachments, enriches context (analyzes images via Gemini), and streams the response.
    """

    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            conversation_service = ConversationService(db)
            chat_workflow = ChatWorkflow(db)
            rag_service = RAGService(use_gemini=True)
            gemini_client = GeminiClient()

            # Get or create conversation
            if conversation_id:
                conv = await conversation_service.get_conversation(conversation_id)
                if not conv or conv.user_id != current_user.id:
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid conversation'})}\n\n"
                    return
                # Update persona/scenario if provided
                if persona or scenario:
                    await conversation_service.update_conversation_attributes(
                        conversation_id=str(conv.id),
                        persona=persona,
                        scenario=scenario,
                    )
                conversation = conv
            else:
                conversation = await conversation_service.create_conversation(
                    user_id=str(current_user.id),
                    home_id=home_id,
                    title="New Conversation",
                    persona=persona,
                    scenario=scenario,
                )

            # Resolve effective home_id
            resolved_home_uuid = None
            try:
                if home_id:
                    resolved_home_uuid = UUID(home_id)
                elif conversation.home_id:
                    resolved_home_uuid = conversation.home_id
            except Exception:
                resolved_home_uuid = None

            if home_id and not conversation.home_id:
                try:
                    conversation.home_id = UUID(home_id)
                    await db.commit()
                    await db.refresh(conversation)
                except Exception:
                    await db.rollback()

            # Save attachments and analyze images
            attachments: List[dict] = []
            image_urls: List[str] = []
            attachment_summaries: List[str] = []
            if files:
                for f in files:
                    try:
                        ext = Path(f.filename or "").suffix or ".bin"
                        dest_dir = Path("uploads/chat") / str(conversation.id)
                        file_path = dest_dir / f"{uuid4()}{ext}"
                        saved_path = await _save_upload_file(f, file_path)
                        url = _portable_url(saved_path)
                        att_type = (
                            "image" if (f.content_type or "").startswith("image/") else (
                                "pdf" if (f.content_type == "application/pdf" or ext.lower() == ".pdf") else "file"
                            )
                        )
                        att: dict = {
                            "filename": f.filename,
                            "content_type": f.content_type,
                            "path": saved_path,
                            "url": url,
                            "type": att_type,
                        }
                        if att_type == "image":
                            try:
                                analysis = await gemini_client.analyze_design(saved_path)
                                if isinstance(analysis, dict):
                                    # Build one-line summary
                                    desc = analysis.get("description") or ""
                                    styles = analysis.get("styles") or []
                                    colors = [c.get("name") for c in (analysis.get("colors") or []) if isinstance(c, dict) and c.get("name")]
                                    summary_bits = []
                                    if desc:
                                        summary_bits.append(desc)
                                    if styles:
                                        summary_bits.append(f"styles: {', '.join(styles[:4])}")
                                    if colors:
                                        summary_bits.append(f"colors: {', '.join(colors[:4])}")
                                    summary_text = "; ".join(summary_bits)
                                    if summary_text:
                                        attachment_summaries.append(f"- {summary_text}")
                                    att["analysis"] = analysis
                            except Exception as ie:
                                logger.warning(f"Image analysis failed: {ie}")
                            image_urls.append(url)
                        attachments.append(att)
                    except Exception as fe:
                        logger.warning(f"Failed to handle attachment {getattr(f,'filename',None)}: {fe}")

            # Digital Twin context temporarily disabled; proceed without RAG context
            context = None
            context_sources: List[str] = []

            # Merge attachment context
            if attachments:
                if not context:
                    context = {"context_text": "", "image_urls": []}
                attach_section = ["\n**USER ATTACHMENTS:**"]
                if image_urls:
                    attach_section.append(f"{len(image_urls)} images attached.")
                non_images = [a for a in attachments if a.get("type") != "image"]
                if non_images:
                    attach_section.append(f"{len(non_images)} files attached (e.g., PDFs).")
                if attachment_summaries:
                    attach_section.append("Image analyses (concise):")
                    attach_section.extend(attachment_summaries[:5])
                context["context_text"] = (context.get("context_text") or "") + "\n" + "\n".join(attach_section)
                # Extend image URLs
                existing = context.get("image_urls") or []
                context["image_urls"] = list(existing) + image_urls

            # Save user message (with attachment metadata)
            await conversation_service.add_message(
                conversation_id=str(conversation.id),
                role="user",
                content=message,
                metadata={
                    "persona": persona,
                    "scenario": scenario,
                    "images": image_urls if image_urls else None,
                    "attachments": [
                        {k: v for k, v in att.items() if k in ("url", "filename", "content_type", "type")}
                        for att in attachments
                    ] if attachments else None,
                },
                context_sources=context_sources,
            )

            # Load history
            history = await conversation_service.get_recent_messages(
                conversation_id=str(conversation.id),
                count=10,
            )

            # Build prompt and stream
            prompt = chat_workflow._build_response_prompt(
                message,
                context,
                history,
                persona,
                scenario,
            )

            full_text = ""
            try:
                async for token in gemini_client.generate_text_stream(
                    prompt=prompt,
                    temperature=0.7,
                    max_tokens=2048,
                ):
                    full_text += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            except Exception as e:
                logger.error(f"Streaming from Gemini failed: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': 'Streaming failed'})}\n\n"
                return

            # Classify intent with extended categories
            intent = "question"
            try:
                classification_prompt = f"""Classify the user's intent from this message. Return ONLY a JSON object.

User message: "{message}"

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
                classification_resp = await gemini_client.generate_text(
                    prompt=classification_prompt,
                    temperature=0.1,
                )
                classification = chat_workflow._parse_json_response(classification_resp)
                intent = classification.get("intent", "question")
            except Exception as e:
                logger.warning(f"Intent classification failed, defaulting to 'question': {e}")
                intent = "question"

            # Suggested actions
            suggested_actions: List[dict] = []
            if intent == "cost_estimate":
                suggested_actions.append({
                    "action": "get_detailed_estimate",
                    "label": "Get Detailed Cost Estimate",
                    "description": "Get a comprehensive cost breakdown for your project",
                    "agent": "cost_estimation",
                })
            elif intent == "product_recommendation":
                suggested_actions.append({
                    "action": "find_products",
                    "label": "Find Matching Products",
                    "description": "Search for products that fit your space and style",
                    "agent": "product_matching",
                })
            elif intent == "design_idea":
                suggested_actions.append({
                    "action": "generate_design",
                    "label": "Generate Design Mockup",
                    "description": "Create AI-generated design visualizations",
                    "agent": "design_studio",
                })
            elif intent == "design_transformation":
                suggested_actions.append({
                    "action": "open_design_studio",
                    "label": "Open Design Studio for Transformation",
                    "description": "Apply paint/flooring/cabinets/furniture/staging to your photo",
                    "agent": "design_studio",
                })
            elif intent == "diy_guide":
                suggested_actions.append({
                    "action": "generate_diy_guide",
                    "label": "Generate DIY Step-by-Step Plan",
                    "description": "Create a structured DIY plan with tools, materials, and safety",
                    "agent": "diy_planner",
                })
            elif intent == "pdf_request":
                suggested_actions.append({
                    "action": "export_pdf",
                    "label": "Export as PDF",
                    "description": "Generate a PDF document you can download",
                    "agent": "pdf_export",
                })

            if persona == "homeowner" or scenario == "contractor_quotes":
                suggested_actions.append({
                    "action": "start_contractor_quotes",
                    "label": "Get Contractor Quotes",
                    "description": "Prepare a brief and collect bids from contractors",
                    "agent": "contractor_quotes",
                })
            if persona == "diy_worker" or scenario == "diy_project_plan":
                suggested_actions.append({
                    "action": "create_diy_plan",
                    "label": "Create My DIY Project Plan",
                    "description": "Get a step-by-step plan with tools and materials",
                    "agent": "diy_planner",
                })
                suggested_actions.append({
                    "action": "export_pdf",
                    "label": "Export DIY Guide as PDF",
                    "description": "Create a printable guide with images",
                    "agent": "pdf_export",
                })


            # Suggested follow-up questions
            suggested_questions: List[str] = []
            if intent == "cost_estimate":
                suggested_questions.extend([
                    "What are the room dimensions (L x W x H)?",
                    "Include labor or materials only?",
                    "What material quality/tier and budget range?",
                    "What is your location (for Canada pricing)?",
                ])
            elif intent == "product_recommendation":
                suggested_questions.extend([
                    "Which room and its dimensions?",
                    "What budget range and style preference?",
                    "Any must-have materials or brands (.ca vendors preferred)?",
                    "Do you need eco-friendly or low-VOC options?",
                ])
            elif intent == "design_idea":
                suggested_questions.extend([
                    "Which room photo should I reference?",
                    "What styles or color palettes do you like?",
                    "Any elements to keep (flooring, cabinets, furniture)?",
                ])
            elif intent == "design_transformation":
                suggested_questions.extend([
                    "Which attached photo should I use?",
                    "What exact edits (paint color, flooring type, cabinets)?",
                    "Should I preserve existing furniture and layout?",
                ])
            elif intent == "diy_guide":
                suggested_questions.extend([
                    "What is your skill level and available time?",
                    "Do you already have any of the required tools?",
                    "What is your budget and deadline?",
                ])
            elif intent == "pdf_request":
                suggested_questions.extend([
                    "Include images and a materials checklist?",
                    "What title should I use for the PDF?",
                    "Do you want a Canadian vendor list appended?",
                ])
            if not suggested_questions:
                suggested_questions.extend([
                    "Which room or area are we focusing on?",
                    "What are the dimensions and current materials?",
                    "What is your budget and timeline?",
                    "Do you prefer DIY plan or contractor quotes?",
                ])


	            # Context-aware refinement of follow-up questions based on conversation history
	            try:
	                history_lines = []
	                for msg in (history or [])[-6:]:
	                    role = "User" if msg.get("role") == "user" else "Assistant"
	                    content = (msg.get("content") or "")[:400]
	                    history_lines.append(f"{role}: {content}")
	                history_text = "\n".join(history_lines)
	                gen_prompt = f"""Given the conversation and latest message, propose 3-4 short follow-up questions that move the user forward.
They must be context-aware, <= 80 characters each, and easy to tap as chips.
Return ONLY a JSON array of strings.

Conversation (most recent first):
{history_text}

Latest message: {message}
Intent: {intent}
Persona: {persona or ""}
Scenario: {scenario or ""}
"""
	                resp = await gemini_client.generate_text(
	                    prompt=gen_prompt,
	                    temperature=0.2,
	                    max_tokens=200,
	                )
	                import json, re
	                m = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', resp, re.DOTALL)
	                arr_text = m.group(1) if m else resp.strip()
	                arr = json.loads(arr_text)
	                if isinstance(arr, list):
	                    cleaned: List[str] = []
	                    for q in arr:
	                        if isinstance(q, str):
	                            q = q.strip()
	                            if q and len(q) <= 100 and q not in cleaned:
	                                cleaned.append(q)
	                    if cleaned:
	                        merged: List[str] = []
	                        for q in cleaned + suggested_questions:
	                            if q not in merged:
	                                merged.append(q)
	                        suggested_questions = merged[:4]
	            except Exception as _fe:
	                logger.debug(f"Contextual follow-up generation skipped: {_fe}")

            # Save assistant message
            await conversation_service.add_message(
                conversation_id=str(conversation.id),
                role="assistant",
                content=full_text,
                metadata={
                    "intent": intent,
                    "suggested_actions": suggested_actions,
                    "suggested_questions": suggested_questions,
                    "persona": persona,
                    "scenario": scenario,
                    "model": "gemini-2.5-flash",
                    "generated_at": datetime.utcnow().isoformat(),
                },
                context_sources=context_sources,
            )

            yield f"data: {json.dumps({'type': 'complete', 'message': {'conversation_id': str(conversation.id)}})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream chat (multipart) error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
