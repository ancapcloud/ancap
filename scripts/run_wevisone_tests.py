#!/usr/bin/env python3
"""Run WeVisOne-VL OCR tests on generated invoice images."""

import json
import sys
import time
from pathlib import Path

import httpx

# Read API key from .env file
def get_api_key():
    env_file = Path(__file__).parent.parent / ".env.wevisone"
    if not env_file.exists():
        print("Error: .env.wevisone not found", file=sys.stderr)
        sys.exit(1)
    with open(env_file, "r") as f:
        for line in f:
            if line.startswith("SMART_PAY_WEVISONE_API_KEY="):
                key = line.split("=", 1)[1].strip()
                return key
    print("Error: SMART_PAY_WEVISONE_API_KEY not found", file=sys.stderr)
    sys.exit(1)

API_KEY = get_api_key()
OCR_URL = "http://127.0.0.1:8097/v1/payment-scanner/parse-image"


def test_image(image_path: str) -> dict:
    """Test OCR on a single image."""
    
    # Wait for API to be ready
    with httpx.Client(base_url=OCR_URL, timeout=30) as client:
        for attempt in range(10):
            try:
                response = client.get("/v1/system/health", timeout=3)
                if response.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(2)
    
    # Authenticate
    auth_response = client.post("/v1/auth/users", json={
        "email": f"local-ocr-{int(time.time())}@example.com",
        "password": "test",
        "display_name": "Local OCR test"
    })
    auth_response.raise_for_status()
    token = auth_response.json().get("access_token")
    client.headers["Authorization"] = f"Bearer {token}"
    
    # Test the image
    try:
        with open(image_path, "rb") as f:
            response = client.post(
                "/v1/payment-scanner/parse-image",
                files={"file": (Path(image_path).name, f, "image/png")}
            )
        response.raise_for_status()
        result = response.json()
        
        # Check for successful recognition
        if all([
            result.get("address") is not None,
            result.get("amount") is not None,
            result.get("currency") is not None,
            result.get("requires_manual_confirm") == True,
            result.get("can_pay_acp") == True
        ]):
            return {
                "status": "success",
                "text": json.dumps(result, ensure_ascii=False),
                "confidence": 1.0
            }
        else:
            return {
                "status": "partial",
                "text": json.dumps(result, ensure_ascii=False),
                "confidence": 0.5,
                "details": result
            }
    except Exception as e:
        return {
            "status": "error",
            "text": str(e),
            "confidence": 0.0,
            "error": str(e)
        }


def main():
    input_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "evidence"
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent.parent / "evidence" / "wevisone-2b-local-2026-10-27.json"
    
    results = {
        "total": 0,
        "success": 0,
        "empty": 0,
        "error": 0,
        "by_language": {},
        "images": []
    }
    
    # Find all invoice images
    images = list(input_dir.glob("invoice_*"))
    images.sort()
    
    print(f"Found {len(images)} images to process")
    
    for image_path in images:
        results["total"] += 1
        
        # Extract language from filename
        name = image_path.stem
        if name.startswith("invoice_"):
            lang = name.replace("invoice_", "")
        else:
            lang = "unknown"
        
        result = test_image(str(image_path))
        result["image"] = image_path.name
        
        results["images"].append(result)
        
        if result["status"] == "success":
            results["success"] += 1
            results["by_language"][lang] = results["by_language"].get(lang, 0) + 1
        elif result["status"] == "empty":
            results["empty"] += 1
            results["by_language"][lang] = results["by_language"].get(lang, 0) + 1
        else:
            results["error"] += 1
        
        print(f"Processed {image_path.name}: {result['status']}")
    
    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print("\nLanguage statistics:")
    for lang, count in sorted(results["by_language"].items()):
        percentage = (count / results["total"]) * 100 if results["total"] > 0 else 0
        print(f"  {lang}: {count}/{results['total']} ({percentage:.1f}%)")


if __name__ == "__main__":
    main()
