"""ACP wallet balance breakdown: hero fields, probe status, operator hot-only withdrawable."""
from decimal import Decimal
from uuid import uuid4

import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def no_live_vesting_rpc(monkeypatch):
    # These tests exercise balance accounting with stubbed chain probes.
    # Vesting is unrelated and must not resolve a live node hostname.
    from app.api.routers import wallet_acp
    monkeypatch.setattr(wallet_acp, "_creator_vesting_snapshot", lambda address: None)


def _free_custodial_hot_bindings() -> None:
    import os

    from sqlalchemy import create_engine, text

    from app.services.acp_tokenomics import CUSTODIAL_HOT_ADDRESS

    db_url = os.environ["DATABASE_URL"].replace("+asyncpg", "").replace(
        "postgresql+asyncpg", "postgresql"
    )
    eng = create_engine(db_url, pool_pre_ping=True)
    with eng.begin() as conn:
        rows = conn.execute(
            text("SELECT user_id::text FROM user_acp_wallets WHERE address = :a"),
            {"a": CUSTODIAL_HOT_ADDRESS},
        ).fetchall()
        for (uid,) in rows:
            conn.execute(
                text(
                    "UPDATE user_acp_wallets SET address = :addr "
                    "WHERE user_id = CAST(:uid AS uuid)"
                ),
                {"addr": f"acp1qcleanup{uuid4().hex[:28]}", "uid": uid},
            )
    eng.dispose()


def test_user_hero_prefers_platform_ledger_when_on_chain_empty(client, monkeypatch):
    """primary_acp / primary_kind use platform credits when deposit on-chain is 0."""
    from app.api.routers import wallet_acp as wallet_acp_router

    monkeypatch.setenv("WELCOME_GRANT_ACP", "100")
    get_settings.cache_clear()

    monkeypatch.setattr(
        wallet_acp_router,
        "_load_balance_result",
        lambda address, interactive=True: {
            "address": address,
            "units": "0",
            "acp": "0",
            "utxo_count": 0,
        },
    )

    try:
        email = f"hero_ledger_{uuid4().hex[:12]}@test.com"
        res = client.post(
            "/v1/auth/users",
            json={"email": email, "password": "password123", "display_name": "Hero Ledger"},
            headers={"Authorization": ""},
        )
        assert res.status_code == 201, res.text
        headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

        hot = client.get("/v1/wallet/acp/hot/balance", headers=headers)
        assert hot.status_code == 200, hot.text
        body = hot.json()
        assert Decimal(body["platform_ledger_acp"]) == Decimal("100")
        assert Decimal(body["primary_acp"]) == Decimal("100")
        assert body["primary_kind"] == "platform_credits"
        assert Decimal(body["on_chain_at_deposit_acp"]) == Decimal("0")
        assert Decimal(body["withdrawable_now_acp"]) == Decimal("0")
        assert body["withdraw_source"] == "none"
        assert body["probe_status"] == "live"
        assert body["balance_status"] == "live"
        # Compat fields still populated.
        assert Decimal(body["acp"]) == Decimal("100")
        assert Decimal(body["headline_acp"]) == Decimal("100")
    finally:
        monkeypatch.setenv("WELCOME_GRANT_ACP", "0")
        get_settings.cache_clear()


def test_empty_error_payload_marks_balance_degraded(client, monkeypatch):
    """Failed probe empty payload must not look like a live zero wallet."""
    from app.api.routers import wallet_acp as wallet_acp_router

    monkeypatch.setenv("WELCOME_GRANT_ACP", "50")
    get_settings.cache_clear()

    monkeypatch.setattr(
        wallet_acp_router,
        "_load_balance_result",
        lambda address, interactive=True: {
            "address": address,
            "units": "0",
            "acp": "0",
            "utxo_count": 0,
            "source": "error",
        },
    )

    try:
        email = f"probe_fail_{uuid4().hex[:12]}@test.com"
        res = client.post(
            "/v1/auth/users",
            json={"email": email, "password": "password123", "display_name": "Probe Fail"},
            headers={"Authorization": ""},
        )
        assert res.status_code == 201, res.text
        headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

        hot = client.get("/v1/wallet/acp/hot/balance", headers=headers)
        assert hot.status_code == 200, hot.text
        body = hot.json()
        assert body["probe_status"] in {"degraded", "unavailable"}
        assert body["balance_status"] == "degraded"
        assert body["on_chain_at_deposit_acp"] is None
        assert Decimal(body["platform_ledger_acp"]) == Decimal("50")
        assert Decimal(body["primary_acp"]) == Decimal("50")
        assert body["primary_kind"] == "platform_credits"
    finally:
        monkeypatch.setenv("WELCOME_GRANT_ACP", "0")
        get_settings.cache_clear()


