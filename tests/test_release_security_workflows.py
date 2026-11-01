from pathlib import Path


BACKEND_CI_PATH = Path(".github/workflows/backend-ci.yml")
RELEASE_WORKFLOW_PATH = Path(".github/workflows/release.yml")
RELEASE_PROCESS_PATH = Path(".github/RELEASE_PROCESS.md")
SECRET_HYGIENE_WORKFLOW_PATH = Path(".github/workflows/secret-hygiene.yml")
TESTS_CONFTEST_PATH = Path("tests/conftest.py")


def test_backend_ci_keeps_honest_bandit_and_docker_build_guards():
    workflow_text = BACKEND_CI_PATH.read_text(encoding="utf-8")

    assert 'GH_TOKEN: ${{ github.token }}' in workflow_text
    assert 'python -m bandit -r app/ -ll -f txt 2>&1 | tee bandit-report.txt' in workflow_text
    assert 'set -o pipefail' in workflow_text
    assert 'docker build -t ancap:build-check .' in workflow_text
    assert '.githooks/**' in workflow_text
    assert 'scripts/check_secret_hygiene.py' in workflow_text
    assert 'scripts/install_git_hooks.py' in workflow_text
    assert 'scripts/render_secret_rotation_evidence.py' in workflow_text
    assert 'scripts/generate_ancap_docs_live_followup.py' in workflow_text
    assert 'scripts/generate_secret_hygiene_evidence.py' in workflow_text
    assert 'tests/test_bootstrap_ancap_docs_repo.py' in workflow_text
    assert 'tests/test_generate_ancap_docs_live_followup.py' in workflow_text
    assert 'pytest tests/test_export_ancap_docs.py tests/test_public_trust_docs.py tests/test_status_summary.py tests/test_ancap_docs_split_ci_guard.py tests/test_bootstrap_ancap_docs_repo.py tests/test_generate_ancap_docs_live_followup.py -q' in workflow_text
    assert '.githooks/**' in workflow_text
    assert '.github/workflows/secret-hygiene.yml' in workflow_text
    assert '.github/workflows/release.yml' in workflow_text
    assert '--target deps' not in workflow_text
    assert '|| true' not in workflow_text


def test_release_workflow_runs_secret_hygiene_gate_before_release_checks():
    workflow_text = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert 'GH_TOKEN: ${{ github.token }}' in workflow_text
    assert '      - name: Checkout' in workflow_text
    assert '          fetch-depth: 0' in workflow_text
    assert '      - name: Secret hygiene evidence bundle' in workflow_text
    assert '        id: secret_hygiene_bundle' in workflow_text
    assert '        continue-on-error: true' in workflow_text
    assert '        run: python scripts/generate_secret_hygiene_evidence.py --recent-history 20' in workflow_text
    assert '      - name: Upload secret hygiene report' in workflow_text
    assert '        uses: actions/upload-artifact@v4' in workflow_text
    assert '          name: secret-hygiene-report' in workflow_text
    assert '          path: tmp/secret-hygiene-report.json' in workflow_text
    assert '          if-no-files-found: warn' in workflow_text
    assert '      - name: Upload secret hygiene history report' in workflow_text
    assert '          name: secret-hygiene-history-report' in workflow_text
    assert '          path: tmp/secret-hygiene-history-report.json' in workflow_text
    assert '      - name: Upload secret rotation evidence' in workflow_text
    assert '          name: secret-rotation-evidence' in workflow_text
    assert '          path: tmp/secret-rotation-evidence.md' in workflow_text
    assert '      - name: Secret hygiene regression' in workflow_text
    assert '        id: secret_hygiene_regression' in workflow_text
    assert '        continue-on-error: true' in workflow_text
    assert '        run: pytest tests/test_secret_hygiene.py tests/test_release_security_workflows.py -q' in workflow_text
    assert '      - name: Enforce secret hygiene gate' in workflow_text
    assert '        if: always()' in workflow_text
    assert '          BUNDLE_OUTCOME: ${{ steps.secret_hygiene_bundle.outcome }}' in workflow_text
    assert '          REGRESSION_OUTCOME: ${{ steps.secret_hygiene_regression.outcome }}' in workflow_text
    assert '            echo "Secret hygiene gate failed (bundle=$BUNDLE_OUTCOME, regression=$REGRESSION_OUTCOME)." >&2' in workflow_text
    assert workflow_text.index('      - name: Secret hygiene evidence bundle') < workflow_text.index('      - name: Enforce secret hygiene gate')
    assert workflow_text.index('      - name: Upload secret hygiene report') < workflow_text.index('      - name: Enforce secret hygiene gate')
    assert workflow_text.index('      - name: Upload secret hygiene history report') < workflow_text.index('      - name: Enforce secret hygiene gate')
    assert workflow_text.index('      - name: Upload secret rotation evidence') < workflow_text.index('      - name: Enforce secret hygiene gate')
    assert workflow_text.index('      - name: Secret hygiene regression') < workflow_text.index('      - name: Enforce secret hygiene gate')
    assert workflow_text.index('      - name: Secret hygiene evidence bundle') < workflow_text.index('      - name: Run Alembic migrations')
    assert workflow_text.index('      - name: Upload secret hygiene report') < workflow_text.index('      - name: Run Alembic migrations')
    assert workflow_text.index('      - name: Upload secret hygiene history report') < workflow_text.index('      - name: Run Alembic migrations')
    assert workflow_text.index('      - name: Upload secret rotation evidence') < workflow_text.index('      - name: Run Alembic migrations')
    assert workflow_text.index('      - name: Secret hygiene regression') < workflow_text.index('      - name: Run Alembic migrations')
    assert workflow_text.index('      - name: Enforce secret hygiene gate') < workflow_text.index('      - name: Run Alembic migrations')


