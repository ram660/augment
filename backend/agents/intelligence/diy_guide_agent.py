"""
DIY Guide Agent

Generates a structured, step-by-step DIY plan for a requested project using
Google Gemini models. Uses official Gemini text generation best practices
(https://ai.google.dev/gemini-api/docs) and returns a JSON-serializable object.

This agent is focused on structured planning; image generation for steps can be
added later via the Design Transformation Service if needed.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.integrations.gemini.client import GeminiClient

logger = logging.getLogger(__name__)


@dataclass
class DIYGuide:
    title: str
    summary: str
    room_type: Optional[str]
    skill_level: Optional[str]
    estimated_time_hours: Optional[float]
    estimated_cost_range: Optional[str]
    materials: List[Dict[str, Any]]
    tools: List[Dict[str, Any]]
    steps: List[Dict[str, Any]]  # each step: {title, instructions, duration_estimate, image_prompt?}
    safety_tips: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "room_type": self.room_type,
            "skill_level": self.skill_level,
            "estimated_time_hours": self.estimated_time_hours,
            "estimated_cost_range": self.estimated_cost_range,
            "materials": self.materials,
            "tools": self.tools,
            "steps": self.steps,
            "safety_tips": self.safety_tips,
        }


class DIYGuideAgent:
    """Agent to generate structured DIY guides."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini = gemini_client or GeminiClient()

    async def process(
        self,
        project_description: str,
        room_type: Optional[str] = None,
        skill_level: Optional[str] = None,
        budget_range: Optional[str] = None,
        room_image_url: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a DIY guide for the given project description.

        Args:
            project_description: The DIY project the user wants to do.
            room_type: e.g., "kitchen", "bathroom", etc.
            skill_level: e.g., "beginner", "intermediate", "advanced".
            budget_range: e.g., "$100-$300".
            room_image_url: Optional reference image of the room.
            region: Optional region for material availability/cost context (prefer Canada/CA if available).

        Returns: JSON-serializable dict representing the DIY guide.
        """
        logger.info("Generating DIY guide for: %s", project_description)

        system_instructions = (
            "You are HomeView AI's DIY planning expert. Create practical, safe, step-by-step "
            "DIY instructions optimized for homeowners/DIYers in Canada when possible. Be concise, clear, and structured."
        )

        guidance = [
            "Return ONLY valid JSON. No prose outside JSON.",
            "Use simple, numbered steps with clear instructions.",
            "Include safety_tips with Canada-relevant guidance when possible.",
            "Materials/tools lists should be minimal but complete, with optional items marked.",
            "Estimate time in hours and provide a cost range (CAD preferred if region implies Canada).",
        ]

        # Structured JSON schema for the response
        schema_block = {
            "title": "string",
            "summary": "string",
            "room_type": "string",
            "skill_level": "string",
            "estimated_time_hours": 0,
            "estimated_cost_range": "string",
            "materials": [
                {"name": "string", "quantity": "string", "notes": "string"}
            ],
            "tools": [
                {"name": "string", "optional": False, "notes": "string"}
            ],
            "steps": [
                {
                    "title": "string",
                    "instructions": "string",
                    "duration_estimate_minutes": 0,
                    "image_prompt": "string"
                }
            ],
            "safety_tips": ["string", "string"]
        }

        # Compose the prompt per official docs
        prompt_parts: List[str] = []
        prompt_parts.append(system_instructions)
        prompt_parts.append("\nProject:")
        prompt_parts.append(project_description)
        if room_type:
            prompt_parts.append(f"\nRoom type: {room_type}")
        if skill_level:
            prompt_parts.append(f"\nSkill level: {skill_level}")
        if budget_range:
            prompt_parts.append(f"\nBudget range: {budget_range}")
        if region:
            prompt_parts.append(f"\nRegion: {region}")
        if room_image_url:
            prompt_parts.append(f"\nReference image URL: {room_image_url}")

        prompt_parts.append("\nOutput JSON schema (example types, not a string):")
        prompt_parts.append(json.dumps(schema_block, indent=2))
        prompt_parts.append("\nReturn ONLY JSON. No markdown code fences.")

        prompt = "\n".join(prompt_parts)

        try:
            text = await self.gemini.generate_text(prompt=prompt, temperature=0.3)
        except Exception as e:
            logger.error("Gemini error generating DIY guide: %s", e, exc_info=True)
            raise

        guide_obj = self._parse_json(text)

        guide = DIYGuide(
            title=guide_obj.get("title") or "DIY Project Plan",
            summary=guide_obj.get("summary") or "",
            room_type=guide_obj.get("room_type"),
            skill_level=guide_obj.get("skill_level"),
            estimated_time_hours=guide_obj.get("estimated_time_hours"),
            estimated_cost_range=guide_obj.get("estimated_cost_range"),
            materials=guide_obj.get("materials") or [],
            tools=guide_obj.get("tools") or [],
            steps=guide_obj.get("steps") or [],
            safety_tips=guide_obj.get("safety_tips") or [],
        )

        logger.info("DIY guide generated: %s (%d steps)", guide.title, len(guide.steps))
        return guide.to_dict()

    def _parse_json(self, raw: str) -> Dict[str, Any]:
        """Handle cases where model returns surrounding text or code fences."""
        import re

        s = (raw or "").strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, flags=re.DOTALL)
        if match:
            s = match.group(1)
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            # fallback: try to find first JSON object
            match = re.search(r"\{.*\}", s, flags=re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise

