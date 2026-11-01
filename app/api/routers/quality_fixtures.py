"""Private operator quality-fixture inspection."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from app.api.deps import DbSession, require_platform_admin
from app.schemas.quality_fixtures import QualityFixtureResponse, QualityFixtureListResponse
from app.services.quality_fixtures import get_quality_fixture, get_all_quality_fixtures

router = APIRouter(prefix="/quality-fixtures", tags=["quality-fixtures-admin"])


@router.get("/{fixture_id}", response_model=QualityFixtureResponse)
async def get_quality_fixture_admin(fixture_id: UUID, db: DbSession, response: Response,
                                     _admin: str = Depends(require_platform_admin)):
    response.headers["Cache-Control"] = "private, no-store"
    fixture = await get_quality_fixture(db, fixture_id)
    if fixture is None:
        raise HTTPException(status_code=404, detail="Quality fixture not found")
    return fixture


@router.get("/", response_model=QualityFixtureListResponse)
async def list_quality_fixtures(db: DbSession, response: Response,
                                limit: int = Query(100, ge=1, le=200),
                                offset: int = Query(0, ge=0),
                                _admin: str = Depends(require_platform_admin)):
    response.headers["Cache-Control"] = "private, no-store"
    fixtures, total = await get_all_quality_fixtures(db, limit=limit, offset=offset)
    return QualityFixtureListResponse(fixtures=fixtures, total=total, limit=limit, offset=offset)
