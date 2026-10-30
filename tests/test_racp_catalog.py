"""An issued receipt without a settlement service must not enable the BSC rail."""
from app.services.exchange_office import build_assets, build_pairs


def test_racp_is_discoverable_but_not_tradeable(monkeypatch):
    monkeypatch.setenv("RACP_REDEEM_ENABLED", "false")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        assets = build_assets()
        token = next(a for a in assets if a.id == "racp_robinhood")
        assert token.availability == "beta"
        assert token.direction == "none"
        assert token.metadata["chain_id"] == 4663
        assert token.metadata["contract_address"] == "0xD53f91A63f95beAc61Ec8417c40C5e620FE3a911"
        assert token.metadata["initial_reserve_confirmed"] is True
        assert token.metadata["redemption_available"] is False
        assert token.metadata["reserve_monitoring"] == "not_implemented"
        assert token.metadata["source_verification"] == "exact_match"
        assert token.metadata["website"] == "https://ancap.cloud/tokens/racp"
        assert not any(
            p.from_asset == token.id or p.to_asset == token.id
            for p in build_pairs(assets)
        )
    finally:
        get_settings.cache_clear()


def test_racp_redeem_flag_flips_catalog_metadata(monkeypatch):
    monkeypatch.setenv("RACP_REDEEM_ENABLED", "true")
    monkeypatch.setenv("RACP_REDEEM_PAUSED", "false")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        assets = build_assets()
        token = next(a for a in assets if a.id == "racp_robinhood")
        assert token.metadata["redemption_available"] is True
        assert token.metadata["reserve_monitoring"] == "job_tick"
        assert token.direction == "into_acp"
        assert token.availability == "live"
        # Still no exchange-office quote pairs for rACP.
        assert not any(
            p.from_asset == token.id or p.to_asset == token.id
            for p in build_pairs(assets)
        )
    finally:
        monkeypatch.setenv("RACP_REDEEM_ENABLED", "false")
        get_settings.cache_clear()
