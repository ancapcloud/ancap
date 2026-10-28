from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import (
    ChainReceipt,
    ChainReceiptStatusEnum,
    LedgerEvent,
    LedgerEventTypeEnum,
    SettlementIntent,
    SettlementIntentStatusEnum,
)
from app.services.chain_anchor import get_anchor_driver
from app.services.ledger import append_event, get_or_create_account


INTENT_TO_LEDGER_EVENT: dict[str, LedgerEventTypeEnum] = {
    "escrow_open": LedgerEventTypeEnum.contract_escrow,
    "escrow_release": LedgerEventTypeEnum.contract_payout,
    "stake_lock": LedgerEventTypeEnum.stake,
    "stake_unlock": LedgerEventTypeEnum.unstake,
    "slash": LedgerEventTypeEnum.slash,
}


def build_correlation_id(provided: str | None) -> str:
    raw = (provided or "").strip()
    return raw or f"settlement-{uuid4().hex}"


def _hash_payload(intent: SettlementIntent) -> str:
    payload = {
        "intent_id": str(intent.id),
        "intent_type": intent.intent_type,
        "source_owner_type": intent.source_owner_type,
        "source_owner_id": str(intent.source_owner_id),
        "target_owner_type": intent.target_owner_type,
        "target_owner_id": str(intent.target_owner_id),
        "amount_currency": intent.amount_currency,
        "amount_value": str(intent.amount_value),
        "correlation_id": intent.correlation_id,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


async def execute_settlement_intent(session: AsyncSession, intent: SettlementIntent) -> tuple[SettlementIntent, ChainReceipt]:
    settings = get_settings()
    driver_name = (settings.chain_anchor_driver or "mock").strip() or "mock"
    chain_id = "acp" if driver_name == "acp" else driver_name

    payload_hash = _hash_payload(intent)
    receipt = ChainReceipt(
        settlement_intent_id=intent.id,
        chain_id=chain_id,
        status=ChainReceiptStatusEnum.submitted.value,
        correlation_id=intent.correlation_id,
        payload_hash=payload_hash,
        receipt_json={"driver": driver_name, "stage": "submitted"},
    )
    session.add(receipt)
    await session.flush()

    if intent.status == SettlementIntentStatusEnum.executed.value:
        receipt.status = ChainReceiptStatusEnum.finalized.value
        receipt.finalized_at = datetime.utcnow()
        receipt.receipt_json = {
            "driver": driver_name,
            "payload_hash": payload_hash,
            "chain_id": chain_id,
            "status": "finalized",
            "replayed": True,
            "note": "Settlement intent was already executed; skipped duplicate execution.",
        }
        await session.flush()
        return intent, receipt

    try:
        src_account = await get_or_create_account(session, intent.source_owner_type, intent.source_owner_id)
        dst_account = await get_or_create_account(session, intent.target_owner_type, intent.target_owner_id)
        event_type = INTENT_TO_LEDGER_EVENT[intent.intent_type]

        existing_ledger_event = (
            await session.execute(
                select(LedgerEvent).where(
                    LedgerEvent.metadata_.contains({"settlement_intent_id": str(intent.id)})
                ).limit(1)
            )
        ).scalar_one_or_none()
        if existing_ledger_event is None:
            await append_event(
                session,
                event_type,
                intent.amount_currency,
                Decimal(intent.amount_value),
                src_account_id=src_account.id,
                dst_account_id=dst_account.id,
                metadata={"settlement_intent_id": str(intent.id), "correlation_id": intent.correlation_id},
            )

        driver = get_anchor_driver(driver_name)
        if not driver:
            raise ValueError(f"Unsupported chain driver: {driver_name}")
        anchor = await driver(
            session,
            chain_id=chain_id,
            payload_type="settlement",
            payload_hash=payload_hash,
            payload_json={"settlement_intent_id": str(intent.id), "intent_type": intent.intent_type},
        )

        intent.status = SettlementIntentStatusEnum.executed.value
        intent.error_message = None
        intent.executed_at = datetime.utcnow()
        receipt.status = ChainReceiptStatusEnum.finalized.value
        receipt.finalized_at = datetime.utcnow()
        receipt.tx_hash = anchor.tx_hash
        receipt.node_public_key = f"{driver_name}-rpc"
        receipt.node_signature = hashlib.sha256(f"{driver_name}:{anchor.tx_hash}:{payload_hash}".encode("utf-8")).hexdigest()
        receipt.receipt_json = {
            "driver": driver_name,
            "anchor_id": str(anchor.id),
            "payload_hash": payload_hash,
            "chain_id": chain_id,
            "tx_hash": anchor.tx_hash,
            "status": "finalized",
            "ledger_event_reused": existing_ledger_event is not None,
        }
    except Exception as exc:
        intent.status = SettlementIntentStatusEnum.failed.value
        intent.error_message = str(exc)
        receipt.status = ChainReceiptStatusEnum.failed.value
        receipt.error_message = str(exc)
        receipt.receipt_json = {"driver": driver_name, "status": "failed", "error": str(exc)}

    await session.flush()
    return intent, receipt
