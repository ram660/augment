# 📚 HomeVision AI - Documentation Index

**Last Updated:** 2025-11-01  
**Version:** 1.0

Welcome to the HomeVision AI documentation. This index provides a complete guide to all available documentation organized by category.

---

## 🚀 Quick Start

**New to the project?** Start here:

1. **[README.md](../README.md)** - Project overview and quick setup
2. **[Getting Started Guide](guides/GETTING_STARTED.md)** - Step-by-step developer onboarding
3. **[Gemini Model Configuration](guides/GEMINI_MODEL_CONFIGURATION.md)** - AI model setup

---

## 📂 Documentation Structure

```
docs/
├── business/           # Business strategy and planning
├── architecture/       # Technical architecture and design
├── guides/            # How-to guides and tutorials
└── reference/         # API reference and feature catalogs
```

---

## 💼 Business Documentation

### [business.md](business/business.md)
**Purpose:** Complete business plan and strategy  
**Contents:**
- Market analysis and opportunity
- Three-pillar platform strategy
- Revenue models and pricing
- Competitive advantages
- Go-to-market strategy
- Financial projections

**Audience:** Founders, investors, business stakeholders

---

### [problem-solving.md](business/problem-solving.md)
**Purpose:** Problem-solution framework  
**Contents:**
- Core problems in home improvement industry
- Solution pillars and approach
- Expected impact and KPIs
- Measurable outcomes

**Audience:** Product managers, stakeholders

---

## 🏗️ Architecture Documentation

### [ENHANCED_AGENTIC_ARCHITECTURE.md](architecture/ENHANCED_AGENTIC_ARCHITECTURE.md)
**Purpose:** Core multi-agent system architecture  
**Contents:**
- 15+ specialized AI agents
- Agent roles and capabilities
- LangGraph workflow patterns
- Technology stack
- Agent interaction patterns

**Audience:** Developers, architects, technical leads

---

### [IMPLEMENTATION_ROADMAP.md](architecture/IMPLEMENTATION_ROADMAP.md)
**Purpose:** 20-week phased development plan  
**Contents:**
- Week-by-week implementation schedule
- Complete database schema (SQL)
- Success metrics for each phase
- Technical milestones
- Resource allocation

**Audience:** Project managers, developers, technical leads

---

### [AGENTIC_WORKFLOW_ARCHITECTURE.md](architecture/AGENTIC_WORKFLOW_ARCHITECTURE.md)
**Purpose:** n8n-style workflow automation architecture  
**Contents:**
- Workflow orchestration engine design
- Agent definitions and responsibilities
- Data flow patterns
- Event-driven architecture
- Workflow composition patterns

**Audience:** Backend developers, workflow engineers

---

### [SYSTEM_ARCHITECTURE_DIAGRAMS.md](architecture/SYSTEM_ARCHITECTURE_DIAGRAMS.md)
**Purpose:** Visual system architecture and workflows  
**Contents:**
- Mermaid diagrams for all major workflows
- Database schema visualizations
- Agent communication patterns
- Integration points
- End-to-end user journeys

**Audience:** All technical team members, visual learners

---

## 📖 Guides

### [GETTING_STARTED.md](guides/GETTING_STARTED.md)
**Purpose:** Developer onboarding and setup  
**Contents:**
- Environment setup
- Installation instructions
- First agent tutorial
- Testing guide
- Common troubleshooting

**Audience:** New developers

---

### [GEMINI_MODEL_CONFIGURATION.md](guides/GEMINI_MODEL_CONFIGURATION.md)
**Purpose:** Complete guide to Gemini 2.5 Flash integration  
**Contents:**
- Model selection rationale
- Configuration examples
- Usage patterns (text, vision, image generation)
- Best practices
- Performance optimization
- Monitoring and debugging

**Audience:** AI/ML developers, backend developers

---

### [FLOORPLAN_IMAGE_LINKING_GUIDE.md](guides/FLOORPLAN_IMAGE_LINKING_GUIDE.md)
**Purpose:** Link floor plan geometry with interior photos using Gemini 2.5
**Contents:**
- Unified schema (Home, Floor, Room, Photo, RoomPhotoLink)
- End-to-end pipeline (plan → photo tagging → linking → pose → UI)
- Photo tagging prompt (Gemini 2.5 Flash)
- Scoring algorithm and QA metrics
- Storage patterns and runbook

**Audience:** Computer vision developers, backend engineers, product engineers

---

### [DEEPSEEK_OCR_FOR_FLOORPLANS.md](guides/DEEPSEEK_OCR_FOR_FLOORPLANS.md)
**Purpose:** Use DeepSeek-OCR to improve plan OCR (labels, dimensions, scale) and boost overall accuracy
**Contents:**
- Where to integrate DeepSeek-OCR in the pipeline
- Hybrid inference (Gemini geometry + DeepSeek OCR refinement)
- Merge logic and confidence rules
- Evaluation metrics and rollout plan

