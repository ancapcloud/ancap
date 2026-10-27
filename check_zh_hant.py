import httpx
import json
from pathlib import Path

API = "http://localhost:8001"
AUTH = None  # Will be set after auth

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
    AUTH = f"Bearer {token}"
    
    with httpx.Client(base_url=API, timeout=30) as client:
        client.headers["Authorization"] = AUTH
        
        # Read the zh-Hant invoice image
        image_path = Path(".wevisone-smoke\invoice-zh-Hant.png")
        if not image_path.exists():
            print(f"Image not found: {image_path}")
            return
        
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        r = client.post("/v1/payment-scanner/parse-image", files={"file": ("invoice.png", image_data, "image/png")})
        print(f"Status: {r.status_code}")
        response_json = r.json()
        print(f"Response JSON:\n{json.dumps(response_json, ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    main()