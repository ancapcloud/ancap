"""Prototype GC / XRF-proxy assay: peaks → purity → indicative ACP value.

This is a desk simulation of gas-chromatographic / spectroscopic purity analysis
for metals and natural gas (and light oil proxy). Not a certified lab instrument.
"""

from __future__ import annotations

import secrets
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from fastapi import HTTPException

from app.schemas.assay_gc import (
    AssayComponentResult,
    AssayGcAnalyzePublic,
    AssayGcAnalyzeRequest,
    AssayGcCatalogItem,
    AssayGcCatalogPublic,
    AssayPeak,
)
from app.services import otc_intake as otc_svc

_Q = Decimal("0.00000001")

# GC component roles for natural gas
_GAS_ROLES: dict[str, tuple[str, Decimal]] = {
    # label_lower: (role, value_weight toward "purity"/calorific usefulness)
    "methane": ("target", Decimal("1.0")),
    "ch4": ("target", Decimal("1.0")),
    "ethane": ("target", Decimal("0.95")),
    "c2h6": ("target", Decimal("0.95")),
    "propane": ("target", Decimal("0.9")),
    "c3h8": ("target", Decimal("0.9")),
    "n-butane": ("target", Decimal("0.85")),
    "i-butane": ("target", Decimal("0.85")),
    "butane": ("target", Decimal("0.85")),
    "nitrogen": ("inert", Decimal("0.05")),
    "n2": ("inert", Decimal("0.05")),
    "co2": ("diluent", Decimal("0.1")),
    "carbon dioxide": ("diluent", Decimal("0.1")),
    "h2s": ("contaminant", Decimal("0.0")),
    "hydrogen sulfide": ("contaminant", Decimal("0.0")),
    "helium": ("inert", Decimal("0.15")),
    "he": ("inert", Decimal("0.15")),
    "oxygen": ("contaminant", Decimal("0.0")),
    "o2": ("contaminant", Decimal("0.0")),
}

_METAL_ROLES: dict[str, tuple[str, Decimal]] = {
    "gold": ("target", Decimal("1.0")),
    "au": ("target", Decimal("1.0")),
    "silver": ("target", Decimal("1.0")),
    "ag": ("target", Decimal("1.0")),
    "platinum": ("target", Decimal("1.0")),
    "pt": ("target", Decimal("1.0")),
    "palladium": ("target", Decimal("1.0")),
    "pd": ("target", Decimal("1.0")),
    "copper": ("diluent", Decimal("0.05")),
    "cu": ("diluent", Decimal("0.05")),
    "nickel": ("diluent", Decimal("0.05")),
    "ni": ("diluent", Decimal("0.05")),
    "iron": ("contaminant", Decimal("0.0")),
    "fe": ("contaminant", Decimal("0.0")),
    "lead": ("contaminant", Decimal("0.0")),
    "pb": ("contaminant", Decimal("0.0")),
    "zinc": ("diluent", Decimal("0.02")),
    "zn": ("diluent", Decimal("0.02")),
}

_DISCLAIMER = (
    "ANCAP GC/XRF desk prototype — educational assay simulation only. "
    "Not a certified chromatographic laboratory, not custody assay, not a firm bid. "
    "Real settlement still requires supervised OTC review and licensed assay where applicable."
)


