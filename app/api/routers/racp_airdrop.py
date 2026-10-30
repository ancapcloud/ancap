from fastapi import APIRouter, Request
from app.api.deps import DbSession, require_auth
from fastapi import Depends
from app.schemas.racp_airdrop import RacpAirdropStatus, RacpAirdropVoucher, RacpAirdropVoucherRequest
from app.services import racp_airdrop
from app.services.rate_limit import build_rate_limit_key, enforce_rate_limit, get_request_ip
from app.services.turnstile import verify_turnstile

router = APIRouter(prefix="/racp/airdrop", tags=["rACP airdrop"])


@router.get("/status", response_model=RacpAirdropStatus)
async def status():
    return await racp_airdrop.public_status()


@router.post("/voucher", response_model=RacpAirdropVoucher)
async def voucher(body: RacpAirdropVoucherRequest, request: Request, session: DbSession, user_id: str = Depends(require_auth)):
    await enforce_rate_limit(key=f"racp_airdrop_user:{user_id}", limit=3, window_seconds=60)
    await enforce_rate_limit(key=build_rate_limit_key(scope="racp_airdrop_ip", ip=get_request_ip(request)), limit=20, window_seconds=60)
    await verify_turnstile(request, body.turnstile_token, "racp_airdrop")
    return await racp_airdrop.issue_voucher(session, user_id, body.address)
