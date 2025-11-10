"""
Persona adaptation service for tailoring responses and features to user types.

Supports:
- Homeowner: Focus on visualization, contractor matching, cost estimates
- DIY Worker: Emphasis on tutorials, step-by-step guidance, tool recommendations
- Contractor: Business tools, lead generation, project management

Features:
- Persona-specific prompt templates
- Feature gating per persona
- Safety warnings (permits, electrical, structural)
- Tone and complexity adaptation
- Persona detection from conversation patterns
"""
import logging
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PersonaType(str, Enum):
    """User persona types."""
    HOMEOWNER = "homeowner"
    DIY_WORKER = "diy_worker"
    CONTRACTOR = "contractor"
    ADMIN = "admin"


class SafetyLevel(str, Enum):
    """Safety warning levels for DIY tasks."""
    SAFE = "safe"                    # No special precautions
    CAUTION = "caution"              # Basic safety gear recommended
    ADVANCED = "advanced"            # Requires experience
    PROFESSIONAL = "professional"    # Strongly recommend hiring professional
    PROHIBITED = "prohibited"        # Illegal without license


@dataclass
class PersonaConfig:
    """Configuration for a persona."""
    persona_type: PersonaType
    display_name: str
    description: str
    
    # Feature access
    enabled_features: Set[str] = field(default_factory=set)
    disabled_features: Set[str] = field(default_factory=set)
    
    # Prompt customization
    tone: str = "professional"  # professional, friendly, technical, casual
    detail_level: str = "medium"  # low, medium, high
    technical_depth: str = "medium"  # low, medium, high
    
    # Safety settings
    show_safety_warnings: bool = True
    require_permit_warnings: bool = True
    
    # Content preferences
    prefer_visual_content: bool = True
    prefer_step_by_step: bool = False
    prefer_cost_estimates: bool = True


@dataclass
class SafetyWarning:
    """Safety warning for a task or project."""
    level: SafetyLevel
    title: str
    description: str
    required_permits: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    safety_equipment: List[str] = field(default_factory=list)
    estimated_difficulty: str = "medium"  # easy, medium, hard, expert