def _dec(raw: str, field: str) -> Decimal:
    try:
        v = Decimal(str(raw).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise HTTPException(status_code=400, detail=f"{field} must be a decimal string") from exc
    if v < 0:
        raise HTTPException(status_code=400, detail=f"{field} must be >= 0")
    return v


def _api_str(v: Decimal) -> str:
    s = format(v.quantize(_Q, rounding=ROUND_HALF_UP), "f").rstrip("0").rstrip(".")
    return s or "0"


def catalog() -> AssayGcCatalogPublic:
    return AssayGcCatalogPublic(
        modes=[
            AssayGcCatalogItem(
                mode="metal_xrf_proxy",
                label="Metal XRF / fire-assay proxy",
                target_assets=["gold", "silver", "platinum", "palladium"],
                unit_hint="g",
                note="Peak areas map to elemental composition; purity drives OTC ACP/g quote.",
            ),
            AssayGcCatalogItem(
                mode="gas_chromatograph",
                label="Gas chromatograph (natural gas / light hydrocarbon)",
                target_assets=["natural_gas", "oil"],
                unit_hint="m3 or bbl",
                note="Retention peaks → CH4/C2+/inerts/H2S; calorific purity score → ACP value.",
            ),
        ],
        disclaimer=_DISCLAIMER,
    )


def _normalize_peaks(peaks: list[AssayPeak]) -> list[AssayPeak]:
    if not peaks:
        raise HTTPException(status_code=400, detail="peaks required (or set simulate=true)")
    areas = [_dec(p.area_pct, "area_pct") for p in peaks]
    total = sum(areas)
    if total <= 0:
        raise HTTPException(status_code=400, detail="peak areas must sum to > 0")
    out: list[AssayPeak] = []
    for p, a in zip(peaks, areas, strict=True):
        pct = (a / total * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        out.append(
            AssayPeak(
                label=p.label.strip()[:64],
                retention_or_energy=str(p.retention_or_energy).strip()[:32],
                area_pct=_api_str(pct),
                notes=p.notes,
            )
        )
    return out


def _simulate_metal_peaks(metal: str, purity_ppt: int) -> list[AssayPeak]:
    purity = Decimal(purity_ppt) / Decimal("10")  # ppt→%
    diluent = (Decimal("100") - purity).quantize(Decimal("0.01"))
    copper = (diluent * Decimal("0.7")).quantize(Decimal("0.01"))
    other = (diluent - copper).quantize(Decimal("0.01"))
    peaks = [
        AssayPeak(label=metal.title(), retention_or_energy="9.71 keV", area_pct=_api_str(purity)),
        AssayPeak(label="Copper", retention_or_energy="8.04 keV", area_pct=_api_str(copper)),
    ]
    if other > 0:
        peaks.append(AssayPeak(label="Iron", retention_or_energy="6.40 keV", area_pct=_api_str(other)))
    return peaks


def _simulate_gas_peaks(*, commodity: str, high_methane: bool = True) -> list[AssayPeak]:
    if commodity == "oil":
        return [
            AssayPeak(label="C5+", retention_or_energy="4.80 min", area_pct="62.0"),
            AssayPeak(label="n-Butane", retention_or_energy="3.10 min", area_pct="12.0"),
            AssayPeak(label="Propane", retention_or_energy="2.20 min", area_pct="10.0"),
            AssayPeak(label="Ethane", retention_or_energy="1.55 min", area_pct="8.0"),
            AssayPeak(label="Methane", retention_or_energy="0.95 min", area_pct="5.0"),
            AssayPeak(label="Nitrogen", retention_or_energy="0.55 min", area_pct="2.0"),
            AssayPeak(label="CO2", retention_or_energy="0.70 min", area_pct="1.0"),
        ]
    if high_methane:
        return [
            AssayPeak(label="Methane", retention_or_energy="0.95 min", area_pct="91.5"),
            AssayPeak(label="Ethane", retention_or_energy="1.55 min", area_pct="4.2"),
            AssayPeak(label="Propane", retention_or_energy="2.20 min", area_pct="1.5"),
            AssayPeak(label="Nitrogen", retention_or_energy="0.55 min", area_pct="1.8"),
            AssayPeak(label="CO2", retention_or_energy="0.70 min", area_pct="0.7"),
            AssayPeak(label="H2S", retention_or_energy="1.10 min", area_pct="0.3"),
        ]
    return [
        AssayPeak(label="Methane", retention_or_energy="0.95 min", area_pct="72.0"),
        AssayPeak(label="Nitrogen", retention_or_energy="0.55 min", area_pct="14.0"),
        AssayPeak(label="CO2", retention_or_energy="0.70 min", area_pct="8.0"),
        AssayPeak(label="Ethane", retention_or_energy="1.55 min", area_pct="4.0"),
        AssayPeak(label="H2S", retention_or_energy="1.10 min", area_pct="2.0"),
    ]


def _role_for(label: str, mode: str) -> tuple[str, Decimal]:
    key = label.strip().lower()
    table = _METAL_ROLES if mode == "metal_xrf_proxy" else _GAS_ROLES
    if key in table:
        return table[key]
    # fuzzy contains
    for k, v in table.items():
        if k in key or key in k:
            return v
    return ("unknown", Decimal("0.2"))


def _score_composition(peaks: list[AssayPeak], mode: str) -> tuple[list[AssayComponentResult], Decimal, list[str]]:
    comps: list[AssayComponentResult] = []
    weighted = Decimal("0")
    flags: list[str] = []
    for p in peaks:
        role, weight = _role_for(p.label, mode)
        area = _dec(p.area_pct, "area_pct")
        weighted += area * weight
        if role == "contaminant" and area >= Decimal("0.2"):
            flags.append(f"Contaminant peak elevated: {p.label} ({p.area_pct}%)")
        if role == "unknown" and area >= Decimal("5"):
            flags.append(f"Unrecognized major peak: {p.label}")
        comps.append(
            AssayComponentResult(
                label=p.label,
                area_pct=p.area_pct,
                role=role,  # type: ignore[arg-type]
                value_weight=_api_str(weight),
            )
        )
    purity_pct = (weighted / Decimal("100") * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    # clamp 0..100
    if purity_pct < 0:
        purity_pct = Decimal("0")
    if purity_pct > 100:
        purity_pct = Decimal("100")
    return comps, purity_pct, flags


def analyze(req: AssayGcAnalyzeRequest) -> AssayGcAnalyzePublic:
    sample_id = (req.sample_id or "").strip() or f"ASM-{secrets.token_hex(3).upper()}"
    device_id = (req.device_id or "").strip() or "ANCAP-GC-PROTO-1"
    qty = _dec(req.quantity, "quantity")
    if qty <= 0:
        raise HTTPException(status_code=400, detail="quantity must be > 0")

    confidence = "medium"
    peaks_in = list(req.peaks or [])

    if req.mode == "metal_xrf_proxy":
        if not req.metal:
            raise HTTPException(status_code=400, detail="metal required for metal_xrf_proxy")
        if req.simulate and not peaks_in:
            ppt = int(req.declared_purity_ppt or 999)
            peaks_in = _simulate_metal_peaks(req.metal, ppt)
            confidence = "simulated"
        peaks = _normalize_peaks(peaks_in)
        comps, purity_pct, flags = _score_composition(peaks, "metal_xrf_proxy")
        # Prefer target metal peak area as purity ppt when present
        target_area = None
        for c in comps:
            if c.label.strip().lower() in (req.metal, req.metal[:2] if len(req.metal) > 2 else req.metal):
                target_area = _dec(c.area_pct, "area")
                break
            role_ok = c.role == "target" and req.metal[:2].lower() in c.label.lower()
            if role_ok or req.metal.lower() in c.label.lower():
                target_area = _dec(c.area_pct, "area")
                break
        if target_area is not None:
            purity_pct = target_area
        purity_ppt = int((purity_pct * Decimal("10")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        purity_ppt = max(100, min(1000, purity_ppt))
        q = otc_svc.quote_metal(
            metal=req.metal,  # type: ignore[arg-type]
            weight_grams=_api_str(qty),
            purity_ppt=purity_ppt,
        )
        if any("Contaminant" in f for f in flags):
            confidence = "low" if confidence != "simulated" else confidence
            flags.append("Desk may haircut ACP settlement after full assay.")
        return AssayGcAnalyzePublic(
            mode=req.mode,
            sample_id=sample_id,
            device_id=device_id,
            asset_label=otc_svc.METAL_LABELS[req.metal],
            quantity=_api_str(qty),
            quantity_unit="g",
            purity_pct=_api_str(purity_pct),
            purity_ppt=purity_ppt,
            composition=comps,
            peaks_normalized=peaks,
            indicative_acp_amount=q.estimated_acp_amount,
            rate_note=q.rate_note,
            confidence=confidence,  # type: ignore[arg-type]
            flags=flags,
            next_step="Attach sample_id to OTC metal intake order; confirm after physical handoff.",
            disclaimer=_DISCLAIMER,
            details={"metal": req.metal, "otc_quote": q.details},
        )

    # gas_chromatograph
    commodity = req.commodity or "natural_gas"
    if commodity not in ("natural_gas", "oil"):
        raise HTTPException(status_code=400, detail="commodity must be natural_gas or oil for GC mode")
    if req.simulate and not peaks_in:
        peaks_in = _simulate_gas_peaks(commodity=commodity)
        confidence = "simulated"
    peaks = _normalize_peaks(peaks_in)
    comps, purity_pct, flags = _score_composition(peaks, "gas_chromatograph")
    # Contaminant haircut on value
    h2s = Decimal("0")
    for c in comps:
        if "h2s" in c.label.lower() or "sulfide" in c.label.lower():
            h2s = _dec(c.area_pct, "h2s")
    value_factor = (purity_pct / Decimal("100")).quantize(_Q, rounding=ROUND_HALF_UP)
    if h2s >= Decimal("1"):
        value_factor *= Decimal("0.85")
        flags.append("H2S ≥ 1% — sweetening required; value factor −15%.")
        confidence = "low" if confidence != "simulated" else confidence
    elif h2s >= Decimal("0.2"):
        value_factor *= Decimal("0.95")
        flags.append("Trace H2S — mild haircut −5%.")

    q = otc_svc.quote_commodity(commodity=commodity, quantity=_api_str(qty))  # type: ignore[arg-type]
    base = Decimal(q.estimated_acp_amount)
    estimated = (base * value_factor).quantize(_Q, rounding=ROUND_HALF_UP)
    unit = otc_svc.COMMODITY_UNITS[commodity]
    return AssayGcAnalyzePublic(
        mode=req.mode,
        sample_id=sample_id,
        device_id=device_id,
        asset_label=otc_svc.COMMODITY_LABELS[commodity],
        quantity=_api_str(qty),
        quantity_unit=unit,
        purity_pct=_api_str(purity_pct),
        purity_ppt=None,
        composition=comps,
        peaks_normalized=peaks,
        indicative_acp_amount=_api_str(estimated),
        rate_note=f"{q.rate_note}; GC purity factor {_api_str(value_factor)}",
        confidence=confidence,  # type: ignore[arg-type]
        flags=flags,
        next_step="Attach sample_id + chromatogram summary to OTC commodity intake; desk confirms after custody assay.",
        disclaimer=_DISCLAIMER,
        details={
            "commodity": commodity,
            "value_factor": _api_str(value_factor),
            "otc_base_acp": q.estimated_acp_amount,
            "otc_quote": q.details,
        },
    )
