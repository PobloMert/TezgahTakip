"""
Test konfigürasyonları
"""
import pytest
from database.connection import DBManager
import os

@pytest.fixture(scope="module")
def test_db():
    """Test veritabanı bağlantısı"""
    db_path = "test_tezgah.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DBManager(db_path)
    db.create_tables()
    yield db
    
    # Test sonrası temizlik
    db.connection.close()
    if os.path.exists(db_path):
        os.remove(db_path)
