"""API keys for agents: create key, optional auth by X-API-Key."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Response

from app.schemas.keys import ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyPublic, AccountApiKeyPublic, AccountApiKeyCreated
from app.services.account_api_keys import account_key, change_account_key, public_key_status, revoke_account_key
from app.api.deps import DbSession, require_auth
from app.db.models import ApiKey, Agent
from app.services.api_keys import create_key
from sqlalchemy import select

async def no_store_key_response(response: Response):
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(prefix="/keys", tags=["Keys"], dependencies=[Depends(no_store_key_response)])


@router.get("/account", response_model=AccountApiKeyPublic)
async def get_account_key(session: DbSession, user_id: str = Depends(require_auth)):
    return public_key_status(await account_key(session, user_id))


@router.post("/account", response_model=AccountApiKeyCreated, status_code=201)
async def create_account_key(session: DbSession, user_id: str = Depends(require_auth)):
    row, raw = await change_account_key(session, user_id)
    return AccountApiKeyCreated(**public_key_status(row).model_dump(), key=raw)


@router.post("/account/rotate", response_model=AccountApiKeyCreated)
async def rotate_account_key(session: DbSession, user_id: str = Depends(require_auth)):
    row, raw = await change_account_key(session, user_id, rotate=True)
    return AccountApiKeyCreated(**public_key_status(row).model_dump(), key=raw)


@router.delete("/account", status_code=204)
async def delete_account_key(session: DbSession, user_id: str = Depends(require_auth)):
    await revoke_account_key(session, user_id)


@router.post("", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(body: ApiKeyCreateRequest, session: DbSession, user_id: str = Depends(require_auth)):
    """Create an API key for an agent. The full key is returned only once; store it securely."""
    try:
        agent_id = UUID(body.agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id")
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if str(agent.owner_user_id or "") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden agent")
    row, raw_key = await create_key(
        session,
        agent_id=agent_id,
        scope=body.scope,
        expires_at=body.expires_at,
    )
    return ApiKeyCreateResponse(
        id=str(row.id),
        agent_id=str(row.agent_id),
        key_prefix=row.key_prefix,
        key=raw_key,
        scope=row.scope,
        expires_at=row.expires_at,
        created_at=row.created_at,
    )


@router.get("", response_model=list[ApiKeyPublic])
async def list_api_keys(
    session: DbSession,
    user_id: str = Depends(require_auth),
    agent_id: str | None = None,
):
    """List API keys (prefix only, no secrets). Filter by agent_id if given."""
    q = select(ApiKey).order_by(ApiKey.created_at.desc())
    if agent_id:
        try:
            uid = UUID(agent_id)
            q = q.where(ApiKey.agent_id == uid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent_id")
        agent = await session.get(Agent, uid)
        if not agent or str(agent.owner_user_id or "") != user_id:
            raise HTTPException(status_code=403, detail="Forbidden agent")
    else:
        owned_agents = (await session.execute(select(Agent.id).where(Agent.owner_user_id == user_id))).scalars().all()
        if not owned_agents:
            return []
        q = q.where(ApiKey.agent_id.in_(owned_agents))
    r = await session.execute(q)
    rows = r.scalars().all()
    return [
        ApiKeyPublic(
            id=str(k.id),
            agent_id=str(k.agent_id),
            key_prefix=k.key_prefix,
            scope=k.scope,
            expires_at=k.expires_at,
            created_at=k.created_at,
        )
        for k in rows
    ]
