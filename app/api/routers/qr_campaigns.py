import logging
from fastapi import APIRouter, Depends, Request, Query, Response
from fastapi.responses import RedirectResponse
from app.api.deps import DbSession, require_platform_admin
from app.schemas.qr_campaigns import QrStats
from app.services import qr_campaigns as svc

router = APIRouter(prefix="/qr", tags=["QR campaigns"])
logger = logging.getLogger(__name__)
NO_CACHE = {"Cache-Control": "no-store, max-age=0", "X-Robots-Tag": "noindex, nofollow"}

@router.api_route("/street", methods=["GET", "HEAD"])
async def street(request: Request, session: DbSession):
    if svc.should_count(request.method, request.headers):
        try:
            # A savepoint preserves redirect availability when the migration or
            # counter write fails; no personal request data is persisted.
            async with session.begin_nested():
                await svc.record_visit(session)
        except Exception:
            logger.warning("QR counter write unavailable")
    return RedirectResponse(svc.DESTINATION, status_code=302, headers=NO_CACHE)

@router.get("/street/stats", response_model=QrStats)
async def stats(response: Response, session: DbSession, days: int = Query(30, ge=1, le=90),
                _admin: str = Depends(require_platform_admin)):
    response.headers.update(NO_CACHE)
    return await svc.get_stats(session, days)
