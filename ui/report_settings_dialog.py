from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, 
                              QLabel, QComboBox, QSpinBox, QCheckBox, QPushButton,
                              QDateEdit, QFormLayout)
from PyQt5.QtCore import QDate

class ReportSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Rapor Ayarları')
        self.setMinimumWidth(400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Tarih Aralığı
        date_group = QGroupBox('Tarih Aralığı')
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit(QDate.currentDate().addDays(-30))
        self.end_date = QDateEdit(QDate.currentDate())
        date_layout.addWidget(QLabel('Başlangıç:'))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel('Bitiş:'))
        date_layout.addWidget(self.end_date)
        date_group.setLayout(date_layout)
        
        # Grafik Ayarları
        graph_group = QGroupBox('Grafik Ayarları')
        graph_layout = QFormLayout()
        self.graph_type = QComboBox()
        self.graph_type.addItems(['Çubuk Grafik', 'Pasta Grafik', 'Çizgi Grafik', 'Alan Grafiği'])
        self.theme = QComboBox()
        self.theme.addItems(['Açık', 'Koyu', 'Renkli'])
        graph_layout.addRow('Grafik Türü:', self.graph_type)
        graph_layout.addRow('Tema:', self.theme)
        graph_group.setLayout(graph_layout)
        
        # Rapor Seçenekleri
        options_group = QGroupBox('Rapor Seçenekleri')
        options_layout = QVBoxLayout()
        self.show_mttr = QCheckBox('MTTR Göster', checked=True)
        self.show_freq = QCheckBox('Bakım Sıklığı Göster', checked=True)
        self.show_failure = QCheckBox('Arıza Oranları Göster')
        self.export_excel = QCheckBox('Excel Çıktısı Oluştur')
        options_layout.addWidget(self.show_mttr)
        options_layout.addWidget(self.show_freq)
        options_layout.addWidget(self.show_failure)
        options_layout.addWidget(self.export_excel)
        options_group.setLayout(options_layout)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton('Uygula')
        self.cancel_btn = QPushButton('İptal')
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        # Ana Layout
        layout.addWidget(date_group)
        layout.addWidget(graph_group)
        layout.addWidget(options_group)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Sinyal bağlantıları
        self.cancel_btn.clicked.connect(self.reject)
        self.apply_btn.clicked.connect(self.accept)
    
    def get_settings(self):
        """Seçilen ayarları döndürür"""
        return {
            'start_date': self.start_date.date().toString('yyyy-MM-dd'),
            'end_date': self.end_date.date().toString('yyyy-MM-dd'),
            'graph_type': self.graph_type.currentText(),
            'theme': self.theme.currentText(),
            'show_mttr': self.show_mttr.isChecked(),
            'show_freq': self.show_freq.isChecked(),
            'show_failure': self.show_failure.isChecked(),
            'export_excel': self.export_excel.isChecked()
        }
