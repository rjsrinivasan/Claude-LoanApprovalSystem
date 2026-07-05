"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config.settings import get_settings
from database.connection import DatabaseConnection
from utils.logging_config import setup_logging


# Initialize logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for app startup/shutdown."""
    # Startup
    DatabaseConnection.initialize()
    print("✓ Database connection initialized")
    yield
    # Shutdown
    DatabaseConnection.close()
    print("✓ Database connections closed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI app
    """
    settings = get_settings()

    app = FastAPI(
        title="Loan Approval System",
        description="Multi-Agent AI system for intelligent loan approval",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(router)

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        return {
            "message": "Loan Approval System API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
        }

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
