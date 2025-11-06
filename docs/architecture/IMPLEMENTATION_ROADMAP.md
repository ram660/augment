# Implementation Roadmap - HomeVision AI Agentic Platform

## Phase 1: Foundation (Weeks 1-4)

### Week 1: Project Setup & Core Infrastructure

**Objectives:**
- Set up development environment
- Establish project structure
- Configure Gemini API integration
- Create base agent framework

**Tasks:**

1. **Initialize Project Structure**
```
homevision-ai/
├── backend/
│   ├── agents/              # All agent implementations
│   │   ├── base/           # Base agent classes
│   │   ├── homeowner/      # Homeowner-facing agents
│   │   ├── contractor/     # Contractor-facing agents
│   │   ├── marketplace/    # Marketplace agents
│   │   └── shared/         # Shared utility agents
│   ├── workflows/          # LangGraph workflow definitions
│   ├── models/             # Database models
│   ├── api/                # FastAPI routes
│   ├── services/           # Business logic services
│   ├── integrations/       # External API integrations
│   │   ├── gemini/        # Gemini API wrapper
│   │   ├── perplexity/    # Perplexity API (future)
│   │   ├── stripe/        # Payment processing
│   │   └── retailers/     # Retailer API integrations
│   └── utils/              # Shared utilities
├── frontend/               # React/Next.js frontend (future)
├── tests/                  # Test suites
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── docker/                 # Docker configurations
```

2. **Install Core Dependencies**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install langchain langgraph langchain-google-genai
pip install fastapi uvicorn pydantic pydantic-settings
pip install sqlalchemy alembic psycopg2-binary
pip install redis celery
pip install python-dotenv python-multipart
pip install pillow opencv-python scikit-image
pip install httpx aiohttp
pip install pytest pytest-asyncio
```

3. **Environment Configuration**
```env
# .env.example
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/homevision
REDIS_URL=redis://localhost:6379/0
STRIPE_SECRET_KEY=your_stripe_key_here
STRIPE_WEBHOOK_SECRET=your_webhook_secret_here
ENVIRONMENT=development
LOG_LEVEL=INFO
```

4. **Base Agent Framework**
- Create abstract `BaseAgent` class with LangChain integration
- Implement agent memory management
- Set up logging and monitoring
- Create agent registry for dynamic loading

**Deliverables:**
- ✅ Project structure initialized
- ✅ Dependencies installed and documented
- ✅ Environment configuration template
- ✅ Base agent classes implemented
- ✅ Gemini API integration tested

---

### Week 2: Database Schema & State Management

**Objectives:**
- Design and implement database schema
- Set up state management for agents
- Create data models for all entities

**Database Schema:**

```sql
-- Users (Homeowners & Contractors)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    user_type VARCHAR(20) NOT NULL, -- 'homeowner' or 'contractor'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Homeowner Profiles
CREATE TABLE homeowner_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    subscription_tier VARCHAR(20) DEFAULT 'free', -- 'free', 'premium'
    subscription_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Contractor Profiles
CREATE TABLE contractor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    business_name VARCHAR(255) NOT NULL,
    license_number VARCHAR(100),
    license_verified BOOLEAN DEFAULT FALSE,
    insurance_verified BOOLEAN DEFAULT FALSE,
    subscription_tier VARCHAR(20) DEFAULT 'solo_pro', -- 'solo_pro', 'growth', 'enterprise'
    subscription_expires_at TIMESTAMP,
    specialties JSONB, -- ['kitchen_remodel', 'bathroom', 'flooring']
    service_radius_km INTEGER DEFAULT 50,
    reputation_score DECIMAL(3,2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Homes (Digital Twin)
CREATE TABLE homes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    address JSONB NOT NULL, -- {street, city, province, postal_code, country}
    home_type VARCHAR(50), -- 'single_family', 'condo', 'townhouse', 'apartment'
    year_built INTEGER,
    square_footage INTEGER,
    num_bedrooms INTEGER,
    num_bathrooms DECIMAL(3,1),
    digital_twin_data JSONB, -- Comprehensive home profile
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Rooms (Part of Digital Twin)
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID REFERENCES homes(id) ON DELETE CASCADE,
    room_name VARCHAR(100) NOT NULL,
    room_type VARCHAR(50), -- 'kitchen', 'bathroom', 'bedroom', 'living_room'
    dimensions JSONB, -- {length, width, height, unit: 'feet'}
    floor_material VARCHAR(100),
    wall_color VARCHAR(100),
    ceiling_height DECIMAL(5,2),
    images JSONB, -- Array of image URLs
    created_at TIMESTAMP DEFAULT NOW()
);

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    homeowner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    home_id UUID REFERENCES homes(id) ON DELETE SET NULL,
    room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
    project_name VARCHAR(255) NOT NULL,
    project_type VARCHAR(100), -- 'kitchen_remodel', 'bathroom_renovation', 'flooring'
    status VARCHAR(50) DEFAULT 'planning', -- 'planning', 'quoted', 'in_progress', 'completed', 'cancelled'
    budget_min DECIMAL(10,2),
    budget_max DECIMAL(10,2),
    design_data JSONB, -- All design specifications
    rfp_generated BOOLEAN DEFAULT FALSE,
    rfp_document_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Design Versions (for collaboration)
