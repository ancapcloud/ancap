from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import require_auth
from app.schemas.payment_scanner import PaymentScannerParseRequest, PaymentScannerPreview
from app.services.payment_image_parse import parse_payment_image
from app.services.payment_text_parse import parse_payment_text
from app.services.payment_document_parse import MAX_DOCUMENT_BYTES, parse_payment_document
import re

router = APIRouter(prefix="/payment-scanner", tags=["Payment Scanner"])


def _to_preview(parsed) -> PaymentScannerPreview:
    can_pay = bool(parsed.currency == "ACP" and parsed.detected_network == "acp" and parsed.amount and parsed.address and re.fullmatch(r"acp1[a-z0-9]{20,100}", parsed.address))
    recommendations = ["Сверьте получателя, сумму и назначение с оригиналом документа и подтвердите реквизиты у отправителя."]
    if not parsed.address:
        recommendations.append("Платёжный ACP-адрес не найден. Запросите реквизиты у получателя.")
    if not parsed.amount or not parsed.currency:
        recommendations.append("Сумма или валюта не определены. Уточните их до оплаты.")
    if any(note.startswith("Ambiguous") for note in parsed.parse_notes):
        recommendations.append("Найдено несколько сумм, валют или получателей. Черновик ACP не готовится, пока реквизиты не однозначны.")
    if parsed.currency in {"USD", "EUR", "USDT", "USDC", "BNB", "ETH"}:
        recommendations.append(f"{parsed.currency} не является ACP. Конвертация — отдельный маршрут с котировкой и условиями расчёта.")
    if can_pay:
        recommendations.append("Можно подготовить оплату в ACP. Кошелёк покажет комиссию и запросит отдельное подтверждение.")
    else:
        recommendations.append("Прямая оплата в ACP недоступна: нужны ACP-адрес и сумма в ACP. Для банковского/валютного счёта нужен подтверждённый маршрут конвертации.")
    return PaymentScannerPreview(
        detected_network=parsed.detected_network,
        address=parsed.address,
        amount=parsed.amount,
        currency=parsed.currency,
        label=parsed.label,
        confidence=parsed.confidence,
        requires_manual_confirm=True,
        parse_notes=parsed.parse_notes,
        recommendations=recommendations,
        can_pay_acp=can_pay,
    )


@router.post("/parse", response_model=PaymentScannerPreview)
async def parse_payment_request(
    body: PaymentScannerParseRequest,
    _user_id: str = Depends(require_auth),
):
    parsed = parse_payment_text(body.raw_text, source=body.source)
    return _to_preview(parsed)


@router.post("/parse-image", response_model=PaymentScannerPreview)
async def parse_payment_image_request(
    file: UploadFile = File(...),
    _user_id: str = Depends(require_auth),
):
    image_bytes = await file.read(MAX_DOCUMENT_BYTES + 1)
    try:
        parsed = await parse_payment_image(image_bytes=image_bytes, content_type=file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _to_preview(parsed)


@router.post("/parse-document", response_model=PaymentScannerPreview)
async def parse_document_request(file: UploadFile = File(...), _user_id: str = Depends(require_auth)):
    data = await file.read(MAX_DOCUMENT_BYTES + 1)
    try:
        parsed = await parse_payment_document(data, file.filename or "", file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _to_preview(parsed)
