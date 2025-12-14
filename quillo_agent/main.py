"""
Main FastAPI application with request logging
"""
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .config import settings
from .routers import health, route, plan, memory, feedback


# Configure loguru
logger.add(
    "logs/quillo_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    logger.info("🚀 Quillo Agent starting up...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Database: {settings.database_url}")
    yield
    logger.info("👋 Quillo Agent shutting down...")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title="Quillo Agent",
        description="AI Chief of Staff orchestrator - MVP",
        version="0.1.0",
        lifespan=lifespan
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests with timing"""
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        logger.info(
            f"[{request_id}] {request.method} {request.url.path}"
        )

        response = await call_next(request)

        duration = time.time() - start_time
        logger.info(
            f"[{request_id}] Completed {response.status_code} "
            f"in {duration:.3f}s"
        )

        return response

    # Include routers
    app.include_router(health.router)
    app.include_router(route.router)
    app.include_router(plan.router)
    app.include_router(memory.router)
    app.include_router(feedback.router)

    return app
