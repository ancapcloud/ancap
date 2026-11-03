from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.api.deps import DbSession, require_auth, require_platform_admin
from app.db.models import PaymentIntent, RobinhoodListing, WorkflowRunRecord
from app.schemas.robinhood_listing import ListingDraft, ListingReview, ListingVersion
from app.services.robinhood_listing import inspect_contract

router = APIRouter(prefix="/workflow-store/robinhood", tags=["Robinhood listings"])


async def owned(db, run_id, user, lock=False):
    stmt = select(WorkflowRunRecord).where(
        WorkflowRunRecord.id == str(run_id),
        WorkflowRunRecord.owner_user_id == user,
        WorkflowRunRecord.workflow_slug == "exchange-listing-submission-pack",
    )
    if await db.scalar(stmt.with_for_update() if lock else stmt) is None:
        raise HTTPException(404, "Run not found")
    return await db.get(RobinhoodListing, str(run_id), with_for_update=lock)


def private(row):
    return {
        "run_id": str(row.run_id),
        "status": row.status,
        "version": row.version,
        "packet": row.packet,
        "contact": row.contact,
        "comment": row.comment,
    }


@router.get("/catalog")
async def catalog(db: DbSession):
    rows = await db.scalars(
        select(RobinhoodListing).where(
            RobinhoodListing.status == "approved", RobinhoodListing.chain_id == 4663
        )
    )
    return [r.packet for r in rows]


@router.get("/review")
async def queue(
    db: DbSession, testnet: bool = False, operator=Depends(require_platform_admin)
):
    rows = await db.scalars(
        select(RobinhoodListing).where(
            RobinhoodListing.status == "pending",
            RobinhoodListing.chain_id == (46630 if testnet else 4663),
        )
    )
    return [private(r) for r in rows]


@router.post("/review/{run_id}")
async def review(
    run_id: UUID,
    body: ListingReview,
    db: DbSession,
    operator=Depends(require_platform_admin),
):
    row = await db.get(RobinhoodListing, str(run_id), with_for_update=True)
    if not row or row.status != "pending" or row.version != body.version:
        raise HTTPException(409, "Refresh the review queue")
    row.status, row.comment = body.decision, body.comment
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(409, "Contract already published")
    return private(row)


@router.get("/{run_id}")
async def read(run_id: UUID, db: DbSession, user=Depends(require_auth)):
    row = await owned(db, run_id, user)
    return private(row) if row else None


@router.put("/{run_id}")
async def preview(
    run_id: UUID, body: ListingDraft, db: DbSession, user=Depends(require_auth)
):
    row = await owned(db, run_id, user, True)
    if row and row.status not in {"draft", "verified", "revision"}:
        raise HTTPException(409, "Application is locked")
    if not row:
        row = RobinhoodListing(run_id=str(run_id), version=0)
        db.add(row)
    row.version += 1
    row.chain_id, row.address, row.contact = body.chain_id, body.address, body.contact
    packet = body.model_dump(mode="json", exclude={"contact"})
    try:
        packet.update(await inspect_contract(body.chain_id, body.address))
        row.status, row.comment = "verified", None
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        row.status, row.comment = (
            "draft",
            "Could not verify network and contract. Check the address and retry.",
        )
    row.packet = packet
    return private(row)


@router.post("/{run_id}/submit")
async def submit(
    run_id: UUID, body: ListingVersion, db: DbSession, user=Depends(require_auth)
):
    row = await owned(db, run_id, user, True)
    if not row or row.version != body.version:
        raise HTTPException(409, "Preview the current version")
    if row.status in {"pending", "approved"}:
        return private(row)
    if row.status != "verified":
        raise HTTPException(409, "Verify the draft first")
    captured = await db.scalar(
        select(PaymentIntent.id)
        .where(
            PaymentIntent.workflow_run_id == str(run_id),
            PaymentIntent.owner_user_id == user,
            PaymentIntent.status == "captured",
            PaymentIntent.capture_ledger_event_id.is_not(None),
        )
        .limit(1)
    )
    if not captured:
        raise HTTPException(402, "Complete payment for this workflow run")
    row.status = "pending"
    return private(row)
