# HomeView AI - Project Structure

This document provides an overview of the project organization and key directories.

## Root Directory Structure

```
homeview-ai/
├── backend/                 # Python FastAPI backend
├── homeview-frontend/       # Next.js main frontend application
├── frontend-studio/         # Design studio UI (React + Vite)
├── frontend/                # Legacy frontend (deprecated)
├── components/              # Shared Python components
├── docs/                    # All documentation
├── scripts/                 # Utility scripts for data processing
├── tests/                   # Test suites
├── notebooks/               # Jupyter notebooks for analysis
├── alembic/                 # Database migrations
├── k8s/                     # Kubernetes deployment configs
├── uploads/                 # User uploaded files
├── exports/                 # Data exports
├── generated_images/        # AI-generated images
├── visualizations/          # Visualization outputs
├── prompts/                 # AI prompt templates
├── images/                  # Sample/test images
└── archive/                 # Archived documentation
```

## Backend Structure

```
backend/
├── agents/                  # AI agent implementations
│   ├── base/               # Base agent classes
│   ├── homeowner/          # Homeowner-facing agents
│   ├── contractor/         # Contractor-facing agents
│   ├── marketplace/        # Marketplace agents
│   └── shared/             # Shared utility agents
├── api/                     # FastAPI route handlers
│   ├── chat/               # Chat endpoints
│   ├── design/             # Design transformation endpoints
│   ├── digital_twin/       # Digital twin endpoints
│   └── intelligence/       # Intelligence/analysis endpoints
├── models/                  # SQLAlchemy database models
│   ├── home.py             # Home and room models
│   ├── user.py             # User models
│   ├── knowledge.py        # RAG/knowledge base models
│   └── ...
├── services/                # Business logic services
│   ├── rag_service.py      # RAG indexing and retrieval
│   ├── image_service.py    # Image processing
│   └── ...
├── integrations/            # External API integrations
│   ├── gemini/             # Google Gemini API
│   └── firebase/           # Firebase/GCS storage
├── workflows/               # LangGraph workflow definitions
├── middleware/              # API middleware
├── utils/                   # Shared utilities
├── database.py              # Database configuration
└── main.py                  # FastAPI application entry point
```

## Frontend Structure

### Main Frontend (Next.js)
```
homeview-frontend/
├── app/                     # Next.js 15 app directory
│   ├── page.tsx            # Home page
│   ├── layout.tsx          # Root layout
│   └── ...
├── components/              # React components
│   ├── ui/                 # UI components
│   └── ...
├── lib/                     # Utility libraries
└── public/                  # Static assets
```

### Design Studio (React + Vite)
```
frontend-studio/
├── src/                     # Source files
│   ├── components/         # React components
│   ├── services/           # API services
│   └── App.jsx             # Main app component
├── index.html              # HTML entry point
└── vite.config.js          # Vite configuration
```

## Documentation Structure

```
docs/
├── INDEX.md                 # Documentation index
├── architecture/            # System architecture
│   ├── ENHANCED_AGENTIC_ARCHITECTURE.md
│   ├── IMPLEMENTATION_ROADMAP.md
│   └── SYSTEM_ARCHITECTURE_DIAGRAMS.md
├── business/                # Business strategy
│   ├── business.md
│   └── problem-solving.md
├── company/                 # Company vision & strategy
│   ├── PMVV_FRAMEWORK.md
│   ├── COMPETITIVE_STRATEGY_VISUAL_DECK.md
│   └── ...
├── guides/                  # Developer guides
│   ├── GETTING_STARTED.md
│   ├── GEMINI_MODEL_CONFIGURATION.md
│   ├── PROMPT_ENGINEERING_GUIDE.md
│   └── ...
└── reference/               # API & feature reference
    ├── FEATURE_CATALOG.md
    └── NOTEBOOKS_PROMPT_CONTEXT.md
```

## Scripts Directory

```
scripts/
├── analyze_images_to_db_aligned.py    # Image analysis to database
├── analyze_images_to_json.py          # Image analysis to JSON
├── foundation_ingest.py               # Initial data ingestion
├── import_enriched_csv_to_db.py       # CSV import to database
├── export_db_to_csv.py                # Database export to CSV
├── compute_links_from_analyses.py     # Link computation
└── print_twin_summary.py              # Digital twin summary
```

## Tests Directory

```
tests/
├── test_floor_type_normalizer.py      # Floor type normalization tests
├── test_image_filename_parser.py      # Image filename parsing tests
├── test_room_type_sanitizer.py        # Room type sanitization tests
├── test_multifloor_persistence.py     # Multi-floor support tests
└── test_rag_service.py                # RAG service tests
```

## Notebooks Directory

```
notebooks/
├── 01_floor_plan_analysis.ipynb       # Floor plan analysis
├── 02_image_tagging_analysis.ipynb    # Image tagging
├── 03_comprehensive_schema_design.ipynb # Schema design
├── 04_schema_summary_and_recommendations.ipynb
├── 05_multi_floor_plan_detection.ipynb # Multi-floor detection
└── 06_image_batch_to_json_and_compare.ipynb
```

## Data Directories

### Uploads
```
uploads/
├── floor_plans/             # User uploaded floor plans
├── room_images/             # User uploaded room images
└── analysis/                # Analysis results (JSON)
```

### Exports
```
exports/
└── analysis_run/            # Analysis run exports
    └── enriched/            # Enriched CSV exports
```

### Generated Content
```
generated_images/            # AI-generated images (Imagen 3)
visualizations/              # Visualization outputs
```

## Configuration Files

- `requirements.txt` - Python dependencies
- `alembic.ini` - Database migration configuration
- `docker-compose.yml` - Docker development setup
- `docker-compose.prod.yml` - Docker production setup
- `Dockerfile` - Docker image definition
- `.gitignore` - Git ignore patterns
- `.env` - Environment variables (not in repo)

## Key Files

- `README.md` - Main project documentation
- `PROJECT_STRUCTURE.md` - This file
- `homevision.db` - SQLite database (development)
- `homevision-credentials.json` - Firebase credentials (not in repo)

## Important Notes

1. **Frontend**: The main frontend is `homeview-frontend/` (Next.js). The `frontend/` directory is legacy.
2. **Database**: Uses SQLite for development, PostgreSQL for production.
3. **Storage**: Firebase/GCS for image storage in production.
4. **Tests**: All test files should be in the `tests/` directory, not in root.
5. **Documentation**: All docs should be in the `docs/` directory with proper categorization.
6. **Generated Files**: Generated images and exports are gitignored but directories are tracked.

## Getting Started

1. See `README.md` for installation instructions
2. See `docs/guides/GETTING_STARTED.md` for detailed setup
3. See `docs/INDEX.md` for complete documentation index

