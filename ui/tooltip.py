from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QFont

class ModernToolTip(QWidget):
    def __init__(self, parent, text):
        super().__init__(parent, Qt.ToolTip)
        self.setWindowFlags(Qt.ToolTip | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        self.label = QLabel(text)
        self.label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 180);
            color: white;
            padding: 5px;
            border-radius: 5px;
        """)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.hide()

    def show_tip(self, pos):
        self.move(pos)
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Arka plan
        painter.setBrush(QColor(0, 0, 0, 180))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

def add_tooltip(widget, text):
    """
    Bir widget'a modern tooltip ekler
    
    Args:
        widget (QWidget): Tooltip eklenecek widget
        text (str): Tooltip metni
    """
    tooltip = ModernToolTip(widget, text)
    
    def enter_event(event):
        pos = widget.mapToGlobal(widget.rect().bottomRight())
        tooltip.show_tip(pos)
    
    def leave_event(event):
        tooltip.hide()
    
    widget.enterEvent = enter_event
    widget.leaveEvent = leave_event
    
    return tooltip
