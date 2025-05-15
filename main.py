import sys
import os
import threading

# Proje dizinini PYTHONPATH'e ekle
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)
import logging
from PyQt5.QtWidgets import QApplication
from src.app import TezgahTakipApp
from database.connection import db_manager
from utils.updater import AutoUpdater

from ui.styles import apply_global_styles

# Uygulama sürüm bilgileri
APP_VERSION = "1.0.0"
GITHUB_USERNAME = "PobloMert"  # GitHub kullanıcı adı
GITHUB_REPO = "TezgahTakip"     # GitHub repo adı

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('tezgah_takip.log'),
            logging.StreamHandler()
        ]
    )

def check_for_updates():
    """
    Arka planda güncelleme kontrolü yapar
    """
    try:
        updater = AutoUpdater(GITHUB_USERNAME, GITHUB_REPO, APP_VERSION)
        updater.check_for_updates()
    except Exception as e:
        logging.error(f"Güncelleme kontrolü sırasında hata: {e}")

def main():
    setup_logging()
    
    # Veritabanı tablolarını oluştur
    db_manager.create_tables()
    
    # Uygulama oluştur
    app = QApplication(sys.argv)
    
    # Global stil ayarlarını uygula
    apply_global_styles(app)
    
    # Ana uygulamayı başlat
    tezgah_app = TezgahTakipApp()
    tezgah_app.show()
    
    # Arka planda güncelleme kontrolü başlat
    # (Ana uygulama açıldıktan sonra)
    update_thread = threading.Thread(target=check_for_updates)
    update_thread.daemon = True
    update_thread.start()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
