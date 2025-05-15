"""
Uygulama ikonu oluşturma scripti.
Bu script, uygulama için basit bir ikon oluşturur.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    # 256x256 boyutunda bir görüntü oluştur
    icon_size = 256
    img = Image.new('RGBA', (icon_size, icon_size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Arka plan dairesi çiz (mavi)
    draw.ellipse((16, 16, icon_size-16, icon_size-16), fill=(52, 152, 219))
    
    # İç daire (beyaz)
    draw.ellipse((48, 48, icon_size-48, icon_size-48), fill=(255, 255, 255))
    
    # Tezgah simgesi (basit bir "T" harfi)
    try:
        # Yazı tipi boyutunu ayarla
        font_size = 120
        font = ImageFont.truetype("arial.ttf", font_size)
        
        # Metni merkeze yerleştir
        text = "T"
        text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:4]
        position = ((icon_size - text_width) / 2, (icon_size - text_height) / 2 - 10)
        
        # Metni çiz
        draw.text(position, text, font=font, fill=(41, 128, 185))
    except Exception as e:
        print(f"Yazı tipi yüklenirken hata: {e}")
        # Alternatif olarak basit bir çizim yap
        draw.rectangle((95, 70, 160, 90), fill=(41, 128, 185))
        draw.rectangle((115, 90, 140, 170), fill=(41, 128, 185))
    
    # Kaydedilecek dosya yolunu belirle
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(current_dir, "app_icon.ico")
    png_path = os.path.join(current_dir, "app_icon.png")
    
    # PNG olarak kaydet
    img.save(png_path)
    print(f"PNG ikon kaydedildi: {png_path}")
    
    # ICO olarak kaydet
    try:
        img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        print(f"ICO ikon kaydedildi: {ico_path}")
    except Exception as e:
        print(f"ICO olarak kaydedilirken hata: {e}")
        # Sadece PNG formatında kaydetmek yeterli olabilir
        print("Sadece PNG formatında kaydedildi.")
    
    return ico_path, png_path

if __name__ == "__main__":
    ico_path, png_path = create_app_icon()
    print(f"İkonlar oluşturuldu:\n  ICO: {ico_path}\n  PNG: {png_path}")
