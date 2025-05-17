from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import pyqtSignal

class SettingsDialog(QDialog):
    theme_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Ayarlar')
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Tema Seçimi
        theme_layout = QHBoxLayout()
        theme_label = QLabel('Tema:')
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Açık', 'Karanlık', 'Sistem'])
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        
        # Canlı Grafik Ayarları
        graph_layout = QHBoxLayout()
        graph_label = QLabel('Grafik Yenileme:')
        self.graph_combo = QComboBox()
        self.graph_combo.addItems(['1 sn', '5 sn', '10 sn', '30 sn'])
        graph_layout.addWidget(graph_label)
        graph_layout.addWidget(self.graph_combo)
        
        # Kaydet Butonu
        save_btn = QPushButton('Ayarları Kaydet')
        save_btn.clicked.connect(self.save_settings)
        
        layout.addLayout(theme_layout)
        layout.addLayout(graph_layout)
        layout.addWidget(save_btn)
        self.setLayout(layout)
    
    def save_settings(self):
        """Seçilen ayarları kaydeder"""
        theme = self.theme_combo.currentText().lower()
        self.theme_changed.emit(theme)
        self.close()