CREATE TABLE design_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    created_by UUID REFERENCES users(id),
    design_snapshot JSONB, -- Complete design state
    render_urls JSONB, -- Array of render image URLs
    cost_estimate JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Contractor Quotes
CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    contractor_id UUID REFERENCES users(id) ON DELETE CASCADE,
    quote_amount DECIMAL(10,2) NOT NULL,
    timeline_days INTEGER,
    quote_document_url TEXT,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'accepted', 'rejected', 'withdrawn'
    materials_breakdown JSONB,
    labor_breakdown JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Contracts & Milestones
CREATE TABLE contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    quote_id UUID REFERENCES quotes(id) ON DELETE SET NULL,
    contractor_id UUID REFERENCES users(id) ON DELETE CASCADE,
    homeowner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    total_amount DECIMAL(10,2) NOT NULL,
    escrow_amount DECIMAL(10,2) DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'disputed', 'cancelled'
    start_date DATE,
    expected_completion_date DATE,
    actual_completion_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID REFERENCES contracts(id) ON DELETE CASCADE,
    milestone_name VARCHAR(255) NOT NULL,
    milestone_order INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'verified', 'paid'
    due_date DATE,
    completion_date DATE,
    verification_photos JSONB,
    ai_verification_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent Conversations (for context retention)
CREATE TABLE agent_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    conversation_history JSONB, -- Array of messages
    context_summary TEXT, -- AI-generated summary
    last_interaction_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Product Catalog (cached from retailers)
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    retailer VARCHAR(100) NOT NULL,
    sku VARCHAR(255) NOT NULL,
    product_name VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    price DECIMAL(10,2),
    image_url TEXT,
    product_url TEXT,
    dimensions JSONB,
    style_tags JSONB, -- ['modern', 'farmhouse', 'industrial']
    embedding VECTOR(1536), -- For semantic search
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(retailer, sku)
);

-- Indexes for performance
CREATE INDEX idx_projects_homeowner ON projects(homeowner_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_quotes_project ON quotes(project_id);
CREATE INDEX idx_quotes_contractor ON quotes(contractor_id);
CREATE INDEX idx_contracts_status ON contracts(status);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_retailer ON products(retailer);
```

**State Management:**
- Implement Redis-based session storage for agent conversations
- Create state serialization/deserialization utilities
- Set up conversation memory with LangChain

**Deliverables:**
- ✅ Database schema implemented with migrations
- ✅ SQLAlchemy models created
- ✅ Redis state management configured
- ✅ Data validation with Pydantic models

---

### Week 3: Core Agent Implementation (Part 1)

**Objectives:**
- Implement foundational agents
- Create Gemini integration wrapper
- Build first LangGraph workflow

**Agents to Implement:**

1. **Conversation & Context Agent**
   - Natural language understanding
   - Intent classification
   - Context retention across sessions
   - Routing to specialist agents

2. **Vision & Analysis Agent**
   - Room dimension extraction
   - Style classification
   - Product identification
   - Quality metrics calculation

3. **Design Orchestrator Agent**
   - Coordinate design workflows
   - Manage design state
   - Handle version control

**Gemini Integration:**
```python
# backend/integrations/gemini/client.py
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from google.generativeai import configure, GenerativeModel
import google.generativeai as genai

class GeminiClient:
    def __init__(self, api_key: str):
        configure(api_key=api_key)
        
        # Text models
        self.flash_text = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.7
        )
        
        self.thinking = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-thinking-exp",
            temperature=0.3
        )
        
        # Vision model
        self.vision = GenerativeModel("gemini-2.0-flash-exp")
        
        # Image generation
        self.image_gen = GenerativeModel("gemini-2.0-flash-exp")
        
        # Embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004"
        )
    
    async def analyze_image(self, image_path: str, prompt: str):
        """Analyze image with vision model"""
        # Implementation
        pass
    
    async def generate_image(self, prompt: str, reference_image=None):
        """Generate or edit images"""
        # Implementation
        pass
