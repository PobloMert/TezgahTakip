"""
Veritabanı işlemleri testleri
"""
from database.connection import DBManager
import pytest

class TestDatabase:
    def test_table_creation(self, test_db):
        """Temel tabloların oluşturulduğunu test eder"""
        tables = test_db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert 'bakimlar' in table_names
        assert 'pil_degisimler' in table_names
        assert 'tezgah' in table_names

    def test_safe_query(self, test_db):
        """Güvenli sorgu çalıştırma testi"""
        # Geçerli parametreli sorgu
        result = test_db.execute_query(
            "SELECT * FROM sqlite_master WHERE type=:table_type",
            params={'table_type': 'table'},
            safe=True
        )
        assert isinstance(result, list)
        
        # Güvensiz sorgu denemesi
        with pytest.raises(ValueError):
            test_db.execute_query("SELECT * FROM sqlite_master", safe=True)
