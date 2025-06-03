import sys
import os
import threading
import traceback
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel, QPushButton, QTableView, QMessageBox # QMainWindow, QTabWidget, QVBoxLayout eklendi
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer, QCoreApplication, QObject, pyqtSignal, QThreadPool # QCoreApplication, QObject, pyqtSignal eklendi

# UI Sekmelerini Import Et
from ui.maintenance_tab import MaintenanceTab
from ui.battery_tab import BatteryTab
from ui.dashboard_tab import DashboardTab
from ui.reports_tab import ReportsTab
from ui.settings_tab import SettingsTab # Ayarlar sekmesini import et

# Yardımcı Modülleri Import Et
from database.connection import db_manager
from utils.updater import AutoUpdater, UpdateCheckWorker, UpdateDownloadWorker, WorkerSignals # Updater ilgili sınıflar import edildi
from utils.widget_style import WidgetStyleManager
from ui.theme_menu import ThemeMenu
from ui.font_menu import FontMenu
from ui.styles import apply_global_styles
from ui.widget_style_dialog import WidgetStyleDialog
from utils.data_cache import DataCache
from utils.backup_manager import BackupManager, BackupWorker # BackupManager ve BackupWorker import edildi
from utils.data_compression import compress_data, decompress_data
from utils.data_reloader import SmartDataReloader
from ui.recent_actions import RecentActionsPanel
from utils.fuzzy_search import fuzzy_search
from utils.quick_reports import QuickReportGenerator
from utils.report_generator import ReportGenerator
# from ui.system_monitor import SystemMonitor # Sistem Monitor kaldırıldı
from ui.error_dialog import ErrorDialog
from utils.logger import setup_logging
from utils.settings_manager import settings_manager # settings_manager import edildi
from utils.popup_manager import check_and_show_battery_warnings # Pil değişim uyarıları için import edildi

# Proje dizinini PYTHONPATH'e ekle
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# Uygulama sürüm bilgileri
APP_VERSION = "1.0.1"
GITHUB_USERNAME = "PobloMert"
GITHUB_REPO = "TezgahTakip" # Depo adı düzeltildi

