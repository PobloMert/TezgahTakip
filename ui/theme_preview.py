"""
Tema önizleme penceresi
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QWidget, QHBoxLayout, QGroupBox
)
from PyQt5.QtCore import Qt

class ThemePreviewDialog(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setWindowTitle("Tema Önizleme")
        self.setMinimumSize(400, 300)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Örnek widget'lar grubu
        sample_group = QGroupBox("Örnek Görünüm")
        sample_layout = QVBoxLayout()
        
        # Örnek widget'lar
        self.sample_label = QLabel("Bu bir örnek etikettir")
        self.sample_button = QPushButton("Örnek Buton")
        self.sample_checkbox = QLabel("☑ Örnek seçim kutusu")
        
        sample_layout.addWidget(self.sample_label)
        sample_layout.addWidget(self.sample_button)
        sample_layout.addWidget(self.sample_checkbox)
        sample_group.setLayout(sample_layout)
        
        # Butonlar
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Uygula")
        self.cancel_button = QPushButton("Vazgeç")
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)
        
        # Ana layout
        layout.addWidget(sample_group)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Bağlantılar
        self.cancel_button.clicked.connect(self.reject)
        
    def preview_theme(self, theme_name):
        """Belirtilen temayı önizleme için uygular"""
        theme = self.theme_manager.get_theme_colors(theme_name)
        
        # Widget stillerini güncelle
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {theme['background']};
                color: {theme['text_primary']};
            }}
            QPushButton {{
                background-color: {theme['primary']};
                color: white;
                padding: 5px;
                border-radius: 4px;
            }}
            QGroupBox {{
                border: 1px solid {theme['border']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }}
            """
        )
