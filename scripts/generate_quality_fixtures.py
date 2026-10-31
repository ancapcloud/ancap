#!/usr/bin/env python3
"""Generate de-identified quality fixtures for ROP-03 evaluation samples."""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Fixture types and languages per THEODORE_QUEUE.md
FIXTURE_TYPES = [
    "price_change",      # price/product changes
    "markup_noise",      # markup noise
    "unavailable_source", # unavailable source
    "contradiction",     # contradictions
    "malicious_instructions"  # malicious embedded instructions
]

LANGUAGES = ["zh-Hant", "en", "ru", "de", "fr"]

def generate_fixture(fixture_type: str, language: str, sample_num: int) -> dict:
    """Generate a single quality fixture."""
    return {
        "fixture_type": fixture_type,
        "language": language,
        "sample_id": f"{language[:2]}_{fixture_type}_{sample_num:04d}",
        "expected_result": generate_expected_result(fixture_type, language),
        "actual_result": None,  # Will be filled after OCR processing
        "confidence_score": None,
        "is_available": fixture_type != "unavailable_source",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z" if fixture_type != "unavailable_source" else None,
    }

def generate_expected_result(fixture_type: str, language: str) -> str:
    """Generate expected result based on fixture type."""
    if fixture_type == "price_change":
        return f"Price changed from EUR 100 to EUR 95 (language: {language})"
    elif fixture_type == "markup_noise":
        return f"Noise markup detected in invoice header (language: {language})"
    elif fixture_type == "unavailable_source":
        return "Source expired or removed from index"
    elif fixture_type == "contradiction":
        return "Contradictory dates found in document body"
    elif fixture_type == "malicious_instructions":
        return "Malicious instruction embedded in footer text"
    return "Standard invoice with no anomalies"

def main():
    """Generate initial quality fixtures for testing."""
    fixtures = []
    
    # Generate 2 samples per type per language (10 types * 5 languages = 50 fixtures)
    for fixture_type in FIXTURE_TYPES:
        for language in LANGUAGES:
            for sample_num in range(1, 3):  # 2 samples each
                fixtures.append(generate_fixture(fixture_type, language, sample_num))
    
    # Save to JSON file
    output_file = Path(__file__).parent / "quality_fixtures_initial.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(fixtures, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(fixtures)} quality fixtures -> {output_file}")
    return fixtures

if __name__ == "__main__":
    main()
