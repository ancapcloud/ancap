import pytest

from app.api.routers.mobile_acp import _infer_recovery_locator_network
from urllib.parse import urlparse


@pytest.mark.parametrize("host,expected", [
    ("bscscan.com", "bsc"), ("testnet.bscscan.com", "bsc"),
    ("ancap.cloud", "acp"), ("acp1.ancap.cloud:443", "acp"),
    ("bscscan.com.evil.example", None), ("fakebscscan.com", None),
    ("ancap.cloud.evil.example", None), ("ancap.cloud@evil.example", None),
])
def test_recovery_network_uses_hostname_boundary(host, expected):
    assert _infer_recovery_locator_network(urlparse(f"https://{host}/acp/tx/fixture")) == expected
