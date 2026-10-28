import asyncpg
import asyncio

async def check():
    conn = await asyncpg.connect('postgresql://postgres@localhost:5432/ancap')
    await conn.close()
    print('PostgreSQL ready')
    return True

asyncio.run(check())
