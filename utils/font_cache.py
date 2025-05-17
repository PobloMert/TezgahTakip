"""
Font önbellek yönetimi
"""

from PyQt5.QtGui import QFont
from PyQt5.QtCore import QObject, pyqtSignal

class FontCache(QObject):
    def __init__(self):
        super().__init__()
        self._cache = {}
    
    def get_font(self, key, default_font):
        """Önbellekten font al veya yeni oluştur"""
        if key not in self._cache:
            self._cache[key] = default_font
        return self._cache[key]
    
    def update_font(self, key, font):
        """Önbellekteki fontu güncelle"""
        self._cache[key] = font
    
    def clear_cache(self):
        """Önbelleği temizle"""
        self._cache.clear()
