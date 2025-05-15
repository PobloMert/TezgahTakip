"""
Tezgah Takip Uygulamasını EXE formatına dönüştürme scripti.
Bu script PyInstaller kullanarak uygulamayı tek bir EXE dosyasına dönüştürür.
Veritabanı bağlantısı ve diğer sorunlar için iyileştirilmiş sürüm.
"""

import os
import sys
import subprocess
import shutil
import sqlite3
from pathlib import Path

def create_empty_database(db_path):
    """Boş bir veritabanı dosyası oluşturur, temel tabloları içerir."""
    try:
        # Eğer dosya yoksa oluştur
        if not os.path.exists(db_path):
            print(f"Yeni veritabanı oluşturuluyor: {db_path}")
            # SQLite bağlantısı oluştur
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Tezgah tablosunu oluştur
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tezgah (
                id INTEGER PRIMARY KEY,
                numarasi TEXT UNIQUE NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
            ''')
            
            # Bakim tablosunu oluştur
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS bakim (
                id INTEGER PRIMARY KEY,
                tezgah_id INTEGER NOT NULL,
                tarih TEXT NOT NULL,
                bakim_yapan TEXT NOT NULL,
                aciklama TEXT,
                FOREIGN KEY (tezgah_id) REFERENCES tezgah(id) ON DELETE CASCADE
            )
            ''')
            
            # Pil değişim tablosunu oluştur
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS pil_degisim (
                id INTEGER PRIMARY KEY,
                tezgah_id INTEGER NOT NULL,
                eksen TEXT NOT NULL,
                pil_modeli TEXT NOT NULL,
                tarih TEXT NOT NULL,
                bakim_yapan TEXT NOT NULL,
                FOREIGN KEY (tezgah_id) REFERENCES tezgah(id) ON DELETE CASCADE
            )
            ''')
            
            # Değişiklikleri kaydet ve bağlantıyı kapat
            conn.commit()
            conn.close()
            print("Veritabanı tabloları başarıyla oluşturuldu.")
            
            return True
        else:
            print(f"Veritabanı dosyası zaten mevcut: {db_path}")
            return True
    except Exception as e:
        print(f"Veritabanı oluşturma hatası: {e}")
        return False

def create_exe():
    """
    PyInstaller kullanarak EXE oluşturur.
    """
    print("Tezgah Takip uygulaması EXE formatına dönüştürülüyor...")
    
    # Çalışma dizinini belirle
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Veritabanı dosyasını kontrol et/oluştur
    db_path = os.path.join(current_dir, "tezgah_takip.db")
    if not create_empty_database(db_path):
        print("UYARI: Veritabanı oluşturulamadı, EXE oluşturma devam ediyor...")
    
    # İkon dosyası kontrolü
    icon_path = os.path.join(current_dir, "resources", "icons", "app_icon.ico")
    icon_option = f"--icon={icon_path}" if os.path.exists(icon_path) else ""
    
    # Daha önce oluşturulmuş build ve dist klasörlerini temizle
    for folder in ["build", "dist"]:
        folder_path = os.path.join(current_dir, folder)
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path)
                print(f"{folder} klasörü temizlendi.")
            except Exception as e:
                print(f"{folder} klasörü temizlenemedi: {e}")
    
    # PyInstaller komutunu oluştur
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--clean",
        "--name=TezgahTakip",
        "--add-data=tezgah_takip.db;.",
        "--add-data=resources;resources",
        "--collect-all=PyQt5",
        "--hidden-import=PyQt5.QtChart",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.sip",
        "--hidden-import=sqlalchemy.sql.default_comparator",
        "--hidden-import=sqlalchemy.ext.declarative",
        "--hidden-import=sqlalchemy.orm",
        "--hidden-import=sqlalchemy.pool",
        icon_option,
        os.path.join(current_dir, "main.py")
    ]
    
    # hooks klasörü oluştur
    hooks_dir = os.path.join(current_dir, "hooks")
    if not os.path.exists(hooks_dir):
        os.makedirs(hooks_dir)
    
    # PyQt5 hook dosyasını oluştur
    hook_file = os.path.join(hooks_dir, "hook-PyQt5.py")
    with open(hook_file, "w") as f:
        f.write("""
from PyInstaller.utils.hooks import collect_data_files

# PyQt5 veri dosyalarını topla
datas = collect_data_files('PyQt5')

# Qt plugins klasörlerini ekle (platformlar, görüntü formatları, vb.)
hiddenimports = ['PyQt5.QtChart', 'PyQt5.sip', 'PyQt5.QtWidgets']
""")
    
    # SQLAlchemy hook dosyasını oluştur
    hook_file = os.path.join(hooks_dir, "hook-sqlalchemy.py")
    with open(hook_file, "w") as f:
        f.write("""
from PyInstaller.utils.hooks import collect_submodules

# SQLAlchemy modüllerini topla
hiddenimports = collect_submodules('sqlalchemy')
""")
    
    # Komutu çalıştır
    print("Derleme başlıyor...")
    print(f"Komut: {' '.join(cmd)}")
    
    try:
        process = subprocess.run(cmd, check=True)
        print(f"Derleme tamamlandı. Çıkış kodu: {process.returncode}")
        
        # EXE dosyasının yolunu göster
        exe_path = os.path.join(current_dir, "dist", "TezgahTakip.exe")
        if os.path.exists(exe_path):
            print(f"\nEXE dosyası başarıyla oluşturuldu!\nKonum: {exe_path}")
            
            # resources klasörünü kopyala
            resources_dir = os.path.join(current_dir, "resources")
            if os.path.exists(resources_dir):
                dist_resources = os.path.join(current_dir, "dist", "resources")
                if not os.path.exists(dist_resources):
                    shutil.copytree(resources_dir, dist_resources)
                    print("Resources klasörü kopyalandı.")
            
            print("\nEXE dosyası GitHub release sayfasına yüklenmeye hazır.")
        else:
            print("EXE dosyası bulunamadı!")
    except subprocess.CalledProcessError as e:
        print(f"Derleme sırasında hata oluştu: {e}")
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")

if __name__ == "__main__":
    create_exe()
