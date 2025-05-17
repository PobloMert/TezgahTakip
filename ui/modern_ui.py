from PyQt5.QtCore import QUrl
from PyQt5.QtQuick import QQuickView
from PyQt5.QtWidgets import QWidget, QVBoxLayout

class ModernDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QQuickView()
        self.view.setSource(QUrl.fromLocalFile('ui/dashboard.qml'))
        
        container = QWidget.createWindowContainer(self.view, self)
        layout = QVBoxLayout()
        layout.addWidget(container)
        self.setLayout(layout)
        
        # Karanlık/Açık tema desteği
        self.theme = 'light'  # Varsayılan tema
        
    def toggle_theme(self):
        self.theme = 'dark' if self.theme == 'light' else 'light'
        self.view.rootObject().setProperty('theme', self.theme)
