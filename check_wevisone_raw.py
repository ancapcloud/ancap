import httpx
import json
from pathlib import Path

API = "http://localhost:8001"

def get_token():
    with httpx.Client(base_url=API, timeout=30) as client:
        r = client.post("/v1/auth/users", json={
            "email": f"local-ocr-{__import__('secrets').token_hex(6)}@example.com",
            "password": __import__('secrets').token_urlsafe(24),
            "display_name": "Local OCR acceptance",
        })
        r.raise_for_status()
        return r.json()["access_token"]

def main():
    token = get_token()
    
    with httpx.Client(base_url=API, timeout=30) as client:
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Read all invoice images
        for lang in ["en", "ru", "uk", "de", "zh-Hant"]:
            image_path = Path(f".wevisone-smoke\invoice-{lang}.png")
            if not image_path.exists():
                print(f"Image not found: {image_path}")
                continue
            
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            r = client.post("/v1/payment-scanner/parse-image", files={"file": ("invoice.png", image_data, "image/png")})
            response_json = r.json()
            
            # Write to file for each language
            output_path = Path(f".wevisone-smoke\{lang}_raw_response.json")
            output_path.write_text(json.dumps(response_json, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{lang}: Status {r.status_code}, address={response_json.get('address')}, confidence={response_json.get('confidence')}")

if __name__ == "__main__":
    main()