import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app import TezgahTakipApp
from database.connection import DatabaseManager
from PyQt5.QtWidgets import QApplication

class TestTezgahTakip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)
        cls.db_manager = DatabaseManager(":memory:")
        
    def test_database_connection(self):
        """Veritabanı bağlantı testi"""
        self.assertTrue(self.db_manager.engine is not None)
        
    def test_main_window_creation(self):
        """Ana pencere oluşturma testi"""
        window = TezgahTakipApp(self.db_manager)
        self.assertEqual(window.windowTitle(), "Tezgah Takip Programı")
        
    def test_report_generation(self):
        """Rapor oluşturma testi"""
        window = TezgahTakipApp(self.db_manager)
        report_data = [
            {'machine_id': 'TZ-001', 'maintenance_count': 5, 'last_maintenance': '2023-01-01', 'status': 'Aktif'}
        ]
        
        try:
            window.export_to_pdf(report_data, "test_report")
            self.assertTrue(os.path.exists("test_report.pdf"))
        finally:
            if os.path.exists("test_report.pdf"):
                os.remove("test_report.pdf")

if __name__ == "__main__":
    unittest.main()
