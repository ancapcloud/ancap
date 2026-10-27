#!/usr/bin/env python3
"""Тест распознавания zh-Hant через API."""
import io
from PIL import Image, ImageDraw, ImageFont
import httpx
import secrets

FONT_ZH = r'C:/Windows/Fonts/msyh.ttc'
ADDRESS = 'acp1qxfgyw9ysk99qsd79yxdfe338yd85vrqnp9'
font = ImageFont.truetype(FONT_ZH, 48)
image = Image.new('RGB', (1800, 550), 'white')
draw = ImageDraw.Draw(image)
draw.text((30, 30), '發票 #LOCAL-1', fill='black', font=font)
draw.text((30, 155), f'收款地址：{ADDRESS}', fill='black', font=font)
draw.text((30, 280), '應付總額：12.50 ACP', fill='black', font=font)
draw.text((30, 405), '網路：acp', fill='black', font=font)

buffer = io.BytesIO()
image.save(buffer, format='PNG')
data = buffer.getvalue()

with httpx.Client(base_url='http://localhost:8001', timeout=90) as client:
    response = client.post('/v1/auth/users', json={
        'email': f'ocr-test-{secrets.token_hex(6)}@example.com',
        'password': secrets.token_urlsafe(24),
        'display_name': 'OCR Test',
    })
    response.raise_for_status()
    client.headers['Authorization'] = 'Bearer ' + response.json()['access_token']

response = client.post('/v1/payment-scanner/parse-image', files={'file': ('invoice.png', data, 'image/png')})
print(response.json())