class TezgahTakipApp(QMainWindow):
    def __init__(self, db_manager=None, backup_manager=None, report_generator=None):
        super().__init__()
        self.db_manager = db_manager
        self.backup_manager = backup_manager # BackupManager saklandı
        self.report_generator = report_generator # ReportGenerator saklandı
        self.setWindowTitle("Tezgah Takip Programı")
        self.resize(1024, 768)

        # QThreadPool instance'ı oluştur
        self.threadpool = QThreadPool()
        logging.info("QThreadPool başlatıldı.")

        # Tab widget oluştur
        self.tab_widget = QTabWidget()

        # Tab'ları ekle
        self.maintenance_tab = MaintenanceTab(self)
        self.battery_tab = BatteryTab(self)
        self.dashboard_tab = DashboardTab(db_manager)
        # ReportsTab instance'ını oluştururken ana pencereyi ve saklanan ReportGenerator'ı ilet
        self.reports_tab = ReportsTab(main_window=self, report_generator=self.report_generator) # self.report_generator kullanıldı
        # SettingsTab'a backup_manager'ı geçirin
        self.settings_tab = SettingsTab(parent=self, backup_manager=self.backup_manager, app_manager=None) # Ayarlar sekmesi örneğini oluştur

        self.tab_widget.addTab(self.maintenance_tab, "Bakım Defteri")
        self.tab_widget.addTab(self.battery_tab, "Pil Takibi")
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        self.tab_widget.addTab(self.reports_tab, "Raporlar")
        self.tab_widget.addTab(self.settings_tab, "Ayarlar") # Ayarlar sekmesini ekle

        # Ana pencereye tab widget'ı yerleştir
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

        # Durum çubuğu oluştur
        self.statusBar()

        # Tab değişikliklerini takip et
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Ayarlardan başlangıç sekmesini yükle
        start_tab_key = settings_manager.get_setting('general', 'start_tab', 'dashboard')
        tab_index_map = {
            'maintenance': 0, # Sekme eklenme sırasına göre indeksler
            'battery': 1,
            'dashboard': 2,
            'reports': 3,
            'settings': 4
        }
        initial_tab_index = tab_index_map.get(start_tab_key, 2) # Varsayılan olarak Dashboard (indeks 2)
        self.tab_widget.setCurrentIndex(initial_tab_index)

        # Otomatik güncelleme (Başlangıçta kontrol ayarını kullan)
        # Updater instance'ı oluştur
        self.updater = AutoUpdater(GITHUB_USERNAME, GITHUB_REPO, APP_VERSION, parent=self)

        # Ayarlardan başlangıçta güncelleme kontrolü yapılıp yapılmayacağını kontrol et
        check_on_startup = settings_manager.get_setting('update', 'check_on_startup', True)
        if check_on_startup:
             # Güncelleme kontrolünü gecikmeli olarak başlat
             QTimer.singleShot(1500, self.updater.check_for_updates_async)

        # Otomatik Yedekleme Zamanlayıcısı
        self.auto_backup_timer = QTimer(self)
        self.auto_backup_timer.timeout.connect(self._perform_auto_backup)
        self._start_auto_backup_timer() # Timer'ı ayara göre başlat veya durdur

        # Animasyon için timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animations)
        self.animation_timer.start(30)  # 30ms'de bir animasyon güncelle

    def _start_auto_backup_timer(self):
        # Ayarlardan otomatik yedeklemenin açık olup olmadığını ve sıklığını kontrol et
        auto_backup_enabled = settings_manager.get_setting('backup', 'auto_backup_enabled', True)
        backup_interval_days = settings_manager.get_setting('backup', 'backup_interval_days', 7)

        if auto_backup_enabled and backup_interval_days > 0:
            # Günleri milisaniyeye çevir
            interval_ms = backup_interval_days * 24 * 60 * 60 * 1000
            # Timer zaten aktifse durdurup yeniden başlat
            if self.auto_backup_timer.isActive():
                self.auto_backup_timer.stop()
            self.auto_backup_timer.start(interval_ms)
            logging.info(f"Otomatik yedekleme zamanlayıcısı başlatıldı. Sıklık: {backup_interval_days} gün ({interval_ms} ms)")
        else:
            if self.auto_backup_timer.isActive():
                self.auto_backup_timer.stop()
            logging.info("Otomatik yedekleme devre dışı.")

    def _perform_auto_backup(self):
        logging.info("Otomatik yedekleme tetiklendi...")
        # Yedekleme işlemini ayrı bir thread veya QRunnable içinde yapmak daha iyi performans sağlar
        # Şimdilik doğrudan çağırıyoruz, gerekirse sonra threading eklenebilir.
        if self.backup_manager:
            success = self.backup_manager.create_backup()
            if success:
                logging.info("Otomatik yedekleme başarıyla tamamlandı.")
                # İsteğe bağlı: Kullanıcıya bildirim gösterilebilir
            else:
                logging.warning("Otomatik yedekleme başarısız oldu.")
                # İsteğe bağlı: Kullanıcıya hata bildirimi gösterilebilir
        else:
            logging.error("BackupManager instance'ı mevcut değil, otomatik yedekleme yapılamaz.")

    # Manuel yedekleme fonksiyonu, SettingsTab'daki butona bağlanacak
    def perform_manual_backup(self):
        logging.info("Manuel yedekleme tetiklendi...")
        if self.backup_manager:
            # Yedekleme işlemini ayrı bir worker thread içinde çalıştır
            db_path = settings_manager.get_setting('database', 'path', 'tezgah_takip.db') # Veritabanı yolunu ayardan al
            worker = BackupWorker(self.backup_manager, db_path) # BackupWorker instance'ı oluştur
            worker.signals.result.connect(self._backup_finished)
            worker.signals.error.connect(self._backup_error)
            worker.signals.message.connect(self.statusBar().showMessage)
            
            # Durum çubuğuna başlangıç mesajı gönder
            self.statusBar().showMessage("Manuel yedekleme başlatılıyor...", 0) # 0: Sürekli göster

            # Worker'ı threadpool'a gönder
            self.threadpool.start(worker)

        else:
            logging.error("BackupManager instance'ı mevcut değil, manuel yedekleme yapılamaz.")
            QMessageBox.critical(self, "Yedekleme Hatası", "Yedekleme yöneticisi başlatılamadı.")
            self.statusBar().showMessage("Yedekleme yöneticisi hatası.", 5000) # 5 saniye göster

    # Yedekleme worker tamamlandığında çağrılır
    def _backup_finished(self, success):
        if success:
            logging.info("Manuel yedekleme worker başarıyla tamamlandı.")
            # Başarı mesajı worker'dan geldiği için burada tekrar göstermeye gerek yok
            # QMessageBox.information(self, "Yedekleme Tamamlandı", "Manuel yedekleme başarıyla oluşturuldu.")
        else:
            logging.warning("Manuel yedekleme worker başarısız oldu.")
            # Hata mesajı worker'dan veya _backup_error metodundan gelecek
            # QMessageBox.warning(self, "Yedekleme Hatası", "Manuel yedekleme oluşturulurken bir sorun oluştu.")

        # Durum çubuğunu temizle veya bitiş mesajı göster (message sinyali ile de gelebilir)
        # self.statusBar().clearMessage()

    # Yedekleme worker hata verdiğinde çağrılır
    def _backup_error(self, error_tuple):
        exctype, value, tb = error_tuple
        logging.error(f"Manuel yedekleme worker hatası: {value}", exc_info=(exctype, value, tb))
        QMessageBox.critical(self, "Yedekleme Hatası", f"Manuel yedekleme sırasında bir hata oluştu: {value}")
        # Hata mesajı worker'dan da gelebilir, çakışabilir. Sinyal mantığına göre ayarlanmalı.
        # self.statusBar().showMessage(f"Yedekleme hatası: {value}", 5000)

    def on_tab_changed(self, index):
        """Sekmeler arasında geçiş yapıldığında çağrılır"""
        # Tüm sekmelere deaktif olduklarını bildir
        # Ayarlar sekmesi eklendi
        all_tabs = [self.maintenance_tab, self.battery_tab, self.dashboard_tab, self.reports_tab, self.settings_tab]

        for i, tab in enumerate(all_tabs):
            if hasattr(tab, 'set_active_status'):
                # True/False durumunu yeni sekmenin indeks numarasına göre ayarla
                tab.set_active_status(i == index)

        # Ayarlar sekmesi aktif olduğunda veya başka ayarlar değiştiğinde timer'ı güncelle
        if isinstance(all_tabs[index], SettingsTab):
             logging.info("Ayarlar sekmesine geçildi, otomatik yedekleme timer'ı güncelleniyor.")
             self._start_auto_backup_timer()
        # Başka bir sekmeden Ayarlar sekmesine geçildiğinde de timer güncellenmeli, bu şu anki mantıkta var.

    def update_styles(self, style_manager):
        """Tüm widget'lara yeni stilleri uygula"""
        # Tüm widget'ları tarayarak stillerini güncelle
        for widget in self.findChildren(QWidget):
            widget_type = 'default'

            if isinstance(widget, QLabel):
                widget_type = 'labels'
            elif isinstance(widget, QPushButton):
                widget_type = 'buttons'
            elif isinstance(widget, QTableView):
                widget_type = 'tables'

            style_manager.apply_style(widget, widget_type)

    def update_animations(self):
        """Widget animasyonlarını günceller"""
        for widget in self.findChildren(QWidget):
            if hasattr(widget, 'update_animation'):
                widget.update_animation()

