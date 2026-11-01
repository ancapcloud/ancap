from scripts.wait_release_ci import ci_state, expected_core
from pathlib import Path

SHA = "a" * 40


def run(name, conclusion="success", status="completed", sha=SHA, event="push"):
    return dict(name=name, conclusion=conclusion, status=status, head_sha=sha, event=event)


def test_runtime_changes_require_both_backend_and_frontend():
    assert expected_core(["app/services/catalog_eur_prices.json"]) == {"Backend CI", "Frontend CI"}
    assert expected_core(["frontend-app/src/app/page.tsx"]) == {"Frontend CI"}
    assert expected_core(["Dockerfile"]) == {"Backend CI", "Frontend CI"}
    assert expected_core(["docker-compose.yml"]) == {"Frontend CI"}
    assert expected_core(["ACP-crypto/Cargo.lock"]) == {"Crypto CI"}
    assert expected_core(["docs/report.md"]) == {"Backend CI"}


def test_matching_green_checks_allow_release():
    state = ci_state([run("Backend CI"),run("Frontend CI"),run("Secret Hygiene")],SHA,{"Backend CI","Frontend CI"})
    assert state["ready"]


def test_old_or_pr_checks_cannot_authorize_push_deployment():
    state = ci_state([run("Backend CI",sha="b"*40),run("Frontend CI",event="pull_request")],SHA,{"Backend CI","Frontend CI"})
    assert not state["ready"] and len(state["missing"]) == 2


def test_failed_cancelled_or_skipped_ci_blocks_release():
    for conclusion in ["failure","cancelled","timed_out","skipped"]:
        state = ci_state([run("Backend CI",conclusion)],SHA,{"Backend CI"})
        assert not state["ready"] and state["failed"]


def test_queued_and_missing_workflows_keep_gate_closed():
    state = ci_state([run("Backend CI",None,"queued")],SHA,{"Backend CI","Frontend CI"})
    assert not state["ready"] and state["pending"] == ["Backend CI"]
    assert state["missing"] == ["Frontend CI"]


def test_only_latest_workflow_run_counts():
    assert ci_state([run("Backend CI"),run("Backend CI","failure")],SHA,{"Backend CI"})["ready"]


def test_deployment_checks_ci_before_exposing_ssh_secrets():
    text = Path('.github/workflows/deploy-ancap-cloud.yml').read_text(encoding='utf-8')
    assert text.index('Wait for matching green CI') < text.index('Validate deploy secrets') < text.index('Deploy over SSH')
    assert 'actions: read' in text
    backend = Path('.github/workflows/backend-ci.yml').read_text(encoding='utf-8')
    assert backend.count('scripts/wait_release_ci.py') == 2
