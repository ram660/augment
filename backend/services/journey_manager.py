"""
Journey management service for tracking user progress through home improvement projects.

Features:
- Journey templates (kitchen renovation, bathroom upgrade, etc.)
- Progress tracking across sessions
- Step completion and validation
- Journey analytics
- Resume capability
- Milestone tracking
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class JourneyStatus(Enum):
    """Status of a journey."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    PAUSED = "paused"


class StepStatus(Enum):
    """Status of a journey step."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class JourneyStep:
    """Single step in a journey."""
    step_id: str
    name: str
    description: str
    required: bool = True
    estimated_duration_minutes: int = 10
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    
    # Actions required
    required_actions: List[str] = field(default_factory=list)
    
    # Status
    status: StepStatus = StepStatus.NOT_STARTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Data collected
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JourneyTemplate:
    """Template for a user journey."""
    template_id: str
    name: str
    description: str
    category: str  # kitchen, bathroom, outdoor, etc.
    
    # Steps
    steps: List[JourneyStep] = field(default_factory=list)
    
    # Estimated metrics
    estimated_duration_days: int = 7
    estimated_cost_range: tuple = (1000, 5000)
    difficulty_level: str = "medium"  # easy, medium, hard
    
    # Tags
    tags: List[str] = field(default_factory=list)


@dataclass
class UserJourney:
    """Active user journey instance."""
    journey_id: str
    user_id: str
    template_id: str
    
    # Status
    status: JourneyStatus = JourneyStatus.NOT_STARTED
    current_step_id: Optional[str] = None
    
    # Steps (copied from template, can be customized)
    steps: List[JourneyStep] = field(default_factory=list)
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    
    # Progress
    completed_steps: int = 0
    total_steps: int = 0
    progress_percentage: float = 0.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class JourneyManager:
    """
    Service for managing user journeys through home improvement projects.
    
    Features:
    - Journey templates
    - Progress tracking
    - Step completion
    - Resume capability
    - Analytics
    """
    
    def __init__(self):
        self.templates: Dict[str, JourneyTemplate] = {}
        self.active_journeys: Dict[str, UserJourney] = {}  # journey_id -> UserJourney
        self.user_journeys: Dict[str, List[str]] = {}  # user_id -> [journey_ids]
        
        # Setup default templates
        self._setup_default_templates()
    
    def _setup_default_templates(self):
        """Setup default journey templates."""
        # Kitchen Renovation Journey
        self.templates["kitchen_renovation"] = JourneyTemplate(
            template_id="kitchen_renovation",
            name="Kitchen Renovation",
            description="Complete kitchen renovation from planning to execution",
            category="kitchen",
            estimated_duration_days=30,
            estimated_cost_range=(10000, 50000),
            difficulty_level="hard",
            tags=["kitchen", "renovation", "major-project"],
            steps=[
                JourneyStep(
                    step_id="initial_consultation",
                    name="Initial Consultation",
                    description="Share photos and discuss your vision",
                    required_actions=["upload_photos", "describe_goals"]
                ),
                JourneyStep(
                    step_id="vision_analysis",
                    name="Vision Analysis",
                    description="AI analyzes your space and provides insights",
                    depends_on=["initial_consultation"],
                    required_actions=["review_analysis"]
                ),
                JourneyStep(
                    step_id="design_options",
                    name="Design Options",
                    description="Explore design transformations",
                    depends_on=["vision_analysis"],
                    required_actions=["select_design"]
                ),
                JourneyStep(
                    step_id="product_selection",
                    name="Product Selection",
                    description="Choose cabinets, countertops, appliances",
                    depends_on=["design_options"],
                    required_actions=["select_products"]
                ),
                JourneyStep(
                    step_id="cost_estimate",
                    name="Cost Estimate",
                    description="Get detailed cost breakdown",
                    depends_on=["product_selection"],
                    required_actions=["review_estimate"]
                ),
                JourneyStep(
                    step_id="contractor_search",
                    name="Find Contractors",
                    description="Connect with local contractors",
                    depends_on=["cost_estimate"],
                    required_actions=["request_quotes"]
                ),
                JourneyStep(
                    step_id="finalize_plan",
                    name="Finalize Plan",
                    description="Export project plan and timeline",
                    depends_on=["contractor_search"],
                    required_actions=["export_pdf"]
                )
            ]
        )
        
        # DIY Project Journey
        self.templates["diy_project"] = JourneyTemplate(
            template_id="diy_project",
            name="DIY Project Planning",
            description="Plan and execute a DIY home improvement project",
            category="diy",
            estimated_duration_days=7,
            estimated_cost_range=(100, 2000),
            difficulty_level="medium",
            tags=["diy", "planning", "tutorials"],
            steps=[
                JourneyStep(
                    step_id="project_definition",
                    name="Define Project",
                    description="Describe what you want to build or fix",
                    required_actions=["describe_project"]
                ),
                JourneyStep(
                    step_id="tutorial_search",
                    name="Find Tutorials",
                    description="Discover relevant YouTube tutorials",
                    depends_on=["project_definition"],
                    required_actions=["watch_tutorials"]
                ),
                JourneyStep(
                    step_id="materials_list",
                    name="Materials & Tools",
                    description="Get shopping list for materials and tools",
                    depends_on=["tutorial_search"],
                    required_actions=["review_materials"]
                ),
                JourneyStep(
                    step_id="cost_planning",
                    name="Budget Planning",
                    description="Estimate costs and plan budget",
                    depends_on=["materials_list"],
                    required_actions=["approve_budget"]
                ),
                JourneyStep(
                    step_id="execution_plan",
                    name="Execution Plan",
                    description="Create step-by-step execution plan",
                    depends_on=["cost_planning"],
                    required_actions=["export_plan"]
                )
            ]
        )
        
        # Bathroom Upgrade Journey
        self.templates["bathroom_upgrade"] = JourneyTemplate(
            template_id="bathroom_upgrade",
            name="Bathroom Upgrade",
            description="Modernize your bathroom with new fixtures and finishes",
            category="bathroom",
            estimated_duration_days=14,
            estimated_cost_range=(5000, 20000),
            difficulty_level="medium",
            tags=["bathroom", "upgrade", "fixtures"],
            steps=[
                JourneyStep(
                    step_id="space_assessment",
                    name="Space Assessment",
                    description="Upload photos and measurements",
                    required_actions=["upload_photos"]
                ),
                JourneyStep(
                    step_id="style_selection",
                    name="Choose Style",
                    description="Select bathroom style and fixtures",
                    depends_on=["space_assessment"],
                    required_actions=["select_style"]
                ),
                JourneyStep(
                    step_id="fixture_selection",
                    name="Select Fixtures",
                    description="Choose vanity, toilet, shower, etc.",
                    depends_on=["style_selection"],
                    required_actions=["select_fixtures"]
                ),
                JourneyStep(
                    step_id="cost_estimate",
                    name="Cost Estimate",
                    description="Get detailed cost breakdown",
                    depends_on=["fixture_selection"],
                    required_actions=["review_estimate"]
                ),
                JourneyStep(
                    step_id="contractor_quotes",
                    name="Get Quotes",
                    description="Request quotes from contractors",
                    depends_on=["cost_estimate"],
                    required_actions=["request_quotes"]
                )
            ]
        )
    
    def start_journey(self, user_id: str, template_id: str, journey_id: Optional[str] = None) -> UserJourney:
        """
        Start a new journey for a user.
        
        Args:
            user_id: User ID
            template_id: Journey template ID
            journey_id: Optional custom journey ID
            
        Returns:
            UserJourney instance
        """
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Journey template '{template_id}' not found")
        
        # Generate journey ID
        if not journey_id:
            journey_id = f"{user_id}_{template_id}_{datetime.utcnow().timestamp()}"
        
        # Create journey
        journey = UserJourney(
            journey_id=journey_id,
            user_id=user_id,
            template_id=template_id,
            status=JourneyStatus.IN_PROGRESS,
            steps=[JourneyStep(**step.__dict__) for step in template.steps],  # Deep copy
            started_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
            total_steps=len(template.steps),
            current_step_id=template.steps[0].step_id if template.steps else None
        )
        
        # Store journey
        self.active_journeys[journey_id] = journey
        
        if user_id not in self.user_journeys:
            self.user_journeys[user_id] = []
        self.user_journeys[user_id].append(journey_id)
        
        logger.info(f"Started journey '{template_id}' for user '{user_id}'")
        return journey
    
    def get_journey(self, journey_id: str) -> Optional[UserJourney]:
        """Get a journey by ID."""
        return self.active_journeys.get(journey_id)
    
    def get_user_journeys(self, user_id: str) -> List[UserJourney]:
        """Get all journeys for a user."""
        journey_ids = self.user_journeys.get(user_id, [])
        return [self.active_journeys[jid] for jid in journey_ids if jid in self.active_journeys]
    
    def complete_step(self, journey_id: str, step_id: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark a step as completed.
        
        Args:
            journey_id: Journey ID
            step_id: Step ID
            data: Optional data collected during step
            
        Returns:
            True if step was completed successfully
        """
        journey = self.active_journeys.get(journey_id)
        if not journey:
            logger.warning(f"Journey '{journey_id}' not found")
            return False
        
        # Find step
        step = next((s for s in journey.steps if s.step_id == step_id), None)
        if not step:
            logger.warning(f"Step '{step_id}' not found in journey '{journey_id}'")
            return False
        
        # Mark as completed
        step.status = StepStatus.COMPLETED
        step.completed_at = datetime.utcnow()
        if data:
            step.data.update(data)
        
        # Update journey progress
        journey.completed_steps = sum(1 for s in journey.steps if s.status == StepStatus.COMPLETED)
        journey.progress_percentage = (journey.completed_steps / journey.total_steps) * 100
        journey.last_activity_at = datetime.utcnow()
        
        # Move to next step
        current_index = next((i for i, s in enumerate(journey.steps) if s.step_id == step_id), -1)
        if current_index >= 0 and current_index < len(journey.steps) - 1:
            journey.current_step_id = journey.steps[current_index + 1].step_id
        else:
            # Journey completed
            journey.status = JourneyStatus.COMPLETED
            journey.completed_at = datetime.utcnow()
        
        logger.info(f"Completed step '{step_id}' in journey '{journey_id}' ({journey.progress_percentage:.1f}% complete)")
        return True
    
    def get_current_step(self, journey_id: str) -> Optional[JourneyStep]:
        """Get the current step for a journey."""
        journey = self.active_journeys.get(journey_id)
        if not journey or not journey.current_step_id:
            return None
        
        return next((s for s in journey.steps if s.step_id == journey.current_step_id), None)
    
    def get_next_steps(self, journey_id: str) -> List[JourneyStep]:
        """Get available next steps (dependencies satisfied)."""
        journey = self.active_journeys.get(journey_id)
        if not journey:
            return []
        
        completed_step_ids = {s.step_id for s in journey.steps if s.status == StepStatus.COMPLETED}
        
        available_steps = []
        for step in journey.steps:
            if step.status == StepStatus.NOT_STARTED:
                # Check if dependencies are satisfied
                if all(dep in completed_step_ids for dep in step.depends_on):
                    available_steps.append(step)
        
        return available_steps
    
    def get_stats(self) -> Dict[str, Any]:
        """Get journey manager statistics."""
        total_journeys = len(self.active_journeys)
        active_journeys = sum(1 for j in self.active_journeys.values() if j.status == JourneyStatus.IN_PROGRESS)
        completed_journeys = sum(1 for j in self.active_journeys.values() if j.status == JourneyStatus.COMPLETED)
        
        return {
            "total_templates": len(self.templates),
            "total_journeys": total_journeys,
            "active_journeys": active_journeys,
            "completed_journeys": completed_journeys,
            "total_users": len(self.user_journeys)
        }


# Singleton instance
_journey_manager: Optional[JourneyManager] = None


def get_journey_manager() -> JourneyManager:
    """Get or create the journey manager singleton."""
    global _journey_manager
    if _journey_manager is None:
        _journey_manager = JourneyManager()
    return _journey_manager

