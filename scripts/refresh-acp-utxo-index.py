"""Refresh wallet balances independently of the commerce jobs transaction.

Run inside the API container: python - < scripts/refresh-acp-utxo-index.py
"""
import asyncio
import json

from app.db.session import async_session_maker
from app.jobs.mobile_acp_indexer_tick import build_address_watchlist
from app.services.acp_utxo_index import acp_utxo_index_tick


async def main():
    async with async_session_maker() as session:
        addresses = await build_address_watchlist(session)
    result = await acp_utxo_index_tick(
        extra_addresses=addresses, chunk=500, max_chunks=4
    )
    print(json.dumps(result), flush=True)
    if not result.get("ok") or not result.get("caught_up"):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
