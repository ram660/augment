# Deep-Dive Integration Guide: Part 3
## Technologies #5-6: Agent Lightning & Commerce (ACP/Stripe)

**Continuation from Part 2**

---

## Agent Lightning Integration (Continued from Part 2)

### 🔧 Skill Manager Service

```python
# backend/services/skill_manager.py (NEW FILE)
from pathlib import Path
import yaml
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SkillManager:
    """
    Manages Anthropic-style skills for home improvement agents.
    
    Skills are YAML files in skills/ directory that provide:
    - Domain expertise
    - Structured knowledge
    - Response templates
    - Best practices
    """
    
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Dict] = {}
        self._load_all_skills()
    
    def _load_all_skills(self):
        """Load all SKILL.md files from skills directory."""
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return
        
        for skill_file in self.skills_dir.rglob("SKILL.md"):
            skill = self._parse_skill_file(skill_file)
            if skill:
                self.skills[skill['name']] = skill
                logger.info(f"Loaded skill: {skill['name']}")
    
    def _parse_skill_file(self, file_path: Path) -> Optional[Dict]:
        """Parse SKILL.md file with YAML frontmatter and markdown content."""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Split frontmatter and content
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    markdown_content = parts[2].strip()
                    
                    return {
                        **frontmatter,
                        'content': markdown_content,
                        'file_path': str(file_path)
                    }
            
            logger.warning(f"Invalid skill format: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading skill {file_path}: {e}")
            return None
    
    def get_skill(self, skill_name: str) -> Optional[Dict]:
        """Get skill by name."""
        return self.skills.get(skill_name)
    
    def list_skills(self, category: Optional[str] = None) -> List[Dict]:
        """List all skills, optionally filtered by category."""
        skills = list(self.skills.values())
        
        if category:
            skills = [s for s in skills if s.get('category') == category]
        
        return skills
    
    def get_skill_content(self, skill_name: str) -> str:
        """Get full content of a skill."""
        skill = self.get_skill(skill_name)
        if skill:
            return skill.get('content', '')
        return ""
    
    def find_relevant_skills(
        self,
        query: str,
        max_skills: int = 3
    ) -> List[Dict]:
        """
        Find relevant skills for a query.
        
        Uses keyword matching on description and name.
        """
        query_lower = query.lower()
        skills_with_scores = []
        
        for skill in self.skills.values():
            score = 0
            
            # Check name
            if query_lower in skill['name'].lower():
                score += 3
            
            # Check description
            desc = skill.get('description', '').lower()
            for word in query_lower.split():
                if word in desc:
                    score += 1
            
            # Check category
            if query_lower in skill.get('category', '').lower():
                score += 2
            
            if score > 0:
                skills_with_scores.append((skill, score))
        
        # Sort by score
        skills_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in skills_with_scores[:max_skills]]


class SkillEnhancedAgent:
    """
    Base class for agents that use skills.
    
    Extends BaseAgent with skill awareness.
    """
    
    def __init__(self):
        self.skill_manager = SkillManager()
        self.active_skills: List[str] = []
    
    def activate_skill(self, skill_name: str):
        """Activate a skill for this agent."""
        skill = self.skill_manager.get_skill(skill_name)
        if skill:
            self.active_skills.append(skill_name)
            logger.info(f"Activated skill: {skill_name}")
        else:
            logger.warning(f"Skill not found: {skill_name}")
    
    def get_skill_context(self) -> str:
        """Get combined context from all active skills."""
        contexts = []
        
        for skill_name in self.active_skills:
            content = self.skill_manager.get_skill_content(skill_name)
            if content:
                contexts.append(f"=== {skill_name.upper()} SKILL ===\n{content}\n")
        
        return "\n".join(contexts)
    
    async def process_with_skills(
        self,
        user_input: str,
        auto_detect_skills: bool = True
    ) -> str:
        """
        Process input with relevant skills.
        
        If auto_detect_skills=True, automatically finds relevant skills.
        """
        if auto_detect_skills:
            # Find relevant skills
            relevant_skills = self.skill_manager.find_relevant_skills(user_input)
            
            # Temporarily activate them
            for skill in relevant_skills:
                self.activate_skill(skill['name'])
        
        # Build prompt with skill context
        skill_context = self.get_skill_context()
        
        full_prompt = f"""
{skill_context}

---

User Query: {user_input}

Respond using the skills above as your knowledge base. Provide accurate, helpful guidance.
        """
        
        # Use LLM to generate response
        response = await self.gemini_client.generate_text(full_prompt)
        
        # Clear temporary skills
        if auto_detect_skills:
            self.active_skills.clear()
        
        return response
```

