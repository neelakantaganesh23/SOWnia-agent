"""FastAPI application entry point for SOWnia.

Configures the application with CORS, logging middleware,
and registers all API route modules.
"""

import logging

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from backend.api.middleware.cors import setup_cors
from backend.api.middleware.logging import setup_logging
from backend.api.routes import auth, upload, review, results
from backend.config import settings

# Configure module logger
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="SOWnia API",
    description="AI-Powered Multi-Agent SOW Review System. "
    "Upload SOW documents (PDF/DOCX) and receive automated, "
    "multi-domain review findings from specialized AI agents.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup middleware
setup_cors(app)
setup_logging(app)

# Register routes
app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(review.router, prefix="/api/v1", tags=["Review"])
app.include_router(results.router, prefix="/api/v1", tags=["Results"])


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root path to interactive Swagger API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint.

    Used by Docker health checks, HF Spaces, and monitoring.

    Returns:
        Service health status.
    """
    return {
        "status": "healthy",
        "service": "sownia-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info(
        f"SOWnia API starting up (environment: {settings.ENVIRONMENT})..."
    )
    logger.info(
        f"CORS origins: {settings.allowed_origins_list}"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("SOWnia API shutting down...")
