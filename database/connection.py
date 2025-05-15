from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.maintenance import Base
import os
import logging
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path='tezgah_takip.db'):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', db_path)
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        # Bu yöntem artık tabloları yeniden oluşturmayacak, sadece bildirim gönderecek
        logging.info('Mevcut veritabanı kullanılıyor, tablolar değiştirilmeyecek.')

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
