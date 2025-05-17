"""
Font değiştirme menüsü
"""

from PyQt5.QtWidgets import QMenu, QAction, QFontDialog, QDialog
from PyQt5.QtGui import QFont
from utils.font_manager import FontManager
from ui.font_scale_dialog import FontScaleDialog

class FontMenu:
    def __init__(self, parent=None):
        self.parent = parent
        self.font_manager = FontManager()
        self.menu = QMenu("Yazı Tipi", parent)
        
        # Font değiştirme actionları
        self.select_font_action = QAction("Yazı Tipi Seç...", self.menu)
        self.select_font_action.triggered.connect(self.show_font_dialog)
        
        # Font ölçeklendirme action
        self.scale_font_action = QAction("Font Boyutunu Ayarla...", self.menu)
        self.scale_font_action.triggered.connect(self.show_scale_dialog)
        
        # Menüye actionları ekle
        self.menu.addAction(self.select_font_action)
        self.menu.addAction(self.scale_font_action)
    
    def show_font_dialog(self):
        """Font seçim dialogunu göster"""
        current_font = self.font_manager.get_font()
        font, ok = QFontDialog.getFont(current_font, self.parent, "Yazı Tipi Seç")
        
        if ok:
            # Yeni font ayarlarını kaydet
            self.font_manager.set_font(
                family=font.family(),
                size=font.pointSize(),
                bold=font.bold(),
                italic=font.italic()
            )
            
            # Uygulamaya yeni fontu uygula
            self.parent.setFont(font)
    
    def show_scale_dialog(self):
        """Font ölçeklendirme dialogunu göster"""
        dialog = FontScaleDialog(self.font_manager, self.parent)
        if dialog.exec_() == QDialog.Accepted:
            # Font değişikliğini ana pencereye uygula
            self.parent.setFont(self.font_manager.get_font())
    
    def get_menu(self):
        """Menüyü döndür"""
        return self.menu
    
    def get_font_manager(self):
        """Font yöneticisini döndür"""
        return self.font_manager