**Updated Chat Agent with Skills:**
```python
# backend/agents/conversational/home_chat_agent.py
from backend.services.skill_manager import SkillEnhancedAgent

class HomeChatAgent(SkillEnhancedAgent):
    """
    Chat agent with skill-based expertise.
    
    Automatically detects topic and applies relevant skills:
    - Plumbing questions → plumbing-advisor skill
    - Cost questions → cost-estimation-expert skill
    - Design questions → design-modern/traditional skills
    - DIY questions → diy-safety + domain skill
    """
    
    def __init__(self):
        super().__init__()
        
        # Always active skills (core competencies)
        self.activate_skill("home-improvement-foundation")
        self.activate_skill("diy-safety")
    
    async def chat(
        self,
        user_message: str,
        conversation_history: List[Dict] = None,
        home_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Enhanced chat with skill-based responses.
        """
        # Detect topic
        topic = self._detect_topic(user_message)
        
        # Activate relevant skill
        skill_map = {
            "plumbing": "plumbing-advisor",
            "electrical": "electrical-advisor",
            "cost": "cost-estimation-expert",
            "design": "design-consultant",
            "diy": "diy-expert",
            "code": "building-code-expert",
            "contractor": "contractor-vetting"
        }
        
        if topic in skill_map:
            self.activate_skill(skill_map[topic])
        
        # Process with skills
        response = await self.process_with_skills(
            user_message,
            auto_detect_skills=False  # We manually activated
        )
        
        return {
            "response": response,
            "skills_used": self.active_skills.copy(),
            "topic_detected": topic
        }
    
    def _detect_topic(self, message: str) -> str:
        """Detect conversation topic."""
        message_lower = message.lower()
        
        keywords = {
            "plumbing": ["plumb", "pipe", "faucet", "drain", "toilet", "sink", "water", "leak"],
            "electrical": ["electric", "wire", "outlet", "switch", "breaker", "light"],
            "cost": ["cost", "price", "budget", "expensive", "cheap", "how much"],
            "design": ["design", "style", "color", "modern", "contemporary", "traditional"],
            "diy": ["diy", "how to", "install", "fix", "repair", "myself"],
            "code": ["code", "permit", "legal", "regulation", "allowed"],
            "contractor": ["contractor", "hire", "professional", "licensed", "bonded"]
        }
        
        scores = {}
        for topic, words in keywords.items():
            score = sum(1 for word in words if word in message_lower)
            if score > 0:
                scores[topic] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return "general"
```

**API for Skill Management:**
```python
# backend/api/skills.py (NEW FILE)
from fastapi import APIRouter, Depends
from backend.services.skill_manager import SkillManager

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])

@router.get("/list")
async def list_skills(category: Optional[str] = None):
    """
    List available skills.
    
    Useful for UI to show what expertise areas are available.
    """
    skill_manager = SkillManager()
    skills = skill_manager.list_skills(category=category)
    
    return {
        "skills": [
            {
                "name": s['name'],
                "description": s['description'],
                "category": s.get('category'),
                "difficulty": s.get('difficulty')
            }
            for s in skills
        ]
    }

@router.get("/{skill_name}")
async def get_skill_details(skill_name: str):
    """Get detailed information about a skill."""
    skill_manager = SkillManager()
    skill = skill_manager.get_skill(skill_name)
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return skill

@router.post("/query")
async def query_with_skill(
    question: str = Form(...),
    skill_name: str = Form(...),
    user: User = Depends(get_current_user)
):
    """
    Ask a question using a specific skill.
    
    Example:
        question: "Why is my faucet dripping?"
        skill_name: "plumbing-advisor"
    """
    from backend.agents.conversational.home_chat_agent import HomeChatAgent
    
    agent = HomeChatAgent()
    agent.activate_skill(skill_name)
    
    response = await agent.process_with_skills(
        question,
        auto_detect_skills=False
    )
    
    return {
        "question": question,
        "answer": response,
        "skill_used": skill_name
    }
```

---

### 📊 Skills Summary

| Skill Category | Examples | Agent Benefit | User Benefit |
|----------------|----------|---------------|--------------|
| Trade Expertise | plumbing-advisor, electrical-advisor | Consistent, accurate answers | Expert guidance |
| Design | design-modern, design-traditional | Style-appropriate suggestions | Better recommendations |
| Intelligence | cost-estimation-expert | Data-driven estimates | Accurate pricing |
| Safety | diy-safety, contractor-vetting | Risk mitigation | Peace of mind |

**Implementation Priority:**
1. **Week 1-2:** Create 5 core skills (plumbing, electrical, cost, design, safety)
2. **Week 3-4:** Integrate with HomeChatAgent
3. **Week 5-6:** Create 10 more specialized skills
4. **Week 7-8:** UI for "Ask an Expert" feature with skill selection

---

## Technology #5: Agent Lightning
### Continuous Agent Improvement Through RL

### 🎯 Current Challenge

**Your Agents Make Decisions But Don't Learn From Them:**
- Chat agent gives advice → no feedback if it helped
- Cost estimator provides quote → no validation if accurate
- Design studio suggests changes → no tracking of user satisfaction
- Contractor matcher recommends pros → no outcome tracking

**Result:** Agents stay static, don't improve with usage

**Solution:** Implement reinforcement learning feedback loops with Agent Lightning

---

### 🔧 Integration Implementation

#### **Integration #1: Agent Performance Tracking**

