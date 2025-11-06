# Agentic Workflow Architecture
## n8n-Style Automation for Home Improvement

---

## 🎯 Vision

Build an agentic automation platform where specialized AI agents collaborate in configurable workflows, similar to n8n automation tools. Each agent handles specific tasks and workflows can be composed to create end-to-end experiences for homeowners, DIY enthusiasts, and contractors.

---

## 🏗️ Core Architecture

### Workflow Orchestration Engine

**Similar to n8n's execution engine:**
- **Nodes** = Agents (specialized AI workers)
- **Edges** = Data flow between agents
- **Triggers** = User actions, scheduled events, webhooks
- **Workflows** = Pre-configured agent chains
- **State Management** = Shared context passed between agents

### Key Components

1. **Workflow Engine** - Orchestrates agent execution
2. **Agent Registry** - Manages all available agents
3. **Data Pipeline** - Handles data flow between agents
4. **State Store** - Persistent workflow state
5. **Event Bus** - Real-time agent communication

---

## 🤖 Agent Definitions

### 1. Data Collection Agent
**Purpose**: Extract accurate dimensional analysis from floor plans and home images

**Responsibilities**:
- Accept floor plans (PDF, images, CAD files)
- Accept home images (rooms, fixtures, appliances)
- Extract spatial data (dimensions, layout, geometry)
- Detect objects and materials
- Extract measurements using photogrammetry
- Store extracted data in Digital Twin Database
- Validate data quality and completeness

**Inputs**:
- Floor plan files (PDF, PNG, JPG, DWG)
- Home images (rooms, fixtures, appliances)
- User metadata (room names, location, etc.)

**Outputs**:
- Room dimensions (length, width, height, square footage)
- Object inventory (appliances, fixtures, furniture)
- Material specifications (flooring, walls, cabinets)
- Spatial relationships (adjacencies, traffic flow)
- 3D layout data

**Tools**:
- Gemini Vision API (spatial understanding)
- OCR for floor plans
- CAD file parsers
- Image processing (OpenCV, PIL)

**Database Schema**:
```sql
digital_twin_data:
  - user_id
  - room_id
  - room_type
  - dimensions (length, width, height)
  - floor_area
  - objects_detected (JSON)
  - materials (JSON)
  - measurements (JSON)
  - spatial_layout (JSON)
  - analysis_timestamp
  - data_quality_score
```

**Workflow Integration**:
- **Trigger**: User uploads images/floor plans
- **Action**: Analyze → Extract → Validate → Store
- **Next**: Can trigger Product Search, Designer, or DIY Agent

---

### 2. Product Search Agent
**Purpose**: Find products matching user needs and space constraints

**Responsibilities**:
- Search products based on room requirements
- Filter by dimensions, style, color, budget
- Match products to digital twin constraints
- Compare products across vendors
- Generate product recommendations
- Create product lists/baskets

**Inputs**:
- Room data from Digital Twin
- User preferences (style, budget, colors)
- Project requirements
- Search query (text or structured)

**Outputs**:
- Product recommendations (ranked list)
- Product details with compatibility check
- Price comparisons
- Availability status
- Alternative suggestions

**Tools**:
- Product catalog API
- Vector search (FAISS) for semantic matching
- Price comparison APIs
- Inventory APIs

**Database Schema**:
```sql
product_searches:
  - search_id
  - user_id
  - room_id
  - search_query
  - filters (JSON)
  - results (JSON)
  - timestamp

product_recommendations:
  - recommendation_id
  - user_id
  - room_id
  - product_id
  - relevance_score
  - reasoning
  - compatibility_status
```

**Workflow Integration**:
- **Trigger**: Digital Twin data ready OR user query
- **Action**: Search → Filter → Rank → Recommend
- **Next**: Can trigger Designer Agent (for design visualization) or Recommended Product Agent (for alternatives)

---

