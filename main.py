import sys
import os
import threading
import traceback
import logging
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMenuBar, QAction, QDockWidget, QMessageBox
from src.app import TezgahTakipApp
from database.connection import DatabaseManager
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
from utils.logger import AppLogger
from ui.theme_loader import load_theme
from utils.performance_monitor import PerformanceMonitor

# Proje dizinini PYTHONPATH'e ekle
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'models'))  # models klasörünü ekle

# Uygulama sürüm bilgileri
APP_VERSION = "1.0.2"
GITHUB_USERNAME = "PobloMert"
GITHUB_REPO = "TezgahTakip"  # Repo adı orijinal haline getirildi

# Uygulama başlatmadan önce DPI ayarları
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

def main():
    try:
        # Logger'ı başlat
        logger = AppLogger().get_logger()
        logger.info("Uygulama başlatılıyor...")
        
        # Veritabanı yöneticisini oluştur
        db_manager = DatabaseManager()
        
        # Uygulamayı başlat
        app = QApplication(sys.argv)
        window = TezgahTakipApp()  # Parametresiz başlat
        window.show()
        sys.exit(app.exec())
        
    except Exception as e:
        logger = AppLogger().get_logger()
        logger.critical(f"Kritik başlatma hatası: {str(e)}", exc_info=True)
        ErrorDialog(
            "Kritik Hata",
            "Uygulama başlatılırken beklenmeyen bir hata oluştu.\n\n"
            "Lütfen teknik destek ile iletişime geçin.",
            f"Hata Detayı: {str(e)}\n\n{traceback.format_exc()}"
        ).exec_()
        sys.exit(1)

if __name__ == '__main__':
    main()