def test_operator_withdrawable_is_hot_live_only(client, monkeypatch):
    """Operator hero is live total; withdrawable_now is custodial hot only."""
    import os

    from sqlalchemy import create_engine, select as sync_select
    from sqlalchemy.orm import Session

    from app.api.routers import wallet_acp as wallet_acp_router
    from app.db.models import User, UserAcpWallet
    from app.services.acp_tokenomics import (
        BRIDGE_RESERVE_ADDRESS,
        CUSTODIAL_HOT_ADDRESS,
        CREATOR_BUCKET_ADDRESS,
        ECOSYSTEM_BUCKET_ADDRESS,
        PROJECT_TREASURY_ADDRESS,
        PUBLIC_BUCKET_ADDRESS,
        VALIDATOR_BUCKET_ADDRESS,
    )

    _free_custodial_hot_bindings()

    email = f"op_break_{uuid4().hex[:10]}@test.com"
    monkeypatch.setenv("WELCOME_GRANT_ACP", "0")
    monkeypatch.setenv("ACP_CUSTODIAL_HOT_HOLDER_EMAILS", email)
    get_settings.cache_clear()

    amounts = {
        CREATOR_BUCKET_ADDRESS: (Decimal("69300000"), 1, True),
        VALIDATOR_BUCKET_ADDRESS: (Decimal("105000000"), 1, True),
        PUBLIC_BUCKET_ADDRESS: (Decimal("200000"), 1, True),
        ECOSYSTEM_BUCKET_ADDRESS: (Decimal("7500000"), 1, True),
        CUSTODIAL_HOT_ADDRESS: (Decimal("1000000"), 1, True),
        PROJECT_TREASURY_ADDRESS: (Decimal("1000000"), 1, True),
        BRIDGE_RESERVE_ADDRESS: (Decimal("26000000"), 1, True),
    }

    def fake_probe(address: str, *, timeout_s: int = 10):
        return amounts.get(address, (Decimal("0"), 0, True))

    def fake_balance(address: str, interactive: bool = True):
        acp, utxos, _ok = amounts.get(address, (Decimal("0"), 0, True))
        units = str(int(acp * Decimal("100000000")))
        return {"address": address, "units": units, "acp": str(acp), "utxo_count": utxos}

    monkeypatch.setattr(wallet_acp_router, "_probe_role_wallet", fake_probe)
    monkeypatch.setattr(wallet_acp_router, "_load_balance_result", fake_balance)
    monkeypatch.setattr(wallet_acp_router, "_chain_supply_info", lambda **_kwargs: None)

    try:
        res = client.post(
            "/v1/auth/users",
            json={"email": email, "password": "password123", "display_name": "Op Break"},
            headers={"Authorization": ""},
        )
        assert res.status_code == 201, res.text
        headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

        db_url = os.environ["DATABASE_URL"].replace("+asyncpg", "").replace(
            "postgresql+asyncpg", "postgresql"
        )
        sync_engine = create_engine(db_url, pool_pre_ping=True)
        with Session(sync_engine) as session:
            user = session.execute(sync_select(User).where(User.email == email)).scalar_one()
            wallet = session.get(UserAcpWallet, user.id)
            wallet.address = CUSTODIAL_HOT_ADDRESS
            session.commit()

        hot = client.get("/v1/wallet/acp/hot/balance", headers=headers)
        assert hot.status_code == 200, hot.text
        body = hot.json()
        assert body["view_mode"] == "operator_hot"
        assert body["primary_kind"] == "operator_total"
        assert body["withdraw_source"] == "custodial_hot"
        assert body["probe_status"] == "live"
        expected_live = Decimal("210000000")
        assert Decimal(body["primary_acp"]) == expected_live
        assert Decimal(body["operator_controlled_live_acp"]) == expected_live
        assert Decimal(body["operator_hot_live_acp"]) == Decimal("1000000")
        assert Decimal(body["withdrawable_now_acp"]) == Decimal("1000000")
        assert Decimal(body["available_acp"]) == Decimal("1000000")
        # Deposit address probe only (hot), not aggregate.
        assert Decimal(body["on_chain_at_deposit_acp"]) == Decimal("1000000")

        with Session(sync_engine) as session:
            user = session.execute(sync_select(User).where(User.email == email)).scalar_one()
            wallet = session.get(UserAcpWallet, user.id)
            wallet.address = f"acp1qcleanup{uuid4().hex[:28]}"
            session.commit()
        sync_engine.dispose()
    finally:
        monkeypatch.setenv("ACP_CUSTODIAL_HOT_HOLDER_EMAILS", "dragon.cat.trx@gmail.com")
        get_settings.cache_clear()
        _free_custodial_hot_bindings()


