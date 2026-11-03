import os

import httpx

NETWORKS = {
    4663: ("mainnet", "https://robinhoodchain.blockscout.com"),
    46630: ("testnet", "https://explorer.testnet.chain.robinhood.com"),
}


async def inspect_contract(chain_id: int, address: str) -> dict:
    network, explorer = NETWORKS[chain_id]
    url = (
        os.getenv(f"ROBINHOOD_{network.upper()}_RPC_URL")
        or f"https://rpc.{network}.chain.robinhood.com"
    )
    async with httpx.AsyncClient(timeout=6) as client:

        async def rpc(method, params):
            response = await client.post(
                url,
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
            )
            response.raise_for_status()
            return response.json().get("result")

        if int(await rpc("eth_chainId", []), 16) != chain_id:
            raise ValueError("RPC chain mismatch")
        block = await rpc("eth_blockNumber", [])
        int(block, 16)
        code = await rpc("eth_getCode", [address, block])
        if not code or code == "0x":
            raise ValueError("No contract code")
        metadata = {}
        for field, selector in (
            ("name", "06fdde03"),
            ("symbol", "95d89b41"),
            ("decimals", "313ce567"),
        ):
            raw = await rpc(
                "eth_call", [{"to": address, "data": "0x" + selector}, block]
            )
            if not isinstance(raw, str) or not raw.startswith("0x"):
                continue
            try:
                data = bytes.fromhex(raw[2:])
                if field == "decimals":
                    if len(data) == 32 and int.from_bytes(data, "big") <= 255:
                        metadata[field] = int.from_bytes(data, "big")
                else:
                    if len(data) == 32:
                        value = data.rstrip(b"\0")
                    elif len(data) >= 64 and int.from_bytes(data[:32], "big") == 32:
                        size = int.from_bytes(data[32:64], "big")
                        if size > min(512, len(data) - 64):
                            continue
                        value = data[64 : 64 + size]
                    else:
                        continue
                    if value:
                        metadata[field] = value.decode()
            except (ValueError, UnicodeError):
                continue
        return {
            "network": network,
            "block": block,
            "explorer": f"{explorer}/address/{address}",
            "metadata": metadata,
            "missing": sorted({"name", "symbol", "decimals"} - metadata.keys()),
        }
