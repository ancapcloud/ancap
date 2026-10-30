"""Field services hub — Starlink / IT / cameras / solar / orbital AI (Germany / NRW first).

ANCAP is a payment and coordination platform. Partners perform physical work.
Not an equipment reseller; not a launch provider; not a Jobcenter / AVGS funding guarantee.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.services.bridge_decimal import WACP_PER_ACP
from app.services.market_economy import get_cached_wacp_usd, usd_to_acp
from app.config import get_settings
from app.services.eur_pricing import eur_to_acp
from fastapi import HTTPException

SERVICE_FEE_EUR = Decimal("3")

SERVICE_IDS: dict[str, str] = {
    "starlink-standard": "a8000008-0000-4000-8000-000000000001",
    "starlink-roof": "a8000008-0000-4000-8000-000000000002",
    "starlink-business": "a8000008-0000-4000-8000-000000000003",
    "starlink-network": "a8000008-0000-4000-8000-000000000004",
    "starlink-mobile": "a8000008-0000-4000-8000-000000000005",
    "starlink-relocate": "a8000008-0000-4000-8000-000000000006",
    "starlink-troubleshoot": "a8000008-0000-4000-8000-000000000007",
    "it-pc-setup": "a8000008-0000-4000-8000-000000000011",
    "it-device-repair": "a8000008-0000-4000-8000-000000000012",
    "it-network-home": "a8000008-0000-4000-8000-000000000013",
    "it-maintenance-visit": "a8000008-0000-4000-8000-000000000014",
    "cam-cctv-install": "a8000008-0000-4000-8000-000000000021",
    "cam-nvr-config": "a8000008-0000-4000-8000-000000000022",
    "cam-maintenance": "a8000008-0000-4000-8000-000000000023",
    "solar-balcony-install": "a8000008-0000-4000-8000-000000000031",
    "solar-panel-service": "a8000008-0000-4000-8000-000000000032",
    "panel-other-mount": "a8000008-0000-4000-8000-000000000033",
    "space-ai-orbit-intake": "a8000008-0000-4000-8000-000000000041",
    "space-ai-beyond-orbit": "a8000008-0000-4000-8000-000000000042",
    "space-ai-superintel-architecture": "a8000008-0000-4000-8000-000000000043",
}

WORKFLOW_CATALOG_EUR: dict[str, str] = {
    "starlink-install-intake": "153",
    "starlink-standard": "153",
    "starlink-roof": "203",
    "starlink-business": "303",
    "starlink-network": "53",
    "starlink-mobile": "183",
    "starlink-relocate": "178",
    "starlink-troubleshoot": "83",
    "it-pc-setup": "123",
    "it-device-repair": "93",
    "it-network-home": "83",
    "it-maintenance-visit": "73",
    "cam-cctv-install": "183",
    "cam-nvr-config": "103",
    "cam-maintenance": "78",
    "solar-balcony-install": "253",
    "solar-panel-service": "123",
    "panel-other-mount": "153",
    "space-ai-orbit-intake": "12003",
    "space-ai-beyond-orbit": "28003",
    "space-ai-superintel-architecture": "48003",
}


def _regions() -> list[dict[str, str]]:
    return [
        {
            "id": "de-nrw",
            "label": "NRW (Nordrhein-Westfalen)",
            "blurb": "Primary service area for Jobcenter / AVGS-ready demos and local installs.",
        },
        {
            "id": "de",
            "label": "Deutschland",
            "blurb": "Nationwide Germany coverage via partner network (lead times vary).",
        },
        {
            "id": "eu-eea-uk",
            "label": "EU / EEA / UK",
            "blurb": "Expanding corridor — confirm availability before travel.",
        },
    ]


def _partners() -> list[dict[str, Any]]:
    return [
        {
            "id": "installer-nrw-verified",
            "label": "Andrew / Verified Installer",
            "location": "Germany · NRW",
            "verified": True,
            "blurb": (
                "Independently qualified field installer for connectivity, IT, CCTV, and "
                "panel mounts. Not employed by Starlink, Telekom, or equipment vendors."
            ),
        }
    ]


def _services() -> list[dict[str, Any]]:
    return [
        # Starlink
        {
            "id": "starlink-standard",
            "group_id": "starlink",
            "review_target_id": SERVICE_IDS["starlink-standard"],
            "label": "Standard Starlink Installation",
            "price_eur": "150",
            "workflow_slug": "starlink-standard",
            "regions": ["de-nrw", "de"],
            "blurb": "Residential kit mount, basic aiming, and handoff. Kit hardware sold separately by Starlink.",
        },
        {
            "id": "starlink-roof",
            "group_id": "starlink",
            "review_target_id": SERVICE_IDS["starlink-roof"],
            "label": "Roof / wall mounting",
            "price_eur": "200",
            "workflow_slug": "starlink-roof",
            "regions": ["de-nrw", "de"],
            "blurb": "Elevated roof or facade mount with partner safety protocol. Permits not included.",
        },
        {
            "id": "starlink-business",
            "group_id": "starlink",
            "review_target_id": SERVICE_IDS["starlink-business"],
            "label": "Business installation",
            "price_eur": "300",
            "workflow_slug": "starlink-business",
            "regions": ["de-nrw", "de", "eu-eea-uk"],
            "blurb": "SME / site install with documented handoff. Complex sites may need a follow-on quote.",
        },
        {
            "id": "starlink-network",
            "group_id": "starlink",
            "review_target_id": SERVICE_IDS["starlink-network"],
            "label": "Network / Wi-Fi configuration",
            "price_eur": "50",
            "workflow_slug": "starlink-network",
            "regions": ["de-nrw", "de"],
            "blurb": "Router / Wi-Fi setup and basic LAN check after dish is online.",
        },
        {
            "id": "starlink-mobile",
            "group_id": "starlink",
            "review_target_id": SERVICE_IDS["starlink-mobile"],
            "label": "Mobile / RV installation",
            "price_eur": "180",
            "workflow_slug": "starlink-mobile",
            "regions": ["de-nrw", "de"],
            "blurb": "Vehicle / RV mount literacy and partner install where local rules allow.",
        },
        {
            "id": "starlink-relocate",
            "group_id": "starlink",
            "review_target_id": SERVICE_IDS["starlink-relocate"],
            "label": "Relocation / reinstallation",
            "price_eur": "175",
            "workflow_slug": "starlink-relocate",
            "regions": ["de-nrw", "de"],
            "blurb": "Move an existing kit to a new site and re-aim.",
        },
        {
            "id": "starlink-troubleshoot",
            "group_id": "starlink",
            "review_target_id": SERVICE_IDS["starlink-troubleshoot"],
            "label": "Troubleshooting & optimization",
            "price_eur": "80",
            "workflow_slug": "starlink-troubleshoot",
            "regions": ["de-nrw", "de"],
            "blurb": "Obstruction, cable, and performance troubleshooting visit.",
        },
        # IT
        {
            "id": "it-pc-setup",
            "group_id": "it",
            "review_target_id": SERVICE_IDS["it-pc-setup"],
            "label": "PC / laptop setup",
            "price_eur": "120",
            "workflow_slug": "it-pc-setup",
            "regions": ["de-nrw", "de"],
            "blurb": "OS install, drivers, basic apps, and data-migration handoff. Hardware sold separately.",
        },
        {
            "id": "it-device-repair",
            "group_id": "it",
            "review_target_id": SERVICE_IDS["it-device-repair"],
            "label": "IT device repair / upgrade",
            "price_eur": "90",
            "workflow_slug": "it-device-repair",
            "regions": ["de-nrw", "de"],
            "blurb": "Diagnosis and partner repair / RAM-SSD upgrade coordination for PCs and peripherals.",
        },
        {
            "id": "it-network-home",
            "group_id": "it",
            "review_target_id": SERVICE_IDS["it-network-home"],
            "label": "Home / office IT network",
            "price_eur": "80",
            "workflow_slug": "it-network-home",
            "regions": ["de-nrw", "de"],
            "blurb": "Router, Wi-Fi, and wired LAN setup for home office or small site.",
        },
        {
            "id": "it-maintenance-visit",
            "group_id": "it",
            "review_target_id": SERVICE_IDS["it-maintenance-visit"],
            "label": "IT maintenance visit",
            "price_eur": "70",
            "workflow_slug": "it-maintenance-visit",
            "regions": ["de-nrw", "de", "eu-eea-uk"],
            "blurb": "On-site cleanup, updates, backup check, and performance tune-up.",
        },
        # Cameras
        {
            "id": "cam-cctv-install",
            "group_id": "cameras",
            "review_target_id": SERVICE_IDS["cam-cctv-install"],
            "label": "CCTV / camera installation",
            "price_eur": "180",
            "workflow_slug": "cam-cctv-install",
            "regions": ["de-nrw", "de"],
            "blurb": "Mount and aim IP / CCTV cameras with partner cabling. Cameras sold separately.",
        },
        {
            "id": "cam-nvr-config",
            "group_id": "cameras",
            "review_target_id": SERVICE_IDS["cam-nvr-config"],
            "label": "NVR / recorder configuration",
            "price_eur": "100",
            "workflow_slug": "cam-nvr-config",
            "regions": ["de-nrw", "de"],
            "blurb": "NVR / DVR setup, remote view, and retention literacy. Not a surveillance company.",
        },
        {
            "id": "cam-maintenance",
            "group_id": "cameras",
            "review_target_id": SERVICE_IDS["cam-maintenance"],
            "label": "Camera system maintenance",
            "price_eur": "75",
            "workflow_slug": "cam-maintenance",
            "regions": ["de-nrw", "de", "eu-eea-uk"],
            "blurb": "Clean, re-aim, firmware check, and recording health visit.",
        },
        # Solar / panels
        {
            "id": "solar-balcony-install",
            "group_id": "solar",
            "review_target_id": SERVICE_IDS["solar-balcony-install"],
            "label": "Balcony / small PV install",
            "price_eur": "250",
            "workflow_slug": "solar-balcony-install",
            "regions": ["de-nrw", "de"],
            "blurb": (
                "Partner coordination for balcony / small PV mount literacy. Panels and inverters "
                "sold separately; electrical sign-off by qualified electrician."
            ),
        },
        {
            "id": "solar-panel-service",
            "group_id": "solar",
            "review_target_id": SERVICE_IDS["solar-panel-service"],
            "label": "Solar panel service",
            "price_eur": "120",
            "workflow_slug": "solar-panel-service",
            "regions": ["de-nrw", "de"],
            "blurb": "Inspection, cleaning literacy, and partner service visit for existing PV.",
        },
        {
            "id": "panel-other-mount",
            "group_id": "solar",
            "review_target_id": SERVICE_IDS["panel-other-mount"],
            "label": "Other panel mount (partner)",
            "price_eur": "150",
            "workflow_slug": "panel-other-mount",
            "regions": ["de-nrw", "de", "eu-eea-uk"],
            "blurb": (
                "Mount coordination for other panel types (thermal / specialty) via partner literacy — "
                "not equipment sales by ANCAP."
            ),
        },
        # Orbital / space AI data centers (partner literacy + coordination)
        {
            "id": "space-ai-orbit-intake",
            "group_id": "space",
            "review_target_id": SERVICE_IDS["space-ai-orbit-intake"],
            "label": "Orbital AI data-center placement (LEO / MEO)",
            "price_eur": "12000",
            "workflow_slug": "space-ai-orbit-intake",
            "regions": ["de-nrw", "de", "eu-eea-uk"],
            "blurb": (
                "Partner literacy and ACP-paid coordination for placing AI compute / data-center "
                "payload concepts on Earth orbit (LEO / MEO). Not a SpaceX / launch ticket; not a "
                "sovereign orbital slot grant."
            ),
        },
        {
            "id": "space-ai-beyond-orbit",
            "group_id": "space",
            "review_target_id": SERVICE_IDS["space-ai-beyond-orbit"],
            "label": "Beyond-orbit AI data-center placement (GEO / cislunar)",
            "price_eur": "28000",
            "workflow_slug": "space-ai-beyond-orbit",
            "regions": ["de-nrw", "de", "eu-eea-uk"],
            "blurb": (
                "Architecture and partner coordination for AI data-center concepts beyond LEO "
                "(GEO / cislunar / deep-space staging literacy). Launch, spectrum, and export "
                "controls remain with licensed partners and the customer."
            ),
        },
        {
            "id": "space-ai-superintel-architecture",
            "group_id": "space",
            "review_target_id": SERVICE_IDS["space-ai-superintel-architecture"],
            "label": "Orbital superintelligence AI-center architecture brief",
            "price_eur": "48000",
            "workflow_slug": "space-ai-superintel-architecture",
            "regions": ["de-nrw", "de", "eu-eea-uk"],
            "blurb": (
                "High-assurance partner brief for sealed orbital / beyond-orbit 'superintelligence' "
                "compute architecture literacy — sealed edge, HSM control plane themes. Not a claim "
                "that ANCAP operates AGI/ASI in space today."
            ),
        },
    ]


def catalog(*, group_id: str | None = None) -> dict[str, Any]:
    services = _services()
    if group_id:
        services = [s for s in services if s.get("group_id") == group_id]
    return {
        "title": "Field services — real-world and orbital installs with ACP",
        "tagline": (
            "Starlink, IT, CCTV, solar / panels, and orbital AI data-center placement literacy "
            "through ancap.cloud. Pay with ACP, wACP, or USDT (via /buy-acp). Germany / NRW first."
        ),
        "compliance_note": (
            "ANCAP is a payment and coordination platform — not an official Starlink / equipment "
            "reseller, not Telekom, not a launch provider (SpaceX or otherwise), and not a Jobcenter "
            "employment guarantee. Physical and orbital work is performed by independently qualified "
            "partners. Building permits, electrical work, roof / height safety, spectrum, export "
            "controls, and launch manifests remain with the customer and licensed partners. Crypto "
            "payments require your own eligibility self-attestation. AVGS / Jobcenter funding is "
            "decided solely by the agency. Orbital SKUs are partner literacy / coordination — not a "
            "promise of AGI/ASI in space or a sovereign orbital slot."
        ),
        "legal_href": "/legal/field-services",
        "service_fee_eur": str(SERVICE_FEE_EUR),
        "official_reseller": False,
        "jobcenter_guarantee": False,
        "groups": [
            {
                "id": "starlink",
                "label": "Starlink",
                "blurb": "Satellite kit mounting, network, RV, and troubleshooting.",
            },
            {
                "id": "it",
                "label": "IT & computers",
                "blurb": "PC / laptop setup, upgrades, home network, maintenance visits.",
            },
            {
                "id": "cameras",
                "label": "Cameras / CCTV",
                "blurb": "Camera install, NVR config, and system maintenance.",
            },
            {
                "id": "solar",
                "label": "Solar & panels",
                "blurb": "Balcony PV, solar service, and other panel mount coordination.",
            },
            {
                "id": "space",
                "label": "Orbital AI / space",
                "blurb": "AI data-center placement on orbit and beyond — partner literacy + ACP desk.",
            },
        ],
        "regions": _regions(),
        "partners": _partners(),
        "services": services,
    }


def starlink_catalog() -> dict[str, Any]:
    """Legacy shape for /starlink-install (Starlink SKUs only)."""
    raw = catalog(group_id="starlink")
    raw["title"] = "Starlink Installation — real-world services with ACP"
    raw["tagline"] = (
        "Order professional Starlink mounting and network setup through ancap.cloud. "
        "Pay with ACP, wACP, or USDT (via /buy-acp). Germany / NRW first, then EU."
    )
    raw["legal_href"] = "/legal/starlink-install"
    raw["compliance_note"] = (
        "ANCAP is a payment and coordination platform — not an official Starlink reseller, "
        "not Telekom, and not a Jobcenter employment guarantee. Mounting is performed by an "
        "independently qualified installer partner. Building permits (Baurecht), roof safety, "
        "and electrical work remain the responsibility of the customer and the partner. "
        "Crypto payments require your own eligibility self-attestation under applicable law. "
        "AVGS / Jobcenter funding is decided solely by the agency — this page describes a "
        "business service model, not a funding promise."
    )
    # Drop groups from legacy response shape (optional field ignored by schema).
    return raw


def find_service(service_id: str) -> dict[str, Any] | None:
    for svc in _services():
        if svc["id"] == service_id:
            return svc
    return None


def quote(
    *,
    service_id: str,
    region: str | None = None,
    payment_currency: str = "ACP",
) -> dict[str, Any]:
    svc = find_service(service_id)
    if svc is None:
        raise ValueError(f"unknown service_id: {service_id}")

    region_ids = {r["id"] for r in _regions()}
    if region and region not in region_ids:
        raise ValueError(f"unknown region: {region}")
    if region and region not in (svc.get("regions") or []):
        raise ValueError(f"service not available in region: {region}")

    install = Decimal(str(svc["price_eur"]))
    fee = SERVICE_FEE_EUR
    total_eur = (install + fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    racp_only = get_settings().external_token_racp_only
    if racp_only and (payment_currency or "ACP").upper() != "ACP":
        raise HTTPException(409, "Service settlement uses internal ACP with EUR pricing; the BSC test route is retired.")
    spot = None if racp_only else get_cached_wacp_usd(allow_stale=True)
    amount_acp = eur_to_acp(total_eur) if racp_only else usd_to_acp(total_eur, wacp_usd=spot)
    amount_wacp = (amount_acp * Decimal(WACP_PER_ACP)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    cur = (payment_currency or "ACP").strip().upper()
    if cur == "WACP":
        pay_amount = amount_wacp
    elif cur == "USDT":
        pay_amount = total_eur
    else:
        cur = "ACP"
        pay_amount = amount_acp

    partner = _partners()[0]
    return {
        "service_id": service_id,
        "group_id": svc.get("group_id"),
        "region": region,
        "label": svc["label"],
        "installation_fee_eur": format(install, "f"),
        "service_fee_eur": format(fee, "f"),
        "total_eur": format(total_eur, "f"),
        "total_usdt": format(total_eur, "f"),
        "amount_acp": format(amount_acp, "f"),
        "amount_wacp": format(amount_wacp, "f"),
        "payment_currency": cur,
        "pay_amount": format(pay_amount, "f"),
        "oracle_wacp_usd": format(spot or Decimal("0"), "f"),
        "workflow_slug": svc.get("workflow_slug") or "starlink-install-intake",
        "provider_label": partner["label"],
        "provider_location": partner["location"],
        "escrow_note": (
            "Funds reserve into ANCAP workflow escrow on payment. Partner payout after "
            "installation confirmation (MVP: operator capture on run completion)."
        ),
    }
