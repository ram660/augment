"""
Chat Workflow API (LEGACY) - Multimodal chat interface for home improvement assistance.

IMPORTANT: This router exposes the older ChatOrchestrator-based chat API
under `/api/v1/chat/orchestrator/*` and is considered legacy. The
canonical chat API is implemented in `backend/api/chat.py` and exposed at
`/api/v1/chat/message`, which uses the LangGraph-based ChatWorkflow.

Endpoints:
- POST /api/v1/chat/orchestrator/message - Send message and get multimodal response (ChatOrchestrator)
- GET /api/v1/chat/conversations - List user conversations
- GET /api/v1/chat/conversations/{id} - Get conversation history
- POST /api/v1/chat/generate-visual - Generate images/videos on demand
- GET /api/v1/chat/workflow-status/{id} - Get renovation workflow progress
"""

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Body
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


# Request/Response Models

class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message."""
    message: str = Field(..., description="User's message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID (auto-generated if not provided)")
    user_id: Optional[str] = Field(None, description="User ID")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ChatMessageResponse(BaseModel):
    """Response model for chat message."""
    success: bool
    message_id: str
    conversation_id: str
    intent: str
    response: Dict[str, Any]
    metadata: Dict[str, Any]


class VisualGenerationRequest(BaseModel):
    """Request model for generating visuals."""
    prompt: str = Field(..., description="Generation prompt")
    conversation_id: str = Field(..., description="Conversation ID")
    type: str = Field("image", description="Type: 'image' or 'video'")
    num_variations: int = Field(3, description="Number of variations to generate")


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history."""
    success: bool
    conversation_id: str
    messages: list
    total_messages: int


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    success: bool
    conversation_id: str
    workflow: Dict[str, Any]


# API Endpoints

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify router is working."""
    return {"status": "ok", "message": "Chat workflow router is working!"}

@router.post("/orchestrator/message")
async def send_chat_message(
    request: Request,
    request_data: ChatMessageRequest
) -> Dict[str, Any]:
    """
    Send a chat message and receive multimodal response.

    The AI will analyze your message and respond with:
    - Text explanation
    - Relevant images (if applicable)
    - Tutorial videos (if applicable)
    - Product recommendations (if applicable)
    - Interactive elements
    """
    try:
        logger.info(f"Received chat message: {request_data.message}")

        # Get chat orchestrator from app state
        chat_orchestrator = request.app.state.chat_orchestrator

        # Generate conversation ID if not provided
        conversation_id = request_data.conversation_id or str(uuid.uuid4())

        # Process message
        response = await chat_orchestrator.process_message(
            message=request_data.message,
            conversation_id=conversation_id,
            user_id=request_data.user_id,
            context=request_data.context
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: str,
    request: Request,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get conversation history.
    
    Returns the last N messages from the conversation.
    """
    try:
        chat_orchestrator = request.app.state.chat_orchestrator
        
        history = chat_orchestrator.get_conversation_history(
            conversation_id=conversation_id,
            limit=limit
        )
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "messages": history,
            "total_messages": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-visual")
async def generate_visual(
    request_data: VisualGenerationRequest,
    request: Request
) -> Dict[str, Any]:
    """
    Generate images or videos on demand.
    
    Use this to generate additional design variations or visual content
    during a conversation.
    """
    try:
        gemini_client = request.app.state.gemini_client
        
        if request_data.type == "image":
            # Generate images
            images = []
            for i in range(request_data.num_variations):
                generated_images = await gemini_client.generate_image(
                    prompt=f"{request_data.prompt} - Variation {i+1}",
                    aspect_ratio="16:9",
                    num_images=1
                )
                
                if generated_images:
                    import os
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"visual_{timestamp}_{i}.png"
                    filepath = os.path.join("uploads", "chat", filename)
                    
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    generated_images[0].save(filepath)
                    
                    images.append({
                        "url": f"/uploads/chat/{filename}",
                        "caption": f"Variation {i+1}",
                        "type": "generated"
                    })
            
            return {
                "success": True,
                "type": "image",
                "images": images,
                "conversation_id": request_data.conversation_id
            }
        
        else:
            return {
                "success": False,
                "error": "Video generation not yet implemented"
            }
        
    except Exception as e:
        logger.error(f"Error generating visual: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow-status/{conversation_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    conversation_id: str,
    request: Request
) -> Dict[str, Any]:
    """
    Get renovation workflow status for a conversation.
    
    Returns current stage, progress, and next steps.
    """
    try:
        chat_orchestrator = request.app.state.chat_orchestrator
        
        workflow = chat_orchestrator.get_workflow_status(conversation_id)
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "workflow": workflow
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

