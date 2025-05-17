from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import pyqtgraph as pg

class StatsWidget(QWidget):
    def __init__(self, title, value, unit='', parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet('font-size: 14px; color: #555;')
        
        self.value_label = QLabel(str(value))
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet('font-size: 24px; font-weight: bold;')
        
        self.unit_label = QLabel(unit)
        self.unit_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.unit_label)
        self.setLayout(layout)

class DonutChartWidget(QWidget):
    def __init__(self, title, data, parent=None):
        super().__init__(parent)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(None)
        
        # Çubuk grafik oluştur
        x = [i for i in range(len(data))]
        y = [val[1] for val in data]
        colors = [val[2] for val in data]
        
        bg = pg.BarGraphItem(x=x, height=y, width=0.6, brushes=colors)
        self.plot_widget.addItem(bg)
        
        # Eksen etiketleri
        self.plot_widget.getAxis('bottom').setTicks([[(i, val[0]) for i, val in enumerate(data)]])
        
        layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