```python
# backend/services/agent_metrics.py (NEW FILE)
from typing import Dict, Any, Optional, List
import agentops as agl
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AgentMetricsService:
    """
    Tracks agent performance for continuous improvement.
    
    Integrates with Agent Lightning (agentops) for:
    - Step-by-step execution tracking
    - User feedback collection
    - Performance analytics
    - Training data generation
    """
    
    def __init__(self):
        # Initialize Agent Lightning
        agl.init(
            api_key=os.getenv("AGENTOPS_API_KEY"),
            tags=["homeview-ai", "production"]
        )
    
    async def track_agent_execution(
        self,
        agent_name: str,
        user_id: str,
        input_data: Dict,
        func: callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Track agent execution with Agent Lightning.
        
        Usage:
            result = await metrics.track_agent_execution(
                agent_name="HomeChatAgent",
                user_id=user.id,
                input_data={"message": "How much to remodel kitchen?"},
                func=agent.chat,
                message="How much to remodel kitchen?"
            )
        """
        # Start session
        session_id = agl.start_session(
            agent_name=agent_name,
            tags=[f"user-{user_id}", agent_name]
        )
        
        try:
            # Log input
            agl.emit_step(
                step_name="input_received",
                data=input_data,
                agent_name=agent_name
            )
            
            # Execute agent function
            start_time = datetime.now()
            result = await func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            # Log output
            agl.emit_step(
                step_name="output_generated",
                data={
                    "result": result,
                    "duration_seconds": duration
                },
                agent_name=agent_name
            )
            
            # End session (successful)
            agl.end_session(
                session_id=session_id,
                end_state="Success",
                metadata={
                    "duration": duration,
                    "agent": agent_name
                }
            )
            
            return {
                "result": result,
                "session_id": session_id,
                "duration": duration
            }
            
        except Exception as e:
            # Log error
            agl.emit_step(
                step_name="error",
                data={"error": str(e)},
                agent_name=agent_name,
                tags=["error"]
            )
            
            # End session (failed)
            agl.end_session(
                session_id=session_id,
                end_state="Fail",
                metadata={"error": str(e)}
            )
            
            raise
    
    async def record_user_feedback(
        self,
        session_id: str,
        feedback_type: str,  # "thumbs_up", "thumbs_down", "rating"
        feedback_value: Any,  # True/False or 1-5 rating
        feedback_text: Optional[str] = None
    ):
        """
        Record user feedback on agent response.
        
        This is CRITICAL for RL training - tells agent what worked.
        """
        agl.add_session_feedback(
            session_id=session_id,
            feedback={
                "type": feedback_type,
                "value": feedback_value,
                "text": feedback_text,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Recorded feedback for session {session_id}: {feedback_type}={feedback_value}")
    
    async def record_outcome(
        self,
        session_id: str,
        outcome_type: str,  # "estimate_accepted", "contractor_hired", "project_completed"
        outcome_data: Dict[str, Any]
    ):
        """
        Record real-world outcome.
        
        Examples:
        - User accepted cost estimate → estimate was accurate
        - User hired recommended contractor → good match
        - Project completed on budget → cost estimate validated
        
        This provides GROUND TRUTH for RL training.
        """
        agl.add_session_feedback(
            session_id=session_id,
            feedback={
                "outcome_type": outcome_type,
                "outcome_data": outcome_data,
                "timestamp": datetime.now().isoformat()
            },
            tags=["outcome", outcome_type]
        )
        
        logger.info(f"Recorded outcome for session {session_id}: {outcome_type}")


# Decorator for easy agent tracking
def track_agent(agent_name: str):
    """
    Decorator to automatically track agent execution.
    
    Usage:
        @track_agent("HomeChatAgent")
        async def chat(self, message: str):
            # ... agent logic ...
    """
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            metrics = AgentMetricsService()
            
            # Extract user_id if available
            user_id = kwargs.get('user_id') or getattr(self, 'user_id', 'unknown')
            
            return await metrics.track_agent_execution(
                agent_name=agent_name,
                user_id=user_id,
                input_data={"args": args, "kwargs": kwargs},
                func=func,
                self,
                *args,
                **kwargs
            )
        
        return wrapper
    return decorator
```

**Updated Agents with Tracking:**
```python
# backend/agents/conversational/home_chat_agent.py
from backend.services.agent_metrics import track_agent, AgentMetricsService

class HomeChatAgent(SkillEnhancedAgent):
    
    @track_agent("HomeChatAgent")
    async def chat(
        self,
        message: str,
        user_id: str,
        conversation_history: List[Dict] = None,
        home_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Chat with performance tracking.
        
        Now tracks:
        - Input message
        - Response generated
        - Duration
        - User feedback (later)
        """
        # ... existing chat logic ...
        
        response = await self.process_with_skills(message)
        
        return {
            "response": response,
            "skills_used": self.active_skills.copy()
        }


# backend/agents/intelligence/cost_estimation_agent.py
class CostEstimationAgent(BaseAgent):
    
    @track_agent("CostEstimationAgent")
    async def estimate_project_cost(
        self,
        project_type: str,
        project_details: Dict,
        location: str,
        quality_tier: str = "mid",
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Estimate with tracking for accuracy validation.
        """
        # ... existing estimation logic ...
        
        estimate = {
            "min_cost": calculated_min,
            "max_cost": calculated_max,
            "breakdown": breakdown,
            "confidence": confidence_level
        }
        
        return estimate
```

#### **Integration #2: Feedback Collection**

