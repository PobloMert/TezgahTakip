import os
import json
import logging

class ConfigManager:
    def __init__(self, config_path='config.json'):
        self.config_path = os.path.join(os.path.dirname(__file__), '..', config_path)
        self.config = self.load_config()

    def load_config(self):
        """Konfigürasyon dosyasını yükler"""
        try:
            if not os.path.exists(self.config_path):
                # Varsayılan konfigürasyon oluştur
                default_config = {
                    "DATABASE_FILE": "tezgah_takip.db",
                    "BACKUP_DIR": "backups",
                    "PASSWORD": None,
                    "GITHUB_USERNAME": "kullanici_adi",
                    "REPO_NAME": "TezgahTakipQt",
                    "CURRENT_VERSION": "1.0.0"
                }
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                logging.info(f"Varsayılan konfigürasyon dosyası oluşturuldu: {self.config_path}")
                return default_config

            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Konfigürasyon yüklenirken hata: {e}")
            return {}

    def get(self, key, default=None):
        """Belirli bir konfigürasyon anahtarını getirir"""
        return self.config.get(key, default)

    def set(self, key, value):
        """Konfigürasyon değerini günceller"""
        try:
            self.config[key] = value
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logging.info(f"Konfigürasyon güncellendi: {key} = {value}")
        except Exception as e:
            logging.error(f"Konfigürasyon güncellenirken hata: {e}")

config_manager = ConfigManager()
