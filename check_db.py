"""Check and create test database."""
import asyncio
from sqlalchemy import create_engine, text

# Try to connect and check if database exists
db_url = 'postgresql://postgres:postgres@localhost:5432/ancap_test'
engine = create_engine(db_url)

with engine.connect() as conn:
    # Check if database exists
    result = conn.execute(text("SELECT datname FROM pg_database WHERE datname = 'ancap_test'"))
    row = result.fetchone()
    if row:
        print('Database ancap_test exists')
    else:
        print('Database ancap_test does not exist, creating...')
        # Create database
        conn.execute(text("CREATE DATABASE ancap_test"))
        conn.commit()
        print('Database created successfully')

engine.dispose()
