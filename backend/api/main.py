"""API entrypoint. Separate liveness/readiness; no sensitive error details."""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.config import settings
from backend.db.engine import init_db
from backend.services.inference import ModelRegistry
from backend.api.deps import get_db
from backend.api.routes import agents, patients, referrals, risks, alerts, audit, analytics, followups, facilities, care, models, helper
from backend.api.auth import auth_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    await init_db()  # Fail startup on DB errors; never swallow them.
    ModelRegistry().load_all()
    yield


app = FastAPI(title="MaaHifazat AI maternal care", description="Experimental clinical support requiring qualified review.", version=settings.APP_VERSION, lifespan=lifespan, docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=False, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    logger.error("Unhandled API error (%s)", type(exc).__name__)
    return JSONResponse(status_code=500, content={"error": "Internal server error", "detail": "Request could not be completed"})


@app.get("/api/health")
async def health():
    from backend.services.model_workbench import catalog
    execution={item["name"]:item["executable"] for item in catalog()}
    return {"status": "ok", "model_execution":execution,"models": ModelRegistry().health_check(), "demo_mode": settings.DEMO_MODE, "clinical_validation": "not established"}


@app.get("/api/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    try:
        # Check migrated tables as well as connectivity.
        from backend.db.models import User, CaseRecord
        from sqlalchemy import select
        await db.execute(select(User.id).limit(1))
        await db.execute(select(CaseRecord.id).limit(1))
        database_ready = True
    except Exception:
        database_ready = False
    health = ModelRegistry().health_check()
    models_ready = health["maternalguard"] and health["fetalwatch"]
    ready = database_ready and (models_ready or not settings.REQUIRE_MODELS)
    return JSONResponse(status_code=200 if ready else 503, content={"status": "ready" if ready else "not_ready", "database": database_ready, "models": health, "supported_models_ready": models_ready})


for router in (auth_router, patients.router, risks.router, referrals.router, agents.router, alerts.router, audit.router, analytics.router, followups.router, facilities.router, care.router, models.router, helper.router):
    app.include_router(router, prefix="/api")
