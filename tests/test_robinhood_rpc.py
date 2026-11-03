import json

import httpx
import pytest
from app.services import robinhood_listing as listing


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "chain,code,error",
    [
        ("0x1237", "0x6000", None),
        ("0x1237", "0x", "No contract"),
        ("0x1", "0x6000", "chain mismatch"),
    ],
)
async def test_rpc_inspection(monkeypatch, chain, code, error):
    def reply(req):
        call = json.loads(req.content)
        values = {
            "eth_chainId": chain,
            "eth_blockNumber": "0x10",
            "eth_getCode": code,
            "eth_call": None,
        }
        if call["method"] == "eth_call" and call["params"][0]["data"] == "0x95d89b41":
            values["eth_call"] = "0x" + b"TOK".ljust(32, b"\0").hex()
        return httpx.Response(200, json={"result": values[call["method"]]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    monkeypatch.setattr(listing.httpx, "AsyncClient", lambda **kwargs: client)
    if error:
        with pytest.raises(ValueError, match=error):
            await listing.inspect_contract(4663, "0x" + "ab" * 20)
    else:
        result = await listing.inspect_contract(4663, "0x" + "ab" * 20)
        assert result["metadata"] == {"symbol": "TOK"}
        assert result["missing"] == ["decimals", "name"]
