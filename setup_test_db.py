"""Setup test database schema."""
import asyncio
from sqlalchemy import create_engine, text
from app.db.session import Base, async_session_maker
from app.config import get_settings

settings = get_settings()
db_url = settings.database_url or 'postgresql+asyncpg://postgres:postgres@localhost:5432/ancap_test'
print('Using DB URL:', db_url)

# Create sync engine for setup
sync_url = db_url.replace('+asyncpg', '').replace('postgresql+asyncpg', 'postgresql')
sync_engine = create_engine(sync_url, pool_pre_ping=True)

with sync_engine.connect() as conn:
    # Drop and recreate schema
    conn.execute(text('DROP SCHEMA IF EXISTS public CASCADE'))
    conn.execute(text('CREATE SCHEMA public'))
    
    # Create tables
    Base.metadata.create_all(sync_engine)
    
    # Stamp alembic
    conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('00000000000000_initial_test_schema')"))
    
conn.close()
print('Test schema created successfully')
