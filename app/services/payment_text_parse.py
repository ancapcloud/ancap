from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

_QR_URI_RE = re.compile(
    r"(?i)(?:ethereum|bitcoin|solana|acp)?:?//?([a-zA-Z0-9]+)@?([0-9.]+)?",
)
_AMOUNT_RE = re.compile(r"(?i)(?:amount|value|amt)[=:]([0-9.]+)")
_EVM_ADDRESS_RE = re.compile(r"(?i)\b(0x[a-f0-9]{40})\b")
_ACP_ADDRESS_RE = re.compile(r"\b(acp1[a-z0-9]{20,120})\b", re.IGNORECASE)
_INVOICE_TOTAL_RE = re.compile(
    r"(?i)(?:total(?:\s+due)?|amount\s+due|grand\s+total|pay(?:able)?(?:\s+amount)?|balance\s+due|итого|к\s+оплате|до\s+сплати|сума|сумма|gesamtbetrag|rechnungsbetrag)\s*[:#]?\s*\$?\s*([0-9]+(?:[.,][0-9]{1,8})?)",
)
_PAY_TO_RE = re.compile(
    r"(?i)(?:pay(?:\s+to)?|recipient|beneficiary|send\s+to|wallet)\s*[:#]?\s*([^\n\r]{6,120})",
)
_CURRENCY_HINT_RE = re.compile(r"(?i)\b(USDT|USDC|BNB|ETH|ACP|USD|EUR)\b")
_INVOICE_LABEL_RE = re.compile(r"(?i)(?:invoice|receipt|payment\s+request)\s*#?\s*([A-Z0-9-]{3,32})")


@dataclass
class PaymentTextParseResult:
    detected_network: str | None
    address: str | None
    amount: str | None
    currency: str | None
    label: str | None
    confidence: float
    parse_notes: list[str]


def _normalize_amount(raw: str) -> str | None:
    cleaned = raw.strip().replace(",", ".")
    try:
        parsed = Decimal(cleaned)
    except InvalidOperation:
        return None
    if not parsed.is_finite() or parsed <= 0:
        return None
    normalized = format(parsed.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized or None


def parse_payment_text(raw_text: str, *, source: str = "paste") -> PaymentTextParseResult:
    text = (raw_text or "").strip()
    notes: list[str] = []
    network: str | None = None
    address: str | None = None
    amount: str | None = None
    currency: str | None = None
    label: str | None = None
    confidence = 0.35 if source != "ocr" else 0.4

    if source == "ocr":
        notes.append("OCR/receipt text normalization applied")

    if text.lower().startswith("acp:"):
        network = "acp"
        parts = text[4:].split("?")
        address = parts[0].strip() or None
        confidence = 0.85
        notes.append("Detected ACP payment URI")
        for segment in parts[1:]:
            for piece in segment.split("&"):
                if piece.lower().startswith("amount="):
                    amount = _normalize_amount(piece.split("=", 1)[1])
                    currency = "ACP"

    uri_match = _QR_URI_RE.search(text)
    if uri_match and not address:
        network = (uri_match.group(0).split(":")[0] or "unknown").lower()
        address = uri_match.group(1)
        if uri_match.group(2):
            amount = _normalize_amount(uri_match.group(2))
        confidence = max(confidence, 0.7)
        notes.append("Detected crypto payment URI pattern")

    acp_match = _ACP_ADDRESS_RE.search(text)
    if acp_match and not address:
        address = acp_match.group(1)
        network = "acp"
        confidence = max(confidence, 0.72)
        notes.append("Detected ACP address in free text")

    evm_match = _EVM_ADDRESS_RE.search(text)
    if evm_match and not address:
        address = evm_match.group(1)
        network = "bsc" if re.search(r"(?i)\b(bsc|binance|bnb)\b", text) else "ethereum"
        confidence = max(confidence, 0.68)
        notes.append("Detected EVM address in free text")

    amount_match = _AMOUNT_RE.search(text)
    if amount_match and not amount:
        amount = _normalize_amount(amount_match.group(1))
        if amount:
            currency = currency or "ACP"
            confidence = max(confidence, 0.55)
            notes.append("Extracted amount token from free text")

    invoice_total = _INVOICE_TOTAL_RE.search(text)
    if invoice_total and not amount:
        amount = _normalize_amount(invoice_total.group(1))
        if amount:
            confidence = max(confidence, 0.62)
            notes.append("Extracted invoice/receipt total")

    pay_to = _PAY_TO_RE.search(text)
    if pay_to and not address:
        candidate = pay_to.group(1).strip(" .,:;")
        acp_in_pay_to = _ACP_ADDRESS_RE.search(candidate)
        evm_in_pay_to = _EVM_ADDRESS_RE.search(candidate)
        if acp_in_pay_to:
            address = acp_in_pay_to.group(1)
            network = "acp"
            confidence = max(confidence, 0.66)
            notes.append("Extracted pay-to ACP address from invoice text")
        elif evm_in_pay_to:
            address = evm_in_pay_to.group(1)
            network = "bsc" if re.search(r"(?i)\b(bsc|binance|bnb)\b", text) else "ethereum"
            confidence = max(confidence, 0.64)
            notes.append("Extracted pay-to EVM address from invoice text")
        elif 20 <= len(candidate) <= 128 and " " not in candidate.strip():
            address = candidate
            confidence = max(confidence, 0.48)
            notes.append("Heuristic pay-to address extraction")

    currency_match = _CURRENCY_HINT_RE.search(text)
    if currency_match and not currency:
        currency = currency_match.group(1).upper()
        if currency in {"USD", "EUR"}:
            network = network or "fiat"
        confidence = max(confidence, 0.5)
        notes.append(f"Detected currency hint: {currency}")

    invoice_label = _INVOICE_LABEL_RE.search(text)
    if invoice_label:
        label = invoice_label.group(1)
        confidence = max(confidence, 0.52)
        notes.append("Detected invoice/receipt label")

    if "@" in text and not address:
        maybe_addr = text.split("@", 1)[-1].split()[0].strip(".,;")
        if 20 <= len(maybe_addr) <= 128:
            address = maybe_addr
            confidence = max(confidence, 0.45)
            notes.append("Heuristic address extraction")

    if source == "ocr" and amount and address:
        confidence = max(confidence, 0.75)
        notes.append("OCR receipt fields matched address and amount")

    if not notes:
        notes.append("Low-confidence parse; manual review required")

    return PaymentTextParseResult(
        detected_network=network,
        address=address,
        amount=amount,
        currency=currency,
        label=label,
        confidence=min(confidence, 0.95),
        parse_notes=notes,
    )