def test_operator_excludes_design_from_live_total_when_probe_fails(client, monkeypatch):
    """Design alloc stays in labeled buckets; live hero excludes unavailable roles."""
    import os

    from sqlalchemy import create_engine, select as sync_select
    from sqlalchemy.orm import Session

    from app.api.routers import wallet_acp as wallet_acp_router
    from app.db.models import User, UserAcpWallet
    from app.services.acp_tokenomics import (
        BRIDGE_RESERVE_ADDRESS,
        BRIDGE_RESERVE_DESIGN_ACP,
        CUSTODIAL_HOT_ADDRESS,
        CREATOR_BUCKET_ADDRESS,
        ECOSYSTEM_BUCKET_ADDRESS,
        GENESIS_TREASURY_DESIGN_ACP,
        PROJECT_TREASURY_ADDRESS,
        PUBLIC_BUCKET_ADDRESS,
        VALIDATOR_BUCKET_ADDRESS,
    )

    _free_custodial_hot_bindings()

    email = f"op_design_{uuid4().hex[:10]}@test.com"
    monkeypatch.setenv("WELCOME_GRANT_ACP", "0")
    monkeypatch.setenv("ACP_CUSTODIAL_HOT_HOLDER_EMAILS", email)
    get_settings.cache_clear()

    probes = {
        CREATOR_BUCKET_ADDRESS: (Decimal("69300000"), 1, True),
        VALIDATOR_BUCKET_ADDRESS: (Decimal("105000000"), 1, True),
        PUBLIC_BUCKET_ADDRESS: (Decimal("0"), 0, False),
        ECOSYSTEM_BUCKET_ADDRESS: (Decimal("7500000"), 1, True),
        CUSTODIAL_HOT_ADDRESS: (Decimal("1000000"), 1, True),
        PROJECT_TREASURY_ADDRESS: (Decimal("1000000"), 1, True),
        BRIDGE_RESERVE_ADDRESS: (Decimal("26000000"), 1, True),
    }

    def fake_probe(address: str, *, timeout_s: int = 10):
        return probes.get(address, (Decimal("0"), 0, False))

    def fake_balance(address: str, interactive: bool = True):
        acp, utxos, ok = probes.get(address, (Decimal("0"), 0, True))
        if not ok:
            acp, utxos = Decimal("0"), 0
        units = str(int(acp * Decimal("100000000")))
        return {"address": address, "units": units, "acp": str(acp), "utxo_count": utxos}

    monkeypatch.setattr(wallet_acp_router, "_probe_role_wallet", fake_probe)
    monkeypatch.setattr(wallet_acp_router, "_load_balance_result", fake_balance)
    monkeypatch.setattr(wallet_acp_router, "_chain_supply_info", lambda **_kwargs: None)

    try:
        res = client.post(
            "/v1/auth/users",
            json={"email": email, "password": "password123", "display_name": "Op Design"},
            headers={"Authorization": ""},
        )
        assert res.status_code == 201, res.text
        headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

        db_url = os.environ["DATABASE_URL"].replace("+asyncpg", "").replace(
            "postgresql+asyncpg", "postgresql"
        )
        sync_engine = create_engine(db_url, pool_pre_ping=True)
        with Session(sync_engine) as session:
            user = session.execute(sync_select(User).where(User.email == email)).scalar_one()
            wallet = session.get(UserAcpWallet, user.id)
            wallet.address = CUSTODIAL_HOT_ADDRESS
            session.commit()

        hot = client.get("/v1/wallet/acp/hot/balance", headers=headers)
        assert hot.status_code == 200, hot.text
        body = hot.json()
        by_key = {b["key"]: b for b in body["tokenomics_buckets"]}
        assert "design" in by_key["public"]["label"].lower()
        assert Decimal(by_key["public"]["acp"]) == GENESIS_TREASURY_DESIGN_ACP
        assert Decimal(by_key["bridge_reserve"]["acp"]) == Decimal("26000000")
        assert Decimal(by_key["bridge_reserve"]["acp"]) != BRIDGE_RESERVE_DESIGN_ACP

        # Live total excludes the unavailable Public bucket's design amount.
        expected_live = Decimal("209800000")
        assert Decimal(body["primary_acp"]) == expected_live
        assert Decimal(body["operator_controlled_live_acp"]) == expected_live
        assert Decimal(body["acp"]) == expected_live
        assert body["probe_status"] == "degraded"
        assert body["balance_status"] == "degraded"
        assert Decimal(body["withdrawable_now_acp"]) == Decimal("1000000")

        with Session(sync_engine) as session:
            user = session.execute(sync_select(User).where(User.email == email)).scalar_one()
            wallet = session.get(UserAcpWallet, user.id)
            wallet.address = f"acp1qcleanup{uuid4().hex[:28]}"
            session.commit()
        sync_engine.dispose()
    finally:
        monkeypatch.setenv("ACP_CUSTODIAL_HOT_HOLDER_EMAILS", "dragon.cat.trx@gmail.com")
        get_settings.cache_clear()
        _free_custodial_hot_bindings()


