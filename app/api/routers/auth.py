from app.services.recoverable_errors import report_optional_failure
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select

from app.api.deps import DbSession, require_auth
from app.config import get_settings
from app.db.models import User, UserEvmWallet
from app.schemas import (
    AuthLoginRequest,
    AuthLoginResponse,
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordForgotRequest,
    PasswordRecoverWithWalletRequest,
    PasswordRecoverWithWalletResponse,
    PasswordForgotResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    UserCreateRequest,
    UserPublic,
    WalletAuthNonceRequest,
    WalletAuthNonceResponse,
    WalletAuthVerifyRequest,
    WalletLinkRequest,
    WalletLinkResponse,
)
from app.services.acp_wallet import (
    create_wallet_for_user,
    decrypt_wallet_secret_with_recovery_key,
    get_wallet_for_user,
    migrate_wallet_to_recovery_ready,
    password_recovery_ready,
    personalize_hot_bound_wallet,
    rewrap_wallet_secret_for_password_change,
    set_wallet_secret_for_password,
)
from app.services.auth import create_access_token, hash_password, verify_password
from app.services.auth_flows import (
    create_password_reset,
    find_user_by_email,
    get_password_reset_token,
    mark_password_reset_token_used,
    send_login_alert,
    send_password_reset_email,
)
from app.services.anti_sybil import evaluate_registration_signals
from app.services.referrals import attribute_referral
from app.services.turnstile import verify_turnstile
from app.services.welcome_grant import issue_welcome_grant_idempotent
from app.services.wallet_auth import create_wallet_auth_challenge, verify_wallet_auth_and_issue_token
from app.services.rate_limit import build_rate_limit_key, enforce_rate_limit, get_request_ip

router = APIRouter(prefix="/auth", tags=["Auth"])


