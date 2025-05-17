"""
İşletim sistemi tema algılama modülü
"""
import darkdetect
from PyQt5.QtCore import QObject, pyqtSignal

class SystemThemeDetector(QObject):
    theme_changed = pyqtSignal(str)  # 'light' veya 'dark'
    
    def __init__(self):
        super().__init__()
        self._current_theme = self.get_system_theme()
    
    def get_system_theme(self):
        """Sistem temasını algılar"""
        try:
            return darkdetect.theme().lower()
        except:
            return 'light'
    
    def check_theme_change(self):
        """Sistem teması değişti mi kontrol eder"""
        new_theme = self.get_system_theme()
        if new_theme != self._current_theme:
            self._current_theme = new_theme
            self.theme_changed.emit(new_theme)