### 3. Designer Agent
**Purpose**: Generate design patterns, visualizations, and AI design features

**Responsibilities**:
- Generate design concepts based on room data
- Create virtual renderings/visualizations
- Suggest color schemes and material combinations
- Create floor plans and layouts
- Generate before/after comparisons
- Provide design style recommendations
- Create mood boards

**Inputs**:
- Room data from Digital Twin
- User style preferences
- Budget constraints
- Product selections

**Outputs**:
- Design concepts (multiple options)
- Rendered images (AI-generated)
- Color palette recommendations
- Material combinations
- Layout suggestions
- Mood boards
- Design documentation

**Tools**:
- Gemini Image Generation API
- Design libraries (color theory, material databases)
- 3D rendering engines (optional)
- Style matching algorithms

**Database Schema**:
```sql
design_concepts:
  - concept_id
  - user_id
  - room_id
  - design_type (color_scheme|layout|full_redesign)
  - concept_data (JSON)
  - generated_images (URLs)
  - style_tags
  - confidence_score

design_visualizations:
  - viz_id
  - concept_id
  - visualization_type (before_after|mood_board|layout)
  - image_url
  - metadata (JSON)
```

**Workflow Integration**:
- **Trigger**: Digital Twin data OR Product selections
- **Action**: Generate concepts → Render → Evaluate → Present
- **Next**: Can trigger DIY Agent (for implementation) or Product Search (for sourcing materials)

---

### 4. DIY Agent
**Purpose**: Transform DIY ideas into actionable documents with content and relevant images

**Responsibilities**:
- Generate step-by-step DIY guides
- Create project documentation (instructions, materials lists)
- Generate shopping lists from projects
- Create visual guides with images
- Provide tool recommendations
- Estimate project difficulty and time
- Generate safety checklists

**Inputs**:
- Project idea/description
- Room data (for context)
- User skill level
- Available tools
- Budget constraints

**Outputs**:
- Complete DIY guide (PDF/document)
- Step-by-step instructions
- Materials list with quantities
- Tool requirements
- Safety guidelines
- Visual references (images, diagrams)
- Time estimates
- Difficulty rating

**Tools**:
- Document generation (PDF, Markdown)
- Image generation for diagrams
- Knowledge base (DIY techniques, tips)
- Material calculation algorithms

**Database Schema**:
```sql
diy_projects:
  - project_id
  - user_id
  - room_id
  - project_name
  - project_type
  - difficulty_level
  - estimated_time
  - cost_estimate
  - guide_content (JSON/Markdown)
  - materials_list (JSON)
  - tools_required (JSON)
  - steps (JSON array)
  - generated_document_url
  - images (URLs)
```

**Workflow Integration**:
- **Trigger**: User requests DIY guide OR Designer Agent suggests DIY project
- **Action**: Research → Generate guide → Create document → Add images
- **Next**: Can trigger Recommended Product Agent (for material sourcing) or Product Search (for tools)

---

### 5. Recommended Product Agent
**Purpose**: Intelligent product recommendations based on context and user history

**Responsibilities**:
- Analyze user context (room, project, preferences)
- Recommend alternative products
- Suggest complementary products
- Personalize recommendations
- Update recommendations based on feedback
- Track recommendation performance

**Inputs**:
- Current product selections
- User preferences and history
- Room context
- Budget constraints
- Project goals

**Outputs**:
- Ranked product recommendations
- Alternative suggestions
- Complementary products
- Bundle recommendations
- Price optimization suggestions

**Tools**:
- Recommendation algorithms (collaborative filtering, content-based)
- User preference learning
- Price optimization algorithms
- Product relationship graphs

**Database Schema**:
```sql
product_recommendations:
  - recommendation_id
  - user_id
  - context_type (alternative|complementary|bundle)
  - base_product_id
  - recommended_products (JSON array)
  - reasoning
  - confidence_score
  - user_feedback

recommendation_history:
  - history_id
  - user_id
  - recommended_product_id
  - clicked (boolean)
  - purchased (boolean)
  - rating
  - feedback_text
```

