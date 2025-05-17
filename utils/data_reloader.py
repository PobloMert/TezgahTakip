"""
Veri yenileme kontrol mekanizması (Gelişmiş Sürüm)
"""
from datetime import datetime, timedelta
from typing import Dict, Optional

class SmartDataReloader:
    def __init__(self, cleanup_interval: int = 24):
        """
        :param cleanup_interval: Saat cinsinden temizleme aralığı
        """
        self.last_update: Dict[str, datetime] = {}
        self.last_cleanup = datetime.now()
        self.cleanup_interval = cleanup_interval
        
    def _cleanup_old_entries(self):
        """Kullanılmayan eski kayıtları temizle"""
        if (datetime.now() - self.last_cleanup) < timedelta(hours=self.cleanup_interval):
            return
            
        cutoff_time = datetime.now() - timedelta(days=7)
        self.last_update = {
            k: v for k, v in self.last_update.items() 
            if v > cutoff_time
        }
        self.last_cleanup = datetime.now()
        
    def needs_reload(self, table_name: str, max_minutes: int = 30) -> bool:
        """
        Belirtilen tablonun yeniden yüklenmesi gerekiyor mu?
        :param table_name: Kontrol edilecek tablo adı
        :param max_minutes: Maksimum yenileme aralığı (dakika)
        :return: Yenileme gerekiyorsa True
        """
        self._cleanup_old_entries()
        last_time = self.last_update.get(table_name)
        return not last_time or (datetime.now() - last_time) > timedelta(minutes=max_minutes)
        
    def update_last_reload(self, table_name: str) -> None:
        """Yenileme zamanını güncelle"""
        self.last_update[table_name] = datetime.now()
        self._cleanup_old_entries()
