from app.db.session import _sessionlocal_engine, SessionLocal
from sqlalchemy import text
import asyncio

async def check():
    session = SessionLocal()
    try:
        result = await session.execute(text("SELECT revision FROM alembic_version LIMIT 1"))
        return result.scalar()
    finally:
        await session.close()

print(asyncio.run(check()))
