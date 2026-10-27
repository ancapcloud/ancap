from PIL import ImageFont

for font_path in ['C:/Windows/Fonts/mingliub.ttc', 'C:/Windows/Fonts/simsun.ttc']:
    try:
        f = ImageFont.truetype(font_path, 48)
        print(f'{font_path} OK')
    except Exception as e:
        print(f'{font_path} FAILED: {e}')
