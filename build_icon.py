"""
Basit bir ikon dosyası oluşturan script.
"""
from PIL import Image, ImageDraw
import os

# 256x256 boyutunda bir görüntü oluştur
icon_size = 256
img = Image.new('RGBA', (icon_size, icon_size), color=(0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Arka plan dairesi çiz (mavi)
draw.ellipse((16, 16, icon_size-16, icon_size-16), fill=(52, 152, 219))

# İç daire çiz (beyaz)
draw.ellipse((48, 48, icon_size-48, icon_size-48), fill=(255, 255, 255))

# Tezgah sembolü çiz (basit bir şekil)
draw.rectangle((95, 70, 160, 90), fill=(41, 128, 185))  # Üst çubuk
draw.rectangle((115, 90, 140, 170), fill=(41, 128, 185))  # Dikey çubuk

# İkon klasörünü doğrula
icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icons")
if not os.path.exists(icons_dir):
    os.makedirs(icons_dir)

# PNG olarak kaydet
png_path = os.path.join(icons_dir, "app_icon.png")
img.save(png_path)
print(f"PNG ikon kaydedildi: {png_path}")

# ICO olarak kaydet
ico_path = os.path.join(icons_dir, "app_icon.ico")
img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f"ICO ikon kaydedildi: {ico_path}")

print("İkon dosyaları başarıyla oluşturuldu!")
