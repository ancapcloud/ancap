"""Тест WeVisOne на реальных изображениях."""
import json
import httpx
import secrets
from pathlib import Path

API_URL = "http://localhost:8001"
EVIDENCE_DIR = Path("C:/Users/drago/Desktop/ANCAP/evidence")

def main():
    client = httpx.Client(base_url=API_URL, timeout=90)
    
    # Получаем токен
    r = client.post("/v1/auth/users", json={
        "email": f"test-{secrets.token_hex(6)}@example.com",
        "password": secrets.token_urlsafe(24),
        "display_name": "Test Real Images"
    })
    token = r.json()["access_token"]
    client.headers["Authorization"] = "Bearer " + token
    
    languages = ["en", "ru", "uk", "de", "zh-Hant"]
    results = []
    
    for lang in languages:
        img_path = EVIDENCE_DIR / f"invoice_{lang}_0001.png"
        if not img_path.exists():
            print(f"{lang}: изображение не найдено")
            continue
        
        with open(img_path, "rb") as f:
            r = client.post("/v1/payment-scanner/parse-image", files={
                "file": ("invoice.png", f, "image/png")
            })
        
        result = {
            "language": lang,
            "status": r.status_code,
            "address": r.json().get("address", "N/A"),
            "amount": r.json().get("amount", "N/A"),
            "currency": r.json().get("currency", "N/A"),
        }
        results.append(result)
    
    # Сохраняем результаты
    output = Path("C:/Users/drago/Desktop/ANCAP/evidence/wevisone-real-images-test.json")
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    
    return results

if __name__ == "__main__":
    main()
