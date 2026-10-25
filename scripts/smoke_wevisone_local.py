"""Real GPU acceptance through Smart Pay API; synthetic invoices, no payments sent."""
from __future__ import annotations
import argparse
import io
import json
import secrets
import time
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

ADDRESS = "acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9"
CASES = {
    "en": ("INVOICE #LOCAL-1", "Pay to", "Total due", "Network"),
    "ru": ("СЧЁТ #LOCAL-1", "Получатель", "К оплате", "Сеть"),
    "uk": ("РАХУНОК #LOCAL-1", "Отримувач", "До сплати", "Мережа"),
    "de": ("RECHNUNG #LOCAL-1", "Empfänger", "Gesamtbetrag", "Netzwerk"),
    "zh-Hant": ("發票 #LOCAL-1", "收款地址", "應付總額", "網路"),
}


def invoice(language: str, font_path: str) -> bytes:
    title, payee, total, network = CASES[language]
    font = ImageFont.truetype(font_path, 48)
    image = Image.new("RGB", (1800, 550), "white")
    draw = ImageDraw.Draw(image)
    for index, line in enumerate((title, f"{payee}: {ADDRESS}", f"{total}: 12.50 ACP", f"{network}: acp")):
        draw.text((30, 30 + index * 125), line, fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://localhost:8001")
    parser.add_argument("--font", required=True, help="Unicode font covering Cyrillic and Traditional Chinese")
    parser.add_argument("--output", default=".wevisone-smoke")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    with httpx.Client(base_url=args.api, timeout=90) as client:
        response = client.post("/v1/auth/users", json={
            "email": f"local-ocr-{secrets.token_hex(6)}@example.com",
            "password": secrets.token_urlsafe(24), "display_name": "Local OCR acceptance",
        })
        response.raise_for_status()
        client.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        for language in CASES:
            data = invoice(language, args.font)
            (out / f"invoice-{language}.png").write_bytes(data)
            started = time.monotonic()
            response = client.post("/v1/payment-scanner/parse-image", files={"file": ("invoice.png", data, "image/png")})
            payload = response.json()
            passed = response.status_code == 200 and all((
                payload.get("address") == ADDRESS, payload.get("amount") == "12.5",
                payload.get("currency") == "ACP", payload.get("requires_manual_confirm") is True,
                payload.get("can_pay_acp") is True,
            ))
            results.append({"language": language, "passed": passed,
                            "seconds": round(time.monotonic() - started, 2), "status": response.status_code,
                            "preview": payload})
            (out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(results[-1], ensure_ascii=True), flush=True)
    (out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if all(item["passed"] for item in results) else 1)


if __name__ == "__main__":
    main()
