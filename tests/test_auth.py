"""Auth: register user, login, password reset flows."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone


from sqlalchemy import create_engine, select as sync_select
from sqlalchemy.orm import Session

from app.api.routers import auth as auth_router
from app.db.models import PasswordResetToken, User, UserAcpWallet, UserEvmWallet
from app.services.acp_wallet import decrypt_wallet_secret_with_password, password_recovery_ready
from tests.conftest import _sync_database_url, unique_email


def test_register_user(client):
    email = unique_email()
    r = client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": "Test User"},
        headers={"Authorization": ""},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["email"] == email
    assert data["display_name"] == "Test User"
    assert "id" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["expires_in"] == 3600
    assert "wallet_backup_mnemonic" in data


def test_register_duplicate_email(client):
    email = unique_email()
    client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": "First"},
        headers={"Authorization": ""},
    )
    r = client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": "Second"},
        headers={"Authorization": ""},
    )
    assert r.status_code == 400


def test_login(client, monkeypatch):
    email = unique_email()
    client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": "Login Test"},
        headers={"Authorization": ""},
    )
    monkeypatch.setattr(auth_router, "send_login_alert", _async_return(False))
    r = client.post("/v1/auth/login", json={"email": email, "password": "password123"}, headers={"Authorization": ""})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert data["expires_in"] == 3600
    set_cookie = r.headers.get("set-cookie", "")
    assert "ancap_token=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Secure" not in set_cookie


def test_login_sets_secure_cookie_for_https_origin(client, monkeypatch):
    email = unique_email()
    client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": "HTTPS Login Test"},
        headers={"Authorization": ""},
    )
    monkeypatch.setattr(auth_router, "send_login_alert", _async_return(False))
    r = client.post(
        "/v1/auth/login",
        json={"email": email, "password": "password123"},
        headers={"Authorization": "", "X-Forwarded-Proto": "https", "Host": "ancap.cloud"},
    )
    assert r.status_code == 200, r.text
    set_cookie = r.headers.get("set-cookie", "")
    assert "ancap_token=" in set_cookie
    assert "Secure" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Domain=.ancap.cloud" in set_cookie


def test_login_does_not_set_secure_cookie_for_https_loopback_origin(client, monkeypatch):
    email = unique_email()
    client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": "Loopback Login Test"},
        headers={"Authorization": ""},
    )
    monkeypatch.setattr(auth_router, "send_login_alert", _async_return(False))
    r = client.post(
        "/v1/auth/login",
        json={"email": email, "password": "password123"},
        headers={"Authorization": "", "X-Forwarded-Proto": "https", "Host": "127.0.0.1:8001"},
    )
    assert r.status_code == 200, r.text
    set_cookie = r.headers.get("set-cookie", "")
    assert "ancap_token=" in set_cookie
    assert "Secure" not in set_cookie


def test_login_wrong_password(client):
    email = unique_email()
    client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": "User"},
        headers={"Authorization": ""},
    )
    r = client.post("/v1/auth/login", json={"email": email, "password": "wrongpass123"}, headers={"Authorization": ""})
    assert r.status_code == 400


def test_password_forgot_skips_email_reset_for_acp_wallet_accounts(client, monkeypatch):
    email = unique_email()
    password = "password123"
    client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "Reset Me"},
        headers={"Authorization": ""},
    )

    sent = {"called": False}

    async def fake_send_password_reset_email(_request, _user, raw_token):
        sent["called"] = True
        sent["token"] = raw_token
        return True

    monkeypatch.setattr(auth_router, "send_password_reset_email", fake_send_password_reset_email)
    forgot = client.post(
        "/v1/auth/password/forgot",
        json={"email": email},
        headers={"Authorization": ""},
    )
    assert forgot.status_code == 200, forgot.text
    assert forgot.json()["success"] is True
    assert sent["called"] is False

    sync_engine = create_engine(_sync_database_url(), pool_pre_ping=True)
    with Session(sync_engine) as session:
        user = session.execute(sync_select(User).where(User.email == email)).scalar_one()
        token_rows = session.execute(
            sync_select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
        ).scalars().all()
        assert token_rows == []
    sync_engine.dispose()

    monkeypatch.setattr(auth_router, "send_login_alert", _async_return(False))
    old_login = client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
        headers={"Authorization": ""},
    )
    assert old_login.status_code == 200, old_login.text


def test_password_reset_returns_structured_acp_wallet_block_error(client, monkeypatch):
    email = unique_email()
    password = "password123"
    register = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "ACP Reset Block"},
        headers={"Authorization": ""},
    )
    assert register.status_code == 201, register.text

    sync_engine = create_engine(_sync_database_url(), pool_pre_ping=True)
    with Session(sync_engine) as session:
        user = session.execute(sync_select(User).where(User.email == email)).scalar_one()
        raw_token = f"reset-{unique_email()}"
        token_row = PasswordResetToken(
            user_id=user.id,
            token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        session.add(token_row)
        session.commit()

    reset = client.post(
        "/v1/auth/password/reset",
        json={"token": raw_token, "password": "newpassword123"},
        headers={"Authorization": ""},
    )
    assert reset.status_code == 409, reset.text
    payload = reset.json()
    assert payload["detail"]["code"] == "ACP_WALLET_PASSWORD_RESET_BLOCKED"
    assert "ACP wallet" in payload["detail"]["message"]
    recovery = payload["detail"]["recovery"]
    assert recovery["type"] == "authenticated_password_rotation"
    assert recovery["wallet_signin_available"] is False
    assert recovery["linked_wallet_address"] is None
    assert recovery["login_target"] == "/login?next=/wallet/acp%23password-security"
    assert recovery["wallet_recovery_target"] == "/wallet/acp#password-security"
    sync_engine.dispose()


def _unique_wallet_address() -> str:
    return f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}"



def test_password_recover_with_wallet_returns_structured_not_available_for_legacy_acp_wallet(client, monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("ACP_WALLET_RECOVERY_MASTER_KEY", "")
    get_settings.cache_clear()

    wallet_address = _unique_wallet_address()
    email = unique_email()
    password = "password123"
    register = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "Wallet Recovery Legacy"},
        headers={"Authorization": ""},
    )
    assert register.status_code == 201, register.text

    sync_engine = create_engine(_sync_database_url(), pool_pre_ping=True)
    with Session(sync_engine) as session:
        user = session.execute(sync_select(User).where(User.email == email)).scalar_one()
        wallet_link = UserEvmWallet(user_id=user.id, wallet_address=wallet_address, chain_id=56)
        session.add(wallet_link)
        session.commit()
    sync_engine.dispose()

    nonce_res = client.post(
        "/v1/auth/wallet/nonce",
        json={
            "address": wallet_address,
            "chain_id": 56,
            "domain": "ancap.cloud",
            "uri": "https://ancap.cloud/login",
        },
        headers={"Authorization": ""},
    )
    assert nonce_res.status_code == 200, nonce_res.text
    payload = nonce_res.json()

    from app.services import wallet_auth
    original_recover = wallet_auth.Account.recover_message
    wallet_auth.Account.recover_message = lambda _encoded, signature: wallet_address
    try:
        recover = client.post(
            "/v1/auth/password/recover-with-wallet",
            json={
                "challenge_id": payload["challenge_id"],
                "address": wallet_address,
                "signature": "0xdeadbeef",
                "new_password": "newpassword123",
            },
            headers={"Authorization": ""},
        )
    finally:
        wallet_auth.Account.recover_message = original_recover

    assert recover.status_code == 409, recover.text
    detail = recover.json()["detail"]
    assert detail["code"] == "ACP_WALLET_RECOVERY_NOT_AVAILABLE"
    assert detail["recovery"]["wallet_signin_available"] is True
    assert detail["recovery"]["linked_wallet_address"] == wallet_address


def test_password_recover_with_wallet_succeeds_for_recovery_ready_wallet(client, monkeypatch):
    monkeypatch.setenv("ACP_WALLET_RECOVERY_MASTER_KEY", "test-master-key")
    from app.config import get_settings
    get_settings.cache_clear()

    wallet_address = _unique_wallet_address()
    email = unique_email()
    password = "password123"
    register = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "Wallet Recovery Ready"},
        headers={"Authorization": ""},
    )
    assert register.status_code == 201, register.text

    sync_engine = create_engine(_sync_database_url(), pool_pre_ping=True)
    with Session(sync_engine) as session:
        user = session.execute(sync_select(User).where(User.email == email)).scalar_one()
        wallet = session.get(UserAcpWallet, user.id)
        assert wallet is not None
        assert password_recovery_ready(wallet) is True
        wallet_link = UserEvmWallet(user_id=user.id, wallet_address=wallet_address, chain_id=56)
        session.add(wallet_link)
        session.commit()
    sync_engine.dispose()

    nonce_res = client.post(
        "/v1/auth/wallet/nonce",
        json={
            "address": wallet_address,
            "chain_id": 56,
            "domain": "ancap.cloud",
            "uri": "https://ancap.cloud/login",
        },
        headers={"Authorization": ""},
    )
    assert nonce_res.status_code == 200, nonce_res.text
    payload = nonce_res.json()

    from app.services import wallet_auth
    original_recover = wallet_auth.Account.recover_message
    wallet_auth.Account.recover_message = lambda _encoded, signature: wallet_address
    try:
        recover = client.post(
            "/v1/auth/password/recover-with-wallet",
            json={
                "challenge_id": payload["challenge_id"],
                "address": wallet_address,
                "signature": "0xdeadbeef",
                "new_password": "newpassword123",
            },
            headers={"Authorization": ""},
        )
    finally:
        wallet_auth.Account.recover_message = original_recover

    assert recover.status_code == 200, recover.text
    assert recover.json()["success"] is True

    login = client.post("/v1/auth/login", json={"email": email, "password": "newpassword123"}, headers={"Authorization": ""})
    assert login.status_code == 200, login.text


def test_cookie_authenticated_post_requires_x_requested_with_header(client, monkeypatch):
    email = unique_email()
    password = "password123"
    register = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "Cookie CSRF Guard"},
        headers={"Authorization": ""},
    )
    assert register.status_code == 201, register.text
    token = register.json()["access_token"]

    missing_header = client.post(
        "/v1/auth/logout",
        cookies={"ancap_token": token},
        headers={"Authorization": ""},
    )
    assert missing_header.status_code == 403, missing_header.text
    assert missing_header.json()["detail"] == "Missing X-Requested-With header for cookie-authenticated request"

    ok = client.post(
        "/v1/auth/logout",
        cookies={"ancap_token": token},
        headers={"Authorization": "", "X-Requested-With": "XMLHttpRequest"},
    )
    assert ok.status_code == 200, ok.text
    cleared = ok.headers.get("set-cookie", "")
    assert "ancap_token=" in cleared
    assert "SameSite=lax" in cleared
    assert "Secure" not in cleared


def test_logout_preflight_allows_explicit_same_origin_headers(client):
    response = client.options(
        "/v1/auth/logout",
        headers={
            "Authorization": "",
            "Origin": "https://ancap.cloud",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-requested-with",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers.get("access-control-allow-origin") == "https://ancap.cloud"
    assert response.headers.get("access-control-allow-credentials") == "true"
    allowed_headers = (response.headers.get("access-control-allow-headers") or "").lower()
    assert "content-type" in allowed_headers
    assert "x-requested-with" in allowed_headers


def test_logout_preflight_rejects_disallowed_origin(client):
    response = client.options(
        "/v1/auth/logout",
        headers={
            "Authorization": "",
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-requested-with",
        },
    )

    assert response.status_code == 400, response.text
    assert response.text == "Disallowed CORS origin"
    assert "access-control-allow-origin" not in response.headers


def test_password_change_rewraps_acp_wallet_secret(client, monkeypatch):
    email = unique_email()
    password = "password123"
    new_password = "newpassword123"
    register = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "Change Password"},
        headers={"Authorization": ""},
    )
    assert register.status_code == 201, register.text

    monkeypatch.setattr(auth_router, "send_login_alert", _async_return(False))
    login = client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
        headers={"Authorization": ""},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    change = client.post(
        "/v1/auth/password/change",
        json={"current_password": password, "new_password": new_password},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert change.status_code == 200, change.text
    assert change.json()["success"] is True

    old_login = client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
        headers={"Authorization": ""},
    )
    assert old_login.status_code == 400, old_login.text

    new_login = client.post(
        "/v1/auth/login",
        json={"email": email, "password": new_password},
        headers={"Authorization": ""},
    )
    assert new_login.status_code == 200, new_login.text

    sync_engine = create_engine(_sync_database_url(), pool_pre_ping=True)
    with Session(sync_engine) as session:
        user = session.execute(sync_select(User).where(User.email == email)).scalar_one()
        wallet = session.get(UserAcpWallet, user.id)
        assert wallet is not None
        decrypted = decrypt_wallet_secret_with_password(wallet, new_password)
        assert decrypted
    sync_engine.dispose()


def _async_return(value):
    async def _inner(*_args, **_kwargs):
        return value

    return _inner