def test_secret_hygiene_workflow_runs_on_push_pull_request_and_history_sweeps():
    workflow_text = SECRET_HYGIENE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert 'name: "Secret Hygiene"' in workflow_text
    assert 'push:' in workflow_text
    assert 'pull_request:' in workflow_text
    assert 'workflow_dispatch:' in workflow_text
    assert 'history_range:' in workflow_text
    assert 'default: ""' in workflow_text
    assert 'schedule:' in workflow_text
    assert '- cron: "17 4 * * 1"' in workflow_text
    assert 'branches: ["master"]' in workflow_text
    assert 'group: secret-hygiene-${{ github.ref }}' in workflow_text
    assert 'uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5' in workflow_text
    assert 'uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6' in workflow_text
    assert 'python-version: "3.11"' in workflow_text
    assert 'run: python scripts/check_secret_hygiene.py --format json --output tmp/secret-hygiene-report.json' in workflow_text
    assert '      - name: Upload secret hygiene report' in workflow_text
    assert '        uses: actions/upload-artifact@v4' in workflow_text
    assert '          name: secret-hygiene-report' in workflow_text
    assert '          path: tmp/secret-hygiene-report.json' in workflow_text
    assert '          if-no-files-found: warn' in workflow_text
    assert '  scan-recent-history:' in workflow_text
    assert "if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'" not in workflow_text
    assert 'fetch-depth: 0' in workflow_text
    assert '      - name: Resolve push history range' in workflow_text
    assert '          BEFORE_SHA: ${{ github.event.before }}' in workflow_text
    assert '          AFTER_SHA: ${{ github.sha }}' in workflow_text
    assert '            history_range="$BEFORE_SHA..$AFTER_SHA"' in workflow_text
    assert '          if [[ -n "$history_range" ]] && git rev-list --reverse "$history_range" >/dev/null 2>&1; then' in workflow_text
    assert '            echo "SECRET_HISTORY_RANGE=$history_range" >> "$GITHUB_ENV"' in workflow_text
    assert '          else' in workflow_text
    assert '            echo "SECRET_RECENT_HISTORY_COUNT=20" >> "$GITHUB_ENV"' in workflow_text
    assert '          fi' in workflow_text
    assert '      - name: Resolve pull-request history range' in workflow_text
    assert '          BASE_SHA: ${{ github.event.pull_request.base.sha }}' in workflow_text
    assert '          HEAD_SHA: ${{ github.event.pull_request.head.sha }}' in workflow_text
    assert '            history_range="$BASE_SHA..$HEAD_SHA"' in workflow_text
    assert '      - name: Resolve scheduled history range' in workflow_text
    assert '        run: echo "SECRET_RECENT_HISTORY_COUNT=20" >> "$GITHUB_ENV"' in workflow_text
    assert '      - name: Resolve manual history range' in workflow_text
    assert '          INPUT_HISTORY_RANGE: ${{ github.event.inputs.history_range }}' in workflow_text
    assert '          history_range="${INPUT_HISTORY_RANGE:-}"' in workflow_text
    assert '          if [[ -z "${history_range//[[:space:]]/}" ]]; then' in workflow_text
    assert '            echo "SECRET_RECENT_HISTORY_COUNT=20" >> "$GITHUB_ENV"' in workflow_text
    assert '          else' in workflow_text
    assert '            echo "SECRET_HISTORY_RANGE=$history_range" >> "$GITHUB_ENV"' in workflow_text
    assert '          fi' in workflow_text
    assert '          if [[ -n "${SECRET_HISTORY_RANGE:-}" ]]; then' in workflow_text
    assert '            python scripts/check_secret_hygiene.py --history-range "$SECRET_HISTORY_RANGE" --format json --output tmp/secret-hygiene-history-report.json' in workflow_text
    assert '          else' in workflow_text
    assert '            python scripts/check_secret_hygiene.py --recent-history "${SECRET_RECENT_HISTORY_COUNT:-20}" --format json --output tmp/secret-hygiene-history-report.json' in workflow_text
    assert '          fi' in workflow_text
    assert '      - name: Upload secret hygiene history report' in workflow_text
    assert '          name: secret-hygiene-history-report' in workflow_text
    assert '          path: tmp/secret-hygiene-history-report.json' in workflow_text
    assert '          if-no-files-found: warn' in workflow_text
    assert '  secret-hygiene-regression:' in workflow_text
    assert '          pip install .[dev]' in workflow_text
    assert '      - name: Secret hygiene regression' in workflow_text
    assert '        run: pytest tests/test_secret_hygiene.py tests/test_release_security_workflows.py -q' in workflow_text
    assert '  render-rotation-evidence:' in workflow_text
    assert '    if: always()' in workflow_text
    assert '    needs:' in workflow_text
    assert '      - scan-tracked-files' in workflow_text
    assert '      - scan-recent-history' in workflow_text
    assert '      - secret-hygiene-regression' in workflow_text
    assert '      - name: Download tracked secret hygiene report' in workflow_text
    assert '        continue-on-error: true' in workflow_text
    assert '      - name: Download history secret hygiene report' in workflow_text
    assert '        uses: actions/download-artifact@v4' in workflow_text
    assert '          name: secret-hygiene-report' in workflow_text
    assert '          name: secret-hygiene-history-report' in workflow_text
    assert '      - name: Check secret hygiene artifact availability' in workflow_text
    assert '        id: secret_hygiene_artifacts' in workflow_text
    assert '          tracked_path="tmp/tracked-report/secret-hygiene-report.json"' in workflow_text
    assert '          history_path="tmp/history-report/secret-hygiene-history-report.json"' in workflow_text
    assert '          echo "tracked_exists=$tracked_exists" >> "$GITHUB_OUTPUT"' in workflow_text
    assert '          echo "history_exists=$history_exists" >> "$GITHUB_OUTPUT"' in workflow_text
    assert '          echo "Skipping secret rotation evidence render because one or more JSON artifacts are unavailable." >&2' in workflow_text
    assert '      - name: Render secret rotation evidence' in workflow_text
    assert "        if: steps.secret_hygiene_artifacts.outputs.tracked_exists == 'true' && steps.secret_hygiene_artifacts.outputs.history_exists == 'true'" in workflow_text
    assert '        run: python scripts/render_secret_rotation_evidence.py --tracked-report tmp/tracked-report/secret-hygiene-report.json --history-report tmp/history-report/secret-hygiene-history-report.json --output tmp/secret-rotation-evidence.md' in workflow_text
    assert '      - name: Upload secret rotation evidence' in workflow_text
    assert '          name: secret-rotation-evidence' in workflow_text
    assert '          path: tmp/secret-rotation-evidence.md' in workflow_text
    assert '          if-no-files-found: warn' in workflow_text


