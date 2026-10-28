"""Operator ACP fund reconcile: on-chain UTXO vs ledger entitlement gaps.

Dry-run by default. Execute only transfers custodial hot → user address when
policy allows (ledger credit, zero/low on-chain). Does not invent issuance.
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import User, UserAcpWallet
from app.services.acp_tokenomics import CUSTODIAL_HOT_ADDRESS

logger = logging.getLogger(__name__)



def _parse_decimal(value: object) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal(0)


def _walletd_cmd() -> list[str]:
    import os

    p = (os.getenv("ACP_WALLETD_PATH") or "").strip()
    if p:
        return [p]
    if shutil.which("walletd"):
        return ["walletd"]
    raise RuntimeError("walletd not configured")


def _run_walletd(args: list[str], timeout_s: int = 90) -> dict:
    proc = subprocess.run(
        _walletd_cmd() + args,
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    out = (proc.stdout or "").strip()
    payload = json.loads(out) if out else {}
    if proc.returncode != 0 or not payload.get("ok"):
        raise RuntimeError(payload.get("error") or proc.stderr or "walletd failed")
    return payload.get("result") or {}


def _on_chain_acp(address: str) -> Decimal:
    settings = get_settings()
    rpc = (settings.acp_rpc_url or "").strip() or "http://127.0.0.1:8545/rpc"
    res = _run_walletd(["balance", "--rpc", rpc, "--address", address])
    return _parse_decimal(res.get("acp"))


async def _ledger_credits_for_user(session: AsyncSession, user_id: str) -> Decimal:
    # Local import avoids circular wallet_acp ↔ reclaim paths at module load.
    from app.api.routers.wallet_acp import _in_work_breakdown_for_user

    _total, _staked, ledger = await _in_work_breakdown_for_user(session, user_id)
    return ledger


def classify_gap(*, on_chain: Decimal, ledger: Decimal) -> str | None:
    """Return gap kind or None when healthy."""
    if ledger <= 0:
        return None
    if on_chain <= 0:
        return "ledger_credit_chain_zero"
    if ledger > on_chain + Decimal("0.00000001"):
        return "ledger_exceeds_chain"
    return None


async def build_reconcile_report(
    session: AsyncSession,
    *,
    limit: int = 500,
    only_gaps: bool = True,
) -> dict[str, Any]:
    rows = (
        await session.execute(
            select(UserAcpWallet, User.email)
            .join(User, User.id == UserAcpWallet.user_id)
            .order_by(UserAcpWallet.created_at.asc())
            .limit(limit)
        )
    ).all()

    items: list[dict[str, Any]] = []
    gaps = 0
    for wallet, email in rows:
        address = (wallet.address or "").strip()
        if not address:
            continue
        try:
            on_chain = _on_chain_acp(address)
        except Exception as exc:
            items.append(
                {
                    "user_id": str(wallet.user_id),
                    "email": email,
                    "address": address,
                    "error": str(exc),
                    "gap": "scan_error",
                }
            )
            gaps += 1
            continue
        ledger = await _ledger_credits_for_user(session, str(wallet.user_id))
        gap = classify_gap(on_chain=on_chain, ledger=ledger)
        if only_gaps and gap is None:
            continue
        if gap:
            gaps += 1
        items.append(
            {
                "user_id": str(wallet.user_id),
                "email": email,
                "address": address,
                "on_chain_acp": str(on_chain),
                "ledger_credits_acp": str(ledger),
                "gap": gap,
                "is_custodial_hot": address == CUSTODIAL_HOT_ADDRESS,
                "suggested_restore_acp": str(ledger) if gap == "ledger_credit_chain_zero" else "0",
            }
        )

    return {
        "dry_run": True,
        "scanned": len(rows),
        "gap_count": gaps,
        "items": items,
        "note": (
            "Dry-run only. Execute via POST /platform-admin/acp-reconcile/execute "
            "with confirm=true for custodial hot transfers covering ledger_credit_chain_zero gaps."
        ),
    }


async def execute_restore_gaps(
    session: AsyncSession,
    *,
    user_ids: list[str] | None = None,
    confirm: bool = False,
    max_transfers: int = 20,
) -> dict[str, Any]:
    if not confirm:
        raise ValueError("confirm=true required to move coin from custodial hot")

    report = await build_reconcile_report(session, limit=2000, only_gaps=True)
    candidates = [
        i
        for i in report["items"]
        if i.get("gap") == "ledger_credit_chain_zero"
        and not i.get("is_custodial_hot")
        and _parse_decimal(i.get("suggested_restore_acp")) > 0
    ]
    if user_ids:
        allow = {str(u) for u in user_ids}
        candidates = [c for c in candidates if c["user_id"] in allow]

    settings = get_settings()
    rpc = (settings.acp_rpc_url or "").strip() or "http://127.0.0.1:8545/rpc"
    ks = (getattr(settings, "acp_hot_mnemonic_file", None) or "").strip()
    # Prefer keystore path used by bridge hot transfer helpers when present.
    import os

    ks_json = (os.getenv("ACP_HOT_KEYSTORE_JSON") or "").strip()
    ks_path = (os.getenv("ACP_HOT_KEYSTORE_FILE") or "").strip()

    transfers: list[dict[str, Any]] = []
    for item in candidates[:max_transfers]:
        amount = str(item["suggested_restore_acp"])
        to_addr = item["address"]
        args = ["transfer", "--rpc", rpc, "--to", to_addr, "--amount-acp", amount]
        if ks_json:
            args.extend(["--keystore-json", ks_json])
        elif ks_path:
            args.extend(["--keystore-file", ks_path])
        elif ks:
            args.extend(["--mnemonic-file", ks])
        else:
            transfers.append(
                {
                    "user_id": item["user_id"],
                    "address": to_addr,
                    "amount_acp": amount,
                    "ok": False,
                    "error": "No custodial hot signing material configured",
                }
            )
            continue
        try:
            res = _run_walletd(args, timeout_s=180)
            transfers.append(
                {
                    "user_id": item["user_id"],
                    "address": to_addr,
                    "amount_acp": amount,
                    "ok": bool(res.get("accepted") or res.get("txid")),
                    "txid": res.get("txid"),
                    "result": res,
                }
            )
        except Exception as exc:
            logger.exception("acp reconcile transfer failed for %s", to_addr)
            transfers.append(
                {
                    "user_id": item["user_id"],
                    "address": to_addr,
                    "amount_acp": amount,
                    "ok": False,
                    "error": str(exc),
                }
            )

    return {
        "dry_run": False,
        "attempted": len(transfers),
        "transfers": transfers,
        "skipped": max(0, len(candidates) - len(transfers)),
    }