class PersonaService:
    """
    Service for persona-based adaptation.
    
    Features:
    - Persona-specific configurations
    - Feature gating
    - Safety warnings
    - Prompt template generation
    - Persona detection
    """
    
    def __init__(self):
        self.persona_configs: Dict[PersonaType, PersonaConfig] = {}
        self.safety_rules: Dict[str, SafetyWarning] = {}
        
        # Setup default configurations
        self._setup_default_personas()
        self._setup_safety_rules()
    
    def _setup_default_personas(self):
        """Setup default persona configurations."""
        # Homeowner persona
        self.persona_configs[PersonaType.HOMEOWNER] = PersonaConfig(
            persona_type=PersonaType.HOMEOWNER,
            display_name="Homeowner",
            description="Visualize designs and find contractors",
            enabled_features={
                "design_studio",
                "contractor_search",
                "cost_estimates",
                "product_recommendations",
                "diy_tutorials",
                "pdf_export"
            },
            tone="friendly",
            detail_level="medium",
            technical_depth="low",
            prefer_visual_content=True,
            prefer_cost_estimates=True
        )
        
        # DIY Worker persona
        self.persona_configs[PersonaType.DIY_WORKER] = PersonaConfig(
            persona_type=PersonaType.DIY_WORKER,
            display_name="DIY Worker",
            description="Plan projects and get AI assistance",
            enabled_features={
                "diy_tutorials",
                "youtube_search",
                "tool_recommendations",
                "materials_list",
                "step_by_step_plans",
                "cost_estimates",
                "product_recommendations",
                "pdf_export"
            },
            tone="technical",
            detail_level="high",
            technical_depth="high",
            prefer_step_by_step=True,
            show_safety_warnings=True,
            require_permit_warnings=True
        )
        
        # Contractor persona
        self.persona_configs[PersonaType.CONTRACTOR] = PersonaConfig(
            persona_type=PersonaType.CONTRACTOR,
            display_name="Contractor",
            description="Find clients and showcase work",
            enabled_features={
                "lead_generation",
                "project_management",
                "cost_estimates",
                "materials_list",
                "design_studio",
                "pdf_export",
                "contractor_brief"
            },
            tone="professional",
            detail_level="high",
            technical_depth="high",
            prefer_cost_estimates=True,
            show_safety_warnings=False  # Contractors know safety
        )
        
        # Admin persona
        self.persona_configs[PersonaType.ADMIN] = PersonaConfig(
            persona_type=PersonaType.ADMIN,
            display_name="Admin",
            description="Platform administration",
            enabled_features={"*"},  # All features
            tone="professional",
            detail_level="high",
            technical_depth="high"
        )
    
    def _setup_safety_rules(self):
        """Setup safety warning rules."""
        # Electrical work
        self.safety_rules["electrical"] = SafetyWarning(
            level=SafetyLevel.PROFESSIONAL,
            title="Electrical Work Requires Licensed Electrician",
            description="Electrical work beyond replacing outlets/switches requires a licensed electrician in most jurisdictions.",
            required_permits=["Electrical Permit"],
            required_skills=["Licensed Electrician"],
            safety_equipment=["Voltage tester", "Insulated tools", "Safety glasses"],
            estimated_difficulty="expert"
        )
        
        # Plumbing
        self.safety_rules["plumbing_major"] = SafetyWarning(
            level=SafetyLevel.ADVANCED,
            title="Major Plumbing Work",
            description="Major plumbing work (moving pipes, gas lines) may require permits and professional help.",
            required_permits=["Plumbing Permit"],
            required_skills=["Plumbing experience", "Pipe fitting"],
            safety_equipment=["Pipe wrench", "Safety glasses", "Gloves"],
            estimated_difficulty="hard"
        )
        
        # Structural changes
        self.safety_rules["structural"] = SafetyWarning(
            level=SafetyLevel.PROHIBITED,
            title="Structural Changes Require Professional Engineer",
            description="Removing or modifying load-bearing walls requires structural engineer approval and permits.",
            required_permits=["Building Permit", "Structural Engineer Approval"],
            required_skills=["Licensed Contractor", "Structural Engineer"],
            safety_equipment=[],
            estimated_difficulty="expert"
        )
        
        # Gas work
        self.safety_rules["gas"] = SafetyWarning(
            level=SafetyLevel.PROHIBITED,
            title="Gas Work Requires Licensed Professional",
            description="Gas line work is illegal without proper licensing due to explosion/fire risk.",
            required_permits=["Gas Permit"],
            required_skills=["Licensed Gas Fitter"],
            safety_equipment=["Gas detector", "Specialized tools"],
            estimated_difficulty="expert"
        )
        
        # Asbestos
        self.safety_rules["asbestos"] = SafetyWarning(
            level=SafetyLevel.PROHIBITED,
            title="Asbestos Requires Certified Abatement",
            description="Asbestos removal requires certified professionals and special procedures.",
            required_permits=["Asbestos Abatement Permit"],
            required_skills=["Certified Asbestos Abatement"],
            safety_equipment=["Respirator", "Protective suit", "HEPA vacuum"],
            estimated_difficulty="expert"
        )
        
        # Roof work
        self.safety_rules["roof"] = SafetyWarning(
            level=SafetyLevel.ADVANCED,
            title="Roof Work - Fall Hazard",
            description="Roof work requires fall protection and experience working at heights.",
            required_permits=["Building Permit (for major work)"],
            required_skills=["Fall protection training", "Roofing experience"],
            safety_equipment=["Fall harness", "Safety rope", "Non-slip shoes"],
            estimated_difficulty="hard"
        )
    
    def get_persona_config(self, persona: str) -> PersonaConfig:
        """Get configuration for a persona."""
        try:
            persona_type = PersonaType(persona)
            return self.persona_configs.get(persona_type, self.persona_configs[PersonaType.HOMEOWNER])
        except ValueError:
            logger.warning(f"Unknown persona: {persona}, defaulting to homeowner")
            return self.persona_configs[PersonaType.HOMEOWNER]
    
    def is_feature_enabled(self, persona: str, feature: str) -> bool:
        """Check if a feature is enabled for a persona."""
        config = self.get_persona_config(persona)
        
        # Admin has access to all features
        if "*" in config.enabled_features:
            return True
        
        # Check if explicitly disabled
        if feature in config.disabled_features:
            return False
        
        # Check if explicitly enabled
        return feature in config.enabled_features
    
    def get_safety_warning(self, task_type: str) -> Optional[SafetyWarning]:
        """Get safety warning for a task type."""
        return self.safety_rules.get(task_type)
    
    def get_prompt_prefix(self, persona: str, scenario: Optional[str] = None) -> str:
        """
        Get persona-specific prompt prefix.
        
        Note: The system is now universal and persona-agnostic per UNIVERSAL_CHAT_IMPLEMENTATION.md.
        This method provides subtle tone/detail adjustments, not hard persona constraints.
        """
        config = self.get_persona_config(persona)
        
        parts = []
        
        # Tone guidance (subtle)
        if config.tone == "friendly":
            parts.append("Use a warm, supportive tone.")
        elif config.tone == "technical":
            parts.append("Use precise technical language.")
        elif config.tone == "professional":
            parts.append("Use professional, clear language.")
        
        # Detail level
        if config.detail_level == "high":
            parts.append("Provide detailed explanations.")
        elif config.detail_level == "low":
            parts.append("Keep explanations concise.")
        
        # Safety warnings
        if config.show_safety_warnings:
            parts.append("Include safety warnings for hazardous tasks.")
        
        # Scenario-specific (if provided)
        if scenario == "contractor_quotes":
            parts.append("Focus on gathering project details for contractor brief.")
        elif scenario == "diy_project_plan":
            parts.append("Focus on step-by-step DIY guidance.")
        
        return " ".join(parts) if parts else ""
    
    def detect_persona_from_message(self, message: str) -> Optional[PersonaType]:
        """
        Detect likely persona from message content.
        
        This is a simple heuristic-based detection.
        """
        message_lower = message.lower()
        
        # Contractor indicators
        contractor_keywords = ["quote", "bid", "estimate for client", "scope of work", "lead", "customer"]
        if any(keyword in message_lower for keyword in contractor_keywords):
            return PersonaType.CONTRACTOR
        
        # DIY indicators
        diy_keywords = ["how do i", "diy", "myself", "tutorial", "step by step", "tools needed"]
        if any(keyword in message_lower for keyword in diy_keywords):
            return PersonaType.DIY_WORKER
        
        # Homeowner indicators (default)
        homeowner_keywords = ["hire", "contractor", "cost", "design", "visualize", "should i"]
        if any(keyword in message_lower for keyword in homeowner_keywords):
            return PersonaType.HOMEOWNER
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get persona service statistics."""
        return {
            "personas_configured": len(self.persona_configs),
            "safety_rules": len(self.safety_rules),
            "personas": [p.value for p in self.persona_configs.keys()]
        }


# Singleton instance
_persona_service: Optional[PersonaService] = None


def get_persona_service() -> PersonaService:
    """Get or create the persona service singleton."""
    global _persona_service
    if _persona_service is None:
        _persona_service = PersonaService()
    return _persona_service