**Workflow Integration**:
- **Trigger**: Product Search results OR Designer selections OR DIY material needs
- **Action**: Analyze context → Generate recommendations → Rank → Present
- **Next**: Can loop back to Product Search or Designer for refinement

---

## 🔄 Workflow Patterns

### Pattern 1: New User Onboarding
**Goal**: Collect and analyze user's home data

```
Trigger: User signs up
  ↓
Data Collection Agent
  - Upload floor plans/images
  - Extract dimensions
  - Build digital twin
  ↓
Store in Database
  ↓
Product Search Agent (optional)
  - Initial recommendations
  ↓
Welcome workflow complete
```

---

### Pattern 2: Design Exploration Workflow
**Goal**: Help user explore design options for their space

```
Trigger: User says "I want to redesign my kitchen"
  ↓
Data Collection Agent (if needed)
  - Verify/update room data
  ↓
Designer Agent
  - Generate design concepts
  - Create visualizations
  ↓
Product Search Agent
  - Find products matching designs
  ↓
Recommended Product Agent
  - Suggest alternatives/combinations
  ↓
User selects favorite
  ↓
DIY Agent (if DIY project)
  - Generate guide
  OR
Product Search Agent
  - Create shopping list
```

---

### Pattern 3: DIY Project Workflow
**Goal**: Transform idea into actionable DIY project

```
Trigger: User says "I want to build a bookshelf"
  ↓
Data Collection Agent
  - Get room dimensions
  ↓
DIY Agent
  - Generate project guide
  - Create materials list
  - Generate diagrams
  ↓
Recommended Product Agent
  - Find materials/products
  - Suggest tools
  ↓
Product Search Agent
  - Create shopping list
  - Check availability
  ↓
Deliver complete guide + shopping list
```

---

### Pattern 4: Contractor Collaboration Workflow
**Goal**: Connect homeowner with contractor using shared context

```
Trigger: Homeowner requests contractor help
  ↓
Data Collection Agent
  - Ensure digital twin is complete
  ↓
Designer Agent
  - Generate project specifications
  ↓
Contractor Agent (NEW - see below)
  - Create project scope
  - Generate RFP/requirements
  ↓
Marketplace Agent (existing)
  - Match contractors
  - Share digital twin data
  ↓
Contractor receives:
  - Digital twin data
  - Design concepts
  - Product recommendations
  - Project scope
```

---

### Pattern 5: Continuous Improvement Workflow
**Goal**: Learn from user interactions and improve recommendations

```
Trigger: User completes action (purchase, rating, etc.)
  ↓
Recommended Product Agent
  - Update user preferences
  - Learn from feedback
  ↓
Product Search Agent
  - Refine search algorithms
  ↓
Designer Agent
  - Improve design suggestions
  ↓
Store learnings in database
```

---

## 🧑‍💼 User Perspectives

### Homeowner Perspective

**Agents Most Useful**:
1. **Data Collection Agent** - "Set up my home profile"
2. **Designer Agent** - "Show me design options"
3. **Product Search Agent** - "Find products that fit"
4. **Recommended Product Agent** - "Suggest similar items"
5. **DIY Agent** - "Can I do this myself?"

**Typical Workflow**:
```
1. Upload home images → Data Collection Agent
2. Browse design ideas → Designer Agent
3. Explore products → Product Search Agent
4. Get recommendations → Recommended Product Agent
5. Decide on DIY → DIY Agent
6. Create shopping list → Product Search Agent
```

---

### DIY Enthusiast Perspective

**Agents Most Useful**:
1. **DIY Agent** - "Generate project guides"
2. **Product Search Agent** - "Find materials and tools"
3. **Data Collection Agent** - "Check if it fits my space"
4. **Designer Agent** - "Visualize the result"

