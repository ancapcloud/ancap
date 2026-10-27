"""A successful pricing check must prove values as well as key parity."""
import json
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_pricing_sync.py"


@pytest.mark.parametrize(
    "backend,frontend,expected,detail",
    [
        ({"sku": "9"}, {"sku": "9"}, 0, "1 identical price entries"),
        ({"sku": "9"}, {"sku": "99"}, 1, "Different prices: sku"),
        ({"sku": "9"}, {"other": "9"}, 1, "Missing frontend keys: sku"),
        ({"sku": "9"}, {"sku": "9", "extra": "1"}, 1, "Extra frontend keys: extra"),
        ([], [], 1, "JSON objects"),
        ({}, {}, 1, "must not be empty"),
    ],
)
def test_catalogue_parity(tmp_path, backend, frontend, expected, detail):
    left, right = tmp_path / "backend.json", tmp_path / "frontend.json"
    left.write_text(json.dumps(backend), encoding="utf-8")
    right.write_text(json.dumps(frontend), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--backend", str(left), "--frontend", str(right)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == expected
    assert detail in result.stdout + result.stderr


def test_defaults_work_outside_project(tmp_path):
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=tmp_path, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "identical price entries" in result.stdout


def test_invalid_json_fails_closed(tmp_path):
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--backend", str(invalid)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "Cannot verify catalogue parity" in result.stderr
