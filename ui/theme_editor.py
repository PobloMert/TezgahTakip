"""
Tema düzenleme arayüzü
"""
from PyQt5.QtWidgets import QDialog, QColorDialog, QVBoxLayout, QPushButton
from PyQt5.QtGui import QColor

class ThemeEditor(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setWindowTitle("Tema Düzenleyici")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Renk seçim butonları
        self.add_color_btn("Ana Renk", "primary", layout)
        self.add_color_btn("Arka Plan", "background", layout)
        # Diğer renk öğeleri...
        
        save_btn = QPushButton("Temayı Kaydet")
        save_btn.clicked.connect(self.save_theme)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)

    def add_color_btn(self, text, color_key, layout):
        btn = QPushButton(text)
        btn.clicked.connect(lambda: self.pick_color(color_key))
        layout.addWidget(btn)

    def pick_color(self, color_key):
        color = QColorDialog.getColor()
        if color.isValid():
            # Seçilen rengi geçici olarak uygula
            self.theme_manager.current_theme[color_key] = color.name()

    def save_theme(self):
        # Temayı dosyaya kaydet
        self.theme_manager.save_custom_theme()
        self.accept()
