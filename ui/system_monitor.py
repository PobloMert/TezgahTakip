"""
Sistem kaynak kullanımını gösteren panel
"""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer
import psutil

class SystemMonitor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        
        self.cpu_label = QLabel()
        self.memory_label = QLabel()
        self.db_label = QLabel()
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Sistem Durumu</b>"))
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.memory_label)
        layout.addWidget(self.db_label)
        self.setLayout(layout)
        
        self.update_stats()
        
    def update_stats(self):
        """Sistem istatistiklerini güncelle"""
        # CPU ve RAM kullanımı
        self.cpu_label.setText(f"CPU: {psutil.cpu_percent()}%")
        self.memory_label.setText(f"RAM: {psutil.virtual_memory().percent}%")
        
        # Veritabanı boyutu
        db_size = "Veritabanı: "
        try:
            size = os.path.getsize('tezgah_takip.db') / (1024*1024)
            db_size += f"{size:.2f} MB"
        except:
            db_size += "-"
        self.db_label.setText(db_size)
        
        # 5 saniye sonra tekrar güncelle
        QTimer.singleShot(5000, self.update_stats)
