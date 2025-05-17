"""
Widget stil ayarları dialog penceresi
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QSlider, QHBoxLayout, QPushButton,
    QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt

class WidgetStyleDialog(QDialog):
    def __init__(self, style_manager, parent=None):
        super().__init__(parent)
        self.style_manager = style_manager
        self.setWindowTitle("Widget Stil Ayarları")
        self.setFixedSize(400, 300)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Widget grupları
        self.sliders = {}
        group = QGroupBox("Widget Ölçeklendirme")
        form_layout = QFormLayout()
        
        # Her widget türü için slider ekle
        widget_types = {
            'labels': "Etiketler",
            'buttons': "Butonlar",
            'tables': "Tablolar",
            'default': "Diğer"
        }
        
        for key, text in widget_types.items():
            slider = QSlider(Qt.Horizontal)
            slider.setRange(50, 200)
            slider.setValue(int(self.style_manager.get_widget_scale(key) * 100))
            slider.valueChanged.connect(
                lambda value, k=key: self.update_scale_label(k, value)
            )
            
            label = QLabel(f"%{slider.value()}")
            
            form_layout.addRow(f"{text}:", slider)
            form_layout.addRow("Değer:", label)
            
            self.sliders[key] = (slider, label)
        
        group.setLayout(form_layout)
        
        # Butonlar
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Uygula")
        cancel_button = QPushButton("Vazgeç")
        
        apply_button.clicked.connect(self.apply_styles)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        
        # Ana layout
        layout.addWidget(group)
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def update_scale_label(self, widget_type, value):
        _, label = self.sliders[widget_type]
        label.setText(f"%{value}")
    
    def apply_styles(self):
        """Tüm widget stillerini uygula"""
        for widget_type, (slider, _) in self.sliders.items():
            scale = slider.value() / 100
            self.style_manager.set_widget_scale(widget_type, scale)
        self.accept()
