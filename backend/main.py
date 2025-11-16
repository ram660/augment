"""Main FastAPI application for HomeVision AI."""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from backend.api import digital_twin_router
from backend.api.intelligence import router as intelligence_router, v1_router as intelligence_v1_router
from backend.api.design import router as design_router
from backend.api.auth import router as auth_router
from backend.api.chat import router as chat_router
from backend.api.product import router as product_router
from backend.api.documents import router as documents_router
from backend.api.admin import router as admin_router
from backend.api.monitoring import router as monitoring_router
from backend.api.journey import router as journey_router
from backend.api.multimodal import router as multimodal_router
from backend.api.workflows import router as workflows_router
from backend.api.chat_workflow import router as chat_workflow_router
from backend.models.base import init_db_async
from backend.middleware import RateLimitMiddleware, MonitoringMiddleware
from backend.services.monitoring_service import get_monitoring_service
from backend.integrations.pixeltable.client import PixeltableClient
from backend.integrations.gemini.client import GeminiClient
from backend.integrations.mcp.client import HomeViewMCPClient
from backend.services.pixeltable_service import PixeltableService
from backend.agents.diy.diy_agent import DIYAgent
from backend.agents.contractor.contractor_agent import ContractorAgent
from backend.agents.chat.chat_orchestrator import ChatOrchestrator
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting HomeVision AI API...")
    try:
        await init_db_async()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {str(e)}")

    # Initialize Pixeltable and Gemini clients
    try:
        logger.info("Initializing Pixeltable client...")
        pxt_client = PixeltableClient(db_path="pixeltable_data")

        logger.info("Initializing Gemini client...")
        gemini_client = GeminiClient()

        logger.info("Initializing Pixeltable service...")
        pixeltable_service = PixeltableService(pxt_client, gemini_client)

        # Initialize MCP client
        logger.info("Initializing MCP client...")
        mcp_server_urls = {
            "video_analysis": "http://localhost:8001",
            "design_studio": "http://localhost:8002",
            "product_search": "http://localhost:8003",
            "diy_guide": "http://localhost:8006"
        }
        mcp_client = HomeViewMCPClient(server_urls=mcp_server_urls)

        # Initialize specialized agents
        logger.info("Initializing specialized agents...")
        diy_agent = DIYAgent(gemini_client, mcp_client)
        contractor_agent = ContractorAgent(gemini_client, mcp_client)
        chat_orchestrator = ChatOrchestrator(gemini_client, mcp_client)

        # Store in app state for dependency injection
        app.state.pixeltable_service = pixeltable_service
        app.state.pxt_client = pxt_client
        app.state.gemini_client = gemini_client
        app.state.mcp_client = mcp_client
        app.state.diy_agent = diy_agent
        app.state.contractor_agent = contractor_agent
        app.state.chat_orchestrator = chat_orchestrator

        logger.info("Multimodal processing and agents initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize multimodal processing: {e}")
        # Don't fail startup, just log the error

    yield

    # Shutdown
    logger.info("Shutting down HomeVision AI API...")


