from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QMessageBox, QProgressBar)
from PyQt5.QtCore import QTimer, Qt
from utils.backup_manager import backup_manager
from utils.report_generator import report_generator

class QuickActionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hızlı İşlemler")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Yedekleme butonu
        backup_button = QPushButton("Hemen Yedek Al")
        backup_button.clicked.connect(self.create_backup)
        layout.addWidget(backup_button)
        
        # Rapor oluşturma butonları
        maintenance_report_button = QPushButton("Bakım Raporu Oluştur")
        maintenance_report_button.clicked.connect(self.create_maintenance_report)
        layout.addWidget(maintenance_report_button)
        
        battery_report_button = QPushButton("Pil Değişim Raporu Oluştur")
        battery_report_button.clicked.connect(self.create_battery_report)
        layout.addWidget(battery_report_button)
        
        # Log görüntüleme
        log_view = QTextEdit()
        log_view.setReadOnly(True)
        layout.addWidget(log_view)
        
        self.setLayout(layout)
        
    def create_backup(self):
        """Anlık yedek alma işlemi"""
        backup_path = backup_manager.create_backup()
        if backup_path:
            QMessageBox.information(self, "Başarılı", f"Yedek oluşturuldu: {backup_path}")
        else:
            QMessageBox.warning(self, "Hata", "Yedek oluşturulamadı")
    
    def create_maintenance_report(self):
        """Bakım raporu oluşturma"""
        report = report_generator.generate_maintenance_report()
        if report:
            QMessageBox.information(
                self, 
                "Rapor Oluşturuldu", 
                f"Excel: {report['excel_path']}\nPDF: {report['pdf_path']}"
            )
        else:
            QMessageBox.warning(self, "Hata", "Rapor oluşturulamadı")
    
    def create_battery_report(self):
        """Pil değişim raporu oluşturma"""
        report = report_generator.generate_battery_report()
        if report:
            QMessageBox.information(
                self, 
                "Rapor Oluşturuldu", 
                f"Excel: {report['excel_path']}\nPDF: {report['pdf_path']}"
            )
        else:
            QMessageBox.warning(self, "Hata", "Rapor oluşturulamadı")

class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tezgah Takip Sistemine Hoş Geldiniz")
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout()
        
        # Hoş geldin mesajı
        welcome_label = QLabel("Tezgah Takip Sistemine Hoş Geldiniz!")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #007bff;")
        layout.addWidget(welcome_label)
        
        # Açıklama
        description_label = QLabel(
            "Bu sistem, tezgahlarınızın bakım ve pil değişim kayıtlarını "
            "yönetmenize yardımcı olur. Hızlı raporlama, yedekleme ve "
            "detaylı izleme özellikleri ile işinizi kolaylaştırır."
        )
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        
        # Özellikler listesi
        features_label = QLabel("Başlıca Özellikler:")
        features_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(features_label)
        
        features = [
            "Detaylı Bakım Kayıtları",
            "Pil Değişim Takibi",
            "Anlık Raporlama",
            "Otomatik Yedekleme",
            "Kullanıcı Dostu Arayüz"
        ]
        
        for feature in features:
            feature_label = QLabel(f"• {feature}")
            layout.addWidget(feature_label)
        
        # İlerleme çubuğu
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        layout.addWidget(progress_bar)
        
        # Başlat butonu
        start_button = QPushButton("Sistemi Kullanmaya Başla")
        start_button.clicked.connect(self.accept)
        layout.addWidget(start_button)
        
        self.setLayout(layout)
        
        # Simüle edilmiş yükleme
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)
        self.progress = 0
    
    def update_progress(self):
        """İlerleme çubuğunu güncelle"""
        self.findChild(QProgressBar).setValue(self.progress)
        self.progress += 2
        if self.progress > 100:
            self.timer.stop()

def show_quick_actions(parent=None):
    """Hızlı işlemler penceresini göster"""
    dialog = QuickActionsDialog(parent)
    dialog.exec_()

def show_welcome_dialog(parent=None):
    """Hoş geldin ekranını göster"""
    dialog = WelcomeDialog(parent)
    return dialog.exec_() == QDialog.Accepted
