import asyncpg
import asyncio

async def check():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/ancap_test')
        result = await conn.execute('SELECT 1')
        print(f'DB OK: {result}')
        await conn.close()
    except Exception as e:
        print(f'DB error: {e}')

asyncio.run(check())
