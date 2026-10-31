from uuid import UUID
from fastapi import APIRouter, Depends, Response
from app.api.deps import DbSession, require_auth
from app.schemas.research_ops import SourceCreate, ClaimCreate, PacketCreate
from app.services import research_ops as research
from app.services import research_packets

router = APIRouter(prefix="/workflow-ops/projects/{project_id}/research", tags=["Research Operations"])


def private(response):
    response.headers["Cache-Control"] = "private, no-store"


@router.get("")
async def brief(project_id: UUID, response: Response, session: DbSession, user: str = Depends(require_auth)):
    private(response)
    return await research.brief(session, user, project_id)


@router.post("/sources", status_code=201)
async def add_source(project_id: UUID, body: SourceCreate, response: Response, session: DbSession, user: str = Depends(require_auth)):
    private(response)
    return await research.add_source(session, user, project_id, body)


@router.post("/sources/{source_id}/check")
async def check_source(project_id: UUID, source_id: UUID, response: Response, session: DbSession, user: str = Depends(require_auth)):
    private(response)
    return await research.check_source(session, user, project_id, source_id)


@router.get("/sources/{source_id}/snapshots")
async def snapshots(project_id: UUID, source_id: UUID, response: Response, session: DbSession, user: str = Depends(require_auth)):
    private(response)
    return await research.snapshots(session, user, project_id, source_id)


@router.post("/claims", status_code=201)
async def add_claim(project_id: UUID, body: ClaimCreate, response: Response, session: DbSession, user: str = Depends(require_auth)):
    private(response)
    return await research.add_claim(session, user, project_id, body)


@router.delete("/sources/{source_id}")
async def remove_source(project_id: UUID, source_id: UUID, response: Response, session: DbSession, user: str = Depends(require_auth)):
    private(response)
    return await research.remove_source(session, user, project_id, source_id)


@router.post("/packets", status_code=201)
async def attach_packet(project_id: UUID, body: PacketCreate, response: Response, session: DbSession, user: str = Depends(require_auth)):
    private(response)
    return await research_packets.attach_packet(session, user, project_id, body)
