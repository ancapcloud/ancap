"""Signed opt-in grants, restricted by both ANCAP account and verified EVM wallet.

The dedicated signer can authorize only this campaign's on-chain capped budget.
It is not the treasury signer. No user passwords, email addresses or wallet keys
are included in vouchers or public chain data. Identity hashes are opaque UUID hashes.
"""
import json
import time
from pathlib import Path

import httpx
from eth_account import Account as EvmAccount
from eth_account.messages import encode_typed_data
from eth_utils import is_address, keccak, to_checksum_address
from fastapi import HTTPException
from sqlalchemy import select

from app.config import get_settings
from app.db.models import UserEvmWallet
from app.schemas.racp_airdrop import RacpAirdropStatus, RacpAirdropVoucher

TOKEN = "0xD53f91A63f95beAc61Ec8417c40C5e620FE3a911"
RPC = "https://rpc.mainnet.chain.robinhood.com"
GRANT_WEI = 500 * 10**18
BUDGET_WEI = 1_000_000 * 10**18


def campaign_config():
    path = Path(get_settings().racp_airdrop_config_file)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data.get("enabled"):
            return None
        if not is_address(data.get("contract", "")):
            raise ValueError("Invalid campaign contract")
        return {"contract": to_checksum_address(data["contract"])}
    except (ValueError, OSError) as e:
        raise HTTPException(503, "Airdrop configuration is unavailable") from e


def selector(signature):
    return "0x" + keccak(text=signature)[:4].hex()


async def chain_state(pool, recipient=None, identity=None):
    methods = [("eth_chainId", [])]
    reads = [(pool, selector("totalClaimed()")), (pool, selector("paused()")),
             (TOKEN, selector("balanceOf(address)") + pool[2:].lower().rjust(64, "0")),
             (pool, selector("signer()"))]
    if recipient is not None:
        reads += [(pool, selector("claimed(address)") + recipient[2:].lower().rjust(64, "0")),
                  (pool, selector("claimedIdentity(bytes32)") + identity[2:])]
    methods += [("eth_call", [{"to": to, "data": data}, "latest"]) for to, data in reads]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(RPC, json=[{"jsonrpc": "2.0", "id": n, "method": method, "params": params} for n, (method, params) in enumerate(methods)])
            response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list) or len(payload) != len(methods):
            raise ValueError("Invalid RPC batch")
        results = {r["id"]: r for r in payload}
        values = [int(results[n]["result"], 16) for n in range(len(methods))]
        if values[0] != 4663 or values[1] > BUDGET_WEI:
            raise ValueError("Unexpected campaign state")
        return {"distributed": values[1], "paused": bool(values[2]), "balance": values[3], "signer": to_checksum_address("0x" + format(values[4], "040x")),
                "claimed": bool(values[5]) if recipient is not None else False,
                "identity_claimed": bool(values[6]) if recipient is not None else False}
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as e:
        raise HTTPException(503, "Live airdrop state is unavailable; no voucher issued") from e


async def public_status():
    config = campaign_config()
    if config is None:
        return RacpAirdropStatus(enabled=False, token_contract=TOKEN)
    state = await chain_state(config["contract"])
    available = min(state["balance"], BUDGET_WEI - state["distributed"])
    return RacpAirdropStatus(enabled=not state["paused"] and available >= GRANT_WEI, token_contract=TOKEN,
        airdrop_contract=config["contract"], distributed=str(state["distributed"] // 10**18),
        available=str(available // 10**18), remaining_claims=available // GRANT_WEI, paused=state["paused"])


def typed_claim(pool, recipient, identity, deadline):
    return {"types": {
        "EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}, {"name": "chainId", "type": "uint256"}, {"name": "verifyingContract", "type": "address"}],
        "Claim": [{"name": "recipient", "type": "address"}, {"name": "eligibilityId", "type": "bytes32"}, {"name": "deadline", "type": "uint256"}]},
        "primaryType": "Claim", "domain": {"name": "ANCAP rACP Airdrop", "version": "1", "chainId": 4663, "verifyingContract": pool},
        "message": {"recipient": recipient, "eligibilityId": identity, "deadline": deadline}}


async def issue_voucher(session, user_id, address):
    if not is_address(address) or int(address, 16) == 0:
        raise HTTPException(400, "Invalid wallet address")
    linked = (await session.execute(select(UserEvmWallet).where(UserEvmWallet.user_id == user_id))).scalar_one_or_none()
    if linked is None or linked.wallet_address.lower() != address.lower():
        raise HTTPException(403, "Verify and link this wallet to your ANCAP account first")
    config = campaign_config()
    if config is None:
        raise HTTPException(503, "Airdrop is not active")
    recipient = to_checksum_address(address)
    identity = "0x" + keccak(text=f"ancap:racp-airdrop:v1:{user_id}").hex()
    state = await chain_state(config["contract"], recipient, identity)
    if state["claimed"] or state["identity_claimed"]:
        raise HTTPException(409, "This account or wallet has already received its grant")
    if state["paused"] or min(state["balance"], BUDGET_WEI - state["distributed"]) < GRANT_WEI:
        raise HTTPException(409, "Airdrop is paused or exhausted")
    try:
        key = Path(get_settings().racp_airdrop_signer_file).read_text(encoding="utf-8").strip()
        if EvmAccount.from_key(key).address != state["signer"]:
            raise ValueError("Signer mismatch")
        deadline = int(time.time()) + 600
        message = encode_typed_data(full_message=typed_claim(config["contract"], recipient, identity, deadline))
        signature = "0x" + bytes(EvmAccount.sign_message(message, key).signature).hex()
    except (OSError, ValueError) as e:
        raise HTTPException(503, "Airdrop signer is unavailable") from e
    return RacpAirdropVoucher(airdrop_contract=config["contract"], token_contract=TOKEN, recipient=recipient,
        eligibility_id=identity, deadline=deadline, signature=signature)
