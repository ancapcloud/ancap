"""Async database session and engine."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.config import get_settings
from app.db.base import Base as Base

settings = get_settings()

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



__all__ = ["Base", "engine", "async_session_maker", "SessionLocal", "get_db"]


async def init_db(session: AsyncSession):
    """Apply all pending migrations to the database."""
    from app.db.models import Base
    await session.execute("SELECT max(version) FROM alembic_version")
    result = await session.execute("SELECT max(version) FROM alembic_version")
    current_max = result.scalar_one_or_none()
    if current_max is None:
        # No migrations applied yet, create initial record
        from sqlalchemy import text
        await session.execute(text("INSERT INTO alembic_version (version) VALUES ('base')"))
        await session.commit()
    await Base.metadata.create_all(bind=engine)