**Typical Workflow**:
```
1. Describe project idea → DIY Agent
2. DIY Agent generates guide
3. DIY Agent creates materials list
4. Product Search Agent finds materials
5. Recommended Product Agent suggests alternatives
6. DIY Agent creates shopping list with links
```

---

### Contractor Perspective

**Agents Most Useful**:
1. **Data Collection Agent** - "Review client's space data"
2. **Designer Agent** - "Understand design intent"
3. **Product Search Agent** - "Source materials"
4. **Contractor Agent** - "Create proposals and estimates"

**New Agent Needed**: **Contractor Agent**
- Create detailed project specifications
- Generate material take-offs (MTO)
- Create proposals and quotes
- Generate installation guides
- Track project milestones

**Typical Workflow**:
```
1. Receive project request → Contractor Agent
2. Access client's digital twin → Data Collection Agent
3. Review design concepts → Designer Agent
4. Create material list → Product Search Agent
5. Generate proposal → Contractor Agent
6. Share proposal with client
```

---

## 🗄️ Database Schema

### Workflow Execution Tracking

```sql
workflows:
  - workflow_id (UUID)
  - workflow_name
  - workflow_type
  - workflow_definition (JSON) -- nodes, edges, triggers
  - created_by (user_id)
  - created_at
  - updated_at
  - is_active (boolean)

workflow_executions:
  - execution_id (UUID)
  - workflow_id
  - user_id
  - execution_state (pending|running|completed|failed)
  - start_time
  - end_time
  - execution_data (JSON) -- state at each step
  - error_logs (JSON)

workflow_nodes (agent executions):
  - node_id (UUID)
  - execution_id
  - agent_type
  - node_status (pending|running|completed|failed)
  - input_data (JSON)
  - output_data (JSON)
  - execution_time_ms
  - error_message
  - retry_count
```

---

## 🔧 Workflow Definition Format (JSON)

```json
{
  "workflow_id": "wf_123",
  "workflow_name": "Kitchen Redesign Workflow",
  "trigger": {
    "type": "user_action",
    "action": "redesign_kitchen"
  },
  "nodes": [
    {
      "node_id": "n1",
      "agent_type": "data_collection",
      "config": {
        "require_floor_plan": false,
        "min_images": 3
      },
      "inputs": ["user_id", "room_type"],
      "outputs": ["digital_twin_data"]
    },
    {
      "node_id": "n2",
      "agent_type": "designer",
      "config": {
        "design_types": ["color_scheme", "layout"],
        "num_concepts": 3
      },
      "inputs": ["digital_twin_data"],
      "depends_on": ["n1"],
      "outputs": ["design_concepts"]
    },
    {
      "node_id": "n3",
      "agent_type": "product_search",
      "config": {
        "max_results": 20,
        "filters": {}
      },
      "inputs": ["design_concepts", "digital_twin_data"],
      "depends_on": ["n2"],
      "outputs": ["product_recommendations"]
    },
    {
      "node_id": "n4",
      "agent_type": "recommended_product",
      "config": {
        "suggestion_types": ["alternatives", "complementary"]
      },
      "inputs": ["product_recommendations"],
      "depends_on": ["n3"],
      "outputs": ["final_recommendations"]
    }
  ],
  "edges": [
    {
      "from": "n1",
      "to": "n2",
      "condition": "digital_twin_data.quality_score > 0.7"
    },
    {
      "from": "n2",
      "to": "n3"
    },
    {
      "from": "n3",
      "to": "n4"
    }
  ]
}
```

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Workflow Orchestration Engine
- [ ] Agent Registry System
- [ ] Basic workflow execution
- [ ] State management
- [ ] Database schema setup

### Phase 2: Core Agents (Weeks 3-4)
- [ ] Data Collection Agent (enhance existing)
- [ ] Product Search Agent (enhance existing)
- [ ] Designer Agent (new)
- [ ] DIY Agent (new)
- [ ] Recommended Product Agent (enhance existing)

