#!/usr/bin/env python3
"""
Генерация тестовых изображений для zh-Hant (традиционный китайский)
Создаёт синтетические чеки с разными форматами документов.
"""

import os
import sys
from pathlib import Path

# Путь к проекту
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image, ImageDraw, ImageFont
import random

def create_zh_hant_invoice(output_dir: Path, count: int = 5):
    """Создаёт тестовые чеки на традиционном китайском."""
    
    # Путь к шрифту для традиционного китайского
    FONT_PATHS = [
        r"C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei (поддерживает TC)
        r"C:/Windows/Fonts/simhei.ttf",  # SimHei (упрощённый, но может работать)
    ]
    
    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(count):
        filename = f"zh-hant-test-{i+1:03d}.png"
        filepath = output_dir / filename
        
        # Создаём изображение 1800×550
        img = Image.new('RGB', (1800, 550), color='white')
        draw = ImageDraw.Draw(img)
        
        # Заголовок чека
        draw.text((50, 30), "收據", fill='black')
        
        # Дата
        date_str = f"2026-10-{(i % 28) + 1:02d}"
        draw.text((50, 70), f"日期：{date_str}", fill='black')
        
        # Товар/услуга (традиционный китайский)
        items = [
            "智慧支付服務",
            "AI 工作流執行",
            "數據分析報告",
            "雲端存儲空間",
        ]
        item = items[i % len(items)]
        
        # Цена в ACP
        price = random.randint(100, 5000)
        
        draw.text((50, 120), f"項目：{item}", fill='black')
        draw.text((50, 160), f"數量：1", fill='black')
        draw.text((50, 200), f"單價：{price} ACP", fill='black')
        
        # Итого
        total = price
        draw.text((50, 240), f"總計：{total} ACP", fill='black', font_size=24)
        
        # Checksum (упрощённый для теста)
        checksum = f"CHK-{i+1:03d}-ZHANT"
        draw.text((50, 290), f"校驗碼：{checksum}", fill='black')
        
        # Подпись
        draw.text((50, 340), "簽名：________________", fill='gray')
        
        # Сохраняем
        img.save(filepath)
        print(f"Created: {filepath}")
    
    return len(list(output_dir.glob("*.png")))

if __name__ == "__main__":
    output_dir = PROJECT_ROOT / "evidence" / "zh-hant-test-invoices-20261028"
    count = 5
    
    print(f"Generating zh-Hant test invoices ({count})...")
    created = create_zh_hant_invoice(output_dir, count)
    print(f"Created: {created} images in {output_dir}")
