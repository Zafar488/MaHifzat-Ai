"""Main FastAPI application — entry point for the MaaHifazat AI backend."""
import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.db.engine import init_db
from backend.services.inference import ModelRegistry
from backend.api.routes import agents, patients, referrals, risks, alerts, audit, analytics
from backend.api.auth import auth_router

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown logic."""
    # --- Startup ---
    logger.info("MaaHifazat AI backend starting up …")

    try:
        await init_db()
        logger.info("Database initialised.")
    except Exception as exc:
        logger.warning("DB init failed (non-fatal in dev): %s", exc)

    try:
        registry = ModelRegistry()
        registry.load_all()
        logger.info("ML models loaded: %s", registry.health_check())
    except Exception as exc:
        logger.warning("Model loading failed (non-fatal): %s", exc)

    yield  # application runs here

    # --- Shutdown ---
    logger.info("MaaHifazat AI backend shutting down.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


app = FastAPI(
    title="MaaHifazat AI — Maternal Health Platform",
    description=(
        "AI-powered maternal and fetal health monitoring platform "
        "for rural Pakistan. Provides risk prediction, smart referrals, "
        "and multi-channel communication."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ---------------------------------------------------------------------------
# CORS middleware  (permissive for development — tighten in production)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a structured JSON error for any unhandled exception."""
    logger.error(
        "Unhandled error on %s %s: %s\n%s",
        request.method,
        request.url.path,
        str(exc),
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url.path),
        },
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/api/health", tags=["system"])
async def health_check():
    """Return API liveness and model availability."""
    registry = ModelRegistry()
    return {
        "status": "ok",
        "models": registry.health_check(),
    }


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

# Authentication
app.include_router(auth_router, prefix="/api")

# Core clinical routes
app.include_router(patients.router, prefix="/api")
app.include_router(risks.router, prefix="/api")
app.include_router(referrals.router, prefix="/api")
app.include_router(agents.router, prefix="/api")

# Alerts, audit, analytics
app.include_router(alerts.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
