"""
Tema değiştirme menüsü
"""

from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtGui import QIcon
from utils.theme_manager import ThemeManager
from ui.theme_preview import ThemePreviewDialog

class ThemeMenu:
    def __init__(self, parent=None):
        self.parent = parent
        self.theme_manager = ThemeManager()
        self.menu = QMenu("Tema", parent)
        self.actions = {}
        self._populate_menu()
        self.change_theme(self.theme_manager.current_theme)

    def _populate_menu(self):
        self.menu.clear()
        self.actions = {}
        
        # Sistem teması takip seçeneği
        self.follow_system_action = QAction("Sistem Temasını Takip Et", self.menu)
        self.follow_system_action.setCheckable(True)
        self.follow_system_action.triggered.connect(self.toggle_follow_system)
        self.menu.addAction(self.follow_system_action)
        self.menu.addSeparator()
        
        # Tema listesi
        theme_names = self.theme_manager.get_theme_list()
        for theme in theme_names:
            action = QAction(theme.capitalize() + " Modu", self.menu)
            action.setCheckable(True)
            
            # Sağ tık menüsü ekle
            action.setMenu(QMenu())
            preview_action = QAction("Önizleme", action.menu())
            preview_action.triggered.connect(lambda: self.preview_theme(theme))
            apply_action = QAction("Uygula", action.menu())
            apply_action.triggered.connect(lambda: self.change_theme(theme))
            
            action.menu().addAction(preview_action)
            action.menu().addAction(apply_action)
            
            self.menu.addAction(action)
            self.actions[theme] = action

    def change_theme(self, theme_name):
        self.theme_manager.apply_theme(theme_name)
        # Action durumlarını güncelle
        for t, action in self.actions.items():
            action.setChecked(t == theme_name)
        # Menü başlığını güncelle
        self.menu.setTitle(f"Tema ({theme_name.capitalize()} Modu)")

    def preview_theme(self, theme_name):
        """Tema önizleme dialogunu göster"""
        preview_dialog = ThemePreviewDialog(self.theme_manager, self.parent)
        preview_dialog.preview_theme(theme_name)
        preview_dialog.exec_()

    def toggle_follow_system(self, checked):
        """Sistem teması takip ayarını değiştir"""
        self.theme_manager.set_follow_system(checked)
        
        # Diğer tema seçeneklerini devre dışı bırak
        for action in self.actions.values():
            action.setEnabled(not checked)

    def get_menu(self):
        return self.menu

    def get_theme_manager(self):
        return self.theme_manager
