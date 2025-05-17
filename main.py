import sys
import os
import threading
import traceback
import logging
from PyQt5.QtWidgets import QApplication, QMenuBar, QAction, QDockWidget, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from src.app import TezgahTakipApp
from database.connection import db_manager
from utils.updater import AutoUpdater
from utils.widget_style import WidgetStyleManager
from ui.theme_menu import ThemeMenu
from ui.font_menu import FontMenu
from ui.styles import apply_global_styles
from ui.widget_style_dialog import WidgetStyleDialog
from utils.data_cache import DataCache
from utils.backup_manager import BackupManager
from utils.data_compression import compress_data, decompress_data
from utils.data_reloader import SmartDataReloader
from ui.recent_actions import RecentActionsPanel
from utils.fuzzy_search import fuzzy_search
from utils.quick_reports import QuickReportGenerator
from ui.system_monitor import SystemMonitor
from ui.error_dialog import ErrorDialog
from utils.logger import setup_logging

# Proje dizinini PYTHONPATH'e ekle
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# Uygulama sürüm bilgileri
APP_VERSION = "1.0.0"
GITHUB_USERNAME = "PobloMert"
GITHUB_REPO = "TezgahTakip"

def check_for_updates():
    try:
        updater = AutoUpdater(GITHUB_USERNAME, GITHUB_REPO, APP_VERSION)
        updater.check_for_updates()
    except Exception as e:
        logging.error(f"Güncelleme hatası: {e}")
        raise

def main():
    try:
        setup_logging()
        logging.info("Uygulama başlatılıyor...")
        
        # Veritabanı ve temel sistemler
        db_manager.create_tables()
        data_cache = DataCache(db_manager)
        data_reloader = SmartDataReloader(cleanup_interval=12)
        
        # Yedekleme
        backup_manager = BackupManager()
        try:
            if backup_manager.create_backup():
                logging.info("Otomatik yedek oluşturuldu")
            else:
                logging.warning("Yedekleme başarısız oldu")
        except Exception as e:
            logging.error(f"Yedekleme hatası: {str(e)}")
        
        # Uygulama başlat
        app = QApplication(sys.argv)
        apply_global_styles(app)
        tezgah_app = TezgahTakipApp(db_manager)
        
        # Sistem izleme
        system_monitor = SystemMonitor()
        tezgah_app.statusBar().addPermanentWidget(system_monitor)
        
        # Uygulamayı başlat
        tezgah_app.show()
        threading.Thread(target=check_for_updates, daemon=True).start()
        sys.exit(app.exec_())
        
    except Exception as e:
        logging.critical(f"Kritik başlatma hatası: {str(e)}", exc_info=True)
        ErrorDialog(
            "Kritik Hata",
            "Uygulama başlatılırken beklenmeyen bir hata oluştu.\n\n"
            "Lütfen teknik destek ile iletişime geçin.",
            f"Hata Detayı: {str(e)}\n\n{traceback.format_exc()}"
        ).exec_()
        sys.exit(1)

if __name__ == '__main__':
    main()
