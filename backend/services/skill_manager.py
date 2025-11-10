"""Skill Manager: minimal skills scaffold for HomeView AI.

Provides concise, intent-aware domain context snippets that can be injected
into LLM prompts without changing existing agent endpoints.

Design goals:
- Lightweight and safe: no external deps, no DB writes
- Short outputs: keep context <= ~10 lines
- Canada-first guidance and DIY safety baked in
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    tags: List[str]
    lines: List[str]

    def render(self, max_lines: int = 8) -> str:
        """Render a compact bullet list string."""
        take = self.lines[:max_lines]
        bullets = "\n".join(f"- {line}" for line in take)
        return bullets


class SkillManager:
    """Simple in-process skill registry and selector."""

    def __init__(self) -> None:
        self._skills: List[Skill] = self._seed_skills()

    def _seed_skills(self) -> List[Skill]:
        return [
            Skill(
                name="DIY Safety",
                description="General DIY safety and tool handling guidance",
                tags=["diy", "safety", "tools"],
                lines=[
                    "Confirm PPE (gloves, eye and hearing protection, respirator if sanding/paint).",
                    "Verify power is off at the breaker before electrical work.",
                    "Ventilate for painting/adhesives; prefer low/zero‑VOC materials.",
                    "Use correct blade/bits; clamp workpieces; keep hands clear.",
                    "Lift with legs; use helpers for heavy/awkward items.",
                    "Follow manufacturer instructions; test in inconspicuous area first.",
                ],
            ),
            Skill(
                name="Canada Building Code (lite)",
                description="High-level Canadian residential code reminders",
                tags=["canada", "code", "permit", "electrical", "egress"],
                lines=[
                    "Verify local permitting; provincial/municipal rules may vary.",
                    "Electrical: use AFCI/GFCI where required; follow box fill and gauge.",
                    "Egress: bedrooms need compliant window size/height; maintain clear exits.",
                    "Stairs/rails: check rise/run, handrail height, baluster spacing.",
                    "Moist areas: moisture barriers and ventilation per code.",
                ],
            ),
            Skill(
                name="Cost Estimation",
                description="Estimating checklist for Canada (CAD)",
                tags=["estimate", "budget", "materials", "labor", "canada"],
                lines=[
                    "Include materials + labor + disposal + contingencies (10–20%).",
                    "Add waste/overage: flooring/tile/paint typically 10–15%.",
                    "Regional pricing in CAD; small/local .ca vendors preferred.",
                    "Specify quality tier; list key assumptions and exclusions.",
                ],
            ),
            Skill(
                name="Product Matching",
                description="Dimension and clearance checks for interior products",
                tags=["product", "fit", "dimensions", "clearance", "canada"],
                lines=[
                    "Capture room dimensions (L×W×H) plus doorways and clearances.",
                    "Check product W×D×H vs available space; maintain walking clearances.",
                    "Consider electrical/plumbing constraints and load/anchoring needs.",
                    "Prefer Canadian suppliers (.ca) and CAD pricing when suggesting items.",
                ],
            ),
        ]

    def select(self, intent: Optional[str], persona: Optional[str], scenario: Optional[str], user_message: Optional[str]) -> List[Skill]:
        intent = (intent or "").lower()
        persona = (persona or "").lower()
        scenario = (scenario or "").lower()
        um = (user_message or "").lower()

        picks: List[Skill] = []

        def add_by_name(name: str) -> None:
            s = next((x for x in self._skills if x.name == name), None)
            if s and s not in picks:
                picks.append(s)

        # Persona/scenario defaults
        if persona == "diy_worker" or scenario == "diy_project_plan":
            add_by_name("DIY Safety")
        if persona == "contractor" or scenario == "contractor_quotes":
            add_by_name("Cost Estimation")

        # Intent-driven
        if intent == "cost_estimate":
            add_by_name("Cost Estimation")
            add_by_name("Canada Building Code (lite)")
        elif intent == "product_recommendation":
            add_by_name("Product Matching")
        elif intent == "diy_guide":
            add_by_name("DIY Safety")
            add_by_name("Canada Building Code (lite)")
        elif intent in ("design_idea", "design_transformation"):
            add_by_name("Product Matching")

        # Heuristic nudges from message text (when intent is unknown)
        if not intent:
            if any(k in um for k in ["estimate", "budget", "cost"]):
                add_by_name("Cost Estimation")
            if any(k in um for k in ["product", "buy", "recommend"]):
                add_by_name("Product Matching")
            if any(k in um for k in ["diy", "step-by-step", "how do i"]):
                add_by_name("DIY Safety")
            if any(k in um for k in ["permit", "code", "inspection"]):
                add_by_name("Canada Building Code (lite)")

        # Always keep it compact: max 2–3 skills
        return picks[:3]

    def get_context(self, intent: Optional[str], persona: Optional[str], scenario: Optional[str], user_message: Optional[str]) -> str:
        skills = self.select(intent, persona, scenario, user_message)
        if not skills:
            return ""
        blocks = []
        for s in skills:
            blocks.append(f"{s.name}:\n{s.render()}")
        # Prefix to make it easy to identify in prompts
        return "\n**SKILL CONTEXT (concise):**\n" + "\n\n".join(blocks) + "\n"

