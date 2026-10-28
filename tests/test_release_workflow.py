import re
from pathlib import Path


WORKFLOW_PATH = Path(".github/workflows/release.yml")


def test_release_workflow_runs_on_tags_and_drafts_github_release():
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert 'name: "Release"' in workflow_text
    assert 'push:' in workflow_text
    assert 'tags:' in workflow_text
    assert '      - "v*"' in workflow_text
    assert 'backend-release-check:' in workflow_text
    assert 'frontend-release-check:' in workflow_text
    assert 'draft-release:' in workflow_text
    assert 'needs:' in workflow_text
    assert re.search(r'uses: softprops/action-gh-release@[0-9a-f]{40}\b', workflow_text)
    assert 'generate_release_notes: true' in workflow_text
    assert 'draft: true' in workflow_text
    assert 'docker build -t ancap:release-check .' in workflow_text
    assert 'pytest -q' in workflow_text
    assert 'npm test -- --run' in workflow_text
    assert 'npm run lint' in workflow_text
    assert 'npm run build' in workflow_text