def _auth_cookie_secure(request: Request) -> bool:
    forwarded_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    scheme = forwarded_proto or (request.url.scheme or "").strip().lower()
    if scheme != "https":
        return False

    host = (
        (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
        or (request.headers.get("host") or "").split(",")[0].strip()
        or request.url.hostname
        or ""
    )
    hostname = host.split(":", 1)[0].strip().lower()
    if hostname in {"127.0.0.1", "localhost", "::1", "[::1]"}:
        return False
    return True


def _auth_cookie_domain(request: Request) -> str | None:
    """Share auth cookie across ancap.cloud ↔ api.ancap.cloud."""
    host = (
        (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
        or (request.headers.get("host") or "").split(",")[0].strip()
        or (request.url.hostname or "")
    )
    hostname = host.split(":", 1)[0].strip().lower()
    if hostname == "ancap.cloud" or hostname.endswith(".ancap.cloud"):
        return ".ancap.cloud"
    return None


def _set_auth_cookie(response: Response, token: str, request: Request) -> None:
    secure = _auth_cookie_secure(request)
    ttl_seconds = max(60, int(get_settings().access_token_expire_minutes) * 60)
    response.set_cookie(
        key="ancap_token",
        value=token,
        httponly=True,
        secure=secure,
        # Lax keeps same-site subdomain auth (ancap.cloud ↔ api.ancap.cloud) working.
        samesite="lax",
        max_age=ttl_seconds,
        path="/",
        domain=_auth_cookie_domain(request),
    )


def _clear_auth_cookie(response: Response, request: Request) -> None:
    response.delete_cookie(
        key="ancap_token",
        path="/",
        httponly=True,
        secure=_auth_cookie_secure(request),
        samesite="lax",
        domain=_auth_cookie_domain(request),
    )


async def _enforce_auth_rate_limit(
    request: Request,
    *,
    scope: str,
    subject: str | None = None,
    limit: int,
    window_seconds: int,
) -> None:
    await enforce_rate_limit(
        key=build_rate_limit_key(scope=scope, ip=get_request_ip(request), subject=subject),
        limit=limit,
        window_seconds=window_seconds,
    )



@router.post("/login", response_model=AuthLoginResponse)
async def login(body: AuthLoginRequest, request: Request, response: Response, session: DbSession):
    await _enforce_auth_rate_limit(
        request,
        scope="auth_login",
        subject=body.email,
        limit=8,
        window_seconds=300,
    )
    await verify_turnstile(request, body.turnstile_token, "login")
    q = select(User).where(User.email == body.email)
    r = await session.execute(q)
    user = r.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    wallet = await get_wallet_for_user(session, str(user.id))
    if wallet is None:
        await create_wallet_for_user(
            session=session,
            user_id=str(user.id),
            password=body.password,
        )
    else:
        try:
            personalized = await personalize_hot_bound_wallet(
                session=session,
                user_id=str(user.id),
                password=body.password,
            )
        except Exception:
            personalized = None
        if personalized is None:
            await migrate_wallet_to_recovery_ready(session, str(user.id), body.password)

    token = create_access_token(str(user.id))
    try:
        await send_login_alert(user=user, request=request, via="password")
    except Exception:
        report_optional_failure('app.api.routers.auth:login:167', quiet=True)
    _set_auth_cookie(response, token, request)
    # Never return mnemonics on login — register (or explicit recover) is the one-shot path.
    return AuthLoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=3600,
        wallet_backup_mnemonic=None,
    )


@router.post("/wallet/nonce", response_model=WalletAuthNonceResponse)
async def wallet_nonce(body: WalletAuthNonceRequest, request: Request, session: DbSession):
    await _enforce_auth_rate_limit(
        request,
        scope="auth_wallet_nonce",
        subject=body.address,
        limit=12,
        window_seconds=300,
    )
    await verify_turnstile(request, body.turnstile_token, "login")
    forwarded_host = (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
    host = forwarded_host or (request.headers.get("host") or "ancap.cloud").split(",")[0].strip()

    forwarded_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    scheme = forwarded_proto or (request.url.scheme or "https").strip().lower()
    if scheme not in {"http", "https"}:
        scheme = "https"

    default_uri = f"{scheme}://{host}/login"
    challenge = await create_wallet_auth_challenge(
        session,
        address=body.address,
        chain_id=body.chain_id,
        domain=(body.domain or host).strip(),
        uri=(body.uri or default_uri).strip(),
    )
    return WalletAuthNonceResponse(
        challenge_id=str(challenge.id),
        address=challenge.wallet_address,
        chain_id=int(challenge.chain_id or 56),
        nonce=challenge.nonce,
        message=challenge.message,
        issued_at=challenge.issued_at,
        expires_at=challenge.expires_at,
    )


@router.post("/wallet/verify", response_model=AuthLoginResponse)
async def wallet_verify(body: WalletAuthVerifyRequest, request: Request, response: Response, session: DbSession):
    await _enforce_auth_rate_limit(
        request,
        scope="auth_wallet_verify",
        subject=body.address,
        limit=10,
        window_seconds=300,
    )
    try:
        token, user = await verify_wallet_auth_and_issue_token(
            session,
            challenge_id=body.challenge_id,
            address=body.address,
            signature=body.signature,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        await send_login_alert(user=user, request=request, via="wallet")
    except Exception:
        report_optional_failure('app.api.routers.auth:wallet_verify:237', quiet=True)
    _set_auth_cookie(response, token, request)
    return AuthLoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=3600,
        wallet_backup_mnemonic=None,
    )


@router.post("/wallet/link", response_model=WalletLinkResponse)
async def wallet_link(
    body: WalletLinkRequest,
    request: Request,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    result = await session.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        await verify_wallet_auth_and_issue_token(
            session,
            challenge_id=body.challenge_id,
            address=body.address,
            signature=body.signature,
            link_to_user=user,
        )
    except ValueError as exc:
        detail = str(exc)
        code = status.HTTP_409_CONFLICT if "already linked to another account" in detail.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=detail) from exc

    wallet_result = await session.execute(select(UserEvmWallet).where(UserEvmWallet.user_id == UUID(user_id)))
    wallet_link_row = wallet_result.scalar_one_or_none()
    return WalletLinkResponse(
        success=True,
        wallet_address=(wallet_link_row.wallet_address if wallet_link_row else body.address.lower()),
        chain_id=int(wallet_link_row.chain_id or 56) if wallet_link_row else 56,
    )


@router.post("/users", response_model=UserPublic, status_code=201)
async def create_user(body: UserCreateRequest, request: Request, response: Response, session: DbSession):
    await _enforce_auth_rate_limit(
        request,
        scope="auth_register",
        subject=body.email,
        limit=6,
        window_seconds=3600,
    )
    await verify_turnstile(request, body.turnstile_token, "register")
    q = select(User).where(User.email == body.email)
    r = await session.execute(q)
    if r.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
    )
    session.add(user)
    await session.flush()
    _, mnemonic = await create_wallet_for_user(
        session=session,
        user_id=str(user.id),
        password=body.password,
    )
    if body.referral_code and body.referral_code.strip():
        await attribute_referral(
            session,
            code=body.referral_code.strip(),
            referred_user_id=user.id,
            referred_agent_id=None,
            source="signup",
        )
    sybil = await evaluate_registration_signals(
        session,
        request=request,
        user_id=user.id,
        device_fingerprint=body.device_fingerprint,
    )
    await issue_welcome_grant_idempotent(
        session,
        user_id=user.id,
        free_grants_allowed=sybil.free_grants_allowed,
    )
    await session.refresh(user)
    token = create_access_token(str(user.id))
    _set_auth_cookie(response, token, request)
    return UserPublic(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
        wallet_backup_mnemonic=mnemonic,
        access_token=token,
        token_type="bearer",
        expires_in=3600,
    )


@router.post("/password/forgot", response_model=PasswordForgotResponse)
async def password_forgot(body: PasswordForgotRequest, request: Request, session: DbSession):
    await _enforce_auth_rate_limit(
        request,
        scope="auth_password_forgot",
        subject=body.email,
        limit=5,
        window_seconds=900,
    )
    await verify_turnstile(request, body.turnstile_token, "login")
    user = await find_user_by_email(session, body.email)
    if user is not None:
        wallet = await get_wallet_for_user(session, str(user.id))
        if wallet is None:
            raw_token, _reset = await create_password_reset(session, user)
            try:
                await send_password_reset_email(request, user, raw_token)
            except Exception:
                report_optional_failure('app.api.routers.auth:password_forgot:359', quiet=True)
    return PasswordForgotResponse(success=True)


@router.post("/password/reset", response_model=PasswordResetResponse)
async def password_reset(body: PasswordResetRequest, request: Request, session: DbSession):
    await _enforce_auth_rate_limit(
        request,
        scope="auth_password_reset",
        subject=body.token[:12],
        limit=8,
        window_seconds=900,
    )
    await verify_turnstile(request, body.turnstile_token, "login")
    try:
        reset = await get_password_reset_token(session, body.token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    result = await session.execute(select(User).where(User.id == reset.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    wallet = await get_wallet_for_user(session, str(user.id))
    if wallet is not None:
        linked_wallet_result = await session.execute(
            select(UserEvmWallet).where(UserEvmWallet.user_id == user.id)
        )
        linked_wallet = linked_wallet_result.scalar_one_or_none()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ACP_WALLET_PASSWORD_RESET_BLOCKED",
                "message": (
                    "Password reset is temporarily blocked for accounts with an ACP wallet. "
                    "Sign in and change your password from an authenticated session so the wallet secret can be re-encrypted safely."
                ),
                "recovery": {
                    "type": "authenticated_password_rotation",
                    "wallet_signin_available": linked_wallet is not None,
                    "linked_wallet_address": (linked_wallet.wallet_address if linked_wallet is not None else None),
                    "login_target": "/login?next=/wallet/acp%23password-security",
                    "wallet_recovery_target": "/wallet/acp#password-security",
                },
            },
        )

    user.password_hash = hash_password(body.password)
    mark_password_reset_token_used(reset)
    return PasswordResetResponse(success=True)


@router.post("/password/recover-with-wallet", response_model=PasswordRecoverWithWalletResponse)
async def password_recover_with_wallet(
    body: PasswordRecoverWithWalletRequest,
    request: Request,
    session: DbSession,
):
    await _enforce_auth_rate_limit(
        request,
        scope="auth_password_recover_wallet",
        subject=body.address,
        limit=6,
        window_seconds=900,
    )
    try:
        _token, user = await verify_wallet_auth_and_issue_token(
            session,
            challenge_id=body.challenge_id,
            address=body.address,
            signature=body.signature,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    wallet = await get_wallet_for_user(session, str(user.id))
    if wallet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ACP wallet not found for this account",
        )

    if not password_recovery_ready(wallet):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ACP_WALLET_RECOVERY_NOT_AVAILABLE",
                "message": (
                    "Wallet-based password recovery is not available for this ACP-wallet account yet. "
                    "The wallet secret is still encrypted under the account password and cannot be safely rewrapped from wallet sign-in alone."
                ),
                "recovery": {
                    "type": "authenticated_password_rotation",
                    "wallet_signin_available": True,
                    "linked_wallet_address": body.address.lower(),
                    "login_target": "/login?next=/wallet/acp%23password-security",
                    "wallet_recovery_target": "/wallet/acp#password-security",
                },
            },
        )

    try:
        wallet_secret = decrypt_wallet_secret_with_recovery_key(wallet)
        await set_wallet_secret_for_password(
            session=session,
            user_id=str(user.id),
            wallet_secret=wallet_secret,
            new_password=body.new_password,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ACP wallet recovery material is present but password recovery failed",
        ) from exc

    user.password_hash = hash_password(body.new_password)
    return PasswordRecoverWithWalletResponse(success=True)


@router.post("/password/change", response_model=PasswordChangeResponse)
async def password_change(
    body: PasswordChangeRequest,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    result = await session.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    try:
        # If this account still points at shared custodial hot, mint a personal wallet
        # first (encrypted with current_password), then re-wrap under the new password.
        await personalize_hot_bound_wallet(
            session=session,
            user_id=str(user.id),
            password=body.current_password,
        )
        await rewrap_wallet_secret_for_password_change(
            session=session,
            user_id=str(user.id),
            current_password=body.current_password,
            new_password=body.new_password,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ACP wallet secret could not be re-encrypted with the new password",
        ) from exc

    user.password_hash = hash_password(body.new_password)
    await migrate_wallet_to_recovery_ready(session, str(user.id), body.new_password)
    return PasswordChangeResponse(success=True)


@router.post("/logout")
async def logout(request: Request, response: Response, user_id: str = Depends(require_auth)):
    """Clear the HttpOnly auth cookie. Returns 200 even if the user is not fully authenticated."""
    _clear_auth_cookie(response, request)
    return {"ok": True}
