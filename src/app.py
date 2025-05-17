import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel, QPushButton, QTableView, QMessageBox, QAction, QToolBar, QDockWidget, QGridLayout
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QColor
import logging
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel, QPushButton, QTableView
from ui.maintenance_tab import MaintenanceTab
from ui.battery_tab import BatteryTab
from ui.dashboard_tab import DashboardTab
from ui.error_dialog import ErrorDialog
from ui.system_monitor import SystemMonitor
from utils.updater import AutoUpdater
from ui.styles import apply_theme, apply_tab_styles
from ui.settings_dialog import SettingsDialog
from ui.dashboard_widgets import StatsWidget, DonutChartWidget
from ui.reports_tab import ReportsTab
import threading
from database.connection import DatabaseManager  # Doğru import yolu

class TezgahTakipApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()  # DB bağlantısı eklendi
        self.setWindowTitle("Tezgah Takip Programı")
        self.resize(1024, 768)

        # Sekmeleri oluştur
        self.tab_widget = QTabWidget()
        
        # Bakım Defteri Sekmesi
        self.maintenance_tab = MaintenanceTab()
        self.tab_widget.addTab(self.maintenance_tab, "Bakım Defteri")
        
        # Pil Takip Sekmesi
        self.battery_tab = BatteryTab()
        self.tab_widget.addTab(self.battery_tab, "Pil Takibi")
        
        # Raporlar Sekmesi
        self.reports_tab = ReportsTab()
        self.tab_widget.addTab(self.reports_tab, "Raporlar")
        
        # Dashboard Sekmesi
        self.dashboard_tab = DashboardTab(self.db)  # DB bağlantısı eklendi
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        self.setCentralWidget(self.tab_widget)
        
        # Stilleri uygula
        apply_tab_styles(self.tab_widget)
        
        # Tab değişikliklerini takip et
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Otomatik güncelleme
        self.updater = AutoUpdater(
            github_username="PobloMert",  # Düzeltildi
            repo_name="TezgahTakipQt",
            current_version="1.0.0"
        )
        self.updater.check_for_updates()
        
        # Animasyon için timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animations)
        self.animation_timer.start(30)  # 30ms'de bir animasyon güncelle

        # Tema değişimi sinyali
        self.theme_changed = pyqtSignal(str)
        
        # Ayarlar menüsü
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.theme_changed.connect(self.change_theme)

        self.init_ui()

    def init_ui(self):
        # Güncelleme toolbar'ı oluştur
        update_toolbar = self.addToolBar('Güncellemeler')
        
        # Simge ekle (varsayılan sistem simgesi)
        check_now_action = QAction(QIcon.fromTheme('view-refresh'), 'Güncellemeleri Kontrol Et', self)
        check_now_action.triggered.connect(self.force_update_check)
        
        # Toolbar'a ekle
        update_toolbar.addAction(check_now_action)
        
        # Menüyü de güncelle
        update_menu = self.menuBar().addMenu('&Güncellemeler')
        update_menu.addAction(check_now_action)

    def on_tab_changed(self, index):
        """Sekmeler arasında geçiş yapıldığında çağrılır"""
        # Tüm sekmelere deaktif olduklarını bildir
        all_tabs = [self.maintenance_tab, self.battery_tab, self.reports_tab, self.dashboard_tab]
        
        for i, tab in enumerate(all_tabs):
            if hasattr(tab, 'set_active_status'):
                # True/False durumunu yeni sekmenin indeks numarasına göre ayarla
                tab.set_active_status(i == index)

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

    def show_update_notification(self, version='', changelog=''):
        """Güncelleme bildirimini gösterir"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(f"Yeni Sürüm: {version}" if version else "Yeni Güncelleme")
        
        text = "Yeni bir sürüm mevcut!\n\n"
        if version:
            text += f"Sürüm: {version}\n\n"
        if changelog:
            text += f"Değişiklikler:\n{changelog}\n\n"
        text += "GitHub'dan indirebilirsiniz."
        
        msg.setText(text)
        msg.addButton('Daha Sonra', QMessageBox.RejectRole)
        download_btn = msg.addButton('İndir', QMessageBox.AcceptRole)
        
        if msg.exec_() == QMessageBox.AcceptRole:
            import webbrowser
            webbrowser.open(f"https://github.com/PobloMert/TezgahTakip/releases/latest")

    def force_update_check(self):
        """Manuel güncelleme kontrolü"""
        from utils.updater import AutoUpdater
        from main import GITHUB_USERNAME, GITHUB_REPO, APP_VERSION
        
        updater = AutoUpdater(GITHUB_USERNAME, GITHUB_REPO, APP_VERSION)
        if updater.check_for_updates(force=True):
            self.show_update_notification()
        else:
            QMessageBox.information(self, "Güncelleme", "Uygulama güncel!")

    def change_theme(self, theme_name):
        """Temayı değiştirir"""
        load_theme(QApplication.instance(), theme_name)
        
    def refresh_data(self):
        """Verileri yeniler"""
        try:
            self.update_dashboard()
        except Exception as e:
            logging.error(f"Veri yenileme hatası: {e}")

    def update_dashboard(self):
        """Dashboard verilerini günceller"""
        try:
            # Veritabanından gerçek verileri al
            active_machines = self.db.session.execute(
                "SELECT COUNT(*) FROM tezgahlar WHERE aktif=1"
            ).scalar()
            
            today_maintenance = self.db.session.execute(
                """SELECT COUNT(*) FROM bakim_gecmisi 
                   WHERE DATE(bakim_tarihi) = DATE('now')"""
            ).scalar()
            
            avg_usage = self.db.session.execute(
                "SELECT AVG(kullanım_saati) FROM tezgahlar"
            ).scalar() or 0
            
            # Widget'ları güncelle
            for i, widget in enumerate(self.dashboard_widgets):
                if isinstance(widget, StatsWidget):
                    values = [active_machines, today_maintenance, round(avg_usage, 1)]
                    widget.value_label.setText(str(values[i]))
                    
        except Exception as e:
            logging.error(f"Dashboard güncelleme hatası: {e}")

    def create_dashboard(self):
        """Yeni detaylı dashboard'u oluşturur"""
        dashboard = QWidget()
        layout = QGridLayout()
        
        # İstatistik widget'ları
        layout.addWidget(StatsWidget('Aktif Tezgahlar', 12, 'adet'), 0, 0)
        layout.addWidget(StatsWidget('Bugünkü Bakım', 3, 'adet'), 0, 1)
        layout.addWidget(StatsWidget('Ort. Çalışma Süresi', 8.2, 'saat'), 0, 2)
        
        # Grafik widget'ları
        bakim_data = [
            ('Planlı', 65, QColor('#4CAF50')),
            ('Acil', 15, QColor('#F44336')),
            ('Rutin', 20, QColor('#FFC107'))
        ]
        layout.addWidget(DonutChartWidget('Bakım Dağılımı', bakim_data), 1, 0, 1, 2)
        
        dashboard.setLayout(layout)
        return dashboard

    def load_large_data(self):
        """Büyük veriler için optimizasyon"""
        try:
            # Sayfalı veri yükleme
            self.current_page = 0
            self.page_size = 100
            
            # Verileri arka planda yükle
            self.data_loader_thread = threading.Thread(
                target=self._load_data_in_background,
                daemon=True
            )
            self.data_loader_thread.start()
            
            # Progress bar göster
            self.show_progress("Veriler yükleniyor...")
            
        except Exception as e:
            self.show_error(f"Veri yükleme hatası: {str(e)}")
    
    def _load_data_in_background(self):
        """Arka planda veri yükleme"""
        try:
            data = self.db.execute_query(
                "SELECT * FROM bakimlar LIMIT :limit OFFSET :offset",
                {"limit": self.page_size, "offset": self.current_page * self.page_size}
            )
            
            # UI güncellemesi için sinyal gönder
            self.data_loaded_signal.emit(data)
            
        except Exception as e:
            self.error_occurred_signal.emit(str(e))

# Uygulama başlat
if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app, 'dark')  # Modern dark tema
    window = TezgahTakipApp()
    window.show()
    sys.exit(app.exec_())
