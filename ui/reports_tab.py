from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QDateEdit, QTableWidget,
                             QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox)
from PyQt5.QtCore import QDate, Qt
import pyqtgraph as pg
from utils.pdf_exporter import PDFExporter
from utils.excel_exporter import ExcelExporter
from utils.excel_template_loader import ExcelTemplateLoader

class ReportsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.pdf_exporter = PDFExporter()
        self.excel_exporter = ExcelExporter()
        self.template_loader = ExcelTemplateLoader()
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Filtreleme Paneli
        filter_panel = QWidget()
        filter_layout = QHBoxLayout()
        
        self.report_type = QComboBox()
        self.report_type.addItems(['Bakım Raporu', 'Pil Ömrü', 'Tezgah Performansı'])
        
        self.start_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit(QDate.currentDate())
        
        generate_btn = QPushButton('Rapor Oluştur')
        generate_btn.clicked.connect(self.generate_report)
        
        # Export butonlarını panelde grupla
        export_panel = QWidget()
        export_layout = QHBoxLayout()
        
        pdf_btn = QPushButton('PDF Olarak Kaydet')
        pdf_btn.clicked.connect(self.export_to_pdf)
        
        excel_btn = QPushButton('Excel Olarak Kaydet')
        excel_btn.clicked.connect(self.export_to_excel)
        
        export_layout.addWidget(pdf_btn)
        export_layout.addWidget(excel_btn)
        export_panel.setLayout(export_layout)
        
        # Şablon seçim combobox'ı ekle
        self.template_combo = QComboBox()
        try:
            templates = self.template_loader.get_available_templates()
            self.template_combo.addItems(templates)
        except Exception as e:
            print(f"Şablon yüklenirken hata: {e}")
        
        filter_layout.addWidget(QLabel('Rapor Türü:'))
        filter_layout.addWidget(self.report_type)
        filter_layout.addWidget(QLabel('Başlangıç:'))
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(QLabel('Bitiş:'))
        filter_layout.addWidget(self.end_date)
        filter_layout.addWidget(generate_btn)
        filter_layout.addWidget(QLabel('Şablon Seç:'))
        filter_layout.addWidget(self.template_combo)
        filter_layout.addWidget(export_panel)
        filter_panel.setLayout(filter_layout)
        
        # Sonuçlar Tablosu
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(['Tezgah', 'Bakım Sayısı', 'Son Bakım', 'Pil Durumu', 'Aksiyon'])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Grafik Alanı
        self.plot_widget = pg.PlotWidget()
        
        main_layout.addWidget(filter_panel)
        main_layout.addWidget(self.results_table)
        main_layout.addWidget(self.plot_widget)
        self.setLayout(main_layout)
    
    def generate_report(self):
        # Rapor oluşturma işlemleri
        pass

    def export_to_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, 'PDF Olarak Kaydet', '', 'PDF Files (*.pdf)')
            
        if filename:
            if not filename.endswith('.pdf'):
                filename += '.pdf'
                
            # Tablo verilerini al
            data = self.get_table_data()
            
            # PDF oluştur
            report_type = self.report_type.currentText()
            self.pdf_exporter.export_report(filename, data, report_type)
            
            QMessageBox.information(self, 'Başarılı', 
                f'Rapor başarıyla kaydedildi:\n{filename}')

    def export_to_excel(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Excel Olarak Kaydet', '', 'Excel Files (*.xlsx)')
            
        if filename:
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'
                
            try:
                # Seçili şablonu yükle
                selected_template = self.template_combo.currentText()
                wb = self.template_loader.get_template(selected_template)
                ws = wb.active
                
                # Verileri şablona ekle
                data = self.get_table_data()
                for row_num, row_data in enumerate(data, 4):  # 4. satırdan itibaren veri ekle
                    ws.cell(row=row_num, column=1, value=row_data['machine_id'])
                    ws.cell(row=row_num, column=2, value=row_data['last_maintenance'])
                    # Diğer sütunları şablona göre ayarla
                    
                wb.save(filename)
                QMessageBox.information(self, 'Başarılı', 
                    f'Rapor başarıyla kaydedildi:\n{filename}')
                    
            except Exception as e:
                QMessageBox.critical(self, 'Hata', 
                    f'Excel oluşturulurken hata:\n{str(e)}')
                
    def get_table_data(self):
        """Tablo verilerini dictionary listesi olarak döndürür"""
        data = []
        for row in range(self.results_table.rowCount()):
            row_data = {
                'machine_id': self.results_table.item(row, 0).text(),
                'maintenance_count': self.results_table.item(row, 1).text(),
                'last_maintenance': self.results_table.item(row, 2).text(),
                'status': self.results_table.item(row, 3).text()
            }
            data.append(row_data)
        return data
