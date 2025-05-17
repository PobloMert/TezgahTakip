"""
Font ölçeklendirme dialog penceresi
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QSlider, QHBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt

class FontScaleDialog(QDialog):
    def __init__(self, font_manager, parent=None):
        super().__init__(parent)
        self.font_manager = font_manager
        self.setWindowTitle("Font Boyutunu Ayarla")
        self.setFixedSize(300, 150)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Başlık
        title = QLabel("Font Ölçeklendirme:")
        title.setAlignment(Qt.AlignCenter)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(50, 200)  # %50-%200 arası
        self.slider.setValue(int(self.font_manager.get_font_scale() * 100))
        self.slider.valueChanged.connect(self.update_scale_label)
        
        # Değer göstergesi
        self.scale_label = QLabel(f"%{self.slider.value()}")
        self.scale_label.setAlignment(Qt.AlignCenter)
        
        # Butonlar
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Uygula")
        cancel_button = QPushButton("Vazgeç")
        
        apply_button.clicked.connect(self.apply_scale)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        
        # Ana layout
        layout.addWidget(title)
        layout.addWidget(self.slider)
        layout.addWidget(self.scale_label)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def update_scale_label(self, value):
        self.scale_label.setText(f"%{value}")
    
    def apply_scale(self):
        scale_factor = self.slider.value() / 100
        self.font_manager.set_font_scale(scale_factor)
        self.accept()
