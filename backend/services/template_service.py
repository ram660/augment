"""
Template service for managing configurable personas, scenarios, and prompts.

Supports:
- YAML/JSON-based template definitions
- Template versioning and A/B testing
- Dynamic template loading
- Template inheritance
- Variable substitution
"""
import logging
import yaml
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import re

logger = logging.getLogger(__name__)


@dataclass
class TemplateVersion:
    """Template version for A/B testing."""
    version_id: str
    name: str
    weight: float = 1.0  # For weighted A/B testing
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Template:
    """Template definition."""
    template_id: str
    name: str
    description: str
    template_type: str  # persona, scenario, prompt, action
    
    # Template content
    content: Dict[str, Any] = field(default_factory=dict)
    
    # Versioning
    version: str = "1.0.0"
    versions: List[TemplateVersion] = field(default_factory=list)
    
    # Inheritance
    extends: Optional[str] = None  # Parent template ID
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # A/B testing
    ab_test_enabled: bool = False
    ab_test_group: Optional[str] = None


class TemplateService:
    """
    Service for managing templates.
    
    Features:
    - Load templates from YAML/JSON files
    - Template inheritance
    - Variable substitution
    - A/B testing support
    - Template versioning
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or Path(__file__).parent.parent / "templates"
        self.templates: Dict[str, Template] = {}
        
        # Create templates directory if it doesn't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Load default templates
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default templates."""
        # Persona templates
        self.templates["homeowner_persona"] = Template(
            template_id="homeowner_persona",
            name="Homeowner Persona",
            description="Default homeowner persona configuration",
            template_type="persona",
            content={
                "display_name": "Homeowner",
                "tone": "friendly",
                "detail_level": "medium",
                "technical_depth": "low",
                "features": [
                    "design_studio",
                    "contractor_search",
                    "cost_estimates",
                    "product_recommendations"
                ],
                "prompt_prefix": "You are helping a homeowner with their home improvement project.",
                "suggested_actions": [
                    "visualize_design",
                    "get_cost_estimate",
                    "find_contractors"
                ]
            },
            tags=["persona", "homeowner"]
        )
        
        self.templates["diy_worker_persona"] = Template(
            template_id="diy_worker_persona",
            name="DIY Worker Persona",
            description="Default DIY worker persona configuration",
            template_type="persona",
            content={
                "display_name": "DIY Worker",
                "tone": "technical",
                "detail_level": "high",
                "technical_depth": "high",
                "features": [
                    "diy_tutorials",
                    "youtube_search",
                    "tool_recommendations",
                    "step_by_step_plans"
                ],
                "prompt_prefix": "You are helping a DIY enthusiast with detailed technical guidance.",
                "suggested_actions": [
                    "create_diy_plan",
                    "find_tutorials",
                    "get_materials_list"
                ],
                "safety_warnings_enabled": True
            },
            tags=["persona", "diy"]
        )
        
        self.templates["contractor_persona"] = Template(
            template_id="contractor_persona",
            name="Contractor Persona",
            description="Default contractor persona configuration",
            template_type="persona",
            content={
                "display_name": "Contractor",
                "tone": "professional",
                "detail_level": "high",
                "technical_depth": "high",
                "features": [
                    "lead_generation",
                    "project_management",
                    "cost_estimates",
                    "contractor_brief"
                ],
                "prompt_prefix": "You are helping a contractor with business and project management.",
                "suggested_actions": [
                    "create_project_brief",
                    "estimate_costs",
                    "manage_timeline"
                ]
            },
            tags=["persona", "contractor"]
        )
        
        # Scenario templates
        self.templates["kitchen_renovation"] = Template(
            template_id="kitchen_renovation",
            name="Kitchen Renovation",
            description="Kitchen renovation journey template",
            template_type="scenario",
            content={
                "display_name": "Kitchen Renovation",
                "steps": [
                    {
                        "step_id": "planning",
                        "name": "Planning & Design",
                        "description": "Define layout, style, and budget",
                        "required_data": ["budget", "style_preference", "layout_constraints"],
                        "suggested_actions": ["visualize_design", "get_cost_estimate"]
                    },
                    {
                        "step_id": "contractor_selection",
                        "name": "Find Contractors",
                        "description": "Get quotes and select contractor",
                        "required_data": ["project_scope", "timeline"],
                        "suggested_actions": ["find_contractors", "create_contractor_brief"]
                    },
                    {
                        "step_id": "execution",
                        "name": "Execution",
                        "description": "Monitor progress and manage changes",
                        "required_data": ["contractor_selected", "start_date"],
                        "suggested_actions": ["track_progress", "manage_changes"]
                    }
                ],
                "estimated_duration": "4-8 weeks",
                "typical_budget_range": "$15,000-$50,000"
            },
            tags=["scenario", "kitchen", "renovation"]
        )
        
        self.templates["diy_project"] = Template(
            template_id="diy_project",
            name="DIY Project",
            description="General DIY project template",
            template_type="scenario",
            content={
                "display_name": "DIY Project",
                "steps": [
                    {
                        "step_id": "research",
                        "name": "Research & Planning",
                        "description": "Learn about the project and plan approach",
                        "suggested_actions": ["find_tutorials", "get_materials_list"]
                    },
                    {
                        "step_id": "preparation",
                        "name": "Gather Materials & Tools",
                        "description": "Purchase materials and prepare workspace",
                        "suggested_actions": ["get_product_recommendations", "create_shopping_list"]
                    },
                    {
                        "step_id": "execution",
                        "name": "Execute Project",
                        "description": "Follow step-by-step plan",
                        "suggested_actions": ["follow_diy_plan", "watch_tutorials"]
                    }
                ],
                "safety_check_required": True
            },
            tags=["scenario", "diy"]
        )
        
        # Prompt templates
        self.templates["cost_estimate_prompt"] = Template(
            template_id="cost_estimate_prompt",
            name="Cost Estimate Prompt",
            description="Prompt template for cost estimation",
            template_type="prompt",
            content={
                "system_prompt": """You are a cost estimation expert for home improvement projects.
Provide detailed cost breakdowns including:
- Materials
- Labor
- Permits
- Contingency (10-15%)

Use regional pricing data for {region}.
Consider project complexity: {complexity}.""",
                "variables": ["region", "complexity", "project_type"],
                "output_format": "structured_json"
            },
            tags=["prompt", "cost_estimate"]
        )
        
        logger.info(f"Loaded {len(self.templates)} default templates")
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """Get a template by ID."""
        return self.templates.get(template_id)
    
    def get_templates_by_type(self, template_type: str) -> List[Template]:
        """Get all templates of a specific type."""
        return [t for t in self.templates.values() if t.template_type == template_type]
    
    def get_templates_by_tag(self, tag: str) -> List[Template]:
        """Get all templates with a specific tag."""
        return [t for t in self.templates.values() if tag in t.tags]
    
    def render_template(self, template_id: str, variables: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Render a template with variable substitution.
        
        Args:
            template_id: Template ID
            variables: Variables to substitute
            
        Returns:
            Rendered template content
        """
        template = self.get_template(template_id)
        if not template:
            logger.warning(f"Template not found: {template_id}")
            return None
        
        # Handle inheritance
        content = self._resolve_inheritance(template)
        
        # Substitute variables
        if variables:
            content = self._substitute_variables(content, variables)
        
        return content
    
    def _resolve_inheritance(self, template: Template) -> Dict[str, Any]:
        """Resolve template inheritance."""
        if not template.extends:
            return template.content.copy()
        
        # Get parent template
        parent = self.get_template(template.extends)
        if not parent:
            logger.warning(f"Parent template not found: {template.extends}")
            return template.content.copy()
        
        # Recursively resolve parent
        parent_content = self._resolve_inheritance(parent)
        
        # Merge with current template (current overrides parent)
        merged = parent_content.copy()
        merged.update(template.content)
        
        return merged
    
    def _substitute_variables(self, content: Any, variables: Dict[str, Any]) -> Any:
        """Substitute variables in template content."""
        if isinstance(content, str):
            # Replace {variable} with value
            for key, value in variables.items():
                content = content.replace(f"{{{key}}}", str(value))
            return content
        elif isinstance(content, dict):
            return {k: self._substitute_variables(v, variables) for k, v in content.items()}
        elif isinstance(content, list):
            return [self._substitute_variables(item, variables) for item in content]
        else:
            return content
    
    def load_template_from_file(self, file_path: Path) -> Optional[Template]:
        """Load a template from a YAML or JSON file."""
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix == '.yaml' or file_path.suffix == '.yml':
                    data = yaml.safe_load(f)
                elif file_path.suffix == '.json':
                    data = json.load(f)
                else:
                    logger.error(f"Unsupported file format: {file_path.suffix}")
                    return None
            
            template = Template(**data)
            self.templates[template.template_id] = template
            logger.info(f"Loaded template from file: {template.template_id}")
            return template
            
        except Exception as e:
            logger.error(f"Failed to load template from {file_path}: {e}")
            return None
    
    def save_template_to_file(self, template_id: str, file_path: Path) -> bool:
        """Save a template to a YAML or JSON file."""
        template = self.get_template(template_id)
        if not template:
            logger.error(f"Template not found: {template_id}")
            return False
        
        try:
            data = {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "template_type": template.template_type,
                "content": template.content,
                "version": template.version,
                "extends": template.extends,
                "tags": template.tags,
                "author": template.author
            }
            
            with open(file_path, 'w') as f:
                if file_path.suffix == '.yaml' or file_path.suffix == '.yml':
                    yaml.dump(data, f, default_flow_style=False)
                elif file_path.suffix == '.json':
                    json.dump(data, f, indent=2)
                else:
                    logger.error(f"Unsupported file format: {file_path.suffix}")
                    return False
            
            logger.info(f"Saved template to file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save template to {file_path}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get template service statistics."""
        return {
            "total_templates": len(self.templates),
            "templates_by_type": {
                template_type: len(self.get_templates_by_type(template_type))
                for template_type in set(t.template_type for t in self.templates.values())
            },
            "templates_dir": str(self.templates_dir)
        }


# Singleton instance
_template_service: Optional[TemplateService] = None


def get_template_service() -> TemplateService:
    """Get or create the template service singleton."""
    global _template_service
    if _template_service is None:
        _template_service = TemplateService()
    return _template_service

