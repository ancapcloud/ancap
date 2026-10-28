from __future__ import annotations

import csv
import io
import re
import uuid
from datetime import datetime, timedelta, timezone, UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import desc, select, func, or_ as sql_or
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession, get_current_user_id
from app.db.models import (
    Agent,
    ApiKey,
    ApiUsageEvent,
    DecisionLog,
    Organization,
    OrganizationMember,
    OrgRoleEnum,
    User,
)
from app.services.api_keys import generate_key
from app.services.org_nfc_policy import require_nfc_for_admin_actions
from app.schemas.keys import OrgApiKeyCreateRequest, OrgApiKeyPublic, OrgApiKeySpendCapRequest


router = APIRouter(prefix="/organizations", tags=["Organizations"])


# --- Schemas ---

class OrgMemberPublic(BaseModel):
    user_id: str
    role: str
    joined_at: str | None = None
    user_email: str | None = None


class OrganizationPublic(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    billing_wallet_address: str | None = None
    member_count: int = 0
    user_role: str | None = None
    created_at: str | None = None


class OrganizationCreate(BaseModel):
    name: str
    description: str | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    billing_wallet_address: str | None = None


class OrgInviteRequest(BaseModel):
    email: str
    role: str = "member"


class OrgRoleUpdateRequest(BaseModel):
    role: str


ASSIGNABLE_ORG_ROLES = {OrgRoleEnum.viewer, OrgRoleEnum.member, OrgRoleEnum.admin}


API_KEY_SPEND_CAPS_FIELD = "paid_api_spend_caps"


def _normalize_api_key_spend_caps(metadata: object) -> dict[str, dict[str, str]]:
    if not isinstance(metadata, dict):
        return {}
    raw_caps = metadata.get(API_KEY_SPEND_CAPS_FIELD)
    if not isinstance(raw_caps, dict):
        return {}

    normalized: dict[str, dict[str, str]] = {}
    for endpoint, currency_map in raw_caps.items():
        endpoint_key = str(endpoint or "").strip()
        if not endpoint_key:
            continue
        if not isinstance(currency_map, dict):
            continue
        normalized_currency_map: dict[str, str] = {}
        for currency, amount in currency_map.items():
            currency_key = str(currency or "").strip().upper()
            amount_value = str(amount or "").strip()
            if not currency_key or not amount_value:
                continue
            normalized_currency_map[currency_key] = amount_value
        if normalized_currency_map:
            normalized[endpoint_key] = normalized_currency_map
    return normalized


# --- Helpers ---

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return (text or "organization")[:80]


async def _get_member_role(session: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID) -> OrgRoleEnum | None:
    q = select(OrganizationMember).where(
        OrganizationMember.org_id == org_id,
        OrganizationMember.user_id == user_id,
    )
    r = await session.execute(q)
    member = r.scalar_one_or_none()
    return member.role if member else None


async def _require_role(session: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID, min_role: OrgRoleEnum) -> None:
    role = await _get_member_role(session, org_id, user_id)
    if role is None:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    hierarchy = [OrgRoleEnum.viewer, OrgRoleEnum.member, OrgRoleEnum.admin, OrgRoleEnum.owner]
    if hierarchy.index(role) < hierarchy.index(min_role):
        raise HTTPException(status_code=403, detail=f"Requires {min_role.value} role or higher")


# --- Endpoints ---

@router.get("", response_model=list[OrganizationPublic])
async def list_user_organizations(
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)

    # Find orgs where user is a member
    q = (
        select(Organization)
        .join(OrganizationMember, OrganizationMember.org_id == Organization.id)
        .where(OrganizationMember.user_id == uid)
        .order_by(desc(Organization.created_at))
    )
    r = await session.execute(q)
    orgs = list(r.scalars().all())

    result: list[OrganizationPublic] = []
    for org in orgs:
        # Count members
        cnt_q = select(func.count()).select_from(OrganizationMember).where(OrganizationMember.org_id == org.id)
        cnt_r = await session.execute(cnt_q)
        member_count = cnt_r.scalar() or 0

        role_q = select(OrganizationMember.role).where(
            OrganizationMember.org_id == org.id,
            OrganizationMember.user_id == uid,
        )
        role_r = await session.execute(role_q)
        user_role = role_r.scalar_one_or_none()

        result.append(OrganizationPublic(
            id=str(org.id),
            name=org.name,
            slug=org.slug,
            description=org.description,
            billing_wallet_address=org.billing_wallet_address,
            member_count=member_count,
            user_role=user_role.value if user_role else None,
            created_at=org.created_at.isoformat() if org.created_at else None,
        ))
    return result


@router.post("", response_model=OrganizationPublic, status_code=201)
async def create_organization(
    body: OrganizationCreate,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)

    # Generate unique slug
    base_slug = slugify(body.name)
    slug = base_slug
    for attempt in range(1, 1000):
        existing = await session.execute(
            select(Organization).where(Organization.slug == slug)
        )
        if existing.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{attempt}"

    org = Organization(
        name=body.name,
        slug=slug,
        description=body.description,
        created_by_user_id=uid,
    )
    session.add(org)
    await session.flush()

    # Add creator as owner
    member = OrganizationMember(
        org_id=org.id,
        user_id=uid,
        role=OrgRoleEnum.owner,
    )
    session.add(member)
    await session.commit()
    await session.refresh(org)

    return OrganizationPublic(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        description=org.description,
        billing_wallet_address=org.billing_wallet_address,
        member_count=1,
        user_role="owner",
        created_at=org.created_at.isoformat() if org.created_at else None,
    )


@router.get("/{org_id}", response_model=OrganizationPublic)
async def get_organization(
    org_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)

    q = select(Organization).where(Organization.id == oid)
    r = await session.execute(q)
    org = r.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check membership
    user_role = await _get_member_role(session, oid, uid)
    if user_role is None:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    cnt_q = select(func.count()).select_from(OrganizationMember).where(OrganizationMember.org_id == oid)
    cnt_r = await session.execute(cnt_q)
    member_count = cnt_r.scalar() or 0

    return OrganizationPublic(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        description=org.description,
        billing_wallet_address=org.billing_wallet_address,
        member_count=member_count,
        user_role=user_role.value if user_role else None,
        created_at=org.created_at.isoformat() if org.created_at else None,
    )


@router.patch("/{org_id}", response_model=OrganizationPublic)
async def update_organization(
    org_id: str,
    body: OrganizationUpdate,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)

    await _require_role(session, oid, uid, OrgRoleEnum.admin)

    q = select(Organization).where(Organization.id == oid)
    r = await session.execute(q)
    org = r.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    fields_set = body.model_fields_set
    if "name" in fields_set:
        org.name = body.name or org.name
    if "description" in fields_set:
        org.description = body.description
    if "billing_wallet_address" in fields_set:
        org.billing_wallet_address = body.billing_wallet_address
    org.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(org)

    user_role = await _get_member_role(session, oid, uid)
    cnt_q = select(func.count()).select_from(OrganizationMember).where(OrganizationMember.org_id == oid)
    cnt_r = await session.execute(cnt_q)

    return OrganizationPublic(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        description=org.description,
        billing_wallet_address=org.billing_wallet_address,
        member_count=cnt_r.scalar() or 0,
        user_role=user_role.value if user_role else None,
        created_at=org.created_at.isoformat() if org.created_at else None,
    )


@router.delete("/{org_id}", status_code=204)
async def delete_organization(
    org_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)

    await _require_role(session, oid, uid, OrgRoleEnum.owner)

    q = select(Organization).where(Organization.id == oid)
    r = await session.execute(q)
    org = r.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    await session.delete(org)
    await session.commit()


@router.get("/{org_id}/members", response_model=list[OrgMemberPublic])
async def list_organization_members(
    org_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)

    await _require_role(session, oid, uid, OrgRoleEnum.viewer)

    q = (
        select(OrganizationMember)
        .options(joinedload(OrganizationMember.user))
        .where(OrganizationMember.org_id == oid)
        .order_by(desc(OrganizationMember.created_at))
    )
    r = await session.execute(q)
    members = list(r.scalars().all())

    return [
        OrgMemberPublic(
            user_id=str(m.user_id),
            role=m.role.value,
            joined_at=m.created_at.isoformat() if m.created_at else None,
            user_email=m.user.email if m.user else None,
        )
        for m in members
    ]


@router.post("/{org_id}/members", status_code=201)
async def add_organization_member(
    org_id: str,
    body: OrgInviteRequest,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)

    await _require_role(session, oid, uid, OrgRoleEnum.admin)

    # Find user by email
    email_q = select(User).where(User.email == body.email.lower().strip())
    email_r = await session.execute(email_q)
    target_user = email_r.scalar_one_or_none()
    if target_user is None:
        raise HTTPException(status_code=404, detail="User with this email not found")

    # Check if already member
    existing_q = select(OrganizationMember).where(
        OrganizationMember.org_id == oid,
        OrganizationMember.user_id == target_user.id,
    )
    existing_r = await session.execute(existing_q)
    if existing_r.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="User is already a member")

    # Validate role
    try:
        role = OrgRoleEnum(body.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role. Must be: admin, member, viewer")
    if role not in ASSIGNABLE_ORG_ROLES:
        raise HTTPException(status_code=400, detail="Owner role cannot be assigned via this endpoint")

    member = OrganizationMember(
        org_id=oid,
        user_id=target_user.id,
        role=role,
    )
    session.add(member)
    await session.commit()

    return OrgMemberPublic(
        user_id=str(target_user.id),
        role=role.value,
        joined_at=member.created_at.isoformat() if member.created_at else None,
        user_email=target_user.email,
    )


@router.delete("/{org_id}/members/{target_user_id}", status_code=204)
async def remove_organization_member(
    org_id: str,
    target_user_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)
    tid = uuid.UUID(target_user_id)

    # Can remove if: you're admin+ OR you're removing yourself
    if uid != tid:
        await _require_role(session, oid, uid, OrgRoleEnum.admin)

    # Can't remove owner
    target_q = select(OrganizationMember).where(
        OrganizationMember.org_id == oid,
        OrganizationMember.user_id == tid,
    )
    target_r = await session.execute(target_q)
    target_member = target_r.scalar_one_or_none()
    if target_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    if target_member.role == OrgRoleEnum.owner:
        raise HTTPException(status_code=400, detail="Cannot remove organization owner")

    await session.delete(target_member)
    await session.commit()


@router.patch("/{org_id}/members/{target_user_id}/role", response_model=OrgMemberPublic)
async def update_member_role(
    org_id: str,
    target_user_id: str,
    body: OrgRoleUpdateRequest,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)
    tid = uuid.UUID(target_user_id)

    await _require_role(session, oid, uid, OrgRoleEnum.admin)

    try:
        new_role = OrgRoleEnum(body.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role. Must be: admin, member, viewer")
    if new_role not in ASSIGNABLE_ORG_ROLES:
        raise HTTPException(status_code=400, detail="Owner role cannot be assigned via this endpoint")

    target_q = select(OrganizationMember).where(
        OrganizationMember.org_id == oid,
        OrganizationMember.user_id == tid,
    )
    target_r = await session.execute(target_q)
    target_member = target_r.scalar_one_or_none()
    if target_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    if target_member.role == OrgRoleEnum.owner:
        raise HTTPException(status_code=400, detail="Cannot change owner role")

    target_member.role = new_role
    await session.commit()
    await session.refresh(target_member)

    return OrgMemberPublic(
        user_id=str(tid),
        role=target_member.role.value,
        joined_at=target_member.created_at.isoformat() if target_member.created_at else None,
    )


@router.post("/{org_id}/agents/{agent_id}", status_code=200)
async def transfer_agent_to_org(
    org_id: str,
    agent_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    """Transfer an agent to be owned by an organization."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)
    aid = uuid.UUID(agent_id)

    await _require_role(session, oid, uid, OrgRoleEnum.admin)

    agent_q = select(Agent).where(Agent.id == aid)
    agent_r = await session.execute(agent_q)
    agent = agent_r.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    org_q = select(Organization).where(Organization.id == oid)
    org_r = await session.execute(org_q)
    org = org_r.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    agent.owner_user_id = None
    agent.metadata_ = dict(agent.metadata_ or {})
    agent.metadata_["org_id"] = str(oid)
    await session.commit()

    return {"agent_id": str(aid), "org_id": str(oid), "transferred": True}


# ── Org-scoped audit export ────────────────────────────────────────────────────


class OrgAuditEvent(BaseModel):
    id: str
    event_type: str
    resource_type: str  # agent | api_key | webhook | member | usage
    resource_id: str | None
    message: str | None
    created_at: str | None


@router.get("/{org_id}/audit", response_model=list[OrgAuditEvent])
async def list_org_audit_events(
    org_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Org-scoped audit log: returns org's agents, API keys, webhooks, and usage events."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)
    await _require_role(session, oid, uid, OrgRoleEnum.viewer)  # even viewers can see audit

    since = datetime.now(UTC) - timedelta(days=days)
    events: list[OrgAuditEvent] = []

    # Agents owned by this org
    agent_q = select(Agent).where(
        Agent.metadata_["org_id"].astext == str(oid),
    )
    agent_r = await session.execute(agent_q)
    org_agent_ids = [a.id for a in agent_r.scalars().all()]

    # API keys for org's agents
    if org_agent_ids:
        key_q = (
            select(ApiKey)
            .where(ApiKey.agent_id.in_(org_agent_ids))
            .where(ApiKey.created_at >= since)
            .order_by(desc(ApiKey.created_at))
            .limit(limit)
        )
        key_r = await session.execute(key_q)
        for k in key_r.scalars().all():
            events.append(OrgAuditEvent(
                id=str(k.id),
                event_type="api_key.created",
                resource_type="api_key",
                resource_id=str(k.id),
                message=f"API key {k.key_prefix}*** created for agent {k.agent_id}",
                created_at=k.created_at.isoformat() if k.created_at else None,
            ))

    # API usage events for org's agents
    if org_agent_ids:
        usage_q = (
            select(ApiUsageEvent)
            .where(ApiUsageEvent.agent_id.in_(org_agent_ids))
            .where(ApiUsageEvent.created_at >= since)
            .order_by(desc(ApiUsageEvent.created_at))
            .limit(limit)
        )
        usage_r = await session.execute(usage_q)
        for u in usage_r.scalars().all():
            events.append(OrgAuditEvent(
                id=str(u.id),
                event_type="api_usage",
                resource_type="usage",
                resource_id=str(u.id),
                message=f"{u.endpoint} → {u.status} ({u.amount_currency} {u.amount_value})",
                created_at=u.created_at.isoformat() if u.created_at else None,
            ))

    # Decision log entries for org's agents
    if org_agent_ids:
        decision_q = (
            select(DecisionLog)
            .where(DecisionLog.actor_id.in_(org_agent_ids))
            .where(DecisionLog.created_at >= since)
            .order_by(desc(DecisionLog.created_at))
            .limit(limit)
        )
        decision_r = await session.execute(decision_q)
        for d in decision_r.scalars().all():
            events.append(OrgAuditEvent(
                id=str(d.id),
                event_type=d.reason_code or "decision",
                resource_type="agent",
                resource_id=str(d.actor_id),
                message=d.message,
                created_at=d.created_at.isoformat() if d.created_at else None,
            ))

    events.sort(key=lambda x: x.created_at or "", reverse=True)
    return events[offset:offset + limit]


@router.get("/{org_id}/audit/export")
async def export_org_audit_csv(
    org_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
    days: int = Query(30, ge=1, le=365),
):
    """Export org audit log as CSV (admin only)."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)
    await _require_role(session, oid, uid, OrgRoleEnum.admin)

    since = datetime.now(UTC) - timedelta(days=days)
    output = io.StringIO()
    writer = csv.writer(output)

    agent_q = select(Agent).where(
        Agent.metadata_["org_id"].astext == str(oid),
    )
    agent_r = await session.execute(agent_q)
    org_agent_ids = [a.id for a in agent_r.scalars().all()]

    writer.writerow(["id", "event_type", "resource_type", "resource_id", "message", "created_at"])

    if org_agent_ids:
        key_q = select(ApiKey).where(
            ApiKey.agent_id.in_(org_agent_ids), ApiKey.created_at >= since
        ).order_by(ApiKey.created_at)
        for k in (await session.execute(key_q)).scalars().all():
            writer.writerow([
                str(k.id), "api_key.created", "api_key", str(k.id),
                f"API key {k.key_prefix}*** created", k.created_at.isoformat() if k.created_at else "",
            ])

        usage_q = select(ApiUsageEvent).where(
            ApiUsageEvent.agent_id.in_(org_agent_ids), ApiUsageEvent.created_at >= since
        ).order_by(ApiUsageEvent.created_at).limit(10000)
        for u in (await session.execute(usage_q)).scalars().all():
            writer.writerow([
                str(u.id), "api_usage", "usage", str(u.id),
                f"{u.endpoint} → {u.status}", u.created_at.isoformat() if u.created_at else "",
            ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=org-audit-{org_id}-{datetime.now(UTC).strftime('%Y-%m-%d')}.csv"},
    )


# ── Org-scoped API keys ────────────────────────────────────────────────────────

@router.post("/{org_id}/api-keys", response_model=dict, status_code=201)
async def create_org_api_key(
    org_id: str,
    body: OrgApiKeyCreateRequest,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    """Create an API key owned directly by the organization (admin+ only)."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)
    await _require_role(session, oid, uid, OrgRoleEnum.admin)

    org = await session.get(Organization, oid)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Generate key directly — set org_id at row creation to avoid update-after-flush issue
    full_key, key_prefix, key_hash = generate_key()
    row = ApiKey(
        id=uuid.uuid4(),
        org_id=oid,
        agent_id=None,
        name=body.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scope=body.scope,
        expires_at=body.expires_at,
    )
    session.add(row)
    await session.commit()

    return {
        "id": str(row.id),
        "org_id": str(oid),
        "name": body.name,
        "key_prefix": row.key_prefix,
        "key": full_key,
        "scope": row.scope,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/{org_id}/api-keys", response_model=list[OrgApiKeyPublic])
async def list_org_api_keys(
    org_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    """List org-owned keys plus agent-owned keys attached to this organization (any org member)."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)
    await _require_role(session, oid, uid, OrgRoleEnum.member)

    org_agent_ids_subq = select(Agent.id).where(Agent.metadata_["org_id"].astext == str(oid))
    q = (
        select(ApiKey)
        .where(sql_or(ApiKey.org_id == oid, ApiKey.agent_id.in_(org_agent_ids_subq)))
        .order_by(desc(ApiKey.created_at))
    )
    r = await session.execute(q)
    rows = r.scalars().all()
    return [
        OrgApiKeyPublic(
            id=str(k.id),
            org_id=str(oid),
            name=k.name or "",
            key_prefix=k.key_prefix,
            scope=k.scope,
            spend_caps=_normalize_api_key_spend_caps(k.metadata_json),
            expires_at=k.expires_at,
            created_at=k.created_at,
        )
        for k in rows
    ]


@router.patch("/{org_id}/api-keys/{key_id}", response_model=OrgApiKeyPublic)
async def set_org_api_key_spend_cap(
    org_id: str,
    key_id: str,
    body: OrgApiKeySpendCapRequest,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    """Set or update a per-endpoint paid API monthly spend cap for an org-owned API key (admin+ only)."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)
    kid = uuid.UUID(key_id)
    await _require_role(session, oid, uid, OrgRoleEnum.admin)

    org_agent_ids_subq = select(Agent.id).where(Agent.metadata_["org_id"].astext == str(oid))
    row = (
        await session.execute(
            select(ApiKey).where(ApiKey.id == kid).where(sql_or(ApiKey.org_id == oid, ApiKey.agent_id.in_(org_agent_ids_subq)))
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="API key not found")

    metadata = dict(row.metadata_json or {})
    spend_caps = _normalize_api_key_spend_caps(metadata)
    endpoint_caps = dict(spend_caps.get(body.endpoint) or {})
    endpoint_caps[body.currency] = body.monthly_cap.strip()
    spend_caps[body.endpoint] = endpoint_caps
    metadata[API_KEY_SPEND_CAPS_FIELD] = spend_caps
    row.metadata_json = metadata
    await session.commit()
    await session.refresh(row)

    return OrgApiKeyPublic(
        id=str(row.id),
        org_id=str(oid),
        name=row.name or "",
        key_prefix=row.key_prefix,
        scope=row.scope,
        spend_caps=_normalize_api_key_spend_caps(row.metadata_json),
        expires_at=row.expires_at,
        created_at=row.created_at,
    )


@router.delete("/{org_id}/api-keys/{key_id}", status_code=204)
async def delete_org_api_key(
    org_id: str,
    key_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    """Delete an org-owned API key (admin+ only)."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uid = uuid.UUID(user_id)
    oid = uuid.UUID(org_id)
    kid = uuid.UUID(key_id)

    # Check role first
    role_q = select(OrganizationMember).where(
        OrganizationMember.org_id == oid,
        OrganizationMember.user_id == uid,
    )
    role_r = await session.execute(role_q)
    member = role_r.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=403, detail="Not a member")
    if member.role not in (OrgRoleEnum.admin, OrgRoleEnum.owner):
        raise HTTPException(status_code=403, detail="Requires admin role or higher")
    await require_nfc_for_admin_actions(session, org_id=oid, user_id=uid, member=member)

    # Use a direct DELETE statement: check org_id match in WHERE, return rowcount
    from sqlalchemy import delete
    del_q = (
        delete(ApiKey)
        .where(ApiKey.id == kid)
        .where(ApiKey.org_id == oid)
    )
    result = await session.execute(del_q)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    await session.commit()
