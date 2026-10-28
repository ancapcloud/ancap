import asyncpg
import asyncio

async def setup():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/postgres')
        # Create test database if not exists
        await conn.execute("CREATE DATABASE ancap_test")
        print('Database ancap_test created/exists')
        
        # Connect to test db
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/ancap_test')
        result = await conn.execute('SELECT 1')
        print(f'Test DB OK: {result}')
        await conn.close()
    except Exception as e:
        print(f'Error: {e}')

asyncio.run(setup())
