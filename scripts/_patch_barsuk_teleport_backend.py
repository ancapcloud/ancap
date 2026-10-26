# -*- coding: utf-8 -*-
"""Patch backend for Barsuk quantum pen + Teleport earphones medevac literacy SKUs."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch_schemas() -> None:
    path = ROOT / "app" / "schemas" / "aeterna.py"
    t = path.read_text(encoding="utf-8")
    if "barsuk_quantum_pen_brief" in t:
        print("schemas already patched")
        return
    t = t.replace(
        '    pulmopure_subscription = "pulmopure_subscription"\n',
        '    pulmopure_subscription = "pulmopure_subscription"\n'
        '    barsuk_quantum_pen_brief = "barsuk_quantum_pen_brief"\n'
        '    teleport_earphones_brief = "teleport_earphones_brief"\n',
        1,
    )
    note = '''    barsuk_note: str = (
        "Project Barsuk / quantum-pen rail is a licensed secure-comms partner brief for conceptual "
        "pen-form cryptography, sensor, and smart-ink literacy. Infographics are fiction / architecture "
        "literacy — not a Parker product, not a CE/FDA device, not a military weapon, and not unbreakable "
        "crypto sold by ANCAP."
    )
    teleport_earphones_note: str = (
        "AIRPODS T-2026 / teleport-earphones rail is a licensed partner brief for fictional medical-evacuation "
        "and quantum-comms literacy. Infographics are sci-fi architecture — not an Apple product, not a real "
        "teleporter, not a military weapon system, and not a guaranteed evacuation outcome."
    )
'''
    # insert before end of AeternaStatusPublic class - after pulmopure_note block
    marker = '        "ANCAP, not ozone therapy, not medical-gas compounding, and not a guaranteed tar-clearance or "\n        "\'clean lungs\' outcome."\n    )\n'
    # find pulmopure_note closing more reliably
    idx = t.rfind("pulmopure_note:")
    if idx < 0:
        raise SystemExit("pulmopure_note missing")
    # find end of that field (next class or blank after closing paren)
    end = t.find("\n\n\nclass ", idx)
    if end < 0:
        end = t.find("\nclass Aeterna", idx + 20)
    # Actually AeternaStatusPublic ends and next may be different - look for closing of last note
    close = t.find("\n)", idx)
    # better: after the pulmopure_note field's closing paren that ends with clean lungs
    needle = 'not a guaranteed tar-clearance or "\n        "\'clean lungs\' outcome."\n    )'
    alt = "not a guaranteed tar-clearance or '\n        \"'clean lungs' outcome.\"\n    )"
    if needle in t:
        t = t.replace(needle, needle + "\n" + note, 1)
    else:
        # try simpler
        simple = '"clean lungs" outcome."\n    )\n'
        if simple not in t:
            # read pulmopure block
            raise SystemExit("cannot find pulmopure note end")
        t = t.replace(simple, simple + note, 1)
    path.write_text(t, encoding="utf-8")
    print("patched schemas")


def patch_aeterna_service() -> None:
    path = ROOT / "app" / "services" / "aeterna.py"
    t = path.read_text(encoding="utf-8")
    if "BARSUK_SLUG" in t:
        print("aeterna service already patched")
        return

    t = t.replace(
        '    "aeterna-pulmopure-subscription",\n]',
        '    "aeterna-pulmopure-subscription",\n'
        '    "aeterna-barsuk-quantum-pen",\n'
        '    "aeterna-teleport-earphones",\n]',
        1,
    )
    t = t.replace(
        'PULMOPURE_ANNUAL_ACP = Decimal("128000")\n',
        'PULMOPURE_ANNUAL_ACP = Decimal("128000")\n'
        'BARSUK_SLUG = "aeterna-barsuk-quantum-pen"\n'
        'BARSUK_PRICE_ACP = Decimal("36000")\n'
        'TELEPORT_SLUG = "aeterna-teleport-earphones"\n'
        'TELEPORT_PRICE_ACP = Decimal("58000")\n',
        1,
    )
    t = t.replace(
        "    AeternaIntentKind.pulmopure_subscription.value: PULMOPURE_SLUG,\n}",
        "    AeternaIntentKind.pulmopure_subscription.value: PULMOPURE_SLUG,\n"
        "    AeternaIntentKind.barsuk_quantum_pen_brief.value: BARSUK_SLUG,\n"
        "    AeternaIntentKind.teleport_earphones_brief.value: TELEPORT_SLUG,\n}",
        1,
    )

    meta = '''
BARSUK_META = {
    "mode": "licensed_secure_comms_partner",
    "unit": "architecture_brief",
    "price_acp": "36000",
    "architecture": "barsuk_quantum_pen_partner_literacy",
    "themes_literacy": [
        "pen_form_secure_comms",
        "quantum_crypto_literacy",
        "sensor_nav_literacy",
        "smart_ink_literacy",
    ],
    "note": (
        "Conceptual Project Barsuk / quantum-pen brief. ANCAP settles ACP and issues a licensed "
        "secure-comms / identity partner handoff. Not a Parker Pen Company product, not a CE/FDA device, "
        "not a military weapon, not unbreakable cryptography, and not a field kit sold by ANCAP. "
        "Infographic ranges and materials are fiction / architecture literacy. Partner screening required."
    ),
}

TELEPORT_META = {
    "mode": "licensed_partner_fiction_brief",
    "unit": "architecture_brief",
    "price_acp": "58000",
    "architecture": "teleport_earphones_medevac_literacy",
    "themes_literacy": [
        "fictional_medevac_teleport",
        "quantum_comms_literacy",
        "neural_interface_literacy",
        "field_case_ruggedization_literacy",
    ],
    "note": (
        "Conceptual AIRPODS T-2026 / teleport-earphones brief focused on medical-evacuation fiction. "
        "ANCAP settles ACP and issues a licensed partner handoff. Not an Apple product, not a real "
        "teleporter, not a military weapon system, not a guaranteed 10,000 km jump, and not a combat "
        "ops kit. Infographic ranges and combat panels are sci-fi literacy; ANCAP frames the SKU around "
        "rescue / medevac themes only. Partner screening required."
    ),
}

'''
    t = t.replace("PULMOPURE_META = {", meta + "PULMOPURE_META = {", 1)
    # Move BARSUK/TELEPORT after PULMOPURE_META instead - oops I inserted before PULMOPURE
    # That's fine - order doesn't matter

    t = t.replace(
        "PulmoPure lung-care subscription, licensed longevity partners.",
        "PulmoPure lung-care subscription, Project Barsuk quantum-pen brief, "
        "teleport-earphones medevac fiction brief, licensed longevity partners.",
        1,
    )

    status_notes = '''        barsuk_note=(
            "Project Barsuk listings are licensed secure-comms partner intakes for pen-form cryptography "
            "and sensor literacy. Infographics are fiction — not a Parker product, not a weapon, and not "
            "unbreakable crypto sold by ANCAP."
        ),
        teleport_earphones_note=(
            "Teleport-earphones listings are licensed partner intakes for fictional medical-evacuation "
            "architecture. Infographics are sci-fi — not an Apple product, not a real teleporter, and not "
            "a military weapon system."
        ),
'''
    t = t.replace(
        '''        pulmopure_note=(
            "PulmoPure listings are licensed pulmonology / respiratory clinic subscriptions for "
            "gas-vibration and lavender-oil architecture literacy. Infographics are conceptual — not a "
            "CE/FDA device, not ozone therapy, not medical-gas compounding, and not a guaranteed "
            "tar-clearance or 'clean lungs' outcome."
        ),
    )''',
        '''        pulmopure_note=(
            "PulmoPure listings are licensed pulmonology / respiratory clinic subscriptions for "
            "gas-vibration and lavender-oil architecture literacy. Infographics are conceptual — not a "
            "CE/FDA device, not ozone therapy, not medical-gas compounding, and not a guaranteed "
            "tar-clearance or 'clean lungs' outcome."
        ),
'''
        + status_notes
        + "    )",
        1,
    )

    gates = '''
    if body.intent_kind == AeternaIntentKind.barsuk_quantum_pen_brief:
        if slug and slug != BARSUK_SLUG:
            raise HTTPException(
                status_code=400,
                detail="barsuk_quantum_pen_brief requires workflow_slug aeterna-barsuk-quantum-pen",
            )
        slug = BARSUK_SLUG
        if body.budget_acp < BARSUK_PRICE_ACP:
            raise HTTPException(
                status_code=400,
                detail="barsuk_quantum_pen_brief budget_acp must be at least 36000 ACP",
            )
        for key, value in BARSUK_META.items():
            meta.setdefault(key, value)
    if body.intent_kind == AeternaIntentKind.teleport_earphones_brief:
        if slug and slug != TELEPORT_SLUG:
            raise HTTPException(
                status_code=400,
                detail="teleport_earphones_brief requires workflow_slug aeterna-teleport-earphones",
            )
        slug = TELEPORT_SLUG
        if body.budget_acp < TELEPORT_PRICE_ACP:
            raise HTTPException(
                status_code=400,
                detail="teleport_earphones_brief budget_acp must be at least 58000 ACP",
            )
        for key, value in TELEPORT_META.items():
            meta.setdefault(key, value)
'''
    t = t.replace(
        """        for key, value in PULMOPURE_META.items():
            meta.setdefault(key, value)
    now = _utcnow()""",
        """        for key, value in PULMOPURE_META.items():
            meta.setdefault(key, value)