**Audience:** AI engineers working on plan parsing accuracy and data quality

---

### [PROMPT_ENGINEERING_GUIDE.md](guides/PROMPT_ENGINEERING_GUIDE.md)
**Purpose:** Universal prompt engineering for home improvement  
**Contents:**
- Core prompt structures
- Room types and configurations
- Transformation categories (paint, flooring, cabinetry, etc.)
- Design styles library
- Quality control patterns
- 2600+ lines of prompt templates

**Audience:** AI developers, prompt engineers, product designers

---

### [AGENT_PROMPTS_GUIDE.md](guides/AGENT_PROMPTS_GUIDE.md)
**Purpose:** Specialized prompts for DIY and Contractor agents  
**Contents:**
- Safety assessment prompts
- Project planning prompts
- Cost estimation prompts
- Compliance checking prompts
- 4000+ lines of agent-specific prompts

**Audience:** Agent developers, AI engineers

---

## 📚 Reference Documentation

### [FEATURE_CATALOG.md](reference/FEATURE_CATALOG.md)
**Purpose:** Complete catalog of implemented features  
**Contents:**
- Core system features
- Image analysis capabilities
- Room transformation features
- Quality metrics
- API integration details

**Audience:** Product managers, QA, developers

---

### [NOTEBOOKS_PROMPT_CONTEXT.md](reference/NOTEBOOKS_PROMPT_CONTEXT.md)
**Purpose:** Original Jupyter notebook documentation  
**Contents:**
- Notebook-based image processing workflows
- Room visualization techniques
- Paint color testing
- Flooring replacement
- Quality metrics implementation

**Audience:** Data scientists, ML engineers, reference for migration

---

## 🎯 Documentation by Use Case

### **I want to understand the business**
1. [business.md](business/business.md)
2. [problem-solving.md](business/problem-solving.md)

### **I want to understand the technical architecture**
1. [ENHANCED_AGENTIC_ARCHITECTURE.md](architecture/ENHANCED_AGENTIC_ARCHITECTURE.md)
2. [SYSTEM_ARCHITECTURE_DIAGRAMS.md](architecture/SYSTEM_ARCHITECTURE_DIAGRAMS.md)
3. [AGENTIC_WORKFLOW_ARCHITECTURE.md](architecture/AGENTIC_WORKFLOW_ARCHITECTURE.md)

### **I want to start developing**
1. [../README.md](../README.md)
2. [GETTING_STARTED.md](guides/GETTING_STARTED.md)
3. [GEMINI_MODEL_CONFIGURATION.md](guides/GEMINI_MODEL_CONFIGURATION.md)
4. [FLOORPLAN_IMAGE_LINKING_GUIDE.md](guides/FLOORPLAN_IMAGE_LINKING_GUIDE.md)

### **I want to build AI agents**
1. [ENHANCED_AGENTIC_ARCHITECTURE.md](architecture/ENHANCED_AGENTIC_ARCHITECTURE.md)
2. [AGENT_PROMPTS_GUIDE.md](guides/AGENT_PROMPTS_GUIDE.md)
3. [PROMPT_ENGINEERING_GUIDE.md](guides/PROMPT_ENGINEERING_GUIDE.md)

### **I want to plan the project**
1. [IMPLEMENTATION_ROADMAP.md](architecture/IMPLEMENTATION_ROADMAP.md)
2. [FEATURE_CATALOG.md](reference/FEATURE_CATALOG.md)

### **I want to understand what's already built**
1. [FEATURE_CATALOG.md](reference/FEATURE_CATALOG.md)
2. [NOTEBOOKS_PROMPT_CONTEXT.md](reference/NOTEBOOKS_PROMPT_CONTEXT.md)

---

## 📊 Documentation Statistics

| Category | Files | Total Lines | Purpose |
|----------|-------|-------------|---------|
| **Business** | 2 | ~1,500 | Strategy and planning |
| **Architecture** | 4 | ~3,500 | System design |
| **Guides** | 4 | ~7,000 | How-to and tutorials |
| **Reference** | 2 | ~1,000 | Feature catalogs |
| **Total** | 12 | ~13,000 | Complete documentation |

---

## 🔄 Documentation Maintenance

### Update Frequency
- **Business docs**: Quarterly or when strategy changes
- **Architecture docs**: When major architectural decisions are made
- **Guides**: When features are added or changed
- **Reference**: Continuously as features are implemented

### Contributing to Documentation
1. Keep documentation in sync with code
2. Update INDEX.md when adding new docs
3. Use clear headings and table of contents
4. Include code examples where applicable
5. Add diagrams for complex concepts

---

## 📞 Getting Help

- **Technical Questions**: See [GETTING_STARTED.md](guides/GETTING_STARTED.md)
- **Business Questions**: See [business.md](business/business.md)
- **Architecture Questions**: See [ENHANCED_AGENTIC_ARCHITECTURE.md](architecture/ENHANCED_AGENTIC_ARCHITECTURE.md)

---

**Happy Building! 🚀**

