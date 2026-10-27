#!/usr/bin/env python3
"""
Генерация тестовых изображений для распознавания WeVisOne-VL.
Создаёт 20+ изображений с документами на всех 5 языках (EN, RU, UK, DE, zh-Hant).
Результаты сохраняются в JSON.
"""

import json
import os
import random
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Пути к шрифтам (используем системные или fallback)
FONT_EN = r"C:/Windows/Fonts/calibri.ttf"
FONT_RU = r"C:/Windows/Fonts/times.ttf"
FONT_UK = FONT_EN  # UK использует тот же шрифт, что и EN
FONT_DE = FONT_EN
FONT_ZH = r"C:/Windows/Fonts/msyh.ttc"

# Языковые настройки
LANGUAGES = {
    "en": {"name": "English", "font": FONT_EN, "currency": "ACP"},
    "ru": {"name": "Русский", "font": FONT_RU, "currency": "ACP"},
    "uk": {"name": "Українська", "font": FONT_UK, "currency": "ACP"},
    "de": {"name": "Deutsch", "font": FONT_DE, "currency": "ACP"},
    "zh-Hant": {"name": "繁體中文", "font": FONT_ZH, "currency": "ACP"},
}

# Адреса для каждого языка (используем реальные форматы)
ADDRESSES = {
    "en": "123 Main St, Springfield, IL 62704, USA",
    "ru": "ул. Ленина, д. 10, г. Москва, 101000, Россия",
    "uk": "вул. Хрещатик, 24, м. Київ, 01001, Україна",
    "de": "Hauptstraße 42, 10115 Berlin, Deutschland",
    "zh-Hant": "台北市中正區中山南路 22 號，台灣",
}

# Суммы для тестирования
AMOUNTS = [
    "12.50 ACP",
    "25.75 ACP",
    "50.00 ACP",
    "100.25 ACP",
    "1000.00 ACP",
]

def create_invoice_image(lang: str, idx: int) -> Image.Image:
    """Создаёт изображение счёта-фактуры на указанном языке."""
    width, height = 1800, 550
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Заголовок
    font_size = 48 if lang == "zh-Hant" else 36
    header_font = ImageFont.truetype(LANGUAGES[lang]["font"], font_size)
    
    title = f"Invoice #{idx:04d}" if lang != "zh-Hant" else f"發票編號 #{idx:04d}"
    draw.text((50, 30), title, fill="black", font=header_font)

    # Информация о продавце
    seller_info = [
        "Seller:",
        "ANCAP Services Ltd.",
        "info@ancap.cloud"
    ]
    if lang == "ru":
        seller_info = ["Продавец:", "ANCAP Services Ltd.", "info@ancap.cloud"]
    elif lang == "uk":
        seller_info = ["Відправник:", "ANCAP Services Ltd.", "info@ancap.cloud"]
    elif lang == "de":
        seller_info = ["Verkäufer:", "ANCAP Services Ltd.", "info@ancap.cloud"]

    y_pos = 100
    for line in seller_info:
        draw.text((50, y_pos), line, fill="black", font=header_font)
        y_pos += 40

    # Информация о покупателе (адрес)
    buyer_info = [
        "Bill To:",
        ADDRESSES[lang]
    ]
    if lang == "ru":
        buyer_info = ["К оплате:", ADDRESSES[lang]]
    elif lang == "uk":
        buyer_info = ["Оплата від:", ADDRESSES[lang]]
    elif lang == "de":
        buyer_info = ["Rechnung an:", ADDRESSES[lang]]

    y_pos += 60
    for line in buyer_info:
        draw.text((50, y_pos), line, fill="black", font=header_font)
        y_pos += 40

    # Сумма
    amount = random.choice(AMOUNTS)
    total_text = f"Total Amount: {amount}" if lang != "zh-Hant" else f"總金額：{amount}"
    draw.text((50, y_pos), total_text, fill="black", font=header_font)

    # Таблица позиций
    items = [
        ("Service Fee", 10.00),
        ("Consultation", 25.00),
        ("API Access", 15.00),
    ]
    
    y_pos += 60
    for i, (item_name, price) in enumerate(items):
        name_text = f"Item {i+1}: {item_name}" if lang != "zh-Hant" else f"項目{i+1}：{item_name}"
        draw.text((50, y_pos), name_text, fill="black", font=header_font)
        draw.text((width - 200, y_pos), f"{price:.2f} ACP", fill="black", font=header_font)
        y_pos += 40

    # Footer
    footer = "Thank you for your business!" if lang != "zh-Hant" else "感謝您的惠顧！"
    draw.text((width // 2 - 150, y_pos), footer, fill="gray", font=header_font)

    return img

def main():
    """Генерирует тестовые изображения и сохраняет результаты в JSON."""
    output_dir = "C:/Users/drago/Desktop/ANCAP/evidence"
    os.makedirs(output_dir, exist_ok=True)

    results = []
    
    # Генерируем по 5 изображений на каждый язык (всего 25)
    for lang_code in LANGUAGES.keys():
        for idx in range(1, 6):
            img = create_invoice_image(lang_code, idx)
            
            filename = f"invoice_{lang_code}_{idx:04d}.png"
            filepath = os.path.join(output_dir, filename)
            img.save(filepath)
            
            result = {
                "language": lang_code,
                "filename": filename,
                "filepath": filepath,
                "address": ADDRESSES[lang_code],
                "amount": random.choice(AMOUNTS),
                "created_at": datetime.now().isoformat(),
                "status": "generated"
            }
            results.append(result)

    # Сохраняем результаты в JSON
    json_path = os.path.join(output_dir, "wevisone-test-invoices.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(results)} test invoice images.")
    print(f"Results saved to: {json_path}")
    print("\nFiles created:")
    for r in results:
        print(f"  - {r['filename']}")

if __name__ == "__main__":
    main()