def test_operator_all_probes_unavailable_does_not_add_ledger_to_supply(client, monkeypatch):
    """When probes fail, ledger claims remain separate from the 210M supply."""
    import os

    from sqlalchemy import create_engine, select as sync_select
    from sqlalchemy.orm import Session

    from app.api.routers import wallet_acp as wallet_acp_router
    from app.db.models import User, UserAcpWallet
    from app.services.acp_tokenomics import (
        GENESIS_SUPPLY_ACP,
    )

    _free_custodial_hot_bindings()

    email = f"op_allfail_{uuid4().hex[:10]}@test.com"
    monkeypatch.setenv("WELCOME_GRANT_ACP", "250")
    monkeypatch.setenv("ACP_CUSTODIAL_HOT_HOLDER_EMAILS", email)
    get_settings.cache_clear()

    def fake_probe(address: str, *, timeout_s: int = 10):
        return Decimal("0"), 0, False

    def fake_balance(address: str, interactive: bool = True):
        return {
            "address": address,
            "units": "0",
            "acp": "0",
            "utxo_count": 0,
            "source": "timeout",
        }

    monkeypatch.setattr(wallet_acp_router, "_probe_role_wallet", fake_probe)
    monkeypatch.setattr(wallet_acp_router, "_load_balance_result", fake_balance)
    monkeypatch.setattr(wallet_acp_router, "_chain_supply_info", lambda **_kwargs: None)

    try:
        res = client.post(
            "/v1/auth/users",
            json={"email": email, "password": "password123", "display_name": "Op All Fail"},
            headers={"Authorization": ""},
        )
        assert res.status_code == 201, res.text
        headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

        db_url = os.environ["DATABASE_URL"].replace("+asyncpg", "").replace(
            "postgresql+asyncpg", "postgresql"
        )
        sync_engine = create_engine(db_url, pool_pre_ping=True)
        with Session(sync_engine) as session:
            user = session.execute(sync_select(User).where(User.email == email)).scalar_one()
            wallet = session.get(UserAcpWallet, user.id)
            wallet.address = f"acp1qpersonal{uuid4().hex[:26]}"
            session.commit()

        hot = client.get("/v1/wallet/acp/hot/balance", headers=headers)
        assert hot.status_code == 200, hot.text
        body = hot.json()
        design = GENESIS_SUPPLY_ACP
        assert body["probe_status"] == "unavailable"
        assert body["view_mode"] == "operator_hot"
        assert Decimal(body["primary_acp"]) == design
        assert Decimal(body["acp"]) == design
        assert Decimal(body["platform_ledger_acp"]) == Decimal("250")
        assert Decimal(body["withdrawable_now_acp"]) == Decimal("0")
        assert body["withdraw_source"] == "none"

        with Session(sync_engine) as session:
            user = session.execute(sync_select(User).where(User.email == email)).scalar_one()
            wallet = session.get(UserAcpWallet, user.id)
            wallet.address = f"acp1qcleanup{uuid4().hex[:28]}"
            session.commit()
        sync_engine.dispose()
    finally:
        monkeypatch.setenv("WELCOME_GRANT_ACP", "0")
        monkeypatch.setenv("ACP_CUSTODIAL_HOT_HOLDER_EMAILS", "dragon.cat.trx@gmail.com")
        get_settings.cache_clear()
        _free_custodial_hot_bindings()