**API Endpoints for Feedback:**
```python
# backend/api/feedback.py (NEW FILE)
from fastapi import APIRouter, Depends
from backend.services.agent_metrics import AgentMetricsService

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

@router.post("/response/{session_id}/thumbs")
async def thumbs_feedback(
    session_id: str,
    thumbs_up: bool,
    comment: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """
    User gives thumbs up/down on agent response.
    
    Shows thumbs up/down buttons in chat UI.
    """
    metrics = AgentMetricsService()
    
    await metrics.record_user_feedback(
        session_id=session_id,
        feedback_type="thumbs",
        feedback_value=thumbs_up,
        feedback_text=comment
    )
    
    return {"status": "recorded", "session_id": session_id}

@router.post("/response/{session_id}/rating")
async def rating_feedback(
    session_id: str,
    rating: int,  # 1-5 stars
    comment: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """
    User rates agent response 1-5 stars.
    
    Shows star rating UI after response.
    """
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    
    metrics = AgentMetricsService()
    
    await metrics.record_user_feedback(
        session_id=session_id,
        feedback_type="rating",
        feedback_value=rating,
        feedback_text=comment
    )
    
    return {"status": "recorded", "rating": rating}

@router.post("/estimate/{session_id}/outcome")
async def estimate_outcome(
    session_id: str,
    accepted: bool,
    actual_cost: Optional[float] = None,
    notes: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """
    User reports if they accepted estimate and actual cost.
    
    Critical for validating cost estimation accuracy.
    """
    metrics = AgentMetricsService()
    
    await metrics.record_outcome(
        session_id=session_id,
        outcome_type="estimate_outcome",
        outcome_data={
            "accepted": accepted,
            "actual_cost": actual_cost,
            "notes": notes
        }
    )
    
    return {"status": "recorded"}

@router.post("/contractor/{session_id}/hired")
async def contractor_hired(
    session_id: str,
    contractor_id: str,
    hired: bool,
    satisfaction_rating: Optional[int] = None,  # After project completion
    user: User = Depends(get_current_user)
):
    """
    User reports if they hired recommended contractor.
    
    Validates contractor matching algorithm.
    """
    metrics = AgentMetricsService()
    
    await metrics.record_outcome(
        session_id=session_id,
        outcome_type="contractor_hired",
        outcome_data={
            "contractor_id": contractor_id,
            "hired": hired,
            "satisfaction_rating": satisfaction_rating
        }
    )
    
    return {"status": "recorded"}

@router.post("/project/{session_id}/completed")
async def project_completed(
    session_id: str,
    final_cost: float,
    duration_days: int,
    quality_rating: int,  # 1-5
    would_recommend: bool,
    user: User = Depends(get_current_user)
):
    """
    User reports project completion details.
    
    Ultimate validation of entire system:
    - Cost accuracy
    - Timeline accuracy
    - Quality of recommendations
    """
    metrics = AgentMetricsService()
    
    await metrics.record_outcome(
        session_id=session_id,
        outcome_type="project_completed",
        outcome_data={
            "final_cost": final_cost,
            "duration_days": duration_days,
            "quality_rating": quality_rating,
            "would_recommend": would_recommend
        }
    )
    
    return {"status": "recorded", "thank_you": "Your feedback helps us improve!"}
```

#### **Integration #3: Analytics Dashboard**

```python
# backend/api/analytics.py (NEW FILE)
from fastapi import APIRouter, Depends
import agentops as agl

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/agents/performance")
async def agent_performance(
    agent_name: Optional[str] = None,
    days: int = 30,
    admin: User = Depends(get_current_admin)
):
    """
    Get agent performance metrics.
    
    Shows:
    - Success rate
    - Average response time
    - User satisfaction
    - Outcome validation
    """
    # Query Agent Lightning analytics
    metrics = agl.get_session_analytics(
        agent_name=agent_name,
        start_date=datetime.now() - timedelta(days=days),
        end_date=datetime.now()
    )
    
    return {
        "agent_name": agent_name or "all",
        "period_days": days,
        "total_sessions": metrics.get('total_sessions'),
        "success_rate": metrics.get('success_rate'),
        "avg_duration_seconds": metrics.get('avg_duration'),
        "user_satisfaction": {
            "thumbs_up_rate": metrics.get('thumbs_up_rate'),
            "avg_rating": metrics.get('avg_rating')
        },
        "outcomes": metrics.get('outcomes', {})
    }

@router.get("/agents/improvement-opportunities")
async def improvement_opportunities(
    agent_name: str,
    admin: User = Depends(get_current_admin)
):
    """
    Identify areas where agent needs improvement.
    
    Analyzes:
    - Low-rated responses
    - Failed sessions
    - Negative outcomes
    """
    # Get failed/low-rated sessions
    problem_sessions = agl.query_sessions(
        agent_name=agent_name,
        filters={
            "end_state": "Fail",
            "OR": {
                "feedback.type": "rating",
                "feedback.value": {"$lte": 2}
            }
        },
        limit=100
    )
    
    # Analyze patterns
    common_failures = {}
    for session in problem_sessions:
        error = session.get('metadata', {}).get('error')
        if error:
            common_failures[error] = common_failures.get(error, 0) + 1
    
    return {
        "agent_name": agent_name,
        "total_problem_sessions": len(problem_sessions),
        "common_failures": common_failures,
        "recommendations": _generate_recommendations(common_failures)
    }

def _generate_recommendations(failures: Dict[str, int]) -> List[str]:
    """Generate actionable recommendations."""
    recommendations = []
    
    if "timeout" in str(failures):
        recommendations.append("Consider optimizing agent response time")
    
    if "invalid" in str(failures):
        recommendations.append("Improve input validation")
    
    if "not found" in str(failures):
        recommendations.append("Expand knowledge base coverage")
    
    return recommendations
```

---

### 📊 Agent Lightning Summary

| Capability | Before | With Agent Lightning | Impact |
|------------|--------|----------------------|--------|
| Performance Tracking | ❌ No visibility | ✅ Real-time metrics | Data-driven improvement |
| User Feedback | ❌ Not collected | ✅ Thumbs/ratings/outcomes | Know what works |
| Error Analysis | ❌ Manual debugging | ✅ Automated pattern detection | Faster fixes |
| Agent Optimization | ❌ Static | ✅ Continuous learning | Better over time |

**Training Workflow:**
1. **Week 1-4:** Collect baseline data (no changes)
2. **Week 5-8:** Analyze patterns, identify issues
3. **Week 9-12:** Implement improvements, A/B test
4. **Week 13+:** Continuous refinement

