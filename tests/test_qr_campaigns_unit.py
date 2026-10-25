"""Isolated QR tests: pytest --noconftest tests/test_qr_campaigns_unit.py."""
from contextlib import asynccontextmanager
from datetime import date
from concurrent.futures import ThreadPoolExecutor
import pytest
pytest.importorskip("aiosqlite")
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.models import QrDailyCount
from app.db.session import get_db
from app.api.deps import require_platform_admin
from app.api.routers.qr_campaigns import router
from app.services import qr_campaigns as svc

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(svc, "campaign_day", lambda: date(2026, 10, 25))
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'qr.db'}")
    maker = async_sessionmaker(engine, expire_on_commit=False)
    @asynccontextmanager
    async def lifespan(app):
        async with engine.begin() as conn:
            await conn.run_sync(QrDailyCount.__table__.create)
        yield
        await engine.dispose()
    app = FastAPI(lifespan=lifespan)
    app.include_router(router, prefix="/v1")
    async def db():
        async with maker() as session:
            yield session
            await session.commit()
    app.dependency_overrides[get_db] = db
    with TestClient(app) as c:
        yield c, app

def allow_admin(app):
    app.dependency_overrides[require_platform_admin] = lambda: "admin"

def test_repeat_visits_persist_and_stats_are_private(client):
    c, app = client
    for _ in range(2):
        res = c.get("/v1/qr/street", follow_redirects=False)
        assert res.status_code == 302
        assert res.headers["location"] == svc.DESTINATION
        assert "no-store" in res.headers["cache-control"]
        assert "set-cookie" not in res.headers
    assert c.get("/v1/qr/street/stats").status_code in (401, 403)
    allow_admin(app)
    stats = c.get("/v1/qr/street/stats?days=3")
    assert stats.status_code == 200
    assert stats.json()["total"] == 2
    assert stats.json()["today"] == 2
    assert [x["visits"] for x in stats.json()["days"]] == [0, 0, 2]
    assert c.get("/v1/qr/street/stats?days=91").status_code == 422

def test_head_prefetch_and_bots_do_not_count(client):
    c, app = client
    assert c.head("/v1/qr/street", follow_redirects=False).status_code == 302
    for headers in [{"Sec-Purpose":"prefetch"}, {"User-Agent":"Googlebot"}, {"User-Agent":"WhatsApp/2"}]:
        assert c.get("/v1/qr/street", headers=headers, follow_redirects=False).status_code == 302
    allow_admin(app)
    assert c.get("/v1/qr/street/stats").json()["total"] == 0

def test_counter_failure_still_redirects(client, monkeypatch):
    c, app = client
    async def fail(session):
        raise RuntimeError("unavailable")
    monkeypatch.setattr(svc, "record_visit", fail)
    assert c.get("/v1/qr/street", follow_redirects=False).status_code == 302

def test_concurrent_increments_are_not_lost(client):
    c, app = client
    def visit(_):
        return c.get("/v1/qr/street", follow_redirects=False).status_code
    with ThreadPoolExecutor(max_workers=5) as pool:
        assert list(pool.map(visit, range(20))) == [302]*20
    allow_admin(app)
    assert c.get("/v1/qr/street/stats").json()["total"] == 20
