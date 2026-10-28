"""Async database session and engine."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.config import get_settings
from app.db.base import Base as Base

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Backward-compatible helper for direct one-off session use from a different
# event loop (for example sync pytest helpers calling asyncio.run()). Keep it on
# a separate NullPool engine so asyncpg connections are never reused across
# loops.
_sessionlocal_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    poolclass=NullPool,
)
SessionLocal = async_sessionmaker(
    _sessionlocal_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    """Dependency: yield async session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()



# Stable imports used by application startup, migrations and test utilities.
__all__ = ["Base", "engine", "async_session_maker", "SessionLocal", "get_db"]
