"""
Chat API endpoints for HomeView AI.

Provides conversational AI interface with context-aware responses.
"""

import logging
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from backend.api.auth import get_current_user
from backend.models.user import User
from backend.models.conversation import Conversation, ConversationMessage
from backend.models.base import get_async_db
from backend.workflows.chat_workflow import ChatWorkflow
from backend.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatMessageRequest(BaseModel):
    """Chat message request."""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None
    home_id: Optional[str] = None
    context: Optional[dict] = {}


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
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationHistoryResponse(BaseModel):
    """Conversation history response."""
    conversation_id: str
    messages: List[dict]
    total_messages: int


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
        chat_workflow = ChatWorkflow()
        
        # Get or create conversation
        if request.conversation_id:
            conversation = await conversation_service.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            if conversation.user_id != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this conversation"
                )
        else:
            # Create new conversation
            conversation = await conversation_service.create_conversation(
                user_id=str(current_user.id),
                home_id=request.home_id,
                title="New Conversation"  # Will be auto-generated from first message
            )
        
        # Execute chat workflow
        workflow_input = {
            "user_message": request.message,
            "conversation_id": str(conversation.id),
            "user_id": str(current_user.id),
            "home_id": request.home_id or "",
            "context": request.context or {}
        }
        
        result = await chat_workflow.execute(workflow_input)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Chat workflow failed")
            )
        
        # Save messages to database
        user_message = await conversation_service.add_message(
            conversation_id=str(conversation.id),
            role="user",
            content=request.message,
            metadata={"intent": result.get("intent", "unknown")}
        )
        
        assistant_message = await conversation_service.add_message(
            conversation_id=str(conversation.id),
            role="assistant",
            content=result.get("response", ""),
            metadata={
                "intent": result.get("intent", "unknown"),
                "suggested_actions": result.get("suggested_actions", [])
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
            response=result.get("response", ""),
            intent=result.get("intent", "unknown"),
            suggested_actions=result.get("suggested_actions", []),
            metadata=result.get("metadata", {})
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat message error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
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
        
        if conversation.user_id != str(current_user.id):
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
        
        # Get conversation
        conversation = await conversation_service.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        if conversation.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
            )
        
        # Delete conversation
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

