import os
import webbrowser
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QTableWidget, QTableWidgetItem, 
                             QMessageBox, QDateEdit, QComboBox, QCheckBox, QGroupBox,
                             QFormLayout, QListWidget, QListWidgetItem, QTabWidget,
                             QScrollArea, QFrame, QSplitter)
from PyQt5.QtCore import Qt, QDate
from utils.report_generator import report_generator
from datetime import datetime, timedelta
import pandas as pd
import shutil
from database.connection import db_manager
from models.maintenance import Tezgah

class ReportsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Ana düzen
        main_layout = QVBoxLayout()

        # Rapor başlığı
        title_label = QLabel("Bakım ve Pil Değişim Raporları")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 16px;")
        main_layout.addWidget(title_label)

        # Veritabanı içe/dışa aktarım butonları
        db_group = QGroupBox("Veritabanı Yönetimi")
        db_layout = QHBoxLayout()
        export_btn = QPushButton("Veritabanını Dışa Aktar")
        export_btn.clicked.connect(self.export_db)
        import_btn = QPushButton("Veritabanını İçe Aktar")
        import_btn.clicked.connect(self.import_db)
        db_layout.addWidget(export_btn)
        db_layout.addWidget(import_btn)
        db_group.setLayout(db_layout)
        main_layout.addWidget(db_group)

        # Rapor oluşturma sekmeleri
        tabs = QTabWidget()
        maintenance_tab = self.create_maintenance_report_tab()
        battery_tab = self.create_battery_report_tab()
        tabs.addTab(maintenance_tab, "Bakım Raporu")
        tabs.addTab(battery_tab, "Pil Değişim Raporu")
        main_layout.addWidget(tabs)

        # Rapor geçmişi başlığı
        rapor_gecmisi_label = QLabel("Rapor Geçmişi")
        rapor_gecmisi_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        main_layout.addWidget(rapor_gecmisi_label)

        # Rapor geçmişi tablosu
        self.rapor_tablosu = QTableWidget()
        self.rapor_tablosu.setColumnCount(4)
        self.rapor_tablosu.setHorizontalHeaderLabels(["Rapor Türü", "Tarih", "Excel", "PDF"])
        self.rapor_tablosu.horizontalHeader().setStretchLastSection(True)
        
        # Tablo çift tıklama eventi
        self.rapor_tablosu.cellDoubleClicked.connect(self.open_report)
        
        main_layout.addWidget(self.rapor_tablosu)

        # Raporları listele
        self.list_reports()

        self.setLayout(main_layout)

    def export_db(self):
        import os, shutil, datetime
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tezgah_takip.db'))
        if not os.path.exists(db_path):
            QMessageBox.warning(self, "Hata", "Veritabanı dosyası bulunamadı!")
            return
        dest_path, _ = QFileDialog.getSaveFileName(self, "Veritabanını Dışa Aktar", f"tezgah_takip_yedek_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db", "Veritabanı Dosyası (*.db)")
        if dest_path:
            try:
                shutil.copy2(db_path, dest_path)
                QMessageBox.information(self, "Başarılı", f"Veritabanı başarıyla dışa aktarıldı:\n{dest_path}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Dışa aktarma sırasında hata oluştu:\n{str(e)}")

    def import_db(self):
        import os, shutil
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tezgah_takip.db'))
        src_path, _ = QFileDialog.getOpenFileName(self, "Veritabanı İçe Aktar", "", "Veritabanı Dosyası (*.db)")
        if src_path:
            try:
                shutil.copy2(src_path, db_path)
                QMessageBox.information(self, "Başarılı", f"Veritabanı başarıyla içe aktarıldı! Uygulamayı yeniden başlatın.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"İçe aktarma sırasında hata oluştu:\n{str(e)}")


    def create_maintenance_report_tab(self):
        """Bakım raporu sekmesini oluştur"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Filtreleme bölümü
        filter_group = QGroupBox("Rapor Filtreleri")
        filter_layout = QFormLayout()

        # Tarih aralığı seçimi
        date_layout = QHBoxLayout()
        self.maintenance_start_date = QDateEdit()
        self.maintenance_start_date.setCalendarPopup(True)
        self.maintenance_start_date.setDate(QDate.currentDate().addMonths(-3))
        self.maintenance_end_date = QDateEdit()
        self.maintenance_end_date.setCalendarPopup(True)
        self.maintenance_end_date.setDate(QDate.currentDate())
        date_layout.addWidget(QLabel("Başlangıç:"))
        date_layout.addWidget(self.maintenance_start_date)
        date_layout.addWidget(QLabel("Bitiş:"))
        date_layout.addWidget(self.maintenance_end_date)
        filter_layout.addRow("Tarih Aralığı:", date_layout)

        # Hızlı tarih seçimi
        quick_date_layout = QHBoxLayout()
        last_month_btn = QPushButton("Son Ay")
        last_3months_btn = QPushButton("Son 3 Ay")
        last_year_btn = QPushButton("Son Yıl")
        all_time_btn = QPushButton("Tüm Zamanlar")
        
        last_month_btn.clicked.connect(lambda: self.set_date_range(self.maintenance_start_date, self.maintenance_end_date, months=1))
        last_3months_btn.clicked.connect(lambda: self.set_date_range(self.maintenance_start_date, self.maintenance_end_date, months=3))
        last_year_btn.clicked.connect(lambda: self.set_date_range(self.maintenance_start_date, self.maintenance_end_date, months=12))
        all_time_btn.clicked.connect(lambda: self.set_date_range(self.maintenance_start_date, self.maintenance_end_date, all_time=True))
        
        quick_date_layout.addWidget(last_month_btn)
        quick_date_layout.addWidget(last_3months_btn)
        quick_date_layout.addWidget(last_year_btn)
        quick_date_layout.addWidget(all_time_btn)
        filter_layout.addRow("Hızlı Seçim:", quick_date_layout)

        # Tezgah seçimi
        self.maintenance_tezgah_list = QListWidget()
        self.maintenance_tezgah_list.setMaximumHeight(150)
        self.maintenance_tezgah_list.setSelectionMode(QListWidget.MultiSelection)
        self.load_tezgah_list(self.maintenance_tezgah_list)
        
        self.maintenance_all_tezgah = QCheckBox("Tüm Tezgahlar")
        self.maintenance_all_tezgah.setChecked(True)
        self.maintenance_all_tezgah.stateChanged.connect(
            lambda state: self.toggle_all_tezgah(state, self.maintenance_tezgah_list)
        )
        
        tezgah_layout = QVBoxLayout()
        tezgah_layout.addWidget(self.maintenance_all_tezgah)
        tezgah_layout.addWidget(self.maintenance_tezgah_list)
        filter_layout.addRow("Tezgahlar:", tezgah_layout)

        # Rapor seçenekleri
        options_layout = QVBoxLayout()
        self.maintenance_include_charts = QCheckBox("Grafikler Dahil Et")
        self.maintenance_include_charts.setChecked(True)
        self.maintenance_include_stats = QCheckBox("İstatistikler Dahil Et")
        self.maintenance_include_stats.setChecked(True)
        options_layout.addWidget(self.maintenance_include_charts)
        options_layout.addWidget(self.maintenance_include_stats)
        filter_layout.addRow("Rapor İçeriği:", options_layout)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # Rapor oluşturma butonu
        generate_btn = QPushButton("Bakım Raporu Oluştur")
        generate_btn.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        generate_btn.clicked.connect(self.generate_maintenance_report)
        layout.addWidget(generate_btn)

        tab.setLayout(layout)
        return tab
        
    def create_battery_report_tab(self):
        """Pil değişim raporu sekmesini oluştur"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Filtreleme bölümü
        filter_group = QGroupBox("Rapor Filtreleri")
        filter_layout = QFormLayout()

        # Tarih aralığı seçimi
        date_layout = QHBoxLayout()
        self.battery_start_date = QDateEdit()
        self.battery_start_date.setCalendarPopup(True)
        self.battery_start_date.setDate(QDate.currentDate().addMonths(-3))
        self.battery_end_date = QDateEdit()
        self.battery_end_date.setCalendarPopup(True)
        self.battery_end_date.setDate(QDate.currentDate())
        date_layout.addWidget(QLabel("Başlangıç:"))
        date_layout.addWidget(self.battery_start_date)
        date_layout.addWidget(QLabel("Bitiş:"))
        date_layout.addWidget(self.battery_end_date)
        filter_layout.addRow("Tarih Aralığı:", date_layout)

        # Hızlı tarih seçimi
        quick_date_layout = QHBoxLayout()
        last_month_btn = QPushButton("Son Ay")
        last_3months_btn = QPushButton("Son 3 Ay")
        last_year_btn = QPushButton("Son Yıl")
        all_time_btn = QPushButton("Tüm Zamanlar")
        
        last_month_btn.clicked.connect(lambda: self.set_date_range(self.battery_start_date, self.battery_end_date, months=1))
        last_3months_btn.clicked.connect(lambda: self.set_date_range(self.battery_start_date, self.battery_end_date, months=3))
        last_year_btn.clicked.connect(lambda: self.set_date_range(self.battery_start_date, self.battery_end_date, months=12))
        all_time_btn.clicked.connect(lambda: self.set_date_range(self.battery_start_date, self.battery_end_date, all_time=True))
        
        quick_date_layout.addWidget(last_month_btn)
        quick_date_layout.addWidget(last_3months_btn)
        quick_date_layout.addWidget(last_year_btn)
        quick_date_layout.addWidget(all_time_btn)
        filter_layout.addRow("Hızlı Seçim:", quick_date_layout)

        # Tezgah seçimi
        self.battery_tezgah_list = QListWidget()
        self.battery_tezgah_list.setMaximumHeight(150)
        self.battery_tezgah_list.setSelectionMode(QListWidget.MultiSelection)
        self.load_tezgah_list(self.battery_tezgah_list)
        
        self.battery_all_tezgah = QCheckBox("Tüm Tezgahlar")
        self.battery_all_tezgah.setChecked(True)
        self.battery_all_tezgah.stateChanged.connect(
            lambda state: self.toggle_all_tezgah(state, self.battery_tezgah_list)
        )
        
        tezgah_layout = QVBoxLayout()
        tezgah_layout.addWidget(self.battery_all_tezgah)
        tezgah_layout.addWidget(self.battery_tezgah_list)
        filter_layout.addRow("Tezgahlar:", tezgah_layout)

        # Pil modeli seçimi
        self.battery_include_model = QCheckBox("Pil Modeline Göre Grupla")
        self.battery_include_model.setChecked(True)
        filter_layout.addRow("Pil Modeli:", self.battery_include_model)

        # Rapor seçenekleri
        options_layout = QVBoxLayout()
        self.battery_include_charts = QCheckBox("Grafikler Dahil Et")
        self.battery_include_charts.setChecked(True)
        self.battery_include_stats = QCheckBox("İstatistikler Dahil Et")
        self.battery_include_stats.setChecked(True)
        options_layout.addWidget(self.battery_include_charts)
        options_layout.addWidget(self.battery_include_stats)
        filter_layout.addRow("Rapor İçeriği:", options_layout)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # Rapor oluşturma butonu
        generate_btn = QPushButton("Pil Değişim Raporu Oluştur")
        generate_btn.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        generate_btn.clicked.connect(self.generate_battery_report)
        layout.addWidget(generate_btn)

        tab.setLayout(layout)
        return tab
    
    def load_tezgah_list(self, list_widget):
        """Tezgah listesini doldur"""
        session = db_manager.get_session()
        try:
            # Tezgah numaralarını sıralı şekilde getir
            tezgahlar = session.query(Tezgah).order_by(Tezgah.numarasi).all()
            for tezgah in tezgahlar:
                item = QListWidgetItem(tezgah.numarasi)
                item.setData(Qt.UserRole, tezgah.id)
                list_widget.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Tezgah listesi yüklenirken hata oluştu: {e}")
        finally:
            session.close()
    
    def toggle_all_tezgah(self, state, list_widget):
        """Tüm tezgahları seç/kaldır"""
        if state:
            list_widget.setEnabled(False)
        else:
            list_widget.setEnabled(True)
            
    def set_date_range(self, start_date_edit, end_date_edit, months=None, all_time=False):
        """Hızlı tarih aralığı ayarlar"""
        if all_time:
            # Varsayılan olarak 10 yıl öncesini kullan
            start_date_edit.setDate(QDate.currentDate().addYears(-10))
        else:
            start_date_edit.setDate(QDate.currentDate().addMonths(-months))
        
        end_date_edit.setDate(QDate.currentDate())
    
    def generate_maintenance_report(self):
        """Bakım raporu oluştur"""
        try:
            # Tarih aralığını al
            start_date = self.maintenance_start_date.date().toPyDate()
            end_date = self.maintenance_end_date.date().toPyDate()
            
            # Tezgah listesini al
            selected_tezgah_ids = []
            if not self.maintenance_all_tezgah.isChecked():
                for i in range(self.maintenance_tezgah_list.count()):
                    item = self.maintenance_tezgah_list.item(i)
                    if item.isSelected():
                        selected_tezgah_ids.append(item.data(Qt.UserRole))
            
            # Rapor seçeneklerini al
            include_charts = self.maintenance_include_charts.isChecked()
            include_stats = self.maintenance_include_stats.isChecked()
            
            # Rapor oluştur
            report = report_generator.generate_maintenance_report(
                start_date=start_date,
                end_date=end_date,
                tezgah_ids=selected_tezgah_ids if not self.maintenance_all_tezgah.isChecked() else None,
                include_charts=include_charts,
                include_stats=include_stats
            )
            
            if report:
                self.list_reports()
                QMessageBox.information(self, "Rapor Oluşturuldu", 
                                        f"Bakım raporu oluşturuldu.\nExcel: {report['excel_path']}\nPDF: {report['pdf_path']}")
            else:
                QMessageBox.warning(self, "Hata", "Rapor oluşturulamadı")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Rapor oluşturulurken hata: {str(e)}")

    def generate_battery_report(self):
        """Pil değişim raporu oluştur"""
        try:
            # Tarih aralığını al
            start_date = self.battery_start_date.date().toPyDate()
            end_date = self.battery_end_date.date().toPyDate()
            
            # Tezgah listesini al
            selected_tezgah_ids = []
            if not self.battery_all_tezgah.isChecked():
                for i in range(self.battery_tezgah_list.count()):
                    item = self.battery_tezgah_list.item(i)
                    if item.isSelected():
                        selected_tezgah_ids.append(item.data(Qt.UserRole))
            
            # Rapor seçeneklerini al
            include_charts = self.battery_include_charts.isChecked()
            include_stats = self.battery_include_stats.isChecked()
            group_by_model = self.battery_include_model.isChecked()
            
            # Rapor oluştur
            report = report_generator.generate_battery_report(
                start_date=start_date,
                end_date=end_date,
                tezgah_ids=selected_tezgah_ids if not self.battery_all_tezgah.isChecked() else None,
                include_charts=include_charts,
                include_stats=include_stats,
                group_by_model=group_by_model
            )
            
            if report:
                self.list_reports()
                QMessageBox.information(self, "Rapor Oluşturuldu", 
                                        f"Pil değişim raporu oluşturuldu.\nExcel: {report['excel_path']}\nPDF: {report['pdf_path']}")
            else:
                QMessageBox.warning(self, "Hata", "Rapor oluşturulamadı")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Rapor oluşturulurken hata: {str(e)}")

    def list_reports(self):
        """Raporları listele"""
        # Raporlar dizini
        reports_dir = os.path.join(os.path.dirname(__file__), '..', 'raporlar')
        
        # Raporları topla
        reports = []
        for filename in os.listdir(reports_dir):
            if filename.endswith(('.xlsx', '.pdf')):
                full_path = os.path.join(reports_dir, filename)
                
                # Dosya bilgilerini al
                created_time = datetime.fromtimestamp(os.path.getctime(full_path))
                report_type = "Bakım Raporu" if "bakim_raporu" in filename else "Pil Değişim Raporu"
                file_ext = os.path.splitext(filename)[1]
                
                reports.append({
                    'type': report_type,
                    'filename': filename,
                    'path': full_path,
                    'created_time': created_time,
                    'ext': file_ext
                })

        # Tabloyu temizle
        self.rapor_tablosu.setRowCount(0)

        # Raporları sırala (en yeni önce)
        reports.sort(key=lambda x: x['created_time'], reverse=True)

        # Tabloyu doldur
        for report in reports:
            row = self.rapor_tablosu.rowCount()
            self.rapor_tablosu.insertRow(row)
            
            # Rapor türü
            self.rapor_tablosu.setItem(row, 0, QTableWidgetItem(report['type']))
            
            # Tarih
            tarih_item = QTableWidgetItem(report['created_time'].strftime("%Y-%m-%d %H:%M:%S"))
            tarih_item.setTextAlignment(Qt.AlignCenter)
            self.rapor_tablosu.setItem(row, 1, tarih_item)
            
            # Excel/PDF butonları
            excel_btn = QPushButton("Aç" if report['ext'] == '.xlsx' else "")
            excel_btn.clicked.connect(lambda checked, path=report['path']: self.open_report(path))
            pdf_btn = QPushButton("Aç" if report['ext'] == '.pdf' else "")
            pdf_btn.clicked.connect(lambda checked, path=report['path']: self.open_report(path))
            
            self.rapor_tablosu.setCellWidget(row, 2, excel_btn if report['ext'] == '.xlsx' else QLabel())
            self.rapor_tablosu.setCellWidget(row, 3, pdf_btn if report['ext'] == '.pdf' else QLabel())

    def open_report(self, path=None):
        """Raporu aç"""
        if isinstance(path, int):  # Tablo hücre tıklamasından geliyorsa
            row = path
            path = self.rapor_tablosu.item(row, 1).text()  # Dosya yolunu al

        try:
            if os.path.exists(path):
                webbrowser.open(path)
            else:
                QMessageBox.warning(self, "Hata", "Rapor dosyası bulunamadı")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Rapor açılırken hata: {str(e)}")
