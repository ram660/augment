# 🏠 HomeView AI - AI-Powered Home Improvement Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-orange.svg)](https://www.langchain.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini%202.0-blue.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

**Transform your home improvement journey with AI-powered design, intelligent planning, and seamless collaboration.**

HomeView AI is an intelligent home improvement platform that combines **AI-powered design tools**, **digital twin technology**, and **smart project planning** to help homeowners visualize, plan, and execute their home improvement projects. Built with Google Gemini 2.0, LangChain, and modern web technologies.

---

## ✨ What Makes HomeView AI Special

🎨 **Design Studio** - Transform any room with 20+ AI-powered design tools
- Paint walls, change flooring, update kitchens, add furniture
- Virtual staging with real product suggestions
- Photorealistic results in 5-15 seconds
- **No login required** - start designing immediately

🏗️ **Digital Twin** - Complete home management system
- Multi-floor floor plan analysis
- Room-by-room documentation
- Material and fixture tracking
- Intelligent data linking

💬 **AI Chat Assistant** - Your personal home improvement advisor
- Natural language project planning
- Image-based design suggestions
- DIY guides and tutorials
- Contractor recommendations

🔗 **Open Platform** - No barriers to entry
- All features accessible without registration
- Upload any image and start transforming
- Download results instantly
- Share with family and contractors

---

## 📑 Table of Contents