def main():
    try:
        setup_logging()
        logging.info("Uygulama başlatılıyor...")

        # Veritabanı ve temel sistemler
        db_manager.create_tables()
        data_cache = DataCache(db_manager)
        data_reloader = SmartDataReloader(cleanup_interval=12)

        # ReportGenerator instance'ı oluştur
        report_generator = ReportGenerator() # ReportGenerator instance'ı main içinde oluşturuldu

        # Yedekleme Manager instance'ını settings_manager kurulduktan sonra oluştur
        backup_manager = BackupManager() # backup_manager instance'ı artık global olarak oluşturulmuyor, burada oluşturuluyor
        try:
            # Uygulama başlangıcında manuel yedekleme kontrolü kaldırıldı, sadece otomatik ayarı kullanılıyor
            pass # Başlangıç yedekleme kontrolü artık _start_auto_backup_timer içinde dolaylı olarak yapılıyor
        except Exception as e:
            logging.error(f"Yedekleme hatası (başlangıç): {str(e)}")

        # Uygulama başlat
        app = QApplication(sys.argv)
        
        # Ayarlardan tema bilgisini al ve uygula
        theme_name = settings_manager.get_setting('general', 'theme', 'system')
        # Ayarlardan font bilgisini al
        font_family = settings_manager.get_setting('appearance', 'font_family', 'Segoe UI') # Varsayılan font ailesi
        font_size = settings_manager.get_setting('appearance', 'font_size', 9) # Varsayılan font boyutu

        # Global stil ayarlarını uygula (tema ve font dahil)
        apply_global_styles(app, font_family=font_family, font_size=font_size)
        
        # apply_theme fonksiyonu sadece temaya özel renk vb. ayarları uygulamalı
        # apply_global_styles çağrısından sonra çağrılması gerekebilir, mevcut yapıda kontrol edelim.
        # Mevcut main.py kodunda apply_theme çağrısı yok, sadece apply_global_styles var. Bu doğru.

        # TezgahTakipApp instance'ı oluştur ve db_manager, backup_manager ve report_generator'ı geç
        window = TezgahTakipApp(db_manager, backup_manager, report_generator) # report_generator geçildi

        window.show()

        # Pil değişim uyarılarını kontrol et ve göster
        check_and_show_battery_warnings()

        # Uygulama event loop'unu başlat
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

if __name__ == "__main__":
    main()
