import requests
import secrets

# Получаем токен
auth_resp = requests.post('http://localhost:8001/v1/auth/users', json={
    'email': f'ocr-test-{secrets.token_hex(6)}@example.com',
    'password': secrets.token_urlsafe(24),
    'display_name': 'OCR Test',
})
auth_resp.raise_for_status()
token = auth_resp.json()['access_token']

# Читаем новый китайский файл как raw bytes
with open(r'C:\Users\drago\Desktop\ANCAP\evidence\invoice_zh-Hant_0002.png', 'rb') as f:
    image_data = f.read()

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body_lines = [
    f'--{boundary}',
    'Content-Disposition: form-data; name="file"; filename="invoice.png"',
    'Content-Type: image/png',
    '',
    image_data.decode('latin-1'),  # отправляем raw bytes как строку
    f'--{boundary}--',
]
body = '\r\n'.join(body_lines)

headers = {'Authorization': f'Bearer {token}', 'Content-Type': f'multipart/form-data; boundary={boundary}'}
ocr_resp = requests.post('http://localhost:8001/v1/payment-scanner/parse-image', 
                         headers=headers, data=body.encode('latin-1'), timeout=60)
print('zh-Hant 0002 Status:', ocr_resp.status_code)
import json
result = json.loads(ocr_resp.content.decode('utf-8'))
print(json.dumps(result, ensure_ascii=False, indent=2))
