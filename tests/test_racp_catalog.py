"""An unfunded receipt must never enable a spend or existing BSC settlement rail."""
from app.services.exchange_office import build_assets, build_pairs


def test_racp_is_discoverable_but_not_tradeable():
    assets = build_assets()
    token = next(a for a in assets if a.id == "racp_robinhood")
    assert token.availability == "planned"
    assert token.direction == "none"
    assert token.metadata["chain_id"] == 4663
    assert token.metadata["contract_address"] == "0xD53f91A63f95beAc61Ec8417c40C5e620FE3a911"
    assert token.metadata["reserve_verified"] is False
    assert not any(
        p.from_asset == token.id or p.to_asset == token.id
        for p in build_pairs(assets)
    )