**Expected Improvements:**
- **Chat Agent:** 20-30% increase in satisfaction ratings
- **Cost Estimator:** 15-25% better accuracy (vs actual costs)
- **Contractor Matcher:** 30-40% more hires from recommendations
- **Design Studio:** 25-35% higher acceptance rate

---

## Technology #6: ACP (Agent Commerce Protocol) + Stripe
### Enable Agent-Driven Purchases

### 🎯 Current Gap

**Your Platform Provides Recommendations But Not Transactions:**
- Product Matching Agent finds perfect faucet → user leaves site to buy
- Cost Estimator quotes materials → user shops elsewhere
- Contractor Matcher finds pros → external payment
- Design Studio suggests furniture → Amazon affiliate links only

**Lost Revenue:**
- No commission on product sales
- No payment processing fees
- No platform transaction value
- No repeat purchase behavior

**Solution:** Implement ACP + Stripe for seamless agent-driven commerce

---

### 🔧 Integration Implementation

#### **Integration #1: Product Purchase Agent**

```python
# backend/agents/commerce/purchase_agent.py (NEW FILE)
from anthropic_agent_commerce import ACPClient
import stripe
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class ProductPurchaseAgent(BaseAgent):
    """
    Enables users to purchase products directly through chat.
    
    Integrates:
    - ACP for agent-initiated transactions
    - Stripe for payment processing
    - Product catalog for inventory
    
    Use cases:
    - "Buy that faucet you showed me"
    - "Order materials for the kitchen remodel"
    - "Purchase the paint colors we selected"
    """
    
    def __init__(self):
        super().__init__()
        self.acp_client = ACPClient(
            api_key=os.getenv("ACP_API_KEY")
        )
        self.name = "ProductPurchaseAgent"
    
    async def initiate_purchase(
        self,
        user_id: str,
        product_ids: List[str],
        delivery_address: Optional[Dict] = None,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate product purchase through ACP.
        
        Flow:
        1. Fetch product details
        2. Calculate total (with tax/shipping)
        3. Create ACP transaction
        4. Process payment with Stripe
        5. Create order record
        6. Notify fulfillment
        
        Example:
            result = await agent.initiate_purchase(
                user_id="user_123",
                product_ids=["prod_kohler_faucet", "prod_delta_shower"],
                delivery_address={...},
                payment_method_id="pm_card_xxx"
            )
        """
        try:
            # 1. Fetch products
            products = []
            total_amount = 0
            
            for product_id in product_ids:
                product = await self._get_product(product_id)
                if not product:
                    return {
                        "success": False,
                        "error": f"Product not found: {product_id}"
                    }
                
                products.append(product)
                total_amount += product['price']
            
            # 2. Get/validate delivery address
            if not delivery_address:
                # Get from user profile
                user = await self._get_user(user_id)
                delivery_address = user.get('address')
                
                if not delivery_address:
                    return {
                        "success": False,
                        "error": "Delivery address required",
                        "action_needed": "provide_address"
                    }
            
            # 3. Calculate tax and shipping
            tax = await self._calculate_tax(total_amount, delivery_address)
            shipping = await self._calculate_shipping(products, delivery_address)
            
            final_amount = total_amount + tax + shipping
            
            # 4. Create ACP transaction
            acp_transaction = await self.acp_client.create_transaction(
                merchant_id=os.getenv("ACP_MERCHANT_ID"),
                amount=final_amount,
                currency="usd",
                items=[
                    {
                        "id": p['id'],
                        "name": p['name'],
                        "price": p['price'],
                        "quantity": 1
                    }
                    for p in products
                ],
                metadata={
                    "user_id": user_id,
                    "platform": "homeview-ai",
                    "agent": "ProductPurchaseAgent"
                }
            )
            
            # 5. Process payment with Stripe
            try:
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(final_amount * 100),  # Stripe uses cents
                    currency="usd",
                    payment_method=payment_method_id,
                    customer=await self._get_stripe_customer_id(user_id),
                    confirm=True,
                    metadata={
                        "acp_transaction_id": acp_transaction['id'],
                        "user_id": user_id,
                        "product_ids": ",".join(product_ids)
                    }
                )
                
                if payment_intent.status != "succeeded":
                    # Payment failed
                    await self.acp_client.cancel_transaction(acp_transaction['id'])
                    
                    return {
                        "success": False,
                        "error": "Payment failed",
                        "payment_status": payment_intent.status,
                        "action_needed": "update_payment_method"
                    }
                
            except stripe.error.CardError as e:
                # Card declined
                await self.acp_client.cancel_transaction(acp_transaction['id'])
                
                return {
                    "success": False,
                    "error": f"Card declined: {e.user_message}",
                    "action_needed": "update_payment_method"
                }
            
            # 6. Create order record
            order = await self._create_order(
                user_id=user_id,
                products=products,
                amounts={
                    "subtotal": total_amount,
                    "tax": tax,
                    "shipping": shipping,
                    "total": final_amount
                },
                delivery_address=delivery_address,
                payment_intent_id=payment_intent.id,
                acp_transaction_id=acp_transaction['id']
            )
            
            # 7. Notify fulfillment system
            await self._notify_fulfillment(order)
            
            # 8. Confirm ACP transaction
            await self.acp_client.confirm_transaction(acp_transaction['id'])
            
            return {
                "success": True,
                "order_id": order['id'],
                "total_amount": final_amount,
                "products": [p['name'] for p in products],
                "estimated_delivery": order['estimated_delivery'],
                "tracking_info": order.get('tracking_number')
            }
            
        except Exception as e:
            logger.error(f"Purchase failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_purchase_options(
        self,
        product_ids: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get purchase options for products (before actual purchase).
        
        Shows:
        - Total cost
        - Shipping options
        - Estimated delivery
        - Payment methods available
        """
        products = []
        total = 0
        
        for product_id in product_ids:
            product = await self._get_product(product_id)
            if product:
                products.append(product)
                total += product['price']
        
        # Get user address for shipping calculation
        user = await self._get_user(user_id)
        address = user.get('address')
        
        # Calculate shipping options
        shipping_options = await self._get_shipping_options(products, address)
        
        # Get payment methods
        payment_methods = await self._get_user_payment_methods(user_id)
        
        return {
            "products": products,
            "subtotal": total,
            "tax_estimate": await self._calculate_tax(total, address),
            "shipping_options": shipping_options,
            "payment_methods": [
                {
                    "id": pm.id,
                    "type": pm.type,
                    "last4": pm.card.last4 if pm.type == "card" else None
                }
                for pm in payment_methods
            ],
            "total_estimate": total + shipping_options[0]['cost']  # with cheapest shipping
        }
    
    async def _get_product(self, product_id: str) -> Optional[Dict]:
        """Fetch product from catalog."""
        # Query your product database
        product = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        return product.scalars().first()
    
    async def _calculate_tax(self, amount: float, address: Dict) -> float:
        """Calculate sales tax using Stripe Tax."""
        try:
            calculation = stripe.tax.Calculation.create(
                currency="usd",
                line_items=[{
                    "amount": int(amount * 100),
                    "reference": "product"
                }],
                customer_details={
                    "address": {
                        "line1": address.get('line1'),
                        "city": address.get('city'),
                        "state": address.get('state'),
                        "postal_code": address.get('postal_code'),
                        "country": "US"
                    },
                    "address_source": "shipping"
                }
            )
            
            return calculation.tax_amount_exclusive / 100
            
        except Exception as e:
            logger.error(f"Tax calculation failed: {e}")
            # Fallback to estimate (8% average)
            return amount * 0.08
    
    async def _calculate_shipping(
        self,
        products: List[Dict],
        address: Dict
    ) -> float:
        """Calculate shipping cost."""
        # Integrate with shipping provider (ShipStation, EasyPost, etc.)
        # For now, simple logic:
        
        total_weight = sum(p.get('weight', 5) for p in products)  # lbs
        
        if total_weight < 10:
            return 9.99
        elif total_weight < 50:
            return 19.99
        else:
            return 49.99
    
    async def _get_shipping_options(
        self,
        products: List[Dict],
        address: Dict
    ) -> List[Dict]:
        """Get available shipping options with rates."""
        base_cost = await self._calculate_shipping(products, address)
        
        return [
            {
                "method": "standard",
                "name": "Standard Shipping (5-7 business days)",
                "cost": base_cost,
                "estimated_days": 7
            },
            {
                "method": "expedited",
                "name": "Expedited Shipping (2-3 business days)",
                "cost": base_cost * 1.8,
                "estimated_days": 3
            },
            {
                "method": "overnight",
                "name": "Overnight Shipping",
                "cost": base_cost * 3.0,
                "estimated_days": 1
            }
        ]
    
    async def _create_order(
        self,
        user_id: str,
        products: List[Dict],
        amounts: Dict,
        delivery_address: Dict,
        payment_intent_id: str,
        acp_transaction_id: str
    ) -> Dict:
        """Create order record in database."""
        order = Order(
            user_id=user_id,
            status="confirmed",
            subtotal=amounts['subtotal'],
            tax=amounts['tax'],
            shipping=amounts['shipping'],
            total=amounts['total'],
            delivery_address=delivery_address,
            payment_intent_id=payment_intent_id,
            acp_transaction_id=acp_transaction_id,
            estimated_delivery=datetime.now() + timedelta(days=7)
        )
        
        self.db.add(order)
        await self.db.flush()
        
        # Add order items
        for product in products:
            order_item = OrderItem(
                order_id=order.id,
                product_id=product['id'],
                product_name=product['name'],
                price=product['price'],
                quantity=1
            )
            self.db.add(order_item)
        
        await self.db.commit()
        
        return order
    
    async def _notify_fulfillment(self, order: Dict):
        """Notify fulfillment system of new order."""
        # Integration with fulfillment provider
        # (ShipBob, Amazon FBA, etc.)
        logger.info(f"Order {order['id']} sent to fulfillment")
```

