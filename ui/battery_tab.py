from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QDateEdit, QMessageBox, QComboBox, QDialog, QFormLayout,
                             QInputDialog)
from PyQt5.QtCore import Qt, QDate
from database.connection import db_manager
from models.bakim import PilDegisim, Tezgah
from sqlalchemy.orm import Session
from datetime import datetime
from ui.battery_detail_dialog import BatteryDetailDialog

class BatteryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Tezgah yönetim bölümü
        tezgah_layout = QHBoxLayout()
        tezgah_header = QLabel("Tezgah Yönetimi")
        tezgah_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        add_tezgah_button = QPushButton("Yeni Tezgah Ekle")
        add_tezgah_button.clicked.connect(self.add_new_tezgah)
        tezgah_layout.addWidget(tezgah_header)
        tezgah_layout.addStretch()
        tezgah_layout.addWidget(add_tezgah_button)
        layout.addLayout(tezgah_layout)

        # Pil değişim formu
        form_layout = QFormLayout()
        
        # Tezgah numarası ComboBox
        self.tezgah_numarasi = QComboBox()
        self.tezgah_numarasi.setEditable(True)
        self.tezgah_numarasi.setPlaceholderText("Tezgah Numarası")
        self.load_tezgah_numaralari() # Mevcut tezgah numaralarını yükle
        
        # Eksen Seçimi
        self.eksen_combo = QComboBox()
        for value, text in PilDegisim.EKSENLER:
            self.eksen_combo.addItem(text, value)
        
        form_layout.addRow("Tezgah No:", self.tezgah_numarasi)
        form_layout.addRow("Eksen:", self.eksen_combo)
        
        self.pil_modeli = QLineEdit()
        self.pil_modeli.setPlaceholderText("Pil Modeli")
        
        self.replacement_date = QDateEdit()
        self.replacement_date.setCalendarPopup(True)
        self.replacement_date.setDate(QDate.currentDate())
        
        self.bakim_yapan = QLineEdit()
        self.bakim_yapan.setPlaceholderText("Bakımı Yapan")
        
        add_button = QPushButton("Kaydet")
        add_button.clicked.connect(self.save_battery_record)

        form_layout.addRow("Pil Modeli:", self.pil_modeli)
        form_layout.addRow("Değişim Tarihi:", self.replacement_date)
        form_layout.addRow("Yapan:", self.bakim_yapan)
        form_layout.addRow("", add_button)

        layout.addLayout(form_layout)

        # Pil değişim kayıtları tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Tezgah No", "Eksen", "Pil Modeli", "Değişim Tarihi", "Yapan", "Sonraki Değişim"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.doubleClicked.connect(self.show_battery_details)
        self.table.setSortingEnabled(True)  # Sıralama özelliğini aktif et

        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_battery_records()

    def load_tezgah_numaralari(self):
        """Mevcut tezgah numaralarını sıralı şekilde ComboBox'a yükle"""
        session = db_manager.get_session()
        try:
            # Tezgah numaralarını sıralı şekilde getir
            tezgahlar = session.query(Tezgah).order_by(Tezgah.numarasi).all()
            self.tezgah_numarasi.clear()
            for tezgah in tezgahlar:
                self.tezgah_numarasi.addItem(tezgah.numarasi)
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Tezgah numaraları yüklenirken hata oluştu: {e}")
        finally:
            session.close()
    
    def add_new_tezgah(self):
        """Yeni tezgah ekleme işlemi"""
        tezgah_no, ok = QInputDialog.getText(self, "Yeni Tezgah", "Tezgah Numarası:")
        
        if ok and tezgah_no:
            session = db_manager.get_session()
            try:
                # Önce bu numarada tezgah var mı kontrol et
                existing = session.query(Tezgah).filter_by(numarasi=tezgah_no).first()
                if existing:
                    QMessageBox.warning(self, "Uyarı", f"{tezgah_no} numaralı tezgah zaten kayıtlı!")
                    return
                
                # Yeni tezgah ekle
                tezgah = Tezgah(numarasi=tezgah_no)
                session.add(tezgah)
                session.commit()
                QMessageBox.information(self, "Başarılı", f"{tezgah_no} numaralı tezgah eklendi.")
                self.load_tezgah_numaralari()
            except Exception as e:
                session.rollback()
                QMessageBox.warning(self, "Hata", f"Tezgah eklenirken hata oluştu: {e}")
            finally:
                session.close()
    
    def save_battery_record(self):
        session = db_manager.get_session()
        try:
            # Tezgah kontrolü ve oluşturma
            tezgah_no = self.tezgah_numarasi.currentText()
            tezgah = session.query(Tezgah).filter_by(numarasi=tezgah_no).first()
            if not tezgah:
                tezgah = Tezgah(numarasi=tezgah_no)
                session.add(tezgah)
                session.commit()
            
            # Pil değişim kaydı oluşturma
            record = PilDegisim(
                tezgah_id=tezgah.id,
                eksen=self.eksen_combo.currentData(),
                pil_modeli=self.pil_modeli.text(),
                tarih=datetime.now(),
                bakim_yapan=self.bakim_yapan.text()
            )
            session.add(record)
            session.commit()
            QMessageBox.information(self, "Başarılı", "Pil değişim kaydı eklendi.")
            self.load_battery_records()
        except Exception as e:
            session.rollback()
            QMessageBox.warning(self, "Hata", f"Kayıt eklenirken hata oluştu: {e}")
        finally:
            session.close()

    def load_battery_records(self):
        session = db_manager.get_session()
        try:
            records = session.query(PilDegisim).join(Tezgah).all()
            self.table.setRowCount(len(records))
            
            for row, record in enumerate(records):
                self.table.setItem(row, 0, QTableWidgetItem(str(record.id)))
                self.table.setItem(row, 1, QTableWidgetItem(record.tezgah.numarasi))
                self.table.setItem(row, 2, QTableWidgetItem(record.eksen))
                self.table.setItem(row, 3, QTableWidgetItem(record.pil_modeli))
                self.table.setItem(row, 4, QTableWidgetItem(record.tarih))
                self.table.setItem(row, 5, QTableWidgetItem(record.bakim_yapan))
                self.table.setItem(row, 6, QTableWidgetItem("Belirlenmemiş"))
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kayıtlar yüklenirken hata oluştu: {e}")
        finally:
            session.close()
    
    def show_battery_details(self, index):
        """Pil değişim detaylarını göster ve düzenleme seçeneği sun"""
        row = index.row()
        record_id = int(self.table.item(row, 0).text())
        
        # Pil değişim kaydını al
        session = db_manager.get_session()
        try:
            record = session.query(PilDegisim).filter_by(id=record_id).first()
            if not record:
                QMessageBox.warning(self, "Hata", "Kayıt bulunamadı.")
                return
            
            # Detay diyaloğunu göster
            dialog = BatteryDetailDialog(record, self)
            dialog.exec_()
            
            # Kayıtlar değiştiyse yeniden yükle
            if dialog.changes_made:
                self.load_battery_records()
                self.load_tezgah_numaralari()
        
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kayıt detayları görüntülenirken hata oluştu: {e}")
        finally:
            session.close()