- [Quick Start](#-quick-start)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Technology Stack](#-technology-stack)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Deployment](#-deployment)
- [Documentation](#-documentation)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Quick Start

Get HomeView AI running locally in 5 minutes!

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher** ([Download](https://www.python.org/downloads/))
- **Node.js 18 or higher** ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/))
- **Google Gemini API Key** ([Get one free](https://aistudio.google.com/app/apikey))

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/homeview-ai.git
cd homeview-ai
```

### Step 2: Set Up Backend

```bash
# Create and activate virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env  # Windows
# OR
cp .env.example .env    # macOS/Linux

# Edit .env and add your Gemini API key:
# GOOGLE_API_KEY=your_gemini_api_key_here

# Initialize database (creates SQLite database)
alembic upgrade head

# Start backend server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

✅ **Backend is now running at:** `http://localhost:8000`
📚 **API Documentation:** `http://localhost:8000/docs`

### Step 3: Set Up Frontend (Choose One)

#### Option A: Main Frontend (Next.js) - Recommended

```bash
# Open a new terminal
cd homeview-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ **Frontend is now running at:** `http://localhost:3000`

#### Option B: Design Studio (React + Vite)

```bash
# Open a new terminal
cd frontend-studio

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ **Design Studio is now running at:** `http://localhost:5173`

### Step 4: Start Using HomeView AI! 🎉

1. Open your browser to `http://localhost:3000` (or `http://localhost:5173` for Design Studio)
2. Upload a room photo or use sample images
3. Try the Design Studio to transform your room
4. Chat with the AI assistant for project ideas
5. Explore the Digital Twin features

---

## 🎨 Features

### 1. **Design Studio** - 20+ AI-Powered Transformations

Transform any room with photorealistic AI-generated designs:

**Surface Transformations:**
- 🎨 Paint walls (any color, any finish)
- 🪵 Change flooring (hardwood, tile, carpet, vinyl, laminate)
- 💡 Update lighting fixtures and ambiance

**Kitchen Transformations:**
- 🗄️ Transform cabinets (color, finish, style)
- 🪨 Change countertops (granite, quartz, marble, butcher block)
- 🧱 Update backsplash (tile patterns, colors, materials)

**Furniture & Staging:**
- 🛋️ Add, remove, or replace furniture
- 🏠 Virtual staging (8 style presets + custom)
- 🧹 Unstaging (remove all furniture)

**Precision Tools:**
- ✂️ Masked editing (surgical precision)
- 🎯 AI segmentation (automatic element detection)
- 📐 Polygon selection (click-to-define areas)

**Advanced Features:**
- 💬 Freeform prompts (natural language transformations)
- 📸 Multi-angle views (see from different perspectives)
- ✨ Image enhancement (2x upscale, quality boost)
- 🧠 Design analysis & AI-generated ideas

**Key Benefits:**
- ⚡ Results in 5-15 seconds
- 🎯 2-4 variations per transformation
- 🛍️ Real product suggestions from Canadian retailers
- 📥 Download high-resolution images
- 🔓 **No login required** - start immediately!

👉 **[Complete Design Studio Documentation](docs/DESIGN_STUDIO_INDEX.md)**

### 2. **Digital Twin** - Complete Home Management

Create a comprehensive digital representation of your home:

- 📐 **Floor Plan Analysis**: Automatic room detection and labeling
- 🏢 **Multi-Floor Support**: Manage homes with multiple levels
- 📸 **Room Documentation**: Link photos to specific rooms
- 🔗 **Intelligent Linking**: Connect floor plans, rooms, and images
- 📊 **Material Tracking**: Track materials, fixtures, and products
- 🎨 **Isometric Visualization**: Beautiful 2D isometric floor plan views

### 3. **AI Chat Assistant** - Your Home Improvement Advisor

Get intelligent help for your projects:

- 💬 **Natural Language**: Ask questions in plain English
- 🖼️ **Image Understanding**: Upload photos for design advice
- 📝 **Project Planning**: Step-by-step DIY guides
- 💰 **Cost Estimation**: Budget planning and material costs
- 🔨 **Contractor Matching**: Find the right professionals
- 📚 **Knowledge Base**: Access to home improvement best practices

### 4. **Journey Management** - Track Your Projects

Organize and manage your home improvement journey:

- 📋 **Project Workflows**: Complete step-by-step plans
- 🎯 **Task Management**: Track progress and milestones
- 📸 **Before/After Gallery**: Document your transformations
- 💾 **Save & Share**: Share projects with family and contractors
- 📊 **Analytics**: Track time, costs, and progress

---

## 📁 Project Structure

```
homeview-ai/
├── backend/                    # FastAPI Backend
│   ├── api/                   # API Routes
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── chat.py           # Chat & AI assistant
│   │   ├── design.py         # Design Studio (25 endpoints)
│   │   ├── digital_twin.py   # Digital Twin management
│   │   ├── intelligence.py   # AI intelligence features
│   │   ├── journey.py        # Journey/project management
│   │   ├── product.py        # Product recommendations
│   │   ├── documents.py      # Document management
│   │   ├── admin.py          # Admin endpoints
│   │   └── monitoring.py     # Health checks & monitoring
│   ├── agents/               # AI Agents (LangChain)
│   │   ├── design_agent.py   # Design orchestration
│   │   ├── chat_agent.py     # Conversational AI
│   │   └── analysis_agent.py # Image & floor plan analysis
│   ├── services/             # Business Logic
│   │   ├── gemini_service.py           # Google Gemini integration
│   │   ├── design_transformation_service.py  # Image transformations
│   │   ├── transformation_storage_service.py # Storage management
│   │   ├── rag_service.py              # RAG for chat
│   │   └── monitoring_service.py       # System monitoring
│   ├── models/               # Database Models (SQLAlchemy)
│   │   ├── base.py          # Base model & DB config
│   │   ├── user.py          # User models
│   │   ├── home.py          # Home, Room, FloorPlan models
│   │   ├── transformation.py # Design transformation models
│   │   ├── knowledge.py     # RAG & document models
│   │   └── analysis.py      # Analysis result models
│   ├── integrations/         # External APIs
│   │   ├── gemini/          # Gemini API wrapper
│   │   └── firebase/        # Google Cloud Storage
│   ├── middleware/           # API Middleware
│   │   ├── rate_limit.py    # Rate limiting
│   │   └── monitoring.py    # Request monitoring
│   ├── utils/                # Utilities
│   └── main.py               # FastAPI app entry point
│
├── homeview-frontend/        # Next.js Frontend (Main UI)
│   ├── app/                 # Next.js 15 App Router
│   │   ├── page.tsx         # Home page
│   │   ├── chat/            # Chat interface
│   │   ├── design/          # Design Studio
│   │   ├── explore/         # Explore page
│   │   └── layout.tsx       # Root layout
│   ├── components/          # React Components
│   │   ├── chat/           # Chat components
│   │   ├── design/         # Design Studio components
│   │   ├── digital-twin/   # Digital Twin components
│   │   └── ui/             # Shared UI components
│   └── lib/                # Utilities & API client
│
├── frontend-studio/          # Design Studio (React + Vite)
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Studio/     # Studio canvas & nodes
│   │   │   ├── Common/     # Shared components
│   │   │   └── Chat/       # Chat interface
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API services
│   │   └── styles/         # CSS styles
│   └── index.html          # Entry point
│
├── docs/                     # Documentation
│   ├── DESIGN_STUDIO_INDEX.md        # Design Studio docs index
│   ├── DESIGN_STUDIO_SUMMARY.md      # Complete feature summary
│   ├── DESIGN_STUDIO_FEATURES.md     # Feature documentation
│   ├── DESIGN_STUDIO_IMPLEMENTATION.md # Implementation guide
│   ├── DESIGN_STUDIO_API_REFERENCE.md  # API reference
│   ├── DESIGN_STUDIO_CUSTOMER_GUIDE.md # User guide
│   ├── DESIGN_STUDIO_QUICK_REFERENCE.md # Quick reference
│   ├── DESIGN_STUDIO_ENDPOINTS_LIST.md  # Endpoint list
│   ├── architecture/        # Architecture docs
│   ├── business/           # Business docs
│   ├── guides/             # Developer guides
│   └── reference/          # API reference
│
├── scripts/                  # Utility Scripts
│   ├── analyze_images_to_db_aligned.py  # Image analysis
│   ├── export_db_to_csv.py             # Data export
│   ├── import_enriched_csv_to_db.py    # Data import
│   └── print_twin_summary.py           # Digital twin summary
│
├── tests/                    # Test Suite
│   ├── test_rag_service.py
│   ├── test_floor_type_normalizer.py
│   └── test_multifloor_persistence.py
│
├── uploads/                  # User Uploads
│   ├── floor_plans/         # Floor plan images
│   ├── room_images/         # Room photos
│   ├── chat/               # Chat uploaded images
│   └── journeys/           # Journey attachments
│
├── generated_images/         # AI-Generated Images
├── exports/                  # Data Exports
├── alembic/                  # Database Migrations
├── .env                      # Environment variables (create from .env.example)
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── alembic.ini              # Alembic configuration
├── docker-compose.yml       # Docker setup
└── README.md                # This file
```

---

## 🔧 Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **AI/ML**:
  - Google Gemini 2.0 Flash (text, vision, reasoning)
  - Google Gemini Imagen 3 (image generation & editing)
  - LangChain & LangGraph (agent orchestration)
- **Database**:
  - SQLite (development)
  - PostgreSQL + pgvector (production)
  - SQLAlchemy ORM
  - Alembic migrations
- **Storage**: Google Cloud Storage / Firebase
- **Image Processing**: Pillow, OpenCV, scikit-image
- **Caching**: Redis (optional)

### Frontend
- **Main UI**: Next.js 15, React 19, TypeScript
- **Design Studio**: React 18, Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Flow Diagrams**: ReactFlow
- **HTTP Client**: Axios

### DevOps & Tools
- **Containerization**: Docker, Docker Compose
- **API Documentation**: FastAPI Swagger/OpenAPI
- **Testing**: Pytest
- **Code Quality**: ESLint, Prettier
- **Version Control**: Git

---

## 📚 API Documentation

### Interactive API Docs

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key API Endpoints

#### Design Studio (25 endpoints)
```
POST /api/v1/design/transform-paint              # Paint transformation
POST /api/v1/design/transform-flooring           # Flooring transformation
POST /api/v1/design/transform-cabinets           # Cabinet transformation
POST /api/v1/design/transform-countertops        # Countertop transformation
POST /api/v1/design/transform-backsplash         # Backsplash transformation
POST /api/v1/design/virtual-staging              # Virtual staging
POST /api/v1/design/virtual-staging-upload       # Virtual staging (upload)
POST /api/v1/design/unstage                      # Remove furniture
POST /api/v1/design/edit-with-mask               # Masked editing
POST /api/v1/design/segment                      # AI segmentation
POST /api/v1/design/transform-prompted           # Freeform prompt
POST /api/v1/design/transform-prompted-upload    # Freeform prompt (upload)
POST /api/v1/design/multi-angle-upload           # Multi-angle views
POST /api/v1/design/enhance-upload               # Image enhancement
POST /api/v1/design/analyze-image                # Design analysis
```

#### Digital Twin
```
POST /api/v1/digital-twin/homes                  # Create home
GET  /api/v1/digital-twin/homes/{home_id}        # Get home details
POST /api/v1/digital-twin/analyze-floor-plan     # Analyze floor plan
POST /api/v1/digital-twin/rooms                  # Create room
POST /api/v1/digital-twin/room-images            # Upload room image
GET  /api/v1/digital-twin/visualization/{home_id} # Get visualization data
```

#### Chat & Intelligence
```
POST /api/v1/chat/message                        # Send chat message
POST /api/v1/chat/multimodal                     # Multimodal chat (text + images)
POST /api/v1/intelligence/analyze-image          # Analyze image
POST /api/v1/intelligence/generate-guide         # Generate DIY guide
```

#### Journey Management
```
POST /api/v1/journey/create                      # Create journey
GET  /api/v1/journey/{journey_id}                # Get journey
POST /api/v1/journey/{journey_id}/step           # Add step
PUT  /api/v1/journey/{journey_id}/step/{step_id} # Update step
```

#### Monitoring
```
GET  /api/v1/monitoring/health                   # Health check
GET  /api/v1/monitoring/metrics                  # System metrics
```

### API Examples

#### Transform Paint Color (Upload)
```bash
curl -X POST "http://localhost:8000/api/v1/design/transform-prompted-upload" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data_url": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "prompt": "paint the walls soft gray with matte finish",
    "enable_grounding": false,
    "num_variations": 2
  }'
```

#### Virtual Staging with Products
```bash
curl -X POST "http://localhost:8000/api/v1/design/virtual-staging-upload" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data_url": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "style_preset": "Modern",
    "furniture_density": "medium",
    "enable_grounding": true,
    "num_variations": 2
  }'
```

#### Chat with AI Assistant
```bash
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to renovate my kitchen. What should I consider?",
    "conversation_id": "optional-conversation-id"
  }'
```

📖 **[Complete API Documentation](docs/DESIGN_STUDIO_API_REFERENCE.md)**

---

## 💻 Development

### Environment Variables

Create a `.env` file in the root directory (copy from `.env.example`):

```env
# ===== REQUIRED =====
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# ===== DATABASE (Development - Default) =====
USE_SQLITE=true
DATABASE_URL=sqlite:///./homevision.db
DATABASE_URL_ASYNC=sqlite+aiosqlite:///./homevision.db

# ===== API CONFIGURATION =====
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000

# ===== OPTIONAL: PRODUCTION DATABASE =====
# USE_SQLITE=false
# DATABASE_URL=postgresql://user:password@localhost:5432/homeview_db
# DATABASE_URL_ASYNC=postgresql+asyncpg://user:password@localhost:5432/homeview_db

# ===== OPTIONAL: GOOGLE CLOUD STORAGE =====
# GCS_BUCKET_NAME=your_bucket_name
# GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# ===== OPTIONAL: RAG/EMBEDDINGS =====
# EMBEDDING_MODEL=hash  # Options: hash, sbert

# ===== OPTIONAL: REDIS CACHING =====
# REDIS_URL=redis://localhost:6379/0
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

### Running Tests

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest

# Run specific test file
pytest tests/test_rag_service.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=backend --cov-report=html

# View coverage report
# On macOS: open htmlcov/index.html
# On Windows: start htmlcov/index.html
# On Linux: xdg-open htmlcov/index.html
```

### Useful Development Scripts

```bash
# Print digital twin summary for a home
python -m scripts.print_twin_summary

# Export database to CSV files
python -m scripts.export_db_to_csv

# Import data from CSV files
python -m scripts.import_enriched_csv_to_db --owner-email demo@example.com

# Analyze images and save to database
python -m scripts.analyze_images_to_db_aligned

# Validate exported data
python -m scripts.validate_exports
```

---

## 🚀 Deployment

### Docker Deployment

#### Development
```bash
# Start all services (backend + database)
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Rebuild and start
docker-compose up -d --build
```

#### Production
```bash
# Start production services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Manual Production Deployment

#### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Set production environment variables
export GOOGLE_API_KEY=your_key
export DATABASE_URL=postgresql://user:pass@host:5432/db
export USE_SQLITE=false
export ENVIRONMENT=production

# Run database migrations
alembic upgrade head

# Start with Gunicorn (production WSGI server)
gunicorn backend.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

#### Frontend (Next.js)

```bash
cd homeview-frontend

# Install dependencies
npm install

# Build for production
npm run build

# Start production server
npm start

# Or use PM2 for process management
pm2 start npm --name "homeview-frontend" -- start
```

#### Frontend (Design Studio)

```bash
cd frontend-studio

# Install dependencies
npm install

# Build for production
npm run build

# Serve with a static file server
npx serve -s dist -l 5173
```

---

## 📚 Documentation

**[📖 Complete Documentation Index](docs/INDEX.md)** - Your guide to all documentation

### Design Studio Documentation
- 📋 **[Design Studio Index](docs/DESIGN_STUDIO_INDEX.md)** - Complete documentation index
- 📊 **[Design Studio Summary](docs/DESIGN_STUDIO_SUMMARY.md)** - Executive overview & business case
- 🎨 **[Features](docs/DESIGN_STUDIO_FEATURES.md)** - All 20+ transformation types
- 💻 **[Implementation Guide](docs/DESIGN_STUDIO_IMPLEMENTATION.md)** - Frontend development guide
- 📖 **[API Reference](docs/DESIGN_STUDIO_API_REFERENCE.md)** - Complete API documentation
- 👥 **[Customer Guide](docs/DESIGN_STUDIO_CUSTOMER_GUIDE.md)** - User-friendly guide
- ⚡ **[Quick Reference](docs/DESIGN_STUDIO_QUICK_REFERENCE.md)** - Developer quick reference
- 📋 **[Endpoints List](docs/DESIGN_STUDIO_ENDPOINTS_LIST.md)** - All 25 endpoints

### Architecture & Development
- 🏗️ **[Multi-Agent System](docs/architecture/ENHANCED_AGENTIC_ARCHITECTURE.md)** - Agent architecture
- 🛣️ **[Implementation Roadmap](docs/architecture/IMPLEMENTATION_ROADMAP.md)** - Development roadmap
- 🔄 **[Workflow Design](docs/architecture/AGENTIC_WORKFLOW_ARCHITECTURE.md)** - LangGraph workflows

### Guides & References
- 🚀 **[Getting Started](docs/guides/GETTING_STARTED.md)** - Setup guide
- 🤖 **[Gemini Configuration](docs/guides/GEMINI_MODEL_CONFIGURATION.md)** - AI model setup
- 📝 **[Prompt Engineering](docs/guides/PROMPT_ENGINEERING_GUIDE.md)** - Prompt best practices
- 📚 **[Feature Catalog](docs/reference/FEATURE_CATALOG.md)** - Complete feature list

### Business & Strategy
- 💼 **[Business Strategy](docs/business/business.md)** - Market analysis & strategy
- 🎯 **[Problem-Solution Framework](docs/business/problem-solving.md)** - Problem analysis

---

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

