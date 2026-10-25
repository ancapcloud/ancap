"""PostgreSQL-backed QR counter and real admin authorization regression."""
from concurrent.futures import ThreadPoolExecutor
from app.config import get_settings


def test_qr_counter_persists_concurrent_visits_and_protects_stats(client, monkeypatch):
    me = client.get("/v1/users/me")
    assert me.status_code == 200, me.text
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", me.json()["id"])
    get_settings.cache_clear()
    try:
        stats_url = "/v1/qr/street/stats?days=3"
        assert client.get(stats_url, headers={"Authorization": ""}).status_code == 401
        before = client.get(stats_url)
        assert before.status_code == 200, before.text
        assert "no-store" in before.headers["cache-control"]
        total = before.json()["total"]
        # HEAD and speculative fetches must never change the counter.
        assert client.head("/v1/qr/street", follow_redirects=False).status_code == 302
        for headers in [{"Sec-Purpose": "prefetch"}, {"User-Agent": "Googlebot"}]:
            assert client.get("/v1/qr/street", headers=headers, follow_redirects=False).status_code == 302
        assert client.get(stats_url).json()["total"] == total
        def visit(_):
            res = client.get("/v1/qr/street", follow_redirects=False)
            assert res.status_code == 302
            assert res.headers["location"] == "https://ancap.cloud/?utm_source=qr&utm_medium=sticker&utm_campaign=street"
            assert "no-store" in res.headers["cache-control"]
        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(visit, range(20)))
        after = client.get(stats_url).json()
        assert after["total"] == total + 20
        assert after["today"] == before.json()["today"] + 20
        assert len(after["days"]) == 3
        assert after["timezone"] == "Europe/Berlin"
        assert client.get("/v1/qr/street/stats?days=91").status_code == 422
        # An ordinary authenticated user must not see operator statistics.
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "00000000-0000-0000-0000-000000000001")
        monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "")
        get_settings.cache_clear()
        assert client.get(stats_url).status_code == 403
    finally:
        get_settings.cache_clear()
