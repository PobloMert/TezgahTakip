from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import numpy as np

class RealTimeGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.graph = pg.PlotWidget()
        self.layout.addWidget(self.graph)
        self.setLayout(self.layout)
        
        # Grafik ayarları
        self.graph.setBackground('w')
        self.curve = self.graph.plot(pen='b')
        
        # Veri güncelleme timer'ı
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(1000)  # 1 saniyede bir güncelle
        
    def update_graph(self):
        """Veritabanından veri çekerek grafiği günceller"""
        from database.connection import db_manager
        data = db_manager.get_recent_data()  # Son 60 veri
        self.curve.setData(data)
