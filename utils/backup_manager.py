"""
Veritabanı yedekleme yönetimi
"""
import os
import shutil
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal

class BackupManager(QObject):
    backup_created = pyqtSignal(str)  # Yedek dosya yolu
    
    def __init__(self, backup_dir='backups'):
        super().__init__()
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, db_path='tezgah_takip.db'):
        """Veritabanının yedeğini oluştur"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{self.backup_dir}/tezgah_backup_{timestamp}.db"
        
        try:
            shutil.copy2(db_path, backup_file)
            self.backup_created.emit(backup_file)
            return True
        except Exception as e:
            print(f"Yedekleme hatası: {e}")
            return False
    
    def get_backup_list(self):
        """Mevcut yedekleri listele"""
        return sorted(
            [f for f in os.listdir(self.backup_dir) if f.startswith('tezgah_backup_')],
            reverse=True
        )
    
    def restore_backup(self, backup_file):
        """Belirtilen yedekten geri yükleme yap"""
        try:
            shutil.copy2(f"{self.backup_dir}/{backup_file}", 'tezgah_takip.db')
            return True
        except Exception as e:
            print(f"Geri yükleme hatası: {e}")
            return False

backup_manager = BackupManager()