```

**First Workflow: Simple Design Request**
```python
# backend/workflows/design_request.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional

class DesignRequestState(TypedDict):
    user_id: str
    user_message: str
    room_images: List[str]
    design_intent: Optional[dict]
    room_analysis: Optional[dict]
    conversation_history: List[dict]
    response: Optional[str]

async def parse_intent(state: DesignRequestState):
    # Use Conversation Agent to understand request
    pass

async def analyze_room(state: DesignRequestState):
    # Use Vision Agent to analyze uploaded images
    pass

async def generate_response(state: DesignRequestState):
    # Synthesize response for user
    pass

# Build workflow
workflow = StateGraph(DesignRequestState)
workflow.add_node("parse_intent", parse_intent)
workflow.add_node("analyze_room", analyze_room)
workflow.add_node("generate_response", generate_response)

workflow.add_edge("parse_intent", "analyze_room")
workflow.add_edge("analyze_room", "generate_response")
workflow.add_edge("generate_response", END)

workflow.set_entry_point("parse_intent")
design_request_app = workflow.compile()
```

**Deliverables:**
- ✅ Gemini client wrapper implemented
- ✅ 3 core agents built and tested
- ✅ First LangGraph workflow operational
- ✅ Unit tests for agents

---

### Week 4: API Layer & Testing

**Objectives:**
- Build FastAPI endpoints
- Implement authentication
- Create comprehensive tests
- Set up monitoring

**API Endpoints:**
```python
# backend/api/v1/design.py
from fastapi import APIRouter, Depends, UploadFile, File
from typing import List

router = APIRouter(prefix="/api/v1/design", tags=["design"])

@router.post("/analyze-room")
async def analyze_room(
    images: List[UploadFile] = File(...),
    user_id: str = Depends(get_current_user)
):
    """Analyze room from uploaded images"""
    pass

@router.post("/chat")
async def chat_with_agent(
    message: str,
    project_id: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Chat with AI assistant"""
    pass

@router.post("/generate-design")
async def generate_design(
    request: DesignRequest,
    user_id: str = Depends(get_current_user)
):
    """Generate design variations"""
    pass
```

**Deliverables:**
- ✅ FastAPI application structure
- ✅ Authentication & authorization
- ✅ API documentation (Swagger)
- ✅ Integration tests
- ✅ Monitoring setup (logging, metrics)

---

## Phase 2: Feature Development (Weeks 5-12)

### Weeks 5-6: Visual Search & Product Discovery
### Weeks 7-8: Cost Estimation & BOM Generation
### Weeks 9-10: Multi-Angle Rendering & Visualization
### Weeks 11-12: Digital Twin & Home Profile

---

## Phase 3: Marketplace & Collaboration (Weeks 13-20)

### Weeks 13-14: Contractor Matching & RFP Generation
### Weeks 15-16: Real-Time Collaboration
### Weeks 17-18: Payment & Escrow System
### Weeks 19-20: Reputation & Trust Systems

---

## Success Metrics

**Phase 1 (Foundation):**
- All core agents respond within 2 seconds
- 95%+ uptime for API endpoints
- Zero critical security vulnerabilities
- 80%+ test coverage

**Phase 2 (Features):**
- Design generation < 30 seconds
- Product search returns results in < 3 seconds
- Cost estimates within 15% accuracy
- User satisfaction > 4.0/5.0

**Phase 3 (Marketplace):**
- Contractor match quality > 80%
- Quote acceptance rate > 30%
- Payment processing 99.9% reliable
- Dispute rate < 5%


