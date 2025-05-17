"""
Widget özel stil ayarları
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, pyqtSignal

class WidgetStyleManager(QObject):
    style_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._widget_scales = {
            'default': 1.0,
            'labels': 1.0,
            'buttons': 1.0,
            'tables': 1.0
        }
    
    def set_widget_scale(self, widget_type, scale):
        """Belirli widget türü için ölçek ayarla"""
        if widget_type in self._widget_scales:
            self._widget_scales[widget_type] = max(0.5, min(2.0, scale))
            self.style_changed.emit()
    
    def get_widget_scale(self, widget_type):
        """Widget türü için ölçek değerini döndür"""
        return self._widget_scales.get(widget_type, 1.0)
    
    def apply_style(self, widget, widget_type='default'):
        """Widget'a özel stil uygula"""
        scale = self.get_widget_scale(widget_type)
        font = widget.font()
        font.setPointSize(int(font.pointSize() * scale))
        widget.setFont(font)
