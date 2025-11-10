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

from backend.api.auth import get_current_user, get_current_user_optional
from backend.models.user import User
from backend.models.conversation import Conversation, ConversationMessage
from backend.models.message_feedback import MessageFeedback
from backend.models.base import get_async_db
from backend.workflows.chat_workflow import ChatWorkflow
from backend.services.conversation_service import ConversationService
from backend.services.rag_service import RAGService
from backend.integrations.gemini.client import GeminiClient
from backend.services.document_parser_service import DocumentParserService, DocumentParseError
from backend.integrations.agentlightning.rewards import RewardCalculator, FeedbackType
from backend.integrations.agentlightning.tracker import AgentTracker

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
    mode: Optional[str] = 'agent'  # 'chat' | 'agent' - controls multimodal features


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


class ExecuteActionRequest(BaseModel):
    """Execute a suggested action within a conversation."""
    conversation_id: str
    action: dict
    context: Optional[dict] = None  # e.g., { room_id, renovation_scope, category, budget_min, budget_max, style_preference }
    persona: Optional[str] = None
    scenario: Optional[str] = None


class ExecuteActionResponse(BaseModel):
    conversation_id: str
    message_id: str
    status: str
    metadata: dict = {}


@router.post("/execute-action", response_model=ExecuteActionResponse)
async def execute_action(
    request: ExecuteActionRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Execute a suggested action (e.g., cost estimate, product match) and append the result
    as an assistant message with structured metadata.
    """
    try:
        conversation_service = ConversationService(db)
        conversation = await conversation_service.get_conversation(request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        # Ownership: if conversation is tied to a user, require that user; anonymous conversations are open
        if conversation.user_id:
            if not current_user or conversation.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation")

        action_type = (request.action or {}).get("action") or (request.action or {}).get("type") or ""
        ctx = request.context or {}

        # Helper to ask for missing info
        async def _ask_for(*fields: str, intent: Optional[str] = None, note: Optional[str] = None) -> ExecuteActionResponse:
            """Politely ask the user for missing details with context-aware chips."""
            missing = ", ".join(fields)

            # Friendlier, intent-aware copy
            if intent == "pdf_request" and "plan_to_export" in fields:
                content = (
                    "I can export a polished PDF for you. I don’t see a DIY plan yet — "
                    "would you like me to create one now and then export it?"
                )
                suggested_actions = [
                    {"action": "create_diy_plan", "label": "Create DIY Plan", "agent": "diy_planner"},
                    {"action": "export_pdf", "label": "Export as PDF", "agent": "pdf_export"},
                ]
                suggested_questions = [
                    "Include images and a materials checklist?",
                    "What title should I use for the PDF?",
                ]
            elif intent == "cost_estimate" and "room_id" in fields:
                content = (
                    "I can get you a detailed estimate. Which room should I use? "
                    "You can pick from your Digital Twin or tell me the room name and dimensions "
                    "(e.g., 12x15 kitchen, 8 ft ceiling)."
                )
                suggested_actions = [
                    {"action": "get_detailed_estimate", "label": "Run Detailed Estimate", "agent": "cost_estimation"},
                ]
                suggested_questions = [
                    "Which room or area are we focusing on?",
                    "What are the dimensions (L x W x H)?",
                ]
            else:
                content = (
                    "Happy to run that. To proceed, I just need: "
                    f"{missing}. Share those details in a quick message."
                )
                suggested_actions = []
                suggested_questions = ["Can you share the missing detail(s)?"]

            if note:
                content += f"\n\n{note}"

            msg = await conversation_service.add_message(
                conversation_id=str(conversation.id),
                role="assistant",
                content=content,
                metadata={
                    "intent": intent or "question",
                    "requested_fields": list(fields),
                    "persona": request.persona,
                    "scenario": request.scenario,
                    "suggested_actions": suggested_actions,
                    "suggested_questions": suggested_questions,
                },
            )
            return ExecuteActionResponse(
                conversation_id=str(conversation.id),
                message_id=str(msg.id),
                status="needs_input",
                metadata={"requested_fields": list(fields)},
            )

        # Route actions
        if action_type == "get_detailed_estimate":
            room_id = ctx.get("room_id") or (ctx.get("room") or {}).get("id")
            if not room_id:
                return await _ask_for(
                    "room_id",
                    intent="cost_estimate",
                    note="Tip: Select a room from your Digital Twin or tell me the room name/dimensions.",
                )

            try:
                from backend.api.intelligence import estimate_renovation_cost, CostEstimateRequest  # local import to avoid cycles
                payload = CostEstimateRequest(
                    room_id=UUID(room_id),
                    renovation_scope=ctx.get("renovation_scope") or "refresh",
                    include_labor=True,
                    include_timeline=True,
                )
                result = await estimate_renovation_cost(payload, db=db)  # type: ignore
                # Compose succinct content
                total = (result.get("cost_estimate") or {}).get("total_range") or {}
                low = total.get("low")
                high = total.get("high")
                scope = result.get("renovation_scope")
                room_name = result.get("room_name")
                summary = f"Cost estimate for {room_name or 'room'} ({scope}): "
                if low is not None and high is not None:
                    summary += f"${low:,} - ${high:,}"
                else:
                    summary += "see breakdown below."

                msg = await conversation_service.add_message(
                    conversation_id=str(conversation.id),
                    role="assistant",
                    content=summary,
                    metadata={
                        "intent": "cost_estimate",
                        "cost_estimates": [result],
                        "persona": request.persona,
                        "scenario": request.scenario,
                    },
                )
                return ExecuteActionResponse(
                    conversation_id=str(conversation.id),
                    message_id=str(msg.id),
                    status="ok",
                    metadata={"intent": "cost_estimate"},
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"execute_action cost_estimate failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to run cost estimate")

        elif action_type == "find_products":
            room_id = ctx.get("room_id") or (ctx.get("room") or {}).get("id")
            if not room_id:
                return await _ask_for(
                    "room_id",
                    intent="product_recommendation",
                    note="Optionally include budget_min/budget_max and style_preference.",
                )
            try:
                from backend.api.product import match_products_to_room, ProductMatchRequest  # local import
                payload = ProductMatchRequest(
                    room_id=str(room_id),
                    category=ctx.get("category"),
                    budget_min=ctx.get("budget_min"),
                    budget_max=ctx.get("budget_max"),
                    style_preference=ctx.get("style_preference"),
                )
                results = await match_products_to_room(payload, current_user=current_user, db=db)  # type: ignore
                count = len(results or [])
                content = f"Found {count} matching products for your room. Here are the top results."
                msg = await conversation_service.add_message(
                    conversation_id=str(conversation.id),
                    role="assistant",
                    content=content,
                    metadata={
                        "intent": "product_recommendation",
                        "products": [r.dict() if hasattr(r, 'dict') else r for r in results],
                        "persona": request.persona,
                        "scenario": request.scenario,
                    },
                )
                return ExecuteActionResponse(
                    conversation_id=str(conversation.id),
                    message_id=str(msg.id),
                    status="ok",
                    metadata={"intent": "product_recommendation"},
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"execute_action product_match failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to match products")

        elif action_type == "generate_diy_guide":
            # Need room and project scope to create a tailored DIY plan
            room_id = ctx.get("room_id") or (ctx.get("room") or {}).get("id")
            project_scope = ctx.get("project_scope") or ctx.get("scope")
            if not room_id or not project_scope:
                missing = []
                if not room_id:
                    missing.append("room_id")
                if not project_scope:
                    missing.append("project_scope")
                return await _ask_for(
                    *missing,
                    intent="diy_guide",
                    note="Tell me the room and what you want to accomplish (e.g., 'paint walls + trim').",
                )

            try:
                # Load room context
                from backend.api.intelligence import load_room_data  # local import
                room_data = await load_room_data(UUID(room_id), db)

                # Build concise structured-output prompt for Gemini
                scope_text = str(project_scope)
                persona = request.persona or "homeowner"
                scenario = request.scenario or "diy_project_plan"

                # Include skill context if available (non-fatal on import error)
                skill_context = ""
                try:
                    from backend.services.skill_manager import SkillManager
                    sm = SkillManager()
                    skill_context = sm.get_context("diy_guide", persona, scenario, scope_text)
                except Exception:
                    pass

                schema_text = (
                    "Return ONLY valid JSON with this schema exactly: {\n"
                    "  \"title\": string,\n"
                    "  \"room\": { \"name\": string, \"type\": string|null, \"dimensions\": { \"length\": number|null, \"width\": number|null, \"height\": number|null, \"area\": number|null } },\n"
                    "  \"scope\": string,\n"
                    "  \"duration_days\": number,\n"
                    "  \"difficulty\": \"easy\"|\"moderate\"|\"hard\",\n"
                    "  \"tools\": [string],\n"
                    "  \"materials\": [string],\n"
                    "  \"steps\": [ { \"step\": number, \"title\": string, \"details\": string, \"safety\": [string], \"estimated_hours\": number } ],\n"
                    "  \"safety_tips\": [string],\n"
                    "  \"prep_checklist\": [string]\n"
                    "}."
                )

                prompt = (
                    "You are HomeView AI. Create a concise, realistic DIY step-by-step plan for the specified project, "
                    "tailored to this room (Canada context, DIY safety first). Keep it pragmatic and use CAD units when relevant.\n\n"
                    f"ROOM DATA (JSON):\n{room_data}\n\n"
                    f"PROJECT SCOPE: {scope_text}\n\n"
                    f"{skill_context}\n"
                    "Constraints:\n"
                    "- Keep plan achievable by a careful DIYer; include safety notes.\n"
                    "- Prefer Canadian codes and terminology.\n"
                    "- Limit steps to 6-10, each with short 'details' and 'safety'.\n"
                    "- Keep tools/materials concise.\n\n"
                    f"{schema_text}"
                )

                # Use existing Gemini client wrapper
                from backend.integrations.gemini.client import GeminiClient
                g = GeminiClient()
                text = await g.generate_text(prompt, temperature=0.3, max_tokens=1200)

                # Best-effort JSON parse
                import json, re
                plan: dict = {}
                try:
                    m = re.search(r"\{[\s\S]*\}", text)
                    if m:
                        plan = json.loads(m.group(0))
                except Exception:
                    plan = {}

                # Compose assistant message
                title = (plan.get("title") if isinstance(plan, dict) else None) or "DIY Plan"
                duration = plan.get("duration_days") if isinstance(plan, dict) else None
                difficulty = plan.get("difficulty") if isinstance(plan, dict) else None
                badges = []
                if isinstance(duration, (int, float)):
                    badges.append(f"~{int(duration)} day(s)")
                if isinstance(difficulty, str):
                    badges.append(difficulty.title())
                summary = f"{title}"
                if badges:
                    summary += " (" + ", ".join(badges) + ")"

                msg = await conversation_service.add_message(
                    conversation_id=str(conversation.id),
                    role="assistant",
                    content=summary,
                    metadata={
                        "intent": "diy_guide",
                        "diy_plan": plan if isinstance(plan, dict) else {},
                        "raw": text,
                        "persona": request.persona,
                        "scenario": request.scenario,
                        "suggested_actions": [
                            {
                                "action": "refine_diy_plan",
                                "label": "Refine Plan",
                                "description": "Adjust difficulty/time or add constraints",
                                "agent": "diy_planner",
                            },
                            {
                                "action": "make_shopping_list",
                                "label": "Make Shopping List",
                                "description": "Consolidate tools and materials into a checklist",
                                "agent": "diy_planner",
                            },
                            {
                                "action": "export_pdf",
                                "label": "Export as PDF",
                                "description": "Download a printable guide",
                                "agent": "pdf_export",
                            },
                        ],
                    },
                )
                return ExecuteActionResponse(
                    conversation_id=str(conversation.id),
                    message_id=str(msg.id),
                    status="ok",
                    metadata={"intent": "diy_guide"},
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"execute_action diy_guide failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to generate DIY guide")

        elif action_type == "refine_diy_plan":
            # Refine the most recent DIY plan using additional constraints
            try:
                # Locate the latest DIY plan in the conversation
                prev_messages = await conversation_service.get_messages(str(conversation.id), limit=100)
                base_plan = None
                for m in reversed(prev_messages):
                    try:
                        md = getattr(m, "message_metadata", None) or {}
                        if isinstance(md, dict) and md.get("diy_plan"):
                            base_plan = md.get("diy_plan")
                            break
                    except Exception:
                        continue

                if not base_plan:
                    return await _ask_for(
                        "diy_plan",
                        intent="diy_guide",
                        note="I couldn't find an existing plan to refine. Please generate a DIY plan first.",
                    )

                # Build refinement notes from context
                constraints: list[str] = []
                difficulty = ctx.get("difficulty")
                if difficulty:
                    constraints.append(f"Target difficulty: {difficulty}")
                duration_days = ctx.get("duration_days")
                if isinstance(duration_days, (int, float)):
                    constraints.append(f"Total duration_days: {int(duration_days)}")
                budget_min = ctx.get("budget_min")
                budget_max = ctx.get("budget_max")
                if budget_min or budget_max:
                    constraints.append(f"Budget range (CAD): {budget_min or 'n/a'} - {budget_max or 'n/a'}")
                focus = ctx.get("focus")
                if focus:
                    constraints.append(f"Focus areas: {focus}")
                finish_level = ctx.get("finish_level")
                if finish_level:
                    constraints.append(f"Finish level: {finish_level}")
                brands = ctx.get("brands")
                if brands:
                    constraints.append(f"Preferred brands: {brands}")
                more_detail = ctx.get("more_detail")
                if more_detail:
                    constraints.append("Increase detail level for steps where helpful")

                constraints_text = "\n".join(f"- {c}" for c in constraints) or "- Improve clarity and add pragmatic tips"

                # Skill context (best-effort)
                skill_context = ""
                try:
                    from backend.services.skill_manager import SkillManager
                    sm = SkillManager()
                    skill_context = sm.get_context("diy_guide", request.persona or "homeowner", request.scenario or "diy_project_plan", str(constraints_text))
                except Exception:
                    pass

                schema_text = (
                    "Return ONLY valid JSON with this schema exactly: {\n"
                    "  \"title\": string,\n"
                    "  \"room\": { \"name\": string, \"type\": string|null, \"dimensions\": { \"length\": number|null, \"width\": number|null, \"height\": number|null, \"area\": number|null } },\n"
                    "  \"scope\": string,\n"
                    "  \"duration_days\": number,\n"
                    "  \"difficulty\": \"easy\"|\"moderate\"|\"hard\",\n"
                    "  \"tools\": [string],\n"
                    "  \"materials\": [string],\n"
                    "  \"steps\": [ { \"step\": number, \"title\": string, \"details\": string, \"safety\": [string], \"estimated_hours\": number } ],\n"
                    "  \"safety_tips\": [string],\n"
                    "  \"prep_checklist\": [string]\n"
                    "}."
                )

                prompt = (
                    "You are HomeView AI. Refine the following DIY plan while preserving its structure and Canadian context.\n\n"
                    f"CURRENT PLAN (JSON):\n{base_plan}\n\n"
                    f"REFINEMENTS:\n{constraints_text}\n\n"
                    f"{skill_context}\n"
                    "Constraints:\n"
                    "- Keep steps succinct (6-10).\n"
                    "- Ensure safety notes are clear and specific.\n"
                    "- Use CAD units and Canada terminology where relevant.\n\n"
                    f"{schema_text}"
                )

                from backend.integrations.gemini.client import GeminiClient
                g = GeminiClient()
                text = await g.generate_text(prompt, temperature=0.3, max_tokens=1100)

                import json, re
                new_plan: dict = {}
                try:
                    m = re.search(r"\{[\s\S]*\}", text)
                    if m:
                        new_plan = json.loads(m.group(0))
                except Exception:
                    new_plan = {}

                title = (new_plan.get("title") if isinstance(new_plan, dict) else None) or "DIY Plan (Refined)"
                duration = new_plan.get("duration_days") if isinstance(new_plan, dict) else None
                difficulty_out = new_plan.get("difficulty") if isinstance(new_plan, dict) else None
                badges = []
                if isinstance(duration, (int, float)):
                    badges.append(f"~{int(duration)} day(s)")
                if isinstance(difficulty_out, str):
                    badges.append(difficulty_out.title())
                summary = f"{title}"
                if badges:
                    summary += " (" + ", ".join(badges) + ")"

                msg = await conversation_service.add_message(
                    conversation_id=str(conversation.id),
                    role="assistant",
                    content=summary,
                    metadata={
                        "intent": "diy_guide",
                        "diy_plan": new_plan if isinstance(new_plan, dict) else {},
                        "raw": text,
                        "persona": request.persona,
                        "scenario": request.scenario,
                        "suggested_actions": [
                            {
                                "action": "refine_diy_plan",
                                "label": "Refine Again",
                                "description": "Adjust plan constraints further",
                                "agent": "diy_planner",
                            },
                            {
                                "action": "make_shopping_list",
                                "label": "Make Shopping List",
                                "description": "Consolidate tools and materials into a checklist",
                                "agent": "diy_planner",
                            },
                            {
                                "action": "export_pdf",
                                "label": "Export as PDF",
                                "description": "Download a printable guide",
                                "agent": "pdf_export",
                            },
                        ],
                    },
                )
                return ExecuteActionResponse(
                    conversation_id=str(conversation.id),
                    message_id=str(msg.id),
                    status="ok",
                    metadata={"intent": "diy_guide"},
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"execute_action refine_diy_plan failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to refine DIY guide")

        elif action_type in ("generate_design", "open_design_studio"):
            # Open Design Studio with a selected image if provided; otherwise ask for one
            image_url = ctx.get("image_to_edit") or ctx.get("image_url") or ((ctx.get("image") or {}).get("url") if isinstance(ctx.get("image"), dict) else None)
            image_id = ctx.get("image_id") or ((ctx.get("image") or {}).get("id") if isinstance(ctx.get("image"), dict) else None)
            if not image_url and not image_id:
                return await _ask_for(
                    "image_to_edit",
                    intent="design_transformation",
                    note="Choose a room photo from your media to open the Design Studio.",
                )

            try:
                from urllib.parse import quote
                route = "/dashboard/design"
                query = f"?image={image_id}" if image_id else (f"?image_url={quote(str(image_url))}" if image_url else "")
                navigate_to = f"{route}{query}"

                msg = await conversation_service.add_message(
                    conversation_id=str(conversation.id),
                    role="assistant",
                    content="Opening Design Studio with your selected image...",
                    metadata={
                        "intent": "design_transformation",
                        "navigate_to": navigate_to,
                        "image_id": image_id,
                        "image_url": image_url,
                        "persona": request.persona,
                        "scenario": request.scenario,
                    },
                )
                return ExecuteActionResponse(
                    conversation_id=str(conversation.id),
                    message_id=str(msg.id),
                    status="ok",
                    metadata={"navigate_to": navigate_to},
                )
            except Exception as e:
                logger.error(f"execute_action open_design_studio failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to open Design Studio")

        elif action_type == "export_pdf":
            # Export the most recent DIY plan to a PDF and return a downloadable link
            try:
                prev_messages = await conversation_service.get_messages(str(conversation.id), limit=100)
                diy_plan = None
                for m in reversed(prev_messages):
                    try:
                        md = getattr(m, "message_metadata", None) or {}
                        if isinstance(md, dict) and md.get("diy_plan"):
                            diy_plan = md.get("diy_plan")
                            break
                    except Exception:
                        continue

                if not diy_plan:
                    return await _ask_for(
                        "plan_to_export",
                        intent="pdf_request",
                        note="I don't see a DIY plan to export yet. Generate one first, then export.",
                    )

                # Map DIY plan schema to PDF export schema
                from backend.services.pdf_export_service import export_guide_to_pdf, PDFExportError
                import os

                def _as_name_list(items: list) -> list:
                    out = []
                    for x in items or []:
                        if isinstance(x, str):
                            out.append({"name": x})
                        elif isinstance(x, dict):
                            name = x.get("name") or x.get("title") or str(x)
                            entry = {"name": name}
                            if x.get("quantity"):
                                entry["quantity"] = x.get("quantity")
                            if x.get("notes"):
                                entry["notes"] = x.get("notes")
                            out.append(entry)
                    return out

                steps_src = diy_plan.get("steps") or []
                steps_mapped = []
                for s in steps_src:
                    if not isinstance(s, dict):
                        continue
                    title = s.get("title") or (isinstance(s.get("step"), int) and f"Step {s.get('step')}") or "Step"
                    instr = s.get("details") or s.get("title") or ""
                    mins = None
                    try:
                        hrs = s.get("estimated_hours")
                        if isinstance(hrs, (int, float)):
                            mins = int(max(0, hrs) * 60)
                    except Exception:
                        mins = None
                    steps_mapped.append({
                        "title": title,
                        "instructions": instr,
                        "duration_estimate_minutes": mins,
                    })

                room_type = None
                try:
                    room_type = (diy_plan.get("room") or {}).get("type")
                except Exception:
                    room_type = None

                est_hours = None
                try:
                    dd = diy_plan.get("duration_days")
                    if isinstance(dd, (int, float)):
                        est_hours = int(dd * 8)
                except Exception:
                    est_hours = None

                pdf_guide = {
                    "title": diy_plan.get("title") or "DIY Project Plan",
                    "summary": diy_plan.get("scope") or "",
                    "room_type": room_type,
                    "skill_level": diy_plan.get("difficulty"),
                    "estimated_time_hours": est_hours,
                    "materials": _as_name_list(diy_plan.get("materials") or []),
                    "tools": _as_name_list(diy_plan.get("tools") or []),
                    "steps": steps_mapped,
                    "safety_tips": diy_plan.get("safety_tips") or [],
                }

                pdf_rel = export_guide_to_pdf(pdf_guide, image_paths=None, output_dir="uploads/pdfs")
                pdf_url = f"/{pdf_rel}"
                filename = os.path.basename(pdf_rel)

                msg = await conversation_service.add_message(
                    conversation_id=str(conversation.id),
                    role="assistant",
                    content=f"Your DIY guide PDF is ready: {pdf_url}",
                    metadata={
                        "intent": "pdf_request",
                        "attachments": [
                            {
                                "type": "pdf",
                                "url": pdf_url,
                                "filename": filename,
                                "content_type": "application/pdf",
                            }
                        ],
                        "persona": request.persona,
                        "scenario": request.scenario,
                    },
                )
                return ExecuteActionResponse(
                    conversation_id=str(conversation.id),
                    message_id=str(msg.id),
                    status="ok",
                    metadata={"pdf_url": pdf_url},
                )
            except PDFExportError as e:
                logger.warning(f"PDF export dependency missing or failed: {e}")
                # Send a helpful message without failing the whole action
                msg = await conversation_service.add_message(
                    conversation_id=str(conversation.id),
                    role="assistant",
                    content=str(e),
                    metadata={"intent": "pdf_request"},
                )
                return ExecuteActionResponse(
                    conversation_id=str(conversation.id),
                    message_id=str(msg.id),
                    status="error",
                    metadata={"error": "pdf_export_unavailable"},
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"execute_action export_pdf failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to export PDF")

        elif action_type == "make_shopping_list":
            # Consolidate tools and materials from the most recent DIY plan into a checklist
            try:
                prev_messages = await conversation_service.get_messages(str(conversation.id), limit=100)
                diy_plan = None
                for m in reversed(prev_messages):
                    try:
                        md = getattr(m, "message_metadata", None) or {}
                        if isinstance(md, dict) and md.get("diy_plan"):
                            diy_plan = md.get("diy_plan")
                            break
                    except Exception:
                        continue

                if not diy_plan:
                    return await _ask_for(
                        "diy_plan",
                        intent="shopping_list",
                        note="Generate a DIY plan first so I can build your shopping list.",
                    )

                materials_src = diy_plan.get("materials") or []
                tools_src = diy_plan.get("tools") or []

                def _name_from(item) -> str:
                    if isinstance(item, str):
                        return item
                    if isinstance(item, dict):
                        return item.get("name") or item.get("title") or str(item)
                    return str(item)

                def _norm(key: str) -> str:
                    return (key or "").strip().lower()

                def _merge(items: list, is_tool: bool = False) -> list:
                    agg: dict[str, dict] = {}
                    for it in items or []:
                        name = _name_from(it)
                        if not name:
                            continue
                        k = _norm(name)
                        entry = agg.get(k) or {"name": name}
                        qty_add = 1.0
                        if isinstance(it, dict):
                            q = it.get("quantity")
                            if isinstance(q, (int, float)):
                                qty_add = float(q)
                            notes = it.get("notes")
                            if notes:
                                if entry.get("notes"):
                                    if notes not in entry["notes"]:
                                        entry["notes"] = f"{entry['notes']}; {notes}"
                                else:
                                    entry["notes"] = notes
                            brand = it.get("brand") or it.get("preferred_brand")
                            if brand and not entry.get("preferred_brand"):
                                entry["preferred_brand"] = brand
                            if is_tool and it.get("optional") is True:
                                entry["optional"] = True
                        entry["quantity"] = (entry.get("quantity") or 0) + qty_add
                        agg[k] = entry
                    out = []
                    for v in agg.values():
                        q = v.get("quantity")
                        try:
                            if float(q).is_integer():
                                v["quantity"] = int(q)
                        except Exception:
                            pass
                        out.append(v)
                    out.sort(key=lambda x: (x.get("optional") is True, str(x.get("name") or "").lower()))
                    return out

                materials = _merge(materials_src, is_tool=False)
                tools = _merge(tools_src, is_tool=True)

                content = f"Here’s your consolidated shopping list ({len(materials)} materials, {len(tools)} tools)."
                msg = await conversation_service.add_message(
                    conversation_id=str(conversation.id),
                    role="assistant",
                    content=content,
                    metadata={
                        "intent": "shopping_list",
                        "shopping_list": {"materials": materials, "tools": tools},
                        "persona": request.persona,
                        "scenario": request.scenario,
                        "suggested_actions": [
                            {
                                "action": "find_products",
                                "label": "Find Products For This List",
                                "description": "Find items that match your list and budget",
                                "agent": "product_recommendation",
                            },
                            {
                                "action": "export_pdf",
                                "label": "Export as PDF",
                                "description": "Download a printable version",
                                "agent": "pdf_export",
                            },
                        ],
                    },
                )
                return ExecuteActionResponse(
                    conversation_id=str(conversation.id),
                    message_id=str(msg.id),
                    status="ok",
                    metadata={"intent": "shopping_list"},
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"execute_action make_shopping_list failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to build shopping list")
        elif action_type in ("start_contractor_quotes", "create_diy_plan"):
            # Simple guidance for now
            content = {
                "start_contractor_quotes": "I'll help you prepare a brief. What room and scope should contractors quote on?",
                "create_diy_plan": "Great! What room and scope should I plan for?",
            }.get(action_type, "Let’s proceed. Tell me more details.")
            msg = await conversation_service.add_message(
                conversation_id=str(conversation.id),
                role="assistant",
                content=content,
                metadata={
                    "intent": "question",
                    "persona": request.persona,
                    "scenario": request.scenario,
                },
            )
            return ExecuteActionResponse(
                conversation_id=str(conversation.id),
                message_id=str(msg.id),
                status="ok",
                metadata={},
            )

        else:
            # Unknown action -> ask the model in the normal chat flow next time
            msg = await conversation_service.add_message(
                conversation_id=str(conversation.id),
                role="assistant",
                content=f"Action '{action_type or 'unknown'}' is not recognized yet. Tell me what you want to do.",
                metadata={"intent": "question"},
            )
            return ExecuteActionResponse(
                conversation_id=str(conversation.id),
                message_id=str(msg.id),
                status="unknown_action",
                metadata={"action": action_type},
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute action error: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute action")


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
            "mode": request.mode or "agent",  # Pass chat/agent mode
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

        # Build assistant message metadata with multimodal content
        assistant_metadata = {
            "intent": result.get("intent", "unknown"),
            "suggested_actions": result.get("suggested_actions", []),
            "suggested_questions": result.get("suggested_questions", []),
            "persona": request.persona,
            "scenario": request.scenario,
        }

        # Add multimodal content if present (Agent mode only)
        response_metadata = result.get("response_metadata", {})
        if response_metadata.get("web_search_results"):
            assistant_metadata["web_search_results"] = response_metadata["web_search_results"]
        if response_metadata.get("web_sources"):
            assistant_metadata["web_sources"] = response_metadata["web_sources"]
        if response_metadata.get("youtube_videos"):
            assistant_metadata["youtube_videos"] = response_metadata["youtube_videos"]
        if response_metadata.get("contractors"):
            assistant_metadata["contractors"] = response_metadata["contractors"]
        if response_metadata.get("generated_images"):
            assistant_metadata["generated_images"] = response_metadata["generated_images"]

        assistant_message = await conversation_service.add_message(
            conversation_id=str(conversation.id),
            role="assistant",
            content=ai_response,
            metadata=assistant_metadata
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
            # Lightweight intent guess for skills context during streaming
            _um = (request.message or "").lower()
            _intent_guess = None
            try:
                if any(k in _um for k in ["estimate", "cost", "budget"]):
                    _intent_guess = "cost_estimate"
                elif any(k in _um for k in ["product", "sofa", "appliance", "faucet", "recommend"]):
                    _intent_guess = "product_recommendation"
                elif any(k in _um for k in ["guide", "step-by-step", "how do i"]):
                    _intent_guess = "diy_guide"
                elif any(k in _um for k in ["pdf", "export", "document", "download", "printable", "print"]):
                    _intent_guess = "pdf_request"
                elif any(k in _um for k in ["design", "paint", "flooring", "cabinets", "mockup", "staging"]):
                    _intent_guess = "design_idea"
            except Exception:
                _intent_guess = None

            prompt = chat_workflow._build_response_prompt(
                request.message,
                context,
                history,
                request.persona,
                request.scenario,
                _intent_guess,
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
                logger.warning(f"Intent classification failed, defaulting to 'question': {e}")
                intent = "question"

            # Heuristic nudge based on phrasing in the user's message (post-classification)
            try:
                um = (request.message or "").lower()
                if intent == "question":
                    if any(k in um for k in ["pdf", "export", "document", "download", "printable", "print"]):
                        intent = "pdf_request"
                    elif ("guide" in um or "step-by-step" in um):
                        intent = "diy_guide"
                    elif ("image" in um or "mockup" in um or "visual" in um):
                        intent = "design_idea"
            except Exception:
                pass

            # Initialize suggested questions list (ensure defined)
            suggested_questions: List[str] = []

            # Build suggested actions (mirrors workflow logic)
            suggested_actions: List[dict] = []

            # Helper to avoid repeating the same action in recent messages
            def _has_recent_action(action_key: str, lookback: int = 3) -> bool:
                """Check if action was shown in last N messages (default: 3)."""
                try:
                    recent = history[-lookback:] if len(history) >= lookback else history
                    for msg in reversed(recent):
                        if (msg.get("role") == "assistant"):
                            acts = ((msg.get("metadata") or {}).get("suggested_actions") or [])
                            for a in acts:
                                if (a.get("action") or a.get("type")) == action_key:
                                    return True
                    return False
                except Exception:
                    return False

            # Intent-based actions (universal, not persona-dependent)
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
            elif intent == "diy_guide" and not _has_recent_action("create_diy_plan"):
                # User is asking for DIY guidance - offer DIY plan
                suggested_actions.append({
                    "action": "create_diy_plan",
                    "label": "Create DIY Step-by-Step Plan",
                    "description": "Get a detailed plan with tools, materials, and safety tips",
                    "agent": "diy_planner",
                })
            elif intent == "pdf_request":
                # User wants PDF export
                suggested_actions.append({
                    "action": "export_pdf",
                    "label": "Export as PDF",
                    "description": "Download your plan as a PDF document",
                    "agent": "pdf_export",
                })

            # Universal workflow actions (based on conversation context, not persona)
            # Only suggest these if they haven't been recently offered and are contextually relevant
            s = request.scenario

            # Suggest contractor quotes if scenario is contractor_quotes OR if user hasn't been offered it recently
            if (s == "contractor_quotes" or intent in ["cost_estimate", "question"]) and not _has_recent_action("start_contractor_quotes"):
                # Check if user is asking about hiring/contractors in their message
                um_lower = (request.message or "").lower()
                if any(k in um_lower for k in ["contractor", "hire", "quote", "bid", "professional"]) or s == "contractor_quotes":
                    suggested_actions.append({
                        "action": "start_contractor_quotes",
                        "label": "Get Contractor Quotes",
                        "description": "Prepare a brief and collect bids from contractors",
                        "agent": "contractor_quotes",
                    })

            # Suggest DIY plan if scenario is diy_project_plan OR if user is asking DIY-related questions
            if (s == "diy_project_plan" or intent in ["diy_guide", "question"]) and not _has_recent_action("create_diy_plan"):
                um_lower = (request.message or "").lower()
                if any(k in um_lower for k in ["diy", "myself", "do it myself", "step", "guide", "how to", "how do i"]) or s == "diy_project_plan":
                    suggested_actions.append({
                        "action": "create_diy_plan",
                        "label": "Create My DIY Project Plan",
                        "description": "Get a step-by-step plan with tools and materials",
                        "agent": "diy_planner",
                    })

            # Suggested follow-up questions (context-aware, avoid repetition)
            suggested_questions: List[str] = []

            # Helper to check if a question was recently asked
            def _has_recent_question(q_text: str) -> bool:
                try:
                    recent = history[-6:] if history else []
                    for msg in reversed(recent):
                        if msg.get("role") == "assistant":
                            qs = ((msg.get("metadata") or {}).get("suggested_questions") or [])
                            if q_text in qs:
                                return True
                    return False
                except Exception:
                    return False

            # Build intent-specific questions
            candidate_questions: List[str] = []
            if intent == "cost_estimate":
                candidate_questions.extend([
                    "What are the room dimensions (L x W x H)?",
                    "Include labor or materials only?",
                    "What material quality/tier and budget range?",
                    "What is your location (for Canada pricing)?",
                ])
            elif intent == "product_recommendation":
                candidate_questions.extend([
                    "Which room and its dimensions?",
                    "What budget range and style preference?",
                    "Any must-have materials or brands (.ca vendors preferred)?",
                    "Do you need eco-friendly or low-VOC options?",
                ])
            elif intent == "design_idea":
                candidate_questions.extend([
                    "Which room photo should I reference?",
                    "What styles or color palettes do you like?",
                    "Any elements to keep (flooring, cabinets, furniture)?",
                ])
            elif intent == "design_transformation":
                candidate_questions.extend([
                    "Which attached photo should I use?",
                    "What exact edits (paint color, flooring type, cabinets)?",
                    "Should I preserve existing furniture and layout?",
                ])
            elif intent == "diy_guide":
                candidate_questions.extend([
                    "What is your skill level and available time?",
                    "Do you already have any of the required tools?",
                    "What is your budget and deadline?",
                ])
            elif intent == "pdf_request":
                candidate_questions.extend([
                    "Include images and a materials checklist?",
                    "What title should I use for the PDF?",
                    "Do you want a Canadian vendor list appended?",
                ])

            # Filter out recently asked questions
            for q in candidate_questions:
                if not _has_recent_question(q):
                    suggested_questions.append(q)

            # Fallback only if no questions survived filtering
            if not suggested_questions:
                fallback = [
                    "Which room or area are we focusing on?",
                    "What are the dimensions and current materials?",
                    "What is your budget and timeline?",
                ]
                for q in fallback:
                    if not _has_recent_question(q):
                        suggested_questions.append(q)


            # Limit suggestions to avoid clutter (max 3 actions, max 4 questions)
            suggested_actions = suggested_actions[:3]
            suggested_questions = suggested_questions[:4]

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
    current_user: Optional[User] = Depends(get_current_user_optional),
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

        # Ownership: if conversation is tied to a user, require that user; anonymous conversations are open
        if conversation.user_id:
            if not current_user or conversation.user_id != current_user.id:
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
    use_digital_twin: bool = Form(False),
    files: Optional[List[UploadFile]] = File(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
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
                if not conv:
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid conversation'})}\n\n"
                    return
                # Ownership rules
                if current_user:
                    if conv.user_id and conv.user_id != current_user.id:
                        yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid conversation'})}\n\n"
                        return
                else:
                    if conv.user_id:
                        yield f"data: {json.dumps({'type': 'error', 'error': 'Login required to access this conversation'})}\n\n"
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
                    user_id=str(current_user.id) if current_user else None,
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
                        elif att_type == "pdf":
                            try:
                                parser = DocumentParserService()
                                parsed = await parser.parse_contractor_quote(saved_path)
                                summary_text = parsed.get("summary") or ""
                                if not summary_text:
                                    items = parsed.get("items") or []
                                    total = (parsed.get("totals") or {}).get("total")
                                    parts = []
                                    if items:
                                        parts.append(f"{len(items)} items")
                                    if total:
                                        parts.append(f"total ~ ${total}")
                                    summary_text = ", ".join(parts)
                                if summary_text:
                                    attachment_summaries.append(f"- PDF: {summary_text}")
                                att["parsed"] = True
                            except Exception as pe:
                                logger.debug(f"PDF parse skipped: {pe}")
                        attachments.append(att)
                    except Exception as fe:
                        logger.warning(f"Failed to handle attachment {getattr(f,'filename',None)}: {fe}")

            # Digital Twin context (optional)
            context = None
            context_sources: List[str] = []
            if use_digital_twin:
                try:
                    # Resolve home_id (conversation.home_id or provided)
                    resolved_home_str = str(resolved_home_uuid) if resolved_home_uuid else None
                    if resolved_home_str:
                        rag_ctx = await rag_service.assemble_context(
                            db=db,
                            query=message,
                            home_id=resolved_home_str,
                            k=8,
                            include_images=True,
                        )
                        # Normalize keys to what the prompt builder expects
                        image_urls_from_twin = rag_ctx.get("images") or []
                        context = {
                            "context_text": rag_ctx.get("context_text") or "",
                            "image_urls": image_urls_from_twin,
                        }
                        meta = rag_ctx.get("metadata") or {}
                        srcs = meta.get("sources") or []
                        if isinstance(srcs, list):
                            context_sources.extend([str(s) for s in srcs if s])
                except Exception as e:
                    logger.warning(f"Digital Twin context fetch failed: {e}")

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
                    "use_digital_twin": use_digital_twin,
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
            # Lightweight intent guess for skills context during streaming
            _um = (message or "").lower()
            _intent_guess = None
            try:
                if any(k in _um for k in ["estimate", "cost", "budget"]):
                    _intent_guess = "cost_estimate"
                elif any(k in _um for k in ["product", "sofa", "appliance", "faucet", "recommend"]):
                    _intent_guess = "product_recommendation"
                elif any(k in _um for k in ["guide", "step-by-step", "how do i"]):
                    _intent_guess = "diy_guide"
                elif any(k in _um for k in ["pdf", "export"]):
                    _intent_guess = "pdf_request"
                elif any(k in _um for k in ["design", "paint", "flooring", "cabinets", "mockup", "staging"]):
                    _intent_guess = "design_idea"
            except Exception:
                _intent_guess = None

            prompt = chat_workflow._build_response_prompt(
                message,
                context,
                history,
                persona,
                scenario,
                _intent_guess,
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
                import re
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


# ==========================
# Canvas state (conversation)
# ==========================
class CanvasState(BaseModel):
    nodes: List[dict] = Field(default_factory=list)
    edges: List[dict] = Field(default_factory=list)
    viewport: Optional[dict] = None
    saved_at: Optional[str] = None


@router.get("/conversations/{conversation_id}/canvas", response_model=dict)
async def get_conversation_canvas(
    conversation_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db),
):
    """Load saved ReactFlow canvas state for the conversation (nodes/edges/viewport).

    Anonymous access permitted only for conversations without a user_id.
    """
    try:
        conversation_service = ConversationService(db)
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

        # Ownership
        if conversation.user_id:
            if not current_user or conversation.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation")

        dest_dir = Path("uploads/chat") / str(conversation.id)
        file_path = dest_dir / "canvas.json"
        if file_path.exists():
            try:
                raw = file_path.read_text("utf-8")
                return json.loads(raw)
            except Exception as e:
                logger.warning(f"Failed to read canvas state: {e}")
                return {}
        return {}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_conversation_canvas failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/conversations/{conversation_id}/canvas", response_model=dict)
async def save_conversation_canvas(
    conversation_id: str,
    state: CanvasState,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db),
):
    """Save ReactFlow canvas state for the conversation to a JSON file."""
    try:
        conversation_service = ConversationService(db)
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

        # Ownership
        if conversation.user_id:
            if not current_user or conversation.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation")

        dest_dir = Path("uploads/chat") / str(conversation.id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        file_path = dest_dir / "canvas.json"

        payload = state.model_dump()
        payload["saved_at"] = datetime.utcnow().isoformat()
        file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"save_conversation_canvas failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Message Feedback Endpoints (Agent Lightning Integration)
# ============================================================================

class MessageFeedbackRequest(BaseModel):
    """Request model for message feedback."""
    message_id: str = Field(..., description="ID of the message being rated")
    feedback_type: str = Field(..., description="Type of feedback: thumbs_up, thumbs_down, rating_1-5, regenerate, copy")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating 1-5 (optional)")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional text feedback")
    helpful: Optional[bool] = None
    accurate: Optional[bool] = None
    complete: Optional[bool] = None


class MessageFeedbackResponse(BaseModel):
    """Response model for message feedback."""
    feedback_id: str
    message_id: str
    feedback_type: str
    reward_score: float
    created_at: datetime


@router.post("/feedback", response_model=MessageFeedbackResponse)
async def submit_message_feedback(
    request: MessageFeedbackRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Submit feedback on a chat message for agent optimization.

    This endpoint allows users to provide feedback (thumbs up/down, ratings, etc.)
    on AI responses. The feedback is used to:
    1. Calculate reward scores for reinforcement learning
    2. Track agent performance over time
    3. Improve response quality through Agent Lightning

    Args:
        request: Feedback request with message_id and feedback details
        current_user: Current user (optional for anonymous feedback)
        db: Database session

    Returns:
        Feedback confirmation with calculated reward score
    """
    try:
        from sqlalchemy import select

        # Get the message
        result = await db.execute(
            select(ConversationMessage).where(ConversationMessage.id == UUID(request.message_id))
        )
        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        # Verify access to conversation (if user is authenticated)
        if current_user:
            result = await db.execute(
                select(Conversation).where(Conversation.id == message.conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if conversation and conversation.user_id and conversation.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this conversation"
                )

        # Map feedback_type to FeedbackType enum
        feedback_type_map = {
            "thumbs_up": FeedbackType.THUMBS_UP,
            "thumbs_down": FeedbackType.THUMBS_DOWN,
            "rating_1": FeedbackType.RATING_1,
            "rating_2": FeedbackType.RATING_2,
            "rating_3": FeedbackType.RATING_3,
            "rating_4": FeedbackType.RATING_4,
            "rating_5": FeedbackType.RATING_5,
            "regenerate": FeedbackType.REGENERATE,
            "copy": FeedbackType.COPY,
            "follow_up": FeedbackType.FOLLOW_UP,
        }

        feedback_enum = feedback_type_map.get(request.feedback_type)
        if not feedback_enum:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid feedback_type: {request.feedback_type}"
            )

        # Calculate reward score
        reward_calculator = RewardCalculator()

        # Prepare additional signals
        additional_signals = {
            "response_length": len(message.content),
            "intent_match": message.intent is not None,
            "used_context": bool(message.context_sources),
        }

        reward_score = reward_calculator.calculate_from_feedback(
            feedback_type=feedback_enum,
            additional_signals=additional_signals
        )

        # Create feedback record
        feedback = MessageFeedback(
            id=uuid4(),
            message_id=UUID(request.message_id),
            conversation_id=message.conversation_id,
            user_id=current_user.id if current_user else None,
            feedback_type=request.feedback_type,
            rating=request.rating,
            reward_score=reward_score,
            comment=request.comment,
            helpful=request.helpful,
            accurate=request.accurate,
            complete=request.complete
        )

        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)

        # Track with Agent Lightning
        try:
            tracker = AgentTracker(agent_name="chat_agent")

            # Get the user message that prompted this response
            result = await db.execute(
                select(ConversationMessage)
                .where(ConversationMessage.conversation_id == message.conversation_id)
                .where(ConversationMessage.created_at < message.created_at)
                .where(ConversationMessage.role == "user")
                .order_by(ConversationMessage.created_at.desc())
                .limit(1)
            )
            user_message = result.scalar_one_or_none()

            if user_message:
                tracker.track_chat_message(
                    user_message=user_message.content,
                    ai_response=message.content,
                    conversation_id=str(message.conversation_id),
                    intent=message.intent,
                    reward=reward_score
                )
                logger.info(f"Tracked feedback for message {request.message_id} with reward {reward_score:.2f}")

        except Exception as tracking_error:
            logger.warning(f"Failed to track feedback with Agent Lightning: {tracking_error}")

        return MessageFeedbackResponse(
            feedback_id=str(feedback.id),
            message_id=str(feedback.message_id),
            feedback_type=feedback.feedback_type,
            reward_score=reward_score,
            created_at=feedback.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit message feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )
