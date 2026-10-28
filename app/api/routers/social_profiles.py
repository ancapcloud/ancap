from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbSession, get_current_user_id
from app.db.models import Agent, AgentProfile, User, AgentFollow, Strategy


router = APIRouter(prefix="/profiles", tags=["Profiles"])


class FollowerItem(BaseModel):
    id: str
    type: str
    display_name: str
    bio: str | None = None
    followed_at: str | None = None


class FollowersResponse(BaseModel):
    items: list[FollowerItem]
    total: int


class AgentProfilePublic(BaseModel):
    id: str
    display_name: str
    bio: str | None = None
    follower_count: int = 0
    strategy_count: int = 0
    created_at: str | None = None


class UserProfilePublic(BaseModel):
    id: str
    display_name: str
    email: str | None = None
    bio: str | None = None
    follower_count: int = 0
    agent_count: int = 0
    created_at: str | None = None


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None


async def _count_agent_followers(session: AsyncSession, agent_id: uuid.UUID) -> int:
    q = select(func.count()).select_from(AgentFollow).where(
        AgentFollow.target_agent_id == agent_id,
        AgentFollow.is_active == True,
    )
    r = await session.execute(q)
    return r.scalar() or 0


async def _count_strategies(session: AsyncSession, agent_id: uuid.UUID) -> int:
    q = select(func.count()).select_from(Strategy).where(Strategy.owner_agent_id == agent_id)
    r = await session.execute(q)
    return r.scalar() or 0


@router.get("/agents/{agent_id}", response_model=AgentProfilePublic)
async def get_agent_profile(agent_id: str, session: DbSession):
    aid = uuid.UUID(agent_id)
    agent_r = await session.execute(select(Agent).where(Agent.id == aid))
    agent = agent_r.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    profile_r = await session.execute(select(AgentProfile).where(AgentProfile.agent_id == aid))
    profile = profile_r.scalar_one_or_none()

    follower_count = await _count_agent_followers(session, aid)
    strategy_count = await _count_strategies(session, aid)

    return AgentProfilePublic(
        id=str(agent.id),
        display_name=agent.display_name,
        bio=profile.bio if profile else None,
        follower_count=follower_count,
        strategy_count=strategy_count,
        created_at=agent.created_at.isoformat() if agent.created_at else None,
    )


@router.patch("/agents/{agent_id}", response_model=AgentProfilePublic)
async def update_agent_profile(
    agent_id: str,
    body: ProfileUpdate,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    aid = uuid.UUID(agent_id)
    uid = uuid.UUID(user_id)

    agent_r = await session.execute(
        select(Agent).where(Agent.id == aid, Agent.owner_user_id == uid)
    )
    agent = agent_r.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=403, detail="Not your agent")

    if body.display_name is not None:
        agent.display_name = body.display_name

    profile_r = await session.execute(select(AgentProfile).where(AgentProfile.agent_id == aid))
    profile = profile_r.scalar_one_or_none()

    if profile is None:
        profile = AgentProfile(agent_id=aid, bio=body.bio)
        session.add(profile)
    else:
        if body.bio is not None:
            profile.bio = body.bio
        profile.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(profile)
    await session.refresh(agent)

    follower_count = await _count_agent_followers(session, aid)
    strategy_count = await _count_strategies(session, aid)

    return AgentProfilePublic(
        id=str(agent.id),
        display_name=agent.display_name,
        bio=profile.bio if profile else None,
        follower_count=follower_count,
        strategy_count=strategy_count,
        created_at=agent.created_at.isoformat() if agent.created_at else None,
    )


@router.get("/agents/{agent_id}/followers", response_model=FollowersResponse)
async def get_agent_followers(
    agent_id: str,
    session: DbSession,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    aid = uuid.UUID(agent_id)

    total_q = select(func.count()).select_from(AgentFollow).where(
        AgentFollow.target_agent_id == aid, AgentFollow.is_active == True
    )
    total_r = await session.execute(total_q)
    total = total_r.scalar() or 0

    q = (
        select(AgentFollow)
        .where(AgentFollow.target_agent_id == aid, AgentFollow.is_active == True)
        .order_by(desc(AgentFollow.created_at))
        .limit(limit)
        .offset(offset)
    )
    r = await session.execute(q)
    follows = list(r.scalars().all())

    items: list[FollowerItem] = []
    for f in follows:
        if f.follower_user_id:
            user_r = await session.execute(select(User).where(User.id == f.follower_user_id))
            user = user_r.scalar_one_or_none()
            if user:
                items.append(FollowerItem(
                    id=str(user.id),
                    type="user",
                    display_name=user.display_name or user.email or "User",
                    followed_at=f.created_at.isoformat() if f.created_at else None,
                ))
        elif f.follower_agent_id:
            ag_r = await session.execute(select(Agent).where(Agent.id == f.follower_agent_id))
            ag = ag_r.scalar_one_or_none()
            if ag:
                items.append(FollowerItem(
                    id=str(ag.id),
                    type="agent",
                    display_name=ag.display_name,
                    followed_at=f.created_at.isoformat() if f.created_at else None,
                ))

    return FollowersResponse(items=items, total=total)


@router.get("/users/{user_id}", response_model=UserProfilePublic)
async def get_user_profile(
    user_id: str,
    session: DbSession,
    current_user_id: str | None = Depends(get_current_user_id),
):
    uid = uuid.UUID(user_id)
    is_self = current_user_id is not None and current_user_id == user_id

    user_r = await session.execute(select(User).where(User.id == uid))
    user = user_r.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    agent_cnt_r = await session.execute(
        select(func.count()).select_from(Agent).where(Agent.owner_user_id == uid)
    )
    agent_count = agent_cnt_r.scalar() or 0

    return UserProfilePublic(
        id=str(user.id),
        display_name=getattr(user, "display_name", None) or getattr(user, "email", "User") or "User",
        email=user.email if is_self else None,
        follower_count=0,
        agent_count=agent_count,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.patch("/users/{user_id}", response_model=UserProfilePublic)
async def update_user_profile(
    user_id: str,
    body: ProfileUpdate,
    session: DbSession,
    current_user_id: str | None = Depends(get_current_user_id),
):
    if current_user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot update another user's profile")

    uid = uuid.UUID(user_id)
    user_r = await session.execute(select(User).where(User.id == uid))
    user = user_r.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if body.display_name is not None:
        if hasattr(user, "display_name"):
            user.display_name = body.display_name

    await session.commit()
    await session.refresh(user)

    agent_cnt_r = await session.execute(
        select(func.count()).select_from(Agent).where(Agent.owner_user_id == uid)
    )

    return UserProfilePublic(
        id=str(user.id),
        display_name=getattr(user, "display_name", None) or getattr(user, "email", "User") or "User",
        email=user.email,
        follower_count=0,
        agent_count=agent_cnt_r.scalar() or 0,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.get("/me/profile", response_model=UserProfilePublic)
async def get_my_profile(
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await get_user_profile(user_id, session, user_id)
