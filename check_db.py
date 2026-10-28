import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(host='localhost', database='postgres', user='postgres')
    rows = await conn.fetch("SELECT datname FROM pg_database WHERE datname = 'ancap_test';")
    print(rows)
    await conn.close()

asyncio.run(main())
