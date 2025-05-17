import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel, QPushButton, QTableView
from PyQt5.QtCore import QTimer
import logging
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel, QPushButton, QTableView
from ui.maintenance_tab import MaintenanceTab
from ui.battery_tab import BatteryTab
from ui.dashboard_tab import DashboardTab
from ui.reports_tab import ReportsTab
from utils.updater import AutoUpdater
from ui.styles import apply_theme

class TezgahTakipApp(QMainWindow):
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.setWindowTitle("Tezgah Takip Programı")
        self.resize(1024, 768)

        # Tab widget oluştur
        self.tab_widget = QTabWidget()
        
        # Tab'ları ekle
        self.maintenance_tab = MaintenanceTab()
        self.battery_tab = BatteryTab()
        self.dashboard_tab = DashboardTab(db_manager)  # db_manager eklendi
        self.reports_tab = ReportsTab()

        self.tab_widget.addTab(self.maintenance_tab, "Bakım Defteri")
        self.tab_widget.addTab(self.battery_tab, "Pil Takibi")
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        self.tab_widget.addTab(self.reports_tab, "Raporlar")

        # Ana pencereye tab widget'ı yerleştir
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)
        
        self.setCentralWidget(central_widget)
        
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

    def on_tab_changed(self, index):
        """Sekmeler arasında geçiş yapıldığında çağrılır"""
        # Tüm sekmelere deaktif olduklarını bildir
        all_tabs = [self.maintenance_tab, self.battery_tab, self.dashboard_tab, self.reports_tab]
        
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

# Uygulama başlat
if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app, 'dark')  # Modern dark tema
    window = TezgahTakipApp()
    window.show()
    sys.exit(app.exec_())
