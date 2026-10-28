"""ANCAP Dating cloud plane (profiles, APs, matches). Mesh stays on-device."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    DatingAccessPoint,
    DatingLike,
    DatingMatch,
    DatingMessage,
    DatingProfile,
    DatingReport,
)
from app.schemas.dating import (
    BLE_SERVICE_UUID,
    DatingAccessPointCreate,
    DatingCatalogPublic,
    DatingMessageCreate,
    DatingProfileUpsert,
    DatingReportCreate,
)


def catalog() -> DatingCatalogPublic:
    return DatingCatalogPublic(
        notes=[
            "BLE peers advertise as ANCAP Dating.",
            "Internet optional for nearby mesh chat.",
            "18+ attestation required.",
            "Inspired by bitchat-style mesh; ANCAP-branded protocol.",
        ]
    )


def _profile_public(row: DatingProfile) -> dict:
    return {
        "id": str(row.id),
        "user_id": str(row.user_id),
        "display_name": row.display_name,
        "bio": row.bio,
        "age_attested_18": bool(row.age_attested_18),
        "visibility": row.visibility,
        "lat": float(row.lat) if row.lat is not None else None,
        "lon": float(row.lon) if row.lon is not None else None,
        "mesh_peer_id": row.mesh_peer_id,
        "updated_at": row.updated_at,
    }


async def get_profile(session: AsyncSession, user_id: UUID) -> DatingProfile | None:
    return await session.scalar(select(DatingProfile).where(DatingProfile.user_id == user_id))


async def upsert_profile(session: AsyncSession, user_id: UUID, body: DatingProfileUpsert) -> DatingProfile:
    if not body.age_attested_18:
        raise HTTPException(status_code=400, detail="age_attested_18 required (18+)")
    row = await get_profile(session, user_id)
    now = datetime.now(timezone.utc)
    if row is None:
        row = DatingProfile(
            id=str(uuid.uuid4()),
            user_id=str(user_id),
            display_name=body.display_name.strip(),
            bio=body.bio,
            age_attested_18=True,
            visibility=body.visibility,
            lat=body.lat,
            lon=body.lon,
            mesh_peer_id=body.mesh_peer_id,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
    else:
        row.display_name = body.display_name.strip()
        row.bio = body.bio
        row.age_attested_18 = True
        row.visibility = body.visibility
        row.lat = body.lat
        row.lon = body.lon
        row.mesh_peer_id = body.mesh_peer_id
        row.updated_at = now
    await session.commit()
    await session.refresh(row)
    return row


async def list_access_points(session: AsyncSession, *, limit: int = 100) -> list[DatingAccessPoint]:
    stmt = (
        select(DatingAccessPoint)
        .where(DatingAccessPoint.status == "active")
        .order_by(DatingAccessPoint.created_at.desc())
        .limit(min(limit, 200))
    )
    return list(await session.scalars(stmt))


async def create_access_point(
    session: AsyncSession, user_id: UUID, body: DatingAccessPointCreate
) -> DatingAccessPoint:
    profile = await get_profile(session, user_id)
    if profile is None or not profile.age_attested_18:
        raise HTTPException(status_code=403, detail="Create a 18+ dating profile first")
    row = DatingAccessPoint(
        id=str(uuid.uuid4()),
        creator_user_id=str(user_id),
        title=body.title.strip(),
        description=body.description,
        lat=body.lat,
        lon=body.lon,
        ble_service_hint=BLE_SERVICE_UUID,
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def like_user(session: AsyncSession, from_user_id: UUID, to_user_id: UUID) -> dict:
    if from_user_id == to_user_id:
        raise HTTPException(status_code=400, detail="Cannot like yourself")
    me = await get_profile(session, from_user_id)
    if me is None or not me.age_attested_18:
        raise HTTPException(status_code=403, detail="18+ profile required")
    existing = await session.scalar(
        select(DatingLike).where(
            DatingLike.from_user_id == str(from_user_id),
            DatingLike.to_user_id == str(to_user_id),
        )
    )
    if existing is None:
        session.add(
            DatingLike(
                id=str(uuid.uuid4()),
                from_user_id=str(from_user_id),
                to_user_id=str(to_user_id),
                created_at=datetime.now(timezone.utc),
            )
        )
        await session.flush()

    reciprocal = await session.scalar(
        select(DatingLike).where(
            DatingLike.from_user_id == str(to_user_id),
            DatingLike.to_user_id == str(from_user_id),
        )
    )
    matched = False
    match_id = None
    if reciprocal is not None:
        a, b = sorted([str(from_user_id), str(to_user_id)])
        match = await session.scalar(
            select(DatingMatch).where(DatingMatch.user_a_id == a, DatingMatch.user_b_id == b)
        )
        if match is None:
            match = DatingMatch(
                id=str(uuid.uuid4()),
                user_a_id=a,
                user_b_id=b,
                created_at=datetime.now(timezone.utc),
            )
            session.add(match)
            await session.flush()
        matched = True
        match_id = str(match.id)

    await session.commit()
    return {"liked": True, "matched": matched, "match_id": match_id}


async def list_matches(session: AsyncSession, user_id: UUID) -> list[dict]:
    uid = str(user_id)
    rows = list(
        await session.scalars(
            select(DatingMatch).where(or_(DatingMatch.user_a_id == uid, DatingMatch.user_b_id == uid))
        )
    )
    out = []
    for m in rows:
        peer = m.user_b_id if m.user_a_id == uid else m.user_a_id
        out.append({"id": str(m.id), "peer_user_id": peer, "created_at": m.created_at})
    return out


async def send_message(session: AsyncSession, user_id: UUID, body: DatingMessageCreate) -> DatingMessage:
    match = await session.get(DatingMatch, body.match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    uid = str(user_id)
    if uid not in {match.user_a_id, match.user_b_id}:
        raise HTTPException(status_code=403, detail="Not a participant")
    row = DatingMessage(
        id=str(uuid.uuid4()),
        match_id=str(match.id),
        sender_user_id=uid,
        body=body.body.strip(),
        created_at=datetime.now(timezone.utc),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def list_messages(session: AsyncSession, user_id: UUID, match_id: str, *, limit: int = 50) -> list[DatingMessage]:
    match = await session.get(DatingMatch, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    uid = str(user_id)
    if uid not in {match.user_a_id, match.user_b_id}:
        raise HTTPException(status_code=403, detail="Not a participant")
    stmt = (
        select(DatingMessage)
        .where(DatingMessage.match_id == match_id)
        .order_by(DatingMessage.created_at.asc())
        .limit(min(limit, 200))
    )
    return list(await session.scalars(stmt))


async def report_user(session: AsyncSession, reporter: UUID, body: DatingReportCreate) -> DatingReport:
    row = DatingReport(
        id=str(uuid.uuid4()),
        reporter_user_id=str(reporter),
        target_user_id=body.target_user_id,
        reason=body.reason.strip(),
        created_at=datetime.now(timezone.utc),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


def access_point_public(row: DatingAccessPoint) -> dict:
    return {
        "id": str(row.id),
        "title": row.title,
        "description": row.description,
        "lat": float(row.lat),
        "lon": float(row.lon),
        "ble_service_hint": row.ble_service_hint or BLE_SERVICE_UUID,
        "status": row.status,
        "created_at": row.created_at,
    }
