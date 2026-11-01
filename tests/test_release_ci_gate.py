from scripts.wait_release_ci import ci_state, expected_core, matches_patterns, WORKFLOWS
from pathlib import Path
import shutil
import yaml

SHA = "a" * 40


def run(name, conclusion="success", status="completed", sha=SHA, event="push"):
    return dict(name=name, conclusion=conclusion, status=status, head_sha=sha, event=event)


def test_runtime_changes_require_both_backend_and_frontend():
    assert expected_core(["app/services/catalog_eur_prices.json"]) == {"Backend CI", "Frontend CI", "CodeQL", "Secret Hygiene"}
    assert expected_core(["frontend-app/src/app/page.tsx"]) == {"Frontend CI", "CodeQL", "Secret Hygiene"}
    assert expected_core(["Dockerfile"]) == {"Backend CI", "Frontend CI", "Secret Hygiene"}
    assert expected_core(["docker-compose.yml"]) == {"Frontend CI", "Secret Hygiene"}
    assert expected_core(["ACP-crypto/Cargo.lock"]) == {"Crypto CI", "Secret Hygiene"}
    assert expected_core(["docs/report.md"]) == {"Backend CI", "Docs CI", "Secret Hygiene"}


def test_non_backend_changes_do_not_require_a_workflow_that_will_not_run():
    assert expected_core(["PRODUCTION_ROADMAP.md"]) == {"Secret Hygiene"}
    assert expected_core([".github/workflows/codeql.yml"]) == {"CodeQL", "Secret Hygiene"}


def test_requirements_follow_the_checked_out_workflow_configuration(tmp_path):
    for filename in WORKFLOWS.values():
        shutil.copyfile(Path(".github/workflows") / filename, tmp_path / filename)
    backend_path = tmp_path / "backend-ci.yml"
    document = yaml.safe_load(backend_path.read_text(encoding="utf-8"))
    document.get("on", document.get(True))["push"]["paths"].append("PRODUCTION_ROADMAP.md")
    backend_path.write_text(yaml.safe_dump(document), encoding="utf-8")
    assert expected_core(["PRODUCTION_ROADMAP.md"], tmp_path) == {"Backend CI", "Secret Hygiene"}


def test_delayed_security_or_docs_workflow_cannot_be_ignored():
    for path in ["app/main.py", "docs/report.md"]:
        required = expected_core([path])
        for missing in required:
            state = ci_state([run(name) for name in required - {missing}], SHA, required)
            assert not state["ready"] and state["missing"] == [missing]


def test_path_filters_handle_recursive_wildcards_and_ordered_exclusions():
    assert matches_patterns("app/deep/file.py", ["app/**"])
    assert not matches_patterns("app/deep/file.py", ["app/*.py"])
    assert matches_patterns("README.md", ["**/*.md"])
    patterns = ["**", "!docs/**", "docs/release/**"]
    assert not matches_patterns("docs/internal/note.md", patterns)
    assert matches_patterns("docs/release/note.md", patterns)


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
