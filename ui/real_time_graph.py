from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg

class RealTimeGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Grafik widget'ını oluştur
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        
        # Grafik ayarları
        self.plot = self.plot_widget.plot(pen='y')
        self.data = []
        
    def update_graph(self, new_value):
        """Grafiği yeni değerle günceller"""
        self.data.append(new_value)
        if len(self.data) > 100:  # Son 100 değeri tut
            self.data = self.data[-100:]
        self.plot.setData(self.data)
