import requests
import secrets
import base64

# Получаем токен
auth_resp = requests.post('http://localhost:8001/v1/auth/users', json={
    'email': f'ocr-test-{secrets.token_hex(6)}@example.com',
    'password': secrets.token_urlsafe(24),
    'display_name': 'OCR Test',
})
auth_resp.raise_for_status()
token = auth_resp.json()['access_token']

# Читаем файл и кодируем в base64
with open(r'C:\Users\drago\Desktop\ANCAP\evidence\invoice_zh-Hant_0001.png', 'rb') as f:
    image_data = f.read()

# Создаём multipart body вручную
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body_lines = [
    f'--{boundary}',
    'Content-Disposition: form-data; name="file"; filename="invoice.png"',
    'Content-Type: image/png',
    '',  # пустая строка
    base64.b64encode(image_data).decode('utf-8'),
    f'--{boundary}--',
]
body = '\r\n'.join(body_lines)

headers = {'Authorization': f'Bearer {token}', 'Content-Type': f'multipart/form-data; boundary={boundary}'}
ocr_resp = requests.post('http://localhost:8001/v1/payment-scanner/parse-image', 
                         headers=headers, data=body.encode('utf-8'), timeout=60)
print('Status:', ocr_resp.status_code)
print('Headers:', dict(ocr_resp.headers))
print('Body:', ocr_resp.text[:2000])
