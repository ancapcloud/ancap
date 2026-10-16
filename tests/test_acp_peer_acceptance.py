import copy
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "check_acp_peers", Path(__file__).resolve().parents[1] / "scripts/check_acp_peers.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def peer():
    return {"height": 18, "tip": "ab6bdd19", "supply": {
        "height": 18, "initialized": True, "supply_invariant_ok": True,
        "issued_supply_units": "21000000000000000", "max_supply_units": "21000000000000000",
    }}


def test_three_matching_peers_pass():
    assert module.peers_agree([peer(), peer(), peer()])


@pytest.mark.parametrize("change", [
    {"error": "connection refused"}, {"height": 17}, {"tip": "fork"},
    {"supply": {**peer()["supply"], "supply_invariant_ok": False}},
    {"supply": {**peer()["supply"], "issued_supply_units": "21000000000000001"}},
    {"supply": {**peer()["supply"], "height": 17}},
])
def test_unhealthy_or_divergent_peer_fails(change):
    changed = copy.deepcopy(peer())
    changed.update(change)
    assert not module.peers_agree([peer(), changed, peer()])
