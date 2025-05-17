"""
Son yapılan işlemlerin gösterildiği panel
"""
from PyQt5.QtWidgets import QListWidget
from datetime import datetime

class RecentActionsPanel(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(150)
        self.setStyleSheet("""
            QListWidget {
                font-size: 11px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        
    def add_action(self, action_text):
        """Yeni işlem ekle"""
        self.insertItem(0, f"{datetime.now().strftime('%H:%M')} - {action_text}")
        if self.count() > 10:
            self.takeItem(10)
