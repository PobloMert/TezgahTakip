"""
Veritabanı bağlantı modülü (Güvenli Sürüm)
"""
import sqlite3
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.maintenance import Base
import os
import sys
import tempfile
from contextlib import contextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor

class DatabaseManager:
    def __init__(self, db_path: str = 'tezgah_takip.db'):
        # İki farklı ortam için uygun veritabanı yolunu hesapla:
        # 1. Normal Python çalıştırması
        # 2. PyInstaller ile paketlenmiş EXE
        self.db_path = self.get_database_path(db_path)
        self.engine = create_engine(
            f'sqlite:///{self.db_path}',
            connect_args={'timeout': 30, 'check_same_thread': False}
        )
        self.Session = sessionmaker(bind=self.engine)
        self.connection = sqlite3.connect(self.db_path)
        
        # SQLite optimizasyon PRAGMA'ları
        self.connection.execute('PRAGMA journal_mode = WAL')
        self.connection.execute('PRAGMA synchronous = NORMAL')
        self.connection.execute('PRAGMA cache_size = -10000')
        self.connection.execute('PRAGMA temp_store = MEMORY')
        self.connection.execute('PRAGMA foreign_keys = ON')
        
        # Önbellek mekanizması
        self._cache = {}
        self.cache_timeout = 300  # 5 dakika

    def get_database_path(self, db_path):
        """Çalışma ortamına göre uygun veritabanı yolunu döndürür."""
        try:
            # PyInstaller ile paketlenmiş mi kontrol et
            if getattr(sys, 'frozen', False):
                # EXE'nin bulunduğu dizin
                base_path = os.path.dirname(sys.executable)
                db_full_path = os.path.join(base_path, db_path)
                logging.info(f"EXE ortamı: Veritabanı yolu: {db_full_path}")
            else:
                # Normal Python çalıştırması
                base_path = os.path.dirname(__file__)
                db_full_path = os.path.join(base_path, '..', db_path)
                logging.info(f"Geliştirme ortamı: Veritabanı yolu: {db_full_path}")
            
            # Yolun geçerli olduğundan emin ol
            db_dir = os.path.dirname(db_full_path)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logging.info(f"Veritabanı dizini oluşturuldu: {db_dir}")
            
            return db_full_path
        except Exception as e:
            # Hata durumunda geçici bir dizine yaz
            temp_db = os.path.join(tempfile.gettempdir(), db_path)
            logging.error(f"Veritabanı yolu hatası: {e}, geçici yol kullanılıyor: {temp_db}")
            return temp_db
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None, safe: bool = True) -> List[Dict[str, Any]]:
        """
        Güvenli sorgu çalıştırma
        :param safe: True ise parametre binding zorunlu
        """
        if safe and not params:
            raise ValueError("Güvenlik nedeniyle parametresiz sorgu yasak")
            
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params if params else {})
            
            if query.strip().upper().startswith('SELECT'):
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            self.connection.commit()
            return []
            
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Sorgu hatası: {str(e)}")
            raise

    async def execute_query_async(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Asenkron veritabanı sorgusu"""
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor, 
                lambda: self.execute_query(query, params)
            )
            return result

    def create_tables(self):
        """Tüm veritabanı tablolarını oluştur"""
        try:
            # Önce mevcut bağlantıları kapat
            if hasattr(self, 'engine') and self.engine:
                self.engine.dispose()
                
            # Veritabanı dosyasını silmeyi dene (eğer varsa)
            if os.path.exists(self.db_path):
                try:
                    os.remove(self.db_path)
                    logging.info(f"Eski veritabanı silindi: {self.db_path}")
                except PermissionError:
                    logging.warning(f"Veritabanı silinemedi, zaten temizlenmiş olabilir: {self.db_path}")
                
            # Yeni tabloları oluştur
            Base.metadata.create_all(self.engine)
            logging.info("Tüm tablolar başarıyla oluşturuldu")
        except Exception as e:
            logging.error(f"Tablo oluşturma hatası: {e}")
            raise

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
        """Tezgah tablosundaki kayıt sayısını döndürür"""
        try:
            result = self.execute_query(
                "SELECT COUNT(*) as count FROM tezgah",
                params={}, safe=False
            )
            return result[0]["count"] if result else 0
        except Exception as e:
            logging.error(f"Tezgah sayısı alınamadı: {e}")
            return 0
            
    def get_pending_maintenance_count(self):
        """Bakım bekleyen tezgah sayısını döndürür"""
        try:
            result = self.execute_query(
                """SELECT COUNT(*) as count FROM bakimlar 
                WHERE durum = 'Bekliyor'""",
                params={}, safe=False
            )
            return result[0]["count"] if result else 0
        except Exception as e:
            logging.error(f"Bakım bekleyen tezgah sayısı alınamadı: {e}")
            return 0

    def get_last_maintenance_date(self):
        """Son bakım tarihini döndürür"""
        try:
            result = self.execute_query(
                """SELECT MAX(tarih) as last_date FROM bakimlar""",
                params={}, safe=False
            )
            return result[0]["last_date"] if result and result[0]["last_date"] else "Kayıt Yok"
        except Exception as e:
            logging.error(f"Son bakım tarihi alınamadı: {e}")
            return "Hata"

    def get_completed_maintenance_count(self):
        """Tamamlanan bakım sayısını döndürür"""
        try:
            result = self.execute_query(
                """SELECT COUNT(*) as count FROM bakimlar 
                WHERE durum = 'Tamamlandı'""",
                params={}, safe=False
            )
            return result[0]["count"] if result else 0
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

db_manager = DatabaseManager()