### Phase 3: Workflow Builder (Weeks 5-6)
- [ ] Visual workflow editor (like n8n UI)
- [ ] Workflow templates
- [ ] Workflow sharing
- [ ] Testing/debugging tools

### Phase 4: Advanced Features (Weeks 7-8)
- [ ] Contractor Agent
- [ ] Collaborative workflows (homeowner + contractor)
- [ ] Workflow analytics
- [ ] Performance optimization

---

## 📊 Agent Communication Patterns

### Synchronous (Sequential)
```
Agent A → Agent B → Agent C
Each waits for previous to complete
```

### Asynchronous (Parallel)
```
Agent A → Agent B
     ↓      ↓
   Agent C  Agent D
```

### Conditional Branching
```
Agent A → Condition Check
    ↓          ↓
Agent B    Agent C
```

### Loop Patterns
```
Agent A → Agent B → Agent C
   ↑                      ↓
   ←←←←←←←←←←←←←←←←←←←←←←←
```

---

## 🎨 Workflow Templates

### Template 1: "Quick Design Check"
```
Data Collection → Designer → Product Search
(Simple 3-node workflow for quick ideas)
```

### Template 2: "Complete DIY Project"
```
Data Collection → DIY Agent → Product Search → Recommended Products
(Full DIY workflow with material sourcing)
```

### Template 3: "Contractor Bid Request"
```
Data Collection → Designer → Contractor Agent → Marketplace
(Workflow for getting contractor proposals)
```

### Template 4: "Design Comparison"
```
Data Collection → Designer (parallel: 3 concepts) → User Selection → Product Search
(Create multiple design options in parallel)
```

---

## 🔐 Security & Privacy

- **User Data Isolation**: Each workflow execution is scoped to user_id
- **Digital Twin Privacy**: Contractors only see shared project data
- **Workflow Sharing**: Users can share workflows (public templates) but not execution data
- **Agent Permissions**: Each agent has defined data access scope

---

## 📈 Analytics & Monitoring

### Workflow Metrics
- Execution time per workflow
- Agent performance (success rate, latency)
- User engagement (workflows run, completions)
- Recommendation quality (click-through, conversion)

### Agent Metrics
- Each agent tracks:
  - Input/output sizes
  - Processing time
  - Error rates
  - Cache hit rates

---

## 🔮 Future Enhancements

1. **Scheduled Workflows**: "Remind me to check for new products every week"
2. **Webhook Triggers**: External systems can trigger workflows
3. **Custom Agents**: Users can create custom agents for specific needs
4. **Agent Marketplace**: Share and discover agent workflows
5. **Mobile App**: Run workflows from mobile device
6. **Voice Triggers**: "Hey assistant, redesign my kitchen"

---

## 📝 Next Steps

1. **Review this architecture** - Get feedback from team
2. **Prioritize agents** - Which agents to build first?
3. **Design workflow builder UI** - User-friendly workflow creation
4. **Build prototype** - Start with 2-3 agents and simple workflow
5. **Test with users** - Get feedback on workflow patterns
6. **Iterate** - Refine based on usage patterns

---

## 🤝 Integration with Existing System

This architecture integrates with your existing:
- ✅ `spatial_analysis.py` → **Data Collection Agent**
- ✅ `recommendation_engine.py` → **Recommended Product Agent**
- ✅ `product_service.py` → **Product Search Agent**
- ✅ `AgentOrchestrator` → **Workflow Engine Foundation**
- ✅ Digital Twin concept → **Database foundation**

**New Components Needed**:
- 🔨 **Designer Agent** (new)
- 🔨 **DIY Agent** (new)
- 🔨 **Contractor Agent** (new)
- 🔨 **Workflow Builder UI** (new)
- 🔨 **Workflow Definition System** (new)

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-27  
**Status**: Draft for Review


