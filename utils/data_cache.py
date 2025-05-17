"""
Veri önbellek yönetimi
"""
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime, timedelta

class DataCache(QObject):
    data_updated = pyqtSignal(str)  # Güncellenen veri türü
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.cache = {
            'tezgahlar': {'data': None, 'last_update': None},
            'bakimlar': {'data': None, 'last_update': None},
            'piller': {'data': None, 'last_update': None}
        }
    
    def get_data(self, data_type, force_update=False):
        """Önbellekten veri al veya veritabanından yükle"""
        if force_update or self._needs_update(data_type):
            self._update_cache(data_type)
        return self.cache[data_type]['data']
    
    def _needs_update(self, data_type):
        """Verinin güncellenmesi gerekiyor mu kontrol et"""
        cache_entry = self.cache.get(data_type)
        if not cache_entry or not cache_entry['data']:
            return True
            
        # 5 dakikadan eski verileri yenile
        return datetime.now() - cache_entry['last_update'] > timedelta(minutes=5)
    
    def _update_cache(self, data_type):
        """Önbelleği veritabanından güncelle"""
        if data_type == 'tezgahlar':
            self.cache[data_type]['data'] = self.db_manager.get_all_tezgahlar()
        elif data_type == 'bakimlar':
            self.cache[data_type]['data'] = self.db_manager.get_all_maintenance()
        elif data_type == 'piller':
            self.cache[data_type]['data'] = self.db_manager.get_all_battery_changes()
            
        self.cache[data_type]['last_update'] = datetime.now()
        self.data_updated.emit(data_type)
