"""
Tema değiştirme menüsü
"""

from PyQt5.QtWidgets import QMenu, QAction, QActionGroup
from PyQt5.QtGui import QIcon
from utils.theme_manager import ThemeManager
from ui.theme_preview import ThemePreviewDialog
from ui.styles import apply_theme

class ThemeMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__('&Tema', parent)
        self.parent = parent
        self.theme_manager = ThemeManager()
        self.theme_group = QActionGroup(self)
        
        themes = [
            ('Koyu Tema', 'dark', 'icons/dark_theme.png'),
            ('Açık Tema', 'light', 'icons/light_theme.png'),
            ('Mavi Tema', 'blue', 'icons/blue_theme.png'),
            ('Profesyonel', 'professional', 'icons/pro_theme.png')
        ]
        
        for name, key, icon in themes:
            action = QAction(QIcon(icon), name, self)
            action.setCheckable(True)
            action.triggered.connect(lambda _, k=key: self.change_theme(k))
            self.theme_group.addAction(action)
            self.addAction(action)
        
        # Varsayılan olarak koyu tema seçili
        self.theme_group.actions()[0].setChecked(True)
        self.change_theme(self.theme_manager.current_theme)

    def change_theme(self, theme_name):
        self.theme_manager.apply_theme(theme_name)
        apply_theme(self.parent, theme_name)
        # Menü başlığını güncelle
        self.setTitle(f"Tema ({theme_name.capitalize()} Modu)")

    def preview_theme(self, theme_name):
        """Tema önizleme dialogunu göster"""
        preview_dialog = ThemePreviewDialog(self.theme_manager, self.parent)
        preview_dialog.preview_theme(theme_name)
        preview_dialog.exec_()

    def toggle_follow_system(self, checked):
        """Sistem teması takip ayarını değiştir"""
        self.theme_manager.set_follow_system(checked)
        
        # Diğer tema seçeneklerini devre dışı bırak
        for action in self.actions():
            action.setEnabled(not checked)

    def get_menu(self):
        return self

    def get_theme_manager(self):
        return self.theme_manager
