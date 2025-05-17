"""
Tema galerisi arayüzü
"""
from PyQt5.QtWidgets import QScrollArea, QWidget, QGridLayout, QPushButton

class ThemeGallery(QScrollArea):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.init_ui()

    def init_ui(self):
        container = QWidget()
        self.layout = QGridLayout(container)
        
        # Temaları galeri olarak göster
        for i, theme_name in enumerate(self.theme_manager.get_theme_list()):
            btn = QPushButton(theme_name.capitalize())
            btn.setStyleSheet(self.get_theme_style(theme_name))
            btn.clicked.connect(lambda _, t=theme_name: self.apply_theme(t))
            self.layout.addWidget(btn, i//3, i%3)
        
        self.setWidget(container)

    def get_theme_style(self, theme_name):
        colors = self.theme_manager.get_theme_colors(theme_name)
        return f"background: {colors['primary']}; color: {colors['text_primary']};"

    def apply_theme(self, theme_name):
        self.theme_manager.apply_theme(theme_name)
