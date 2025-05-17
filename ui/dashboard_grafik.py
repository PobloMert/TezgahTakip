from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

class GrafDashboard(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Bakım istatistikleri grafiği
        fig1 = Figure(figsize=(8, 4))
        ax1 = fig1.add_subplot(111)
        self.plot_maintenance_stats(ax1)
        canvas1 = FigureCanvasQTAgg(fig1)
        layout.addWidget(canvas1)
        
        # Tezgah durum grafiği
        fig2 = Figure(figsize=(8, 4))
        ax2 = fig2.add_subplot(111)
        self.plot_tezgah_status(ax2)
        canvas2 = FigureCanvasQTAgg(fig2)
        layout.addWidget(canvas2)
        
        self.setLayout(layout)
    
    def plot_maintenance_stats(self, ax):
        """Bakım istatistiklerini görselleştir"""
        stats = self.db.get_maintenance_stats()
        labels = ['Tamamlanan', 'Bekleyen']
        values = [stats['completed'], stats['pending']]
        
        ax.bar(labels, values, color=['green', 'orange'])
        ax.set_title('Bakım İstatistikleri')
        ax.set_ylabel('Adet')
    
    def plot_tezgah_status(self, ax):
        """Tezgah durumlarını görselleştir"""
        status = self.db.get_tezgah_status_distribution()
        ax.pie(status.values(), labels=status.keys(), autopct='%1.1f%%')
        ax.set_title('Tezgah Durum Dağılımı')
