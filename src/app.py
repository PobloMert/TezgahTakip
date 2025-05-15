import sys
import os

# Proje dizinini PYTHONPATH'e ekle
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
import logging
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from ui.maintenance_tab import MaintenanceTab
from ui.battery_tab import BatteryTab
from ui.dashboard_tab import DashboardTab
from ui.reports_tab import ReportsTab
from utils.updater import AutoUpdater

class TezgahTakipApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tezgah Takip Programı")
        self.resize(1024, 768)

        # Tab widget oluştur
        self.tab_widget = QTabWidget()
        
        # Tab'ları ekle
        self.maintenance_tab = MaintenanceTab()
        self.battery_tab = BatteryTab()
        self.dashboard_tab = DashboardTab()
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
            github_username="kullanici_adi",
            repo_name="TezgahTakipQt",
            current_version="1.0.0"
        )
        self.updater.check_for_updates()
        
    def on_tab_changed(self, index):
        """Sekmeler arasında geçiş yapıldığında çağrılır"""
        # Tüm sekmelere deaktif olduklarını bildir
        all_tabs = [self.maintenance_tab, self.battery_tab, self.dashboard_tab, self.reports_tab]
        
        for i, tab in enumerate(all_tabs):
            if hasattr(tab, 'set_active_status'):
                # True/False durumunu yeni sekmenin indeks numarasına göre ayarla
                tab.set_active_status(i == index)
