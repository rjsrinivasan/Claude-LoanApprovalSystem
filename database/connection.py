"""Database connection management."""

import logging
from typing import Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from config.settings import get_settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections and session creation."""

    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None

    @classmethod
    def initialize(cls) -> None:
        """Initialize database connection pool."""
        if cls._engine is not None:
            return

        settings = get_settings()

        # Create engine with connection pooling
        cls._engine = create_engine(
            settings.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
            echo=False,
            connect_args={"connect_timeout": 10},
        )

        # Register event listener for connection pool
        @event.listens_for(Engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Configure connection on creation."""
            if hasattr(dbapi_conn, "timeout"):
                dbapi_conn.timeout = 10

        cls._session_factory = sessionmaker(
            bind=cls._engine,
            expire_on_commit=False,
            autoflush=False,
        )

        logger.info("Database connection initialized")

    @classmethod
    def get_session(cls) -> Session:
        """Get a new database session."""
        if cls._session_factory is None:
            cls.initialize()
        return cls._session_factory()

    @classmethod
    def close(cls) -> None:
        """Close all connections."""
        if cls._engine is not None:
            cls._engine.dispose()
            logger.info("Database connections closed")

    @classmethod
    def health_check(cls) -> bool:
        """Check database connectivity."""
        try:
            if cls._engine is None:
                cls.initialize()

            with cls._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database health check passed")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False


def get_db_session() -> Session:
    """Dependency injection for database sessions."""
    session = DatabaseConnection.get_session()
    try:
        yield session
    finally:
        session.close()
