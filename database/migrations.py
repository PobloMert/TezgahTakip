from alembic import context
from sqlalchemy import engine_from_config
from models.maintenance import Base
import logging
import os

# Alembic yapılandırması
def run_migrations():
    """Veritabanı migrasyonlarını çalıştır"""
    config = context.config
    
    # Veritabanı bağlantısı
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            compare_type=True
        )
        
        with context.begin_transaction():
            context.run_migrations()

# Otomatik yedekleme
class AutoBackup:
    def __init__(self, db_path):
        self.db_path = db_path
        
    def create_backup(self):
        """Günlük veritabanı yedeği oluştur"""
        import shutil
        import datetime
        
        backup_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'tezgah_takip_{timestamp}.db')
        
        try:
            shutil.copy2(self.db_path, backup_path)
            logging.info(f"Yedek oluşturuldu: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Yedekleme hatası: {e}")
            return False
