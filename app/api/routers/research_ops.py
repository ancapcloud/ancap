from uuid import UUID
from fastapi import APIRouter, Depends, Response
from app.api.deps import DbSession, require_auth
from app.schemas.research_ops import SourceCreate, ClaimCreate, PacketCreate, PriceChangeFixture, MarkupNoiseFixture, UnavailableSourceFixture, ContradictionFixture, MaliciousEmbeddedFixture
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


@router.post("/quality/fixtures", status_code=201)
async def upload_quality_fixtures(project_id: UUID, fixtures: dict, response: Response, session: DbSession, user: str = Depends(require_auth)):
    """Upload quality test fixtures for ROP-03 bounded collection."""
    private(response)
    result = await research.upload_quality_fixtures(session, str(project_id), fixtures)
    return result


@router.get("/quality/fixtures/{fixture_id}")
async def get_quality_fixture(project_id: UUID, fixture_id: str, response: Response, session: DbSession, user: str = Depends(require_auth)):
    """Get a quality test fixture by ID."""
    private(response)
    result = await research.get_quality_fixture(session, str(project_id), fixture_id)
    return result


@router.delete("/quality/fixtures/{fixture_id}")
async def remove_quality_fixture(project_id: UUID, fixture_id: str, response: Response, session: DbSession, user: str = Depends(require_auth)):
    """Remove a quality test fixture."""
    private(response)
    result = await research.remove_quality_fixture(session, str(project_id), fixture_id)
    return result