def test_release_process_doc_uses_secret_hygiene_gate():
    release_process = RELEASE_PROCESS_PATH.read_text(encoding="utf-8")

    assert 'python scripts/check_secret_hygiene.py --staged' in release_process
    assert 'python scripts/check_secret_hygiene.py --history-range HEAD~20..HEAD' in release_process
    assert 'python scripts/check_secret_hygiene.py --recent-history 20' in release_process
    assert 'python scripts/check_secret_hygiene.py --pending-push' in release_process
    assert 'py -3 scripts/check_secret_hygiene.py --staged' in release_process
    assert 'py -3 scripts/check_secret_hygiene.py --history-range HEAD~20..HEAD' in release_process
    assert 'py -3 scripts/check_secret_hygiene.py --recent-history 20' in release_process
    assert 'py -3 scripts/check_secret_hygiene.py --pending-push' in release_process
    assert 'python scripts/check_secret_hygiene.py --format json --output tmp/secret-hygiene-report.json' in release_process
    assert 'py -3 scripts/check_secret_hygiene.py --format json --output tmp/secret-hygiene-report.json' in release_process
    assert 'py -3 scripts/check_secret_hygiene.py --history-range HEAD~20..HEAD --format json --output tmp/secret-hygiene-history-report.json' in release_process
    assert 'py -3 scripts/check_secret_hygiene.py --recent-history 20 --format json --output tmp/secret-hygiene-history-report.json' in release_process
    assert 'python scripts/render_secret_rotation_evidence.py --tracked-report tmp/secret-hygiene-report.json --history-report tmp/secret-hygiene-history-report.json --output tmp/secret-rotation-evidence.md' in release_process
    assert 'py -3 scripts/render_secret_rotation_evidence.py --tracked-report tmp/secret-hygiene-report.json --history-report tmp/secret-hygiene-history-report.json --output tmp/secret-rotation-evidence.md' in release_process
    assert 'py -3 scripts/render_secret_rotation_evidence.py --tracked-report tmp/secret-hygiene-report.json --secondary-report tmp/secret-hygiene-pending-push-report.json --output tmp/secret-rotation-evidence.md' in release_process
    assert 'python scripts/generate_secret_hygiene_evidence.py' in release_process
    assert 'py -3 scripts/generate_secret_hygiene_evidence.py' in release_process
    assert 'python scripts/generate_secret_hygiene_evidence.py --recent-history 20' in release_process
    assert 'py -3 scripts/generate_secret_hygiene_evidence.py --recent-history 20' in release_process
    assert 'python scripts/install_git_hooks.py --dry-run' in release_process
    assert 'py -3 scripts/install_git_hooks.py --dry-run' in release_process
    assert 'python scripts/install_git_hooks.py --check' in release_process
    assert 'py -3 scripts/install_git_hooks.py --check' in release_process
    assert 'pytest tests/test_secret_hygiene.py tests/test_release_security_workflows.py -q' in release_process
    assert '# 2. Secret hygiene gates pass before release' in release_process


def test_db_runtime_reset_only_touches_postgres_for_db_backed_fixtures():
    conftest_text = TESTS_CONFTEST_PATH.read_text(encoding="utf-8")

    assert 'DB_STATE_RESET_FIXTURES = {"client", "client_unauth", "db_cursor", "base_vertical_id"}' in conftest_text
    assert 'def reset_test_runtime_state(request):' in conftest_text
    assert 'if DB_STATE_RESET_FIXTURES.intersection(request.fixturenames):' in conftest_text
    assert 'text-only/document/workflow tests should stay' in conftest_text