"""
        + gates
        + "    now = _utcnow()",
        1,
    )

    path.write_text(t, encoding="utf-8")
    print("patched aeterna service")


def patch_workflow() -> None:
    path = ROOT / "app" / "services" / "workflow_execution.py"
    t = path.read_text(encoding="utf-8")
    if "aeterna-barsuk-quantum-pen" in t:
        print("workflow already patched")
        return

    templates = '''
    WorkflowTemplatePublic(
        slug="aeterna-barsuk-quantum-pen",
        title="AETERNA Project Barsuk Quantum Pen Brief",
        category="AETERNA",
        summary=(
            "Licensed secure-comms partner brief for Project Barsuk pen-form cryptography, sensor, "
            "and smart-ink literacy — 36,000 ACP."
        ),
        description=(
            "Settles 36,000 ACP and issues a licensed-partner brief for a conceptual titanium pen with "
            "quantum-crypto, sensor, AI, and smart-ink literacy. Infographic ranges (comms, sensors, "
            "standby) are fiction / architecture literacy. ANCAP is not affiliated with Parker Pen Company, "
            "does not sell a CE/FDA or military device, and does not claim unbreakable cryptography or a "
            "field weapon. Physical modules, if any, remain with a licensed secure-comms partner after screening."
        ),
        price=Money(amount="36000", currency="ACP"),
        accepted_currencies=["ACP", "wACP"],
        estimated_time_minutes=40,
        preview_items=[
            "Secure-comms theme map",
            "Licensed partner match",
            "Non-claim protocol pack",
        ],
        output_items=[
            "Barsuk quantum-pen intake brief",
            "Licensed secure-comms handoff",
            "Non-claim checklist (no Parker claim / no weapon / no unbreakable crypto / no CE-FDA)",
            "Proof receipt",
        ],
        receipt_items=["workflow_slug", "price_snapshot", "intent_kind", "architecture", "status_timeline"],
        tags=["aeterna", "barsuk", "quantum-pen", "secure-comms", "consult"],
    ),
    WorkflowTemplatePublic(
        slug="aeterna-teleport-earphones",
        title="AETERNA Teleport Earphones Medevac Fiction Brief",
        category="AETERNA",
        summary=(
            "Licensed partner brief for AIRPODS T-2026 fictional medical-evacuation / quantum-comms "
            "literacy — 58,000 ACP."
        ),
        description=(
            "Settles 58,000 ACP and issues a licensed-partner brief for sci-fi teleport-earphones framed "
            "around medical evacuation and rescue literacy. Infographic ranges (10,000 km, 0.1–0.3 s) and "
            "combat panels are fiction. ANCAP is not affiliated with Apple, does not sell a real teleporter "
            "or military weapon system, and does not guarantee evacuation outcomes. The SKU emphasizes "
            "rescue / medevac themes only — not offensive teleport ops."
        ),
        price=Money(amount="58000", currency="ACP"),
        accepted_currencies=["ACP", "wACP"],
        estimated_time_minutes=45,
        preview_items=[
            "Medevac fiction theme map",
            "Licensed partner match",
            "Non-claim protocol pack",
        ],
        output_items=[
            "Teleport-earphones medevac intake brief",
            "Licensed partner handoff",
            "Non-claim checklist (no Apple claim / no real teleport / no weapon system / no guaranteed evac)",
            "Proof receipt",
        ],
        receipt_items=["workflow_slug", "price_snapshot", "intent_kind", "architecture", "status_timeline"],
        tags=["aeterna", "teleport", "medevac", "fiction", "consult"],
    ),
'''
    t = t.replace(
        '        tags=["aeterna", "pulmopure", "subscription", "pulmonology", "consult"],\n'
        '        billing="subscription",\n'
        '        subscription_price_monthly=Money(amount="14000", currency="ACP"),\n'
        '        subscription_price_quarterly=Money(amount="38000", currency="ACP"),\n'
        '        subscription_price_annual=Money(amount="128000", currency="ACP"),\n'
        "    ),\n\n"
        '    WorkflowTemplatePublic(\n'
        '        slug="market-direction-brief",',
        '        tags=["aeterna", "pulmopure", "subscription", "pulmonology", "consult"],\n'
        '        billing="subscription",\n'
        '        subscription_price_monthly=Money(amount="14000", currency="ACP"),\n'
        '        subscription_price_quarterly=Money(amount="38000", currency="ACP"),\n'
        '        subscription_price_annual=Money(amount="128000", currency="ACP"),\n'
        "    ),"
        + templates
        + '\n    WorkflowTemplatePublic(\n'
        '        slug="market-direction-brief",',
        1,
    )

    deliverables = '''
        if template.slug == "aeterna-barsuk-quantum-pen":
            deliverable["intent"] = str(payload.get("intent_kind") or "barsuk_quantum_pen_brief")
            deliverable["compliance"] = (
                "Licensed secure-comms partner only. Not a Parker product, not a weapon, not unbreakable "
                "crypto, and not a CE/FDA device sold by ANCAP."
            )
            deliverable["barsuk_quantum_pen"] = {
                "mode": "licensed_secure_comms_partner",
                "architecture": "barsuk_quantum_pen_partner_literacy",
                "price_acp": "36000",
                "themes_literacy": [
                    "pen_form_secure_comms",
                    "quantum_crypto_literacy",
                    "sensor_nav_literacy",
                    "smart_ink_literacy",
                ],
                "note": (
                    "ANCAP settles ACP and issues a partner handoff brief. Infographic ranges are fiction "
                    "literacy, not a product claim."
                ),
            }
        if template.slug == "aeterna-teleport-earphones":
            deliverable["intent"] = str(payload.get("intent_kind") or "teleport_earphones_brief")
            deliverable["compliance"] = (
                "Licensed partner fiction brief only. Not an Apple product, not a real teleporter, not a "
                "military weapon system, and not a guaranteed medical-evacuation outcome."
            )
            deliverable["teleport_earphones"] = {
                "mode": "licensed_partner_fiction_brief",
                "architecture": "teleport_earphones_medevac_literacy",
                "price_acp": "58000",
                "themes_literacy": [
                    "fictional_medevac_teleport",
                    "quantum_comms_literacy",
                    "neural_interface_literacy",
                    "field_case_ruggedization_literacy",
                ],
                "note": (
                    "ANCAP settles ACP and issues a partner handoff brief framed around medevac fiction. "
                    "Infographic combat panels are sci-fi literacy, not ops doctrine."
                ),
            }
'''
    t = t.replace(
        '''            deliverable["pulmopure_subscription"] = {
                "mode": "licensed_clinic_subscription",
                "architecture": "pulmopure_gas_vibration_partner_literacy",
                "billing": "subscription",
                "price_acp_monthly": "14000",
                "price_acp_quarterly": "38000",
                "price_acp_annual": "128000",
                "modules": {
                    "gas_vibration": "licensed_clinic_literacy",
                    "medical_gas_mix": "partner_protocol_literacy_only",
                    "lavender_oil_atomizer": "aromatherapy_literacy",
                    "soft_standard_intensive_modes": "partner_mode_literacy",
                },
                "note": (
                    "ANCAP settles the subscription period in ACP and issues a partner handoff brief. "
                    "Physical sessions occur only under a licensed clinician after screening. Infographic "
                    "modes and before/after alveoli are protocol literacy, not a product claim."
                ),
            }
        execution_summary = {''',
        '''            deliverable["pulmopure_subscription"] = {
                "mode": "licensed_clinic_subscription",
                "architecture": "pulmopure_gas_vibration_partner_literacy",
                "billing": "subscription",
                "price_acp_monthly": "14000",
                "price_acp_quarterly": "38000",
                "price_acp_annual": "128000",
                "modules": {
                    "gas_vibration": "licensed_clinic_literacy",
                    "medical_gas_mix": "partner_protocol_literacy_only",
                    "lavender_oil_atomizer": "aromatherapy_literacy",
                    "soft_standard_intensive_modes": "partner_mode_literacy",
                },
                "note": (
                    "ANCAP settles the subscription period in ACP and issues a partner handoff brief. "
                    "Physical sessions occur only under a licensed clinician after screening. Infographic "
                    "modes and before/after alveoli are protocol literacy, not a product claim."
                ),
            }
'''
        + deliverables
        + "        execution_summary = {",
        1,
    )

    path.write_text(t, encoding="utf-8")
    print("patched workflow")


def patch_tests() -> None:
    path = ROOT / "tests" / "api" / "test_advanced_tracks.py"
    t = path.read_text(encoding="utf-8")
    if "barsuk_quantum_pen_brief" in t:
        print("tests already patched")
        return
    t = t.replace(
        '    assert AeternaIntentKind.pulmopure_subscription.value == "pulmopure_subscription"\n',
        '    assert AeternaIntentKind.pulmopure_subscription.value == "pulmopure_subscription"\n'
        '    assert AeternaIntentKind.barsuk_quantum_pen_brief.value == "barsuk_quantum_pen_brief"\n'
        '    assert AeternaIntentKind.teleport_earphones_brief.value == "teleport_earphones_brief"\n',
        1,
    )
    t = t.replace(
        '    assert AeternaStatusPublic.model_fields["pulmopure_note"]\n',
        '    assert AeternaStatusPublic.model_fields["pulmopure_note"]\n'
        '    assert AeternaStatusPublic.model_fields["barsuk_note"]\n'
        '    assert AeternaStatusPublic.model_fields["teleport_earphones_note"]\n',
        1,
    )
    t = t.replace("assert len(aeterna) >= 22", "assert len(aeterna) >= 24", 1)
    t = t.replace(
        '        "aeterna-pulmopure-subscription": "14000",\n',
        '        "aeterna-pulmopure-subscription": "14000",\n'
        '        "aeterna-barsuk-quantum-pen": "36000",\n'
        '        "aeterna-teleport-earphones": "58000",\n',
        1,
    )
    t = t.replace(
        '    assert "aeterna-pulmopure-subscription" in slugs\n',
        '    assert "aeterna-pulmopure-subscription" in slugs\n'
        '    assert "aeterna-barsuk-quantum-pen" in slugs\n'
        '    assert "aeterna-teleport-earphones" in slugs\n',
        1,
    )
    tests = '''

def test_barsuk_execution_is_partner_handoff_only():
    from app.services.workflow_execution import execute_workflow_template, find_workflow_template

    tpl = find_workflow_template("aeterna-barsuk-quantum-pen")
    assert tpl is not None
    out = execute_workflow_template(tpl, {"intent_kind": "barsuk_quantum_pen_brief"})
    item = out["deliverable"]["barsuk_quantum_pen"]
    assert item["price_acp"] == "36000"
    assert item["architecture"] == "barsuk_quantum_pen_partner_literacy"
    blob = str(out).lower()
    assert "parker" in blob
    assert "weapon" in blob


def test_barsuk_intent_default_slug_and_reject_low_budget(client):
    from app.services.aeterna import BARSUK_SLUG

    too_low = client.post(
        "/v1/aeterna/intents",
        json={"intent_kind": "barsuk_quantum_pen_brief", "budget_acp": "1000"},
    )
    assert too_low.status_code == 400, too_low.text
    created = client.post(
        "/v1/aeterna/intents",
        json={"intent_kind": "barsuk_quantum_pen_brief", "budget_acp": "36000"},
    )
    assert created.status_code == 201, created.text
    payload = created.json()
    assert payload["workflow_slug"] == BARSUK_SLUG
    assert payload["metadata_json"]["architecture"] == "barsuk_quantum_pen_partner_literacy"


def test_teleport_earphones_execution_is_partner_handoff_only():
    from app.services.workflow_execution import execute_workflow_template, find_workflow_template

    tpl = find_workflow_template("aeterna-teleport-earphones")
    assert tpl is not None
    out = execute_workflow_template(tpl, {"intent_kind": "teleport_earphones_brief"})
    item = out["deliverable"]["teleport_earphones"]
    assert item["price_acp"] == "58000"
    assert item["architecture"] == "teleport_earphones_medevac_literacy"
    blob = str(out).lower()
    assert "apple" in blob
    assert "medevac" in blob or "evacuation" in blob or "rescue" in blob


def test_teleport_intent_default_slug_and_reject_low_budget(client):
    from app.services.aeterna import TELEPORT_SLUG

    too_low = client.post(
        "/v1/aeterna/intents",
        json={"intent_kind": "teleport_earphones_brief", "budget_acp": "1000"},
    )
    assert too_low.status_code == 400, too_low.text
    created = client.post(
        "/v1/aeterna/intents",
        json={"intent_kind": "teleport_earphones_brief", "budget_acp": "58000"},
    )
    assert created.status_code == 201, created.text
    payload = created.json()
    assert payload["workflow_slug"] == TELEPORT_SLUG
    assert payload["metadata_json"]["architecture"] == "teleport_earphones_medevac_literacy"

'''
    t = t.replace(
        "\ndef test_advanced_track_routes_include_org_aeterna_intents():",
        tests + "\ndef test_advanced_track_routes_include_org_aeterna_intents():",
        1,
    )
    path.write_text(t, encoding="utf-8")
    print("patched tests")


if __name__ == "__main__":
    patch_schemas()
    patch_aeterna_service()
    patch_workflow()
    patch_tests()
