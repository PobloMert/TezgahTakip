from PyQt5.QtWidgets import (QLabel, QVBoxLayout, QWidget, QProgressBar)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QMovie, QFont

class UpdateAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("TezgahTakip - Güncelleme")
        self.setFixedSize(400, 250)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Loading animasyonu
        self.movie = QMovie("ui/assets/update_loading.gif")
        self.loading_label = QLabel()
        self.loading_label.setMovie(self.movie)
        self.loading_label.setAlignment(Qt.AlignCenter)
        
        # İlerleme çubuğu
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Belirsiz mod
        self.progress.setTextVisible(False)
        
        # Durum yazısı
        self.status_label = QLabel("Uygulama güncelleniyor, lütfen bekleyin...")
        self.status_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        self.status_label.setFont(font)
        
        layout.addWidget(self.loading_label)
        layout.addWidget(self.progress)
        layout.addSpacing(15)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def start_animation(self):
        self.movie.start()
        self.show()
        
    def stop_animation(self, message, is_success=True):
        self.movie.stop()
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.status_label.setText(message)
        
        if is_success:
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setStyleSheet("color: red;")
            
        QTimer.singleShot(2000, self.close)
