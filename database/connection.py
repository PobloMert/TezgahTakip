"""
Veritabanı bağlantısı modülü (Güvenli Sürüm)
"""
import sqlite3
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from models.bakim import Base, Tezgah, Bakim  # Tüm modelleri tek dosyadan import et
import os
import sys
import tempfile
from contextlib import contextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor
import shutil
from PyQt5.QtCore import pyqtSignal, QObject  # PyQt5 import eklendi
from datetime import datetime

class DatabaseManager(QObject):
    data_changed = pyqtSignal()  # Sınıf seviyesinde tanım

    def __init__(self, db_path=None):
        """Veritabanı bağlantısını başlat"""
        super().__init__()
        
        # Sinyal artık sınıf seviyesinde tanımlı
        
        try:
            # Veritabanı yolu kontrolü
            if not db_path:
                db_path = self.get_default_db_path()
                
            # Klasör yoksa oluştur
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Engine'i önce oluştur
            self.engine = create_engine(f'sqlite:///{db_path}')
            self.db_path = db_path
            
            # Veritabanı yoksa yedekten geri yükle veya yeni oluştur
            if not os.path.exists(db_path):
                self.restore_from_backup(db_path)
                
            # Session oluştur
            self.Session = sessionmaker(bind=self.engine)
            self.session = self.Session()
            
            # SQLite optimizasyonları
            self.execute("PRAGMA journal_mode = WAL")
            self.execute("PRAGMA synchronous = NORMAL")
            self.execute("PRAGMA foreign_keys = ON")
            
        except Exception as e:
            logging.error(f"Veritabanı bağlantı hatası: {e}")
            raise
            
    def restore_from_backup(self, db_path):
        """Yedekten veritabanını geri yükle"""
        try:
            backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
            
            # Önce engine oluştur
            self.engine = create_engine(f'sqlite:///{db_path}')
            
            if os.path.exists(backup_dir):
                latest_backup = max(
                    [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.bak')],
                    key=os.path.getmtime, default=None
                )
                if latest_backup:
                    shutil.copy(latest_backup, db_path)
                    logging.info(f"Yedekten veritabanı geri yüklendi: {latest_backup}")
                    return
            
            # Yedek yoksa yeni veritabanı oluştur
            logging.info("Yeni veritabanı oluşturuluyor")
            Base.metadata.create_all(self.engine)
            
        except Exception as e:
            logging.error(f"Yedekten geri yükleme hatası: {e}")
            raise

    def get_default_db_path(self):
        """Çalışma ortamına göre uygun veritabanı yolunu döndürür."""
        try:
            # PyInstaller ile paketlenmiş mi kontrol et
            if getattr(sys, 'frozen', False):
                # EXE'nin bulunduğu dizin
                base_path = os.path.dirname(sys.executable)
                db_full_path = os.path.join(base_path, 'database/tezgah_takip.db')
                logging.info(f"EXE ortamı: Veritabanı yolu: {db_full_path}")
            else:
                # Normal Python çalıştırması
                base_path = os.path.dirname(__file__)
                db_full_path = os.path.join(base_path, '..', 'database/tezgah_takip.db')
                logging.info(f"Geliştirme ortamı: Veritabanı yolu: {db_full_path}")
            
            # Yolun geçerli olduğundan emin ol
            db_dir = os.path.dirname(db_full_path)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logging.info(f"Veritabanı dizini oluşturuldu: {db_dir}")
            
            return db_full_path
        except Exception as e:
            # Hata durumunda geçici bir dizine yaz
            temp_db = os.path.join(tempfile.gettempdir(), 'tezgah_takip.db')
            logging.error(f"Veritabanı yolu hatası: {e}, geçici yol kullanılıyor: {temp_db}")
            return temp_db
    
    def execute_query(self, query, params=None):
        """Parametreli sorgu ve transaction desteği ekle"""
        try:
            with self.engine.begin() as connection:
                if params:
                    result = connection.execute(text(query), params)
                else:
                    result = connection.execute(text(query))
                return result
        except Exception as e:
            logging.error(f"Sorgu hatası: {e}")
            raise

    async def execute_query_async(self, query, params=None):
        """Asenkron veritabanı sorgusu"""
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor, 
                lambda: self.execute_query(query, params)
            )
            return result

    def create_tables(self):
        try:
            Base.metadata.create_all(self.engine)
            logging.info("Tablolar oluşturuldu")
            return True
        except Exception as e:
            logging.error(f"Tablo oluşturma hatası: {e}")
            return False

    def get_session(self):
        """Veritabanı oturumu döndürür
        UYARI: Bu metodu kullanırken, oturumu kapatmak sizin sorumluluğunuzdadır.
        Daha güvenli bir kullanım için session_scope kullanın.
        """
        return self.Session()
        
    def session_factory(self):
        """Yeni veritabanı oturumu oluşturur
        UYARI: Bu metodu kullanırken, oturumu kapatmak sizin sorumluluğunuzdadır.
        Daha güvenli bir kullanım için session_scope kullanın.
        """
        return self.Session()
        
    @contextmanager
    def session_scope(self):
        """Veritabanı oturumu için güvenli bir bağlam yöneticisi sağlar.
        Bu yöntem, oturumun otomatik olarak kapatılmasını garantiler.
        
        Kullanım:
            with db_manager.session_scope() as session:
                # session ile veritabanı işlemleri yap
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_tezgah_count(self):
        try:
            with self.Session() as session:
                count = session.query(Tezgah).count()
                return count
        except Exception as e:
            logging.error(f"Tezgah sayısı alınamadı: {e}")
            return 0
            
    def get_pending_maintenance_count(self):
        """Bakım bekleyen tezgah sayısını döndürür"""
        try:
            result = self.execute_query(
                """SELECT COUNT(*) as count FROM bakimlar 
                WHERE durum = 'Bekliyor'""",
                params=None
            )
            return result.scalar() if result else 0
        except Exception as e:
            logging.error(f"Bakım bekleyen tezgah sayısı alınamadı: {e}")
            return 0

    def get_last_maintenance_date(self):
        """Son bakım tarihini döndürür"""
        try:
            result = self.execute_query(
                """SELECT MAX(tarih) as last_date FROM bakimlar""",
                params=None
            )
            return result.scalar() if result else "Kayıt Yok"
        except Exception as e:
            logging.error(f"Son bakım tarihi alınamadı: {e}")
            return "Hata"

    def get_completed_maintenance_count(self):
        """Tamamlanan bakım sayısını döndürür"""
        try:
            result = self.execute_query(
                """SELECT COUNT(*) as count FROM bakimlar 
                WHERE durum = 'Tamamlandı'""",
                params=None
            )
            return result.scalar() if result else 0
        except Exception as e:
            logging.error(f"Tamamlanan bakım sayısı alınamadı: {e}")
            return 0

    def get_maintenance_stats(self):
        """Bakım istatistiklerini döndürür"""
        try:
            return {
                "pending": self.get_pending_maintenance_count(),
                "completed": self.get_completed_maintenance_count(),
                "last_date": self.get_last_maintenance_date()
            }
        except Exception as e:
            logging.error(f"Bakım istatistikleri alınamadı: {e}")
            return {}

    def get_system_stats(self):
        """Tüm sistem istatistiklerini tek metodda topla"""
        try:
            return {
                'tezgah_count': self.get_tezgah_count(),
                'pending_maintenance': self.get_pending_maintenance_count(),
                'completed_maintenance': self.get_completed_maintenance_count(),
                'last_maintenance': self.get_last_maintenance_date()
            }
        except Exception as e:
            logging.error(f"Sistem istatistikleri alınamadı: {e}")
            return {}

    def optimize_indexes(self):
        """Veritabanı indekslerini optimize et"""
        queries = [
            "ANALYZE sqlite_master;",
            "REINDEX;",
            "VACUUM;"
        ]
        
        for query in queries:
            try:
                self.execute_query(query, safe=False)
            except Exception as e:
                logging.warning(f"Optimizasyon hatası: {e}")

    def execute(self, query):
        try:
            cursor = self.session.bind.execute(query)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logging.error(f"Sorgu hatası: {str(e)}")
            raise

    def clean_prediction_tables(self):
        """Tahminle ilgili gereksiz tabloları temizler"""
        try:
            self.session.execute("DROP TABLE IF EXISTS model_metrics")
            self.session.execute("DROP TABLE IF EXISTS prediction_logs")
            self.session.commit()
            logging.info("Tahmin tabloları temizlendi")
        except Exception as e:
            self.session.rollback()
            logging.error(f"Tahmin tabloları temizleme hatası: {e}")

    def add_sample_data(self):
        try:
            with self.Session() as session:
                # Önce mevcut verileri kontrol et
                if session.query(Tezgah).count() > 0:
                    return False
                
                # Örnek verileri ekle
                tezgahlar = [
                    Tezgah(tezgah_no="TZ-001", lokasyon="Üretim-1", durum="Aktif"),
                    Tezgah(tezgah_no="TZ-002", lokasyon="Üretim-2", durum="Bakımda")
                ]
                session.add_all(tezgahlar)
                session.commit()
                return True
        except Exception as e:
            logging.error(f"Örnek veri ekleme hatası: {e}")
            return False

    def add_tezgah(self, tezgah_data):
        try:
            with self.Session() as session:
                tezgah = Tezgah(**tezgah_data)
                session.add(tezgah)
                session.commit()
                self.data_changed.emit()  # Sinyal gönder
                return True
        except Exception as e:
            logging.error(f"Tezgah ekleme hatası: {e}")
            return False

    def update_tezgah(self, tezgah_id, new_data):
        try:
            with self.Session() as session:
                tezgah = session.query(Tezgah).get(tezgah_id)
                for key, value in new_data.items():
                    setattr(tezgah, key, value)
                session.commit()
                self.data_changed.emit()  # Sinyal gönder
                return True
        except Exception as e:
            logging.error(f"Tezgah güncelleme hatası: {e}")
            return False

    def recreate_database(self):
        try:
            # Önce mevcut bağlantıyı kapat
            self.engine.dispose()
            
            # Tabloları sil ve yeniden oluştur
            Base.metadata.drop_all(self.engine)
            Base.metadata.create_all(self.engine)
            
            logging.info("Veritabanı başarıyla yeniden oluşturuldu")
            return True
        except Exception as e:
            logging.error(f"Veritabanı yeniden oluşturma hatası: {e}")
            return False

    def get_all_tezgahlar(self):
        """Tüm tezgahları getirir"""
        with self.Session() as session:
            return session.query(Tezgah).all()
        
    def get_today_maintenance(self):
        """Bugünkü bakım sayısını getirir"""
        with self.Session() as session:
            today = datetime.now().date()
            return session.query(Bakim).filter(
                func.date(Bakim.tarih) == today
            ).count()
        
    def get_avg_usage(self):
        """Ortalama kullanım süresini getirir"""
        with self.Session() as session:
            return session.query(
                func.avg(Tezgah.kullanim_suresi)
            ).scalar() or 0

db_manager = DatabaseManager()
