from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox,
                             QInputDialog)
from PyQt5.QtCore import Qt
from database.connection import db_manager
from models.bakim import Tezgah

class MaintenanceDetailDialog(QDialog):
    """Bakım detaylarını gösteren ve düzenleme için şifre soran dialog"""
    def __init__(self, record, parent=None):
        super().__init__(parent)
        self.record = record
        self.changes_made = False
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle(f"Bakım Detayı - ID: {self.record.id}")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Bilgi alanı
        form_layout = QFormLayout()
        form_layout.addRow("Tezgah No:", QLabel(self.record.tezgah.numarasi))
        form_layout.addRow("Tarih:", QLabel(self.record.tarih))
        form_layout.addRow("Açıklama:", QLabel(self.record.aciklama))
        form_layout.addRow("Bakımı Yapan:", QLabel(self.record.bakim_yapan))
        layout.addLayout(form_layout)
        
        # Düzenle butonu
        edit_button = QPushButton("Düzenle")
        edit_button.clicked.connect(self.edit_record)
        
        # Kapat butonu
        close_button = QPushButton("Kapat")
        close_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(edit_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
    
    def edit_record(self):
        """Kaydı düzenlemek için şifre sor"""
        password, ok = QInputDialog.getText(
            self, "Güvenlik", "Düzenleme şifresini girin:", 
            QLineEdit.Password
        )
        
        if ok and password == "mtbbakım":
            self.show_edit_dialog()
        elif ok:
            QMessageBox.warning(self, "Hata", "Yanlış şifre!")
    
    def show_edit_dialog(self):
        """Düzenleme diyaloğunu göster"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Bakım Kaydını Düzenle")
        
        layout = QVBoxLayout(dialog)
        
        # Düzenleme alanları
        form_layout = QFormLayout()
        
        tezgah_combo = QComboBox()
        tezgah_combo.setEditable(True)
        # Mevcut tezgahları yükle
        session = db_manager.get_session()
        try:
            tezgahlar = session.query(Tezgah).all()
            for tezgah in tezgahlar:
                tezgah_combo.addItem(tezgah.numarasi)
            tezgah_combo.setCurrentText(self.record.tezgah.numarasi)
        finally:
            session.close()
        
        aciklama = QLineEdit(self.record.aciklama or "")
        yapan = QLineEdit(self.record.bakim_yapan or "")
        
        form_layout.addRow("Tezgah No:", tezgah_combo)
        form_layout.addRow("Açıklama:", aciklama)
        form_layout.addRow("Bakımı Yapan:", yapan)
        
        layout.addLayout(form_layout)
        
        # Butonlar
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        cancel_btn = QPushButton("İptal")
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Fonksiyonlar
        def save_changes():
            session = db_manager.get_session()
            try:
                # Tezgah numarası değiştiyse
                if tezgah_combo.currentText() != self.record.tezgah.numarasi:
                    tezgah = session.query(Tezgah).filter_by(numarasi=tezgah_combo.currentText()).first()
                    if not tezgah:
                        tezgah = Tezgah(numarasi=tezgah_combo.currentText())
                        session.add(tezgah)
                        session.commit()
                    self.record.tezgah_id = tezgah.id
                
                # Diğer alanları güncelle
                self.record.aciklama = aciklama.text()
                self.record.bakim_yapan = yapan.text()
                
                session.commit()
                QMessageBox.information(dialog, "Başarılı", "Bakım kaydı güncellendi.")
                self.changes_made = True
                dialog.accept()
            except Exception as e:
                session.rollback()
                QMessageBox.warning(dialog, "Hata", f"Güncelleme sırasında hata oluştu: {e}")
            finally:
                session.close()
        
        save_btn.clicked.connect(save_changes)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()
