import importlib.util
from pathlib import Path


def test_hardening_preserves_auth_but_removes_tool_escape_paths():
    path = Path(__file__).resolve().parents[2] / "scripts/harden_openclaw.py"
    spec = importlib.util.spec_from_file_location("harden_openclaw", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = {"gateway": {"auth": {"token": "fixture-only"}}, "tools": {"profile": "full"},
                "agents": {"entries": {"theodore": {"sandbox": {"mode": "off"}, "tools": {"profile": "full"}}}}}
    result = module.harden(original, "sha256:" + "a" * 64)
    assert result["gateway"] == original["gateway"]
    assert original["tools"]["profile"] == "full"
    sandbox = result["agents"]["defaults"]["sandbox"]
    assert sandbox["mode"] == "all" and sandbox["workspaceAccess"] == "none"
    assert sandbox["docker"]["network"] == "none"
    assert sandbox["docker"]["binds"] == [] and sandbox["docker"]["env"] == {}
    assert result["tools"]["elevated"] == {"enabled": False}
    assert result["tools"]["exec"]["host"] == "sandbox"
    assert "gateway" in result["tools"]["deny"]
    assert result["agents"]["entries"]["theodore"]["sandbox"] == sandbox
