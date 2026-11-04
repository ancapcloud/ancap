"""Tests for Research Operations onboarding template (ROP-05)."""

import json
import re
from pathlib import Path


def test_onboarding_template_exists():
    """Verify onboarding template file exists and is valid."""
    template_path = Path("docs/onboarding-template.md")
    assert template_path.exists(), "Onboarding template should exist"
    
    content = template_path.read_text()
    assert "Reusable Settings" in content
    assert "Source categories" in content
    assert "Packet template structure" in content


def test_onboarding_template_no_client_secrets():
    """Verify template doesn't contain previous client data."""
    template_path = Path("docs/onboarding-template.md")
    content = template_path.read_text()
    
    # Should not contain actual credentials or PII
    assert "password" not in content.lower()
    assert "api_key" not in content.lower()
    assert "secret" not in content.lower()
    assert "token" not in content.lower()


def test_onboarding_template_structure():
    """Verify template has required sections."""
    template_path = Path("docs/onboarding-template.md")
    content = template_path.read_text()
    
    # Check for key sections
    assert "Project configuration defaults" in content
    assert "Source categories" in content
    assert "Packet template structure" in content
    assert "Onboarding Checklist" in content
    assert "Client-specific customization notes" in content


def test_onboarding_template_json_example():
    """Verify JSON example in template is valid."""
    template_path = Path("docs/onboarding-template.md")
    content = template_path.read_text()
    
    # Check that JSON blocks exist (simple string check)
    assert '```json' in content, "Template should contain JSON code blocks"
    assert '"format":' in content, "JSON example should have format field"
    assert '"research":' in content, "JSON example should have research object"
    assert '"result":' in content, "JSON example should have result object"
    
    # Verify JSON is syntactically valid by checking balanced braces
    json_blocks = re.findall(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    assert len(json_blocks) >= 2, "Should have at least 2 JSON blocks"
    
    # Parse first JSON block (project config)
    first_block = json_blocks[0].strip()
    data1 = json.loads(first_block)
    assert "retention_days_default" in data1
    
    # Parse second JSON block (packet template)
    second_block = json_blocks[1].strip()
    data2 = json.loads(second_block)
    assert "format" in data2
    assert "research" in data2
    assert "result" in data2


def test_onboarding_template_constraints():
    """Verify template includes constraint warnings."""
    template_path = Path("docs/onboarding-template.md")
    content = template_path.read_text()
    
    # Check for important constraints
    assert "never include previous client documents" in content.lower()
    assert "credentials" in content.lower()
    assert "identifiers" in content.lower()
    assert "personal data" in content.lower()


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Run all tests
    from tests.unit.test_onboarding_template import (
        test_onboarding_template_exists,
        test_onboarding_template_no_client_secrets,
        test_onboarding_template_structure,
        test_onboarding_template_json_example,
        test_onboarding_template_constraints,
    )
    
    tests = [
        test_onboarding_template_exists,
        test_onboarding_template_no_client_secrets,
        test_onboarding_template_structure,
        test_onboarding_template_json_example,
        test_onboarding_template_constraints,
    ]
    
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            raise
