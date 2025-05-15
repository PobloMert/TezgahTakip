import os
import shutil
import sqlite3
import logging
from datetime import datetime
from utils.config_manager import config_manager

class BackupManager:
    def __init__(self):
        self.backup_dir = config_manager.get("BACKUP_DIR", "backups")
        self.database_path = config_manager.get("DATABASE_FILE", "tezgah_takip.db")
        
        # Backup dizinini oluştur
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self):
        """
        Veritabanının yedeğini oluşturur
        
        Returns:
            str: Yedeklenen dosyanın yolu
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"tezgah_takip_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)

            # Veritabanı bağlantısını kapatarak yedekleme
            with sqlite3.connect(self.database_path) as source_conn:
                with sqlite3.connect(backup_path) as backup_conn:
                    source_conn.backup(backup_conn)

            logging.info(f"Veritabanı yedeği oluşturuldu: {backup_path}")
            return backup_path
        except Exception as e:
            logging.error(f"Yedekleme sırasında hata: {e}")
            return None

    def list_backups(self):
        """
        Mevcut yedekleri listeler
        
        Returns:
            list: Yedek dosyalarının listesi
        """
        try:
            backups = [f for f in os.listdir(self.backup_dir) if f.startswith("tezgah_takip_backup_") and f.endswith(".db")]
            return sorted(backups, reverse=True)
        except Exception as e:
            logging.error(f"Yedekler listelenemedi: {e}")
            return []

    def restore_backup(self, backup_filename):
        """
        Belirli bir yedeği geri yükler
        
        Args:
            backup_filename (str): Geri yüklenecek yedek dosyasının adı
        
        Returns:
            bool: Geri yükleme başarılı mı
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Mevcut veritabanını yedekle
            current_backup = self.create_backup()
            
            # Veritabanını geri yükle
            shutil.copy2(backup_path, self.database_path)
            
            logging.info(f"Yedek geri yüklendi: {backup_filename}")
            return True
        except Exception as e:
            logging.error(f"Geri yükleme sırasında hata: {e}")
            return False

    def cleanup_old_backups(self, max_backups=10):
        """
        Eski yedekleri temizler
        
        Args:
            max_backups (int): Tutulacak maksimum yedek sayısı
        """
        try:
            backups = self.list_backups()
            if len(backups) > max_backups:
                for backup in backups[max_backups:]:
                    os.remove(os.path.join(self.backup_dir, backup))
                    logging.info(f"Eski yedek silindi: {backup}")
        except Exception as e:
            logging.error(f"Yedek temizleme sırasında hata: {e}")

backup_manager = BackupManager()
