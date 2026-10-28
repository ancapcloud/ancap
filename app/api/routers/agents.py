from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Query, HTTPException, Depends

from app.schemas import AgentCreateRequest, AgentPublic, Pagination
from app.api.deps import DbSession, get_current_user_id
from app.config import get_settings
from app.db.models import Agent, AgentStatusEnum, AgentAttestation
from app.services.agent_graph_metrics import get_agent_graph_metrics
from sqlalchemy import select, func

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("", response_model=AgentPublic, status_code=201)
async def register_agent(
    body: AgentCreateRequest,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    settings = get_settings()
    # L3: daily registration limit
    if settings.registration_max_agents_per_day > 0:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        count_q = select(func.count(Agent.id)).where(Agent.created_at >= today_start)
        count_r = await session.execute(count_q)
        n = count_r.scalar() or 0
        if n >= settings.registration_max_agents_per_day:
            raise HTTPException(
                status_code=429,
                detail=f"Registration limit reached ({settings.registration_max_agents_per_day} per day)",
            )
    attestation_id = None
    if body.attestation_id:
        try:
            aid = UUID(body.attestation_id)
            r = await session.execute(select(AgentAttestation).where(AgentAttestation.id == aid))
            if r.scalar_one_or_none():
                attestation_id = aid
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid attestation ID") from None
    # L3 stake-to-activate: when required, activation only via stake (not attestation)
    stake_required = float(settings.stake_to_activate_amount or "0") > 0
    activated_at = None if stake_required else (datetime.utcnow() if attestation_id else None)
    created_by_agent_id = None
    if body.created_by_agent_id:
        try:
            created_by_agent_id = UUID(body.created_by_agent_id)
        except ValueError:
            created_by_agent_id = None
    owner_user_id = None
    # Prefer authenticated user as owner (golden path). Optional override via body.owner_user_id.
    if user_id:
        try:
            owner_user_id = UUID(user_id)
        except ValueError:
            owner_user_id = None
    elif body.owner_user_id:
        try:
            owner_user_id = UUID(body.owner_user_id)
        except ValueError:
            owner_user_id = None
    agent = Agent(
        display_name=body.display_name,
        public_key=body.public_key,
        roles=[r.value for r in body.roles],
        status=AgentStatusEnum.active,
        metadata_=body.metadata,
        attestation_id=attestation_id,
        owner_user_id=owner_user_id,
        created_by_agent_id=created_by_agent_id,
        activated_at=activated_at,
    )
    session.add(agent)
    await session.flush()
    await session.refresh(agent)
    return AgentPublic(
        id=str(agent.id),
        display_name=agent.display_name,
        roles=agent.roles,
        public_key=agent.public_key,
        owner_user_id=str(agent.owner_user_id) if getattr(agent, "owner_user_id", None) else None,
        created_by_agent_id=str(agent.created_by_agent_id) if agent.created_by_agent_id else None,
        status=agent.status.value,
        activated_at=agent.activated_at,
        created_at=agent.created_at,
    )


@router.get("", response_model=Pagination[AgentPublic])
async def list_agents(
    session: DbSession,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    mine: bool = Query(False),
    owner_user_id: UUID | None = Query(None),
    user_id: str | None = Depends(get_current_user_id),
):
    q = select(Agent).order_by(Agent.created_at.desc()).limit(limit + 1)
    if mine and user_id:
        try:
            q = q.where(Agent.owner_user_id == UUID(user_id))
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid authenticated user ID") from None
    elif owner_user_id:
        q = q.where(Agent.owner_user_id == owner_user_id)
    if cursor:
        try:
            q = q.where(Agent.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    r = await session.execute(q)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(
        items=[
            AgentPublic(
                id=str(a.id),
                display_name=a.display_name,
                roles=a.roles,
                public_key=a.public_key,
                owner_user_id=str(a.owner_user_id) if getattr(a, "owner_user_id", None) else None,
                created_by_agent_id=str(a.created_by_agent_id) if getattr(a, "created_by_agent_id", None) else None,
                status=a.status.value,
                activated_at=a.activated_at,
                created_at=a.created_at,
            )
            for a in items
        ],
        next_cursor=next_cursor,
    )


@router.get("/{agent_id}/graph-metrics")
async def get_agent_graph_metrics_endpoint(agent_id: UUID, session: DbSession):
    """ROADMAP 2.1: reciprocity_score (and later cluster_cohesion, suspicious_density) from agent_relationships."""
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await get_agent_graph_metrics(session, agent_id)


@router.get("/{agent_id}", response_model=AgentPublic)
async def get_agent(agent_id: UUID, session: DbSession):
    q = select(Agent).where(Agent.id == agent_id)
    r = await session.execute(q)
    agent = r.scalar_one_or_none()
    if not agent:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentPublic(
        id=str(agent.id),
        display_name=agent.display_name,
        roles=agent.roles,
        public_key=agent.public_key,
        owner_user_id=str(agent.owner_user_id) if getattr(agent, "owner_user_id", None) else None,
        created_by_agent_id=str(agent.created_by_agent_id) if getattr(agent, "created_by_agent_id", None) else None,
        status=agent.status.value,
        activated_at=agent.activated_at,
        created_at=agent.created_at,
    )
