# 🏠 HomeView AI - Agentic SaaS Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-orange.svg)](https://www.langchain.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

**An AI-native platform bridging homeowners, DIY workers, and contractors through intelligent multi-agent automation.**

HomeView AI transforms the $500B home improvement industry by replacing manual processes with autonomous AI agents. Built on LangChain and LangGraph, powered by Google Gemini's multimodal capabilities, our platform handles everything from design visualization to contractor matching, project planning, and payment processing.

## ✨ What Makes HomeView AI Different

- 🤖 **Agentic Architecture**: Multi-agent system built with LangChain & LangGraph for autonomous task execution
- 🎨 **AI-Powered Design**: Transform rooms with Gemini Imagen 3, get instant design variations
- 🏗️ **Digital Twin**: Comprehensive home management with multi-floor support and intelligent data linking
- 💬 **Intelligent Chat**: RAG-powered assistant that understands your home's context
- 🔗 **Collaborative Ecosystem**: Connect homeowners, DIY enthusiasts, and contractors in one platform

## 📑 Table of Contents

- [Vision](#-vision)
- [Architecture](#️-architecture)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Key Features](#-key-features)
- [API Examples](#-api-examples)
- [Technology Stack](#-technology-stack)
- [Documentation](#-documentation)
- [Roadmap](#️-roadmap)
- [Testing](#-testing)
- [Docker Deployment](#-docker-deployment)
- [Contributing](#-contributing)
- [Project Status](#-project-status)
- [Contact](#-contact--links)

## 🎯 Vision

Transform the $500B home improvement industry by replacing manual processes with autonomous AI agents that handle design, planning, contractor matching, project management, and payment processing.

## 🏗️ Architecture

### Three-Pillar System

1. **Smart Project Planner** - AI-powered design and planning tools
2. **Digital Twin Platform** - Comprehensive home management system
3. **Trust & Collaboration Marketplace** - Verified contractor network

### Multi-Agent Ecosystem

Built on **LangChain** and **LangGraph** with specialized agents:

- **Homeowner Experience Agents**: Design Orchestrator, Vision Analysis, Product Discovery, Cost Intelligence, Rendering
- **Digital Twin Agents**: Home Profile Manager, Predictive Maintenance, Compliance & Code
- **Contractor Agents**: Matching, RFP Generation, Quote Optimization, Project Management, Payment
- **Collaboration Agents**: Real-Time Sync, Conversation, Notification
- **Trust Agents**: Verification, Reputation Scoring

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or SQLite for development)
- Redis 7+ (optional, for production)
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/homeview-ai.git
cd homeview-ai

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file in the root directory with the following:
# GOOGLE_API_KEY=your_gemini_api_key_here
# GCS_BUCKET_NAME=your_bucket_name (optional, for production)

# Run database migrations (creates SQLite database by default)
alembic upgrade head

# Start the development server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive API documentation.

### Environment Variables

Create a `.env` file in the root directory:

```env
# Required
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional - Database (defaults to SQLite)
USE_SQLITE=true
DATABASE_URL=sqlite:///./homevision.db
DATABASE_URL_ASYNC=sqlite+aiosqlite:///./homevision.db

# Optional - Google Cloud Storage (for production)
GCS_BUCKET_NAME=your_bucket_name
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Optional - RAG/Embeddings
EMBEDDING_MODEL=hash  # Options: hash, sbert

# Optional - API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Running the Frontend

**Main Frontend (Next.js)**:
```bash
cd homeview-frontend
npm install
npm run dev
```

**Design Studio (React + Vite)**:
```bash
cd frontend-studio
npm install
npm run dev
```

## 📁 Project Structure

```
homeview-ai/
├── backend/
│   ├── agents/              # All agent implementations
│   │   ├── base/           # Base agent classes
│   │   ├── homeowner/      # Homeowner-facing agents
│   │   ├── contractor/     # Contractor-facing agents
│   │   ├── marketplace/    # Marketplace agents
│   │   └── shared/         # Shared utility agents
│   ├── workflows/          # LangGraph workflow definitions
│   ├── models/             # Database models (SQLAlchemy)
│   ├── api/                # FastAPI routes
│   ├── services/           # Business logic services
│   ├── integrations/       # External API integrations
│   │   ├── gemini/        # Gemini API wrapper
│   │   └── firebase/      # Firebase/GCS storage
│   ├── middleware/         # API middleware
│   └── utils/              # Shared utilities
├── homeview-frontend/      # Next.js frontend (main UI)
├── frontend-studio/        # Design studio UI (React + Vite)
├── tests/                  # Test suites
├── docs/                   # Documentation
│   ├── architecture/      # System architecture docs
│   ├── business/          # Business strategy docs
│   ├── company/           # Company vision & PMVV
│   ├── guides/            # Developer guides
│   └── reference/         # API & feature reference
├── scripts/                # Utility scripts
├── notebooks/              # Jupyter notebooks for analysis
├── uploads/                # User uploaded files
│   ├── floor_plans/       # Floor plan images
│   ├── room_images/       # Room photos
│   └── analysis/          # Analysis results
├── exports/                # Data exports
├── generated_images/       # AI-generated images
└── visualizations/         # Visualization outputs
```

## 🎨 Key Features

### 1. **AI-Powered Floor Plan Analysis**
- Automatic room detection and labeling
- Multi-floor plan support
- Dimension extraction
- Room type normalization

### 2. **Image Transformation & Design Studio**
- Style transfer using Gemini Imagen 3
- Room redesign with AI
- Multiple design variations
- Before/after comparisons

### 3. **Digital Twin Visualization**
- Isometric 2D floor plan views
- Room-to-image linking
- Multi-floor navigation
- Comprehensive home data management

### 4. **Intelligent Chat Assistant** (In Progress)
- RAG-powered contextual responses
- Home data integration
- Natural language queries
- Multi-modal understanding (text + images)

### 5. **Agentic Workflows** (Planned)
- Multi-agent orchestration with LangGraph
- Contractor matching
- Cost estimation
- Project planning automation

## 🧪 API Examples

### Analyze a Floor Plan

```bash
curl -X POST "http://localhost:8000/api/digital-twin/analyze-floor-plan" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@floor_plan.jpg" \
  -F "home_id=your_home_id"
```

### Transform a Room Image

```bash
curl -X POST "http://localhost:8000/api/design/transform" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://storage.googleapis.com/your-bucket/room.jpg",
    "transformation_type": "style_transfer",
    "prompt": "modern minimalist living room with natural light"
  }'
```

### Query the RAG System

```bash
curl -X POST "http://localhost:8000/api/digital-twin/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the dimensions of the kitchen on the main floor?",
    "home_id": "your_home_id",
    "floor_level": 1
  }'
```

## 🔧 Technology Stack

- **AI Framework**: LangChain, LangGraph
- **AI Models**: Google Gemini 2.0 Flash (text, vision, image generation with Imagen 3)
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy
- **Database**: PostgreSQL (production) / SQLite (development)
- **Storage**: Google Cloud Storage
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Real-Time**: WebSockets (planned)
- **Image Processing**: Pillow, OpenCV

## 📚 Documentation

**[📖 Complete Documentation Index](docs/INDEX.md)** - Your guide to all documentation

### Quick Access
- 💼 **Business**: [Strategy & Market Analysis](docs/business/business.md) | [Problem-Solution Framework](docs/business/problem-solving.md)
- 🏗️ **Architecture**: [Multi-Agent System](docs/architecture/ENHANCED_AGENTIC_ARCHITECTURE.md) | [Implementation Roadmap](docs/architecture/IMPLEMENTATION_ROADMAP.md) | [Workflow Design](docs/architecture/AGENTIC_WORKFLOW_ARCHITECTURE.md)
- 📖 **Guides**: [Getting Started](docs/guides/GETTING_STARTED.md) | [Gemini Configuration](docs/guides/GEMINI_MODEL_CONFIGURATION.md) | [Prompt Engineering](docs/guides/PROMPT_ENGINEERING_GUIDE.md)
- 📚 **Reference**: [Feature Catalog](docs/reference/FEATURE_CATALOG.md) | [Notebooks Context](docs/reference/NOTEBOOKS_PROMPT_CONTEXT.md)

## 🛣️ Roadmap

### Phase 1: Foundation ✅ Complete
- [x] Project structure
- [x] Base agent framework
- [x] Gemini integration (text, vision, image generation)
- [x] Database schema (multi-floor support)
- [x] Firebase/GCS storage integration
- [x] Floor plan analysis
- [x] Room image tagging and linking

### Phase 2: Digital Twin & Design Studio 🚧 In Progress
- [x] Digital twin visualization (isometric view)
- [x] Image transformation system (Imagen 3)
- [x] Design studio UI
- [x] Multi-floor plan detection
- [ ] RAG system for intelligent chat
- [ ] Cost estimation engine
- [ ] Product discovery integration

### Phase 3: Agentic Workflows (Weeks 8-16)
- [ ] LangGraph workflow orchestration
- [ ] Multi-agent collaboration
- [ ] Contractor matching agent
- [ ] Project planning agent
- [ ] Quote generation system

### Phase 4: Marketplace & Collaboration (Weeks 17-24)
- [ ] Social feed for home improvement
- [ ] DIY agent marketplace
- [ ] Real-time collaboration
- [ ] Payment processing (Stripe)

## � Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_rag_service.py

# Run with coverage
pytest --cov=backend --cov-report=html
```

## 🐳 Docker Deployment

### Development

```bash
docker-compose up -d
```

### Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## �🤝 Contributing

This is currently a private project. Contribution guidelines will be added when open-sourced.

## 📄 License

Proprietary - All rights reserved

## 🙏 Acknowledgments

- **LangChain & LangGraph** - For the powerful agentic AI framework
- **Google Gemini** - For state-of-the-art multimodal AI capabilities
- **FastAPI** - For the high-performance async API framework
- **Next.js & React** - For the modern frontend framework

## 📚 Additional Resources

### Agentic RAG System

The project includes a lightweight RAG (Retrieval-Augmented Generation) system for contextual data retrieval:

- **Data Model**: `backend/models/knowledge.py` (Documents, Chunks, Embeddings, Agent Tasks/Traces)
- **Service**: `backend/services/rag_service.py` (builds index and queries it)
- **API Endpoints**:
  - `POST /api/digital-twin/rag/reindex` — Build the index from DB rows
  - `POST /api/digital-twin/rag/query` — Query with filters (home_id, room_id, floor_level)

### Database Options

**Development (SQLite)**:
```bash
# Default - no configuration needed
alembic upgrade head
```

**Production (PostgreSQL + pgvector)**:
```bash
# Set environment variables
export USE_SQLITE=false
export DATABASE_URL="postgresql://user:pass@localhost:5432/homeview_db"
export DATABASE_URL_ASYNC="postgresql+asyncpg://user:pass@localhost:5432/homeview_db"
export EMBEDDING_MODEL="sbert"  # Optional: uses sentence-transformers

# Run migrations
alembic upgrade head
```

### Useful Scripts

```bash
# Import data from CSV exports
python -m scripts.import_enriched_csv_to_db --owner-email demo@example.com

# Export database to CSV
python -m scripts.export_db_to_csv

# Print digital twin summary
python -m scripts.print_twin_summary

# Analyze images and save to database
python -m scripts.analyze_images_to_db_aligned
```

## � Project Status

**Current Phase**: Phase 2 - Digital Twin & Design Studio (In Progress)

**What's Working**:
- ✅ Floor plan analysis with multi-floor support
- ✅ Image transformation using Gemini Imagen 3
- ✅ Digital twin visualization (isometric views)
- ✅ Design studio UI with before/after comparisons
- ✅ Google Cloud Storage integration
- ✅ SQLite and PostgreSQL support
- ✅ FastAPI backend with comprehensive endpoints

**In Development**:
- 🚧 RAG system for intelligent chat
- 🚧 Cost estimation engine
- 🚧 LangGraph workflow orchestration
- 🚧 Multi-agent collaboration

**Planned**:
- 📋 Contractor matching system
- 📋 Social feed and marketplace
- 📋 Real-time collaboration
- 📋 Payment processing

## �📧 Contact & Links

- **Website**: [www.homeviewai.ca](https://www.homeviewai.ca) (in development)
- **Location**: Vancouver, BC, Canada
- **Documentation**: [docs/INDEX.md](docs/INDEX.md)
- **Project Structure**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## ⚠️ Important Notes

1. **API Keys**: You must have a Google Gemini API key to use this project. Get one at [Google AI Studio](https://aistudio.google.com/app/apikey).
2. **Storage**: For production use, configure Google Cloud Storage. Development mode works with local file storage.
3. **Database**: SQLite is used by default for development. For production, use PostgreSQL with pgvector extension.
4. **Environment**: Always create a `.env` file with your configuration. Never commit credentials to Git.

---

**Built with ❤️ using LangChain, LangGraph, and Google Gemini**