# Create FastAPI app with comprehensive documentation
app = FastAPI(
    title="HomeView AI API",
    description="""
## 🏠 HomeView AI - Intelligent Home Improvement Platform

An AI-powered SaaS platform for homeowners, DIY workers, and contractors featuring:

### 🤖 **Multi-Agent Architecture**
- **Digital Twin Agent** - Create digital representations of homes with floor plans and images
- **Chat Agent** - Context-aware conversational AI for home improvement questions
- **Cost Estimation Agent** - AI-powered cost estimates with regional pricing
- **Product Matching Agent** - Dimension-aware product recommendations
- **Design Studio Agent** - AI image generation and style transformations

### 🔐 **Authentication & Security**
- JWT-based authentication with access and refresh tokens
- Role-based access control (homeowner, contractor, diy_worker, admin)
- Secure password hashing with bcrypt

### 🎨 **Key Features**
- **Digital Twin Creation** - Upload floor plans and room images
- **AI Chat Assistant** - Ask questions about your home and get intelligent responses
- **Cost Estimation** - Get accurate renovation cost estimates
- **Product Matching** - Find products that fit your rooms perfectly
- **Design Studio** - Transform room designs with AI-powered image generation
- **Design Variations** - Generate multiple design options with different styles

### 🚀 **Technology Stack**
- **Framework:** FastAPI with async/await
- **AI Models:** Google Gemini 2.5 Flash, Gemini Imagen 4.0
- **Workflows:** LangGraph for multi-step AI workflows
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Authentication:** JWT tokens with HTTPBearer

### 📚 **API Documentation**
- **Swagger UI:** `/docs` (interactive API documentation)
- **ReDoc:** `/redoc` (alternative documentation view)
- **OpenAPI Schema:** `/openapi.json` (machine-readable API spec)

### 🔗 **Quick Start**
1. Register a new account: `POST /api/v1/auth/register`
2. Login to get JWT tokens: `POST /api/v1/auth/login`
3. Use the access token in the `Authorization: Bearer <token>` header
4. Start chatting: `POST /api/v1/chat/message`

### 📞 **Support**
- Documentation: [GitHub Repository](https://github.com/homeview-ai)
- Issues: [GitHub Issues](https://github.com/homeview-ai/issues)
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "HomeView AI Support",
        "url": "https://homeview.ai/support",
        "email": "support@homeview.ai"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User authentication and authorization endpoints. Register, login, and manage JWT tokens."
        },
        {
            "name": "chat",
            "description": "Conversational AI chat interface. Send messages and get context-aware responses about your home."
        },
        {
            "name": "products",
            "description": "Product catalog and matching. Search products and get dimension-aware recommendations for your rooms."
        },
        {
            "name": "digital-twin",
            "description": "Digital twin creation and management. Upload floor plans and room images to create digital home representations."
        },
        {
            "name": "intelligence",
            "description": "AI intelligence services. Cost estimation, product matching, and smart recommendations."
        },
        {
            "name": "design",
            "description": "Design studio and image generation. Transform room designs with AI-powered style transfer and variations."
        },
        {
            "name": "documents",
            "description": "Document parsing endpoints. Upload contractor quotes, datasheets, and inspection reports to extract structured data."
        },
        {
            "name": "health",
            "description": "System health and monitoring endpoints."
        },
        {
            "name": "journey",
            "description": "Journey management for tracking user progress through home improvement projects."
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
# Get allowed origins from environment variable or use defaults
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:8000").split(",")

# For development, allow all origins (including file:// protocol for local HTML files)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add monitoring middleware (first to track all requests)
app.add_middleware(MonitoringMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(product_router)
app.include_router(digital_twin_router)
app.include_router(intelligence_router)
app.include_router(intelligence_v1_router)  # NEW: V1 Intelligence API (image gen, grounding)
app.include_router(design_router)
app.include_router(documents_router)
app.include_router(admin_router)
app.include_router(monitoring_router)  # NEW: Monitoring and health checks
app.include_router(journey_router)  # NEW: Journey management
app.include_router(multimodal_router)  # NEW: Multimodal processing (video/audio/image)
app.include_router(workflows_router)  # NEW: AI agentic workflows (home tour, DIY, contractor)

# LEGACY: ChatOrchestrator-based chat API (feature-flagged)
ENABLE_LEGACY_CHAT_ORCHESTRATOR = os.getenv("ENABLE_LEGACY_CHAT_ORCHESTRATOR", "true").lower() == "true"
if ENABLE_LEGACY_CHAT_ORCHESTRATOR:
    app.include_router(chat_workflow_router)  # Legacy ChatOrchestrator API (/api/v1/chat/orchestrator/*)
    logger.info("Legacy ChatOrchestrator API enabled")
else:
    logger.info("Legacy ChatOrchestrator API disabled; using ChatWorkflow-only chat API")

# Mount static files for frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# Mount uploads for serving images in studio/room views
uploads_path = Path("uploads")
if uploads_path.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")
# Mount generated_images for chat image generations
generated_path = Path("generated_images")
if generated_path.exists():
    app.mount("/generated_images", StaticFiles(directory=str(generated_path)), name="generated_images")




@app.get("/")
async def root():
    """Serve the frontend UI."""
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        return FileResponse(frontend_file)
    return {
        "message": "Welcome to HomeVision AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns the current health status of the API and its dependencies.
    """
    import psutil
    import time
    from datetime import datetime, timezone

    return {
        "status": "healthy",
        "service": "HomeView AI API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": time.time() - psutil.boot_time(),
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    }


@app.get("/health/ready", tags=["health"])
async def readiness_check():
    """
    Readiness check endpoint.

    Returns whether the API is ready to accept requests.
    Checks database connectivity and other critical dependencies.
    """
    from backend.models.base import get_async_session
    from datetime import datetime, timezone
    from sqlalchemy import text

    checks = {
        "database": False,
        "api": True
    }

    # Check database connectivity
    try:
        async for session in get_async_session():
            await session.execute(text("SELECT 1"))
            checks["database"] = True
            break
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = False

    all_healthy = all(checks.values())

    return {
        "ready": all_healthy,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/health/live", tags=["health"])
async def liveness_check():
    """
    Liveness check endpoint.

    Returns whether the API is alive and responding.
    Used by orchestrators like Kubernetes to determine if the pod should be restarted.
    """
    from datetime import datetime, timezone

    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/metrics", tags=["health"])
async def get_metrics():
    """
    Get API metrics and performance statistics.

    Returns detailed metrics including:
    - Request counts and durations
    - Error rates
    - Status code distributions
    - Endpoint-specific metrics
    """
    monitoring = get_monitoring_service()
    return monitoring.get_metrics()


@app.get("/metrics/{method}/{path:path}", tags=["health"])
async def get_endpoint_metrics(method: str, path: str):
    """
    Get metrics for a specific endpoint.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Endpoint path

    Returns:
        Endpoint-specific metrics
    """
    monitoring = get_monitoring_service()
    metrics = monitoring.get_endpoint_metrics(f"/{path}", method.upper())

    if metrics is None:
        return {
            "error": "No metrics found for this endpoint",
            "endpoint": f"{method.upper()} /{path}"
        }

    return metrics


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request, exc: RequestValidationError):
    """Custom handler for validation errors to avoid encoding binary data."""
    logger.warning(f"Validation error: {exc}")
    # Return a simplified error message without trying to encode binary data
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "error_count": len(exc.errors()),
            "message": "Please check your request format and try again"
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(_request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