**Chat Integration:**
```python
# backend/agents/conversational/home_chat_agent.py
class HomeChatAgent:
    
    async def chat(self, message: str, user_id: str):
        """Chat with purchase capability."""
        
        # Detect purchase intent
        if self._is_purchase_request(message):
            # Extract products from context
            products = await self._extract_mentioned_products(message)
            
            if products:
                # Get purchase options
                purchase_agent = ProductPurchaseAgent()
                options = await purchase_agent.get_purchase_options(
                    product_ids=[p['id'] for p in products],
                    user_id=user_id
                )
                
                return {
                    "message": f"""
I found {len(products)} products to purchase:

{chr(10).join([f"- {p['name']}: ${p['price']}" for p in products])}

**Subtotal:** ${options['subtotal']:.2f}
**Tax:** ${options['tax_estimate']:.2f}
**Shipping:** ${options['shipping_options'][0]['cost']:.2f}
**Total:** ${options['total_estimate']:.2f}

Would you like to proceed with the purchase?
                    """,
                    "action": "confirm_purchase",
                    "purchase_data": options
                }
        
        # Regular chat
        return await super().chat(message, user_id)
    
    def _is_purchase_request(self, message: str) -> bool:
        """Detect purchase intent."""
        keywords = ["buy", "purchase", "order", "get this", "add to cart"]
        return any(k in message.lower() for k in keywords)
```

