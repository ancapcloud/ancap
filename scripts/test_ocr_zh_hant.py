"""Test OCR on zh-Hant invoice samples."""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-dir", required=True, help="Directory with invoice images")
    parser.add_argument("--output-dir", default="C:/Users/drago/Desktop/ANCAP/results", help="Output directory for results")
    parser.add_argument("--model", default="wevisone-vl", help="OCR model name")
    parser.add_argument("--api", default="http://localhost:8001", help="OCR API endpoint")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_dir = Path(args.image_dir)
    
    # Filter for zh-Hant images
    zh_hant_images = sorted(image_dir.glob("invoice_zh-Hant_*.png"))
    
    if not zh_hant_images:
        print("No zh-Hant invoice images found!")
        raise SystemExit(1)
    
    print(f"Found {len(zh_hant_images)} zh-Hant invoice images")
    
    results = []
    
    with httpx.Client(base_url=args.api, timeout=90) as client:
        # Wait for API to be ready
        for attempt in range(30):
            try:
                response = client.get("/v1/system/health", timeout=3)
                if response.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(2)
        
        # Authenticate with fixed user
        auth_response = client.post("/v1/auth/users", json={
            "email": "ocr-test@example.com",
            "password": "secure_password_123",
            "display_name": "OCR Test User",
        })
        if auth_response.status_code == 200:
            token = auth_response.json().get("access_token")
            client.headers["Authorization"] = f"Bearer {token}"
            print(f"Authenticated with user: ocr-test@example.com")
            print(f"Token expires in: {auth_response.json().get('expires_in')} seconds")
        
        for image_path in zh_hant_images:
            started = time.monotonic()
            
            try:
                with open(image_path, "rb") as f:
                    image_data = f.read()
                
                response = client.post(
                    "/v1/payment-scanner/parse-image",
                    files={"file": ("invoice.png", image_data, "image/png")}
                )
                
                elapsed = time.monotonic() - started
                
                if response.status_code == 200:
                    payload = response.json()
                    result = {
                        "filename": image_path.name,
                        "filepath": str(image_path),
                        "status": "success",
                        "elapsed_seconds": round(elapsed, 2),
                        "preview": payload,
                    }
                else:
                    result = {
                        "filename": image_path.name,
                        "filepath": str(image_path),
                        "status": f"error ({response.status_code})",
                        "elapsed_seconds": round(elapsed, 2),
                        "preview": {"error": response.text[:500]},
                    }
            except Exception as e:
                result = {
                    "filename": image_path.name,
                    "filepath": str(image_path),
                    "status": f"exception: {str(e)}",
                    "elapsed_seconds": 0,
                    "preview": {},
                }
            
            results.append(result)
            
            # Save individual result
            output_file = output_dir / image_path.name
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"Processed {image_path.name}: {result['status']} in {elapsed:.2f}s")
    
    # Save all results
    results_file = output_dir / "zh-hant-ocr-results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    # Summary
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"Summary: {success_count}/{len(results)} images processed successfully")
    
    raise SystemExit(0)


if __name__ == "__main__":
    main()
