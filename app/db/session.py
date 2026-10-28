"""Async database session and engine."""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.config import get_settings
from app.db.base import Base

# Use the same URL builder as conftest.py to ensure consistency
def _make_async_connection_string():
    """Build async connection string with proper encoding."""
    url = os.environ.get("DATABASE_URL", "")
    if "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Add client_encoding for Windows compatibility
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    if 'client_encoding' not in params:
        params['client_encoding'] = 'utf8'
    new_query = urllib.parse.urlencode(params, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))

settings = get_settings()

engine = create_async_engine(
    _make_async_connection_string(),
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
    _make_async_connection_string(),
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