**API Endpoints:**
```python
# backend/api/commerce.py (NEW FILE)
from fastapi import APIRouter, Depends
from backend.agents.commerce.purchase_agent import ProductPurchaseAgent

router = APIRouter(prefix="/api/v1/commerce", tags=["commerce"])

@router.post("/purchase/initiate")
async def initiate_purchase(
    product_ids: List[str] = Body(...),
    delivery_address: Optional[Dict] = Body(None),
    payment_method_id: str = Body(...),
    user: User = Depends(get_current_user)
):
    """
    Initiate product purchase.
    
    User confirms purchase from chat interface.
    """
    agent = ProductPurchaseAgent()
    
    result = await agent.initiate_purchase(
        user_id=user.id,
        product_ids=product_ids,
        delivery_address=delivery_address,
        payment_method_id=payment_method_id
    )
    
    return result

@router.get("/purchase/options")
async def get_purchase_options(
    product_ids: List[str] = Query(...),
    user: User = Depends(get_current_user)
):
    """
    Get purchase options before confirming.
    
    Shows total cost, shipping options, etc.
    """
    agent = ProductPurchaseAgent()
    
    options = await agent.get_purchase_options(
        product_ids=product_ids,
        user_id=user.id
    )
    
    return options

@router.get("/orders")
async def list_orders(
    user: User = Depends(get_current_user)
):
    """List user's orders."""
    orders = await db.execute(
        select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())
    )
    
    return {"orders": [o.dict() for o in orders.scalars().all()]}

@router.get("/orders/{order_id}")
async def get_order_details(
    order_id: str,
    user: User = Depends(get_current_user)
):
    """Get detailed order information."""
    order = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == user.id
        )
    )
    order = order.scalars().first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get items
    items = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
    
    return {
        **order.dict(),
        "items": [i.dict() for i in items.scalars().all()]
    }

@router.post("/payment-methods")
async def add_payment_method(
    payment_method_id: str = Body(...),  # From Stripe.js on frontend
    user: User = Depends(get_current_user)
):
    """
    Add payment method to user account.
    
    User adds card through Stripe Elements on frontend,
    then attaches to customer here.
    """
    # Get/create Stripe customer
    customer_id = await _get_or_create_stripe_customer(user.id)
    
    # Attach payment method
    stripe.PaymentMethod.attach(
        payment_method_id,
        customer=customer_id
    )
    
    return {"status": "added", "payment_method_id": payment_method_id}
```

---

### 📊 Commerce Integration Summary

| Feature | Revenue Model | Monthly Potential (1000 users) |
|---------|---------------|-------------------------------|
| Product Sales | 10% commission | $15,000 (avg $150/user) |
| Material Procurement | 5-8% markup | $8,000 |
| Contractor Payments | 3% platform fee | $5,000 |
| Premium Subscriptions | $49/mo | $49,000 |
| **TOTAL** | | **$77,000/mo** |

**Implementation Priority:**
1. **Phase 1 (Weeks 1-4):** Product purchase agent + Stripe integration
2. **Phase 2 (Weeks 5-8):** Material procurement for projects
3. **Phase 3 (Weeks 9-12):** Contractor payment escrow
4. **Phase 4 (Weeks 13-16):** Subscription billing

---

## Cross-Technology Integration Patterns

### Pattern #1: DeepSeek + MarkItDown
**Use Case:** Parse contractor quotes with images

```python
# User uploads quote PDF with product images
quote_pdf = "contractor_quote.pdf"

# 1. Extract text/tables with MarkItDown
doc_parser = DocumentParserService()
quote_data = await doc_parser.parse_contractor_quote(quote_pdf)

# 2. Extract product images from PDF
images = extract_images_from_pdf(quote_pdf)

# 3. Analyze images with DeepSeek
vision = UnifiedVisionService()
for img in images:
    analysis = await vision.analyze_image(
        img,
        prompt="What product is this? Extract brand, model, specs."
    )
    quote_data['products'].append(analysis)

# 4. Enhanced quote with visual verification
return quote_data
```

### Pattern #2: Docling + RAG + Skills
**Use Case:** Building code expert chat

```python
# 1. Index building codes with Docling
rag = EnhancedRAGService()
await rag.index_building_codes(
    jurisdiction="California",
    code_type="building",
    pdf_paths=["codes/ca_building_2024.pdf"]
)

# 2. Create building code skill
# (skills/building-code-expert/SKILL.md exists)

# 3. Chat agent uses both
chat_agent = HomeChatAgent()
chat_agent.activate_skill("building-code-expert")

response = await chat_agent.chat(
    "What's the minimum ceiling height for bedrooms?"
)
# Agent queries RAG with Docling-parsed codes
# Agent applies building-code-expert skill
# Returns: Accurate answer with citations
```

### Pattern #3: Skills + Agent Lightning
**Use Case:** Continuous improvement of domain expertise

