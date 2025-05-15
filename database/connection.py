from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.maintenance import Base
import os
import sys
import logging
import tempfile
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path='tezgah_takip.db'):
        # İki farklı ortam için uygun veritabanı yolunu hesapla:
        # 1. Normal Python çalıştırması
        # 2. PyInstaller ile paketlenmiş EXE
        self.db_path = self.get_database_path(db_path)
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        self.Session = sessionmaker(bind=self.engine)

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
    
    def create_tables(self):
        """Veritabanı tablolarını oluşturur."""
        try:
            # Base.metadata.drop_all(self.engine)  # Tüm tabloları silmek için (tehlikeli)
            Base.metadata.create_all(self.engine)
            logging.info(f'Veritabanı tabloları oluşturuldu veya mevcut tablolar kontrol edildi. DB Yolu: {self.db_path}')
            
            # Tablo oluşturma başarılı mı diye kontrol et
            from sqlalchemy import inspect
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            logging.info(f"Mevcut tablolar: {tables}")
            
            return True
        except Exception as e:
            logging.error(f'Tablo oluşturma hatası: {e}')
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

db_manager = DatabaseManager()