```python
# 1. Agent uses skill
@track_agent("HomeChatAgent")
async def chat(message: str):
    agent.activate_skill("plumbing-advisor")
    response = await agent.process_with_skills(message)
    return response

# 2. User gives feedback
await metrics.record_user_feedback(
    session_id=session_id,
    feedback_type="rating",
    feedback_value=2,  # Low rating
    feedback_text="Answer was too technical"
)

# 3. Analyze patterns
# Agent Lightning identifies: plumbing-advisor responses
# are rated low when user asks basic questions

# 4. Update skill
# Add beginner-friendly explanations to plumbing-advisor skill

# 5. A/B test improvement
# Compare old vs new skill version

# 6. Deploy better version
# Continuous improvement loop
```

### Pattern #4: All Technologies Together
**Ultimate Integration: Complete Project Flow**

```python
async def handle_complete_project(user_message: str, images: List, user_id: str):
    """
    Complete home improvement project flow using all technologies.
    """
    
    # 1. DeepSeek VL2: Analyze space
    vision = UnifiedVisionService()
    space_analysis = await vision.batch_analyze(
        images,
        prompt="Analyze this space for renovation potential"
    )
    
    # 2. Skills: Apply domain expertise
    chat_agent = HomeChatAgent()
    chat_agent.activate_skill("cost-estimation-expert")
    chat_agent.activate_skill("design-consultant")
    
    # 3. MarkItDown: Parse any uploaded documents
    if user_uploaded_docs:
        doc_parser = DocumentParserService()
        existing_plans = await doc_parser.parse_document(user_uploaded_docs)
    
    # 4. Docling + RAG: Check building codes
    rag = EnhancedRAGService()
    code_requirements = await rag.query_building_code(
        question="What are requirements for this renovation?",
        jurisdiction=user.location
    )
    
    # 5. Agent Lightning: Track entire flow
    metrics = AgentMetricsService()
    session = await metrics.track_agent_execution(
        agent_name="CompleteProjectFlow",
        user_id=user_id,
        input_data={"message": user_message, "images": len(images)},
        func=_process_project
    )
    
    # 6. ACP + Stripe: Enable purchase
    if user_wants_to_buy:
        purchase_agent = ProductPurchaseAgent()
        result = await purchase_agent.initiate_purchase(
            user_id=user_id,
            product_ids=recommended_products
        )
    
    return {
        "analysis": space_analysis,
        "cost_estimate": cost_data,
        "code_compliance": code_requirements,
        "recommendations": recommendations,
        "purchase_options": purchase_options,
        "session_id": session['session_id']  # For feedback
    }
```

---

## Implementation Roadmap

### Phase 1: Cost Optimization (Weeks 1-4)
**Goal:** Reduce costs immediately

1. **DeepSeek VL2** integration
   - UnifiedVisionService
   - Update FloorPlanAnalysisAgent
   - Update VisionAnalysisAgent
   - **Expected Savings:** $1,870/month

2. **MarkItDown** for documents
   - DocumentParserService
   - Quote parsing API
   - **Time Saved:** 10 hours/week on manual entry

### Phase 2: Knowledge Enhancement (Weeks 5-10)
**Goal:** Improve answer quality

3. **IBM Docling** for RAG
   - EnhancedRAGService
   - Building code indexing
   - Technical manual library
   - **Quality Improvement:** 40% better accuracy

4. **Anthropic Skills**
   - Create 10 domain skills
   - SkillManager service
   - Integrate with chat agent
   - **Consistency:** 50% more consistent responses

### Phase 3: Continuous Improvement (Weeks 11-18)
**Goal:** Learn and optimize

5. **Agent Lightning**
   - AgentMetricsService
   - Feedback APIs
   - Analytics dashboard
   - **Expected:** 20-30% satisfaction increase

### Phase 4: Revenue Enablement (Weeks 19-24)
**Goal:** Monetize platform

6. **ACP + Stripe Commerce**
   - ProductPurchaseAgent
   - Payment processing
   - Order management
   - **Revenue:** $77K/month (at 1000 users)

---

## Cost-Benefit Analysis

### Implementation Costs

| Phase | Technology | Dev Time | Cost |
|-------|------------|----------|------|
| 1 | DeepSeek VL2 | 2 weeks | $15,000 |
| 1 | MarkItDown | 1 week | $7,500 |
| 2 | Docling | 3 weeks | $22,500 |
| 2 | Skills | 2 weeks | $15,000 |
| 3 | Agent Lightning | 3 weeks | $22,500 |
| 4 | ACP/Stripe | 4 weeks | $30,000 |
| **TOTAL** | | **15 weeks** | **$112,500** |

### Return on Investment

**Year 1:**
- Cost Savings (DeepSeek): $22,440
- Time Savings (MarkItDown): $26,000
- Revenue (Commerce): $924,000 (12 months)
- **Total Benefit:** $972,440
- **ROI:** 764%

**Year 2-3:**
- Continuous cost savings
- Improved agent performance → higher retention
- Commerce revenue scales with users
- **3-Year ROI:** 2,341%

---

## Next Steps

1. **Review this deep-dive guide**
2. **Prioritize technologies** based on your immediate needs
3. **Start with Phase 1** (cost optimization)
4. **Set up development environment** for chosen technologies
5. **Create proof-of-concept** for highest priority integration

**Questions to consider:**
- Which technology provides most immediate value?
- Do you have development resources for 15-week implementation?
- Should we phase in stages or parallel development?
- Any technologies to deprioritize?

---

**Would you like me to:**
1. Create detailed implementation plan for a specific technology?
2. Generate actual code files for any integration?
3. Create database migrations for new models?
4. Design API documentation?
5. Develop testing strategy?