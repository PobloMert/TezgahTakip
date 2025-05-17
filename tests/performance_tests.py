import unittest
import timeit
from memory_profiler import profile
from database.connection import DatabaseManager
from utils.performance_monitor import PerformanceMonitor

class PerformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseManager()
        cls.monitor = PerformanceMonitor()
    
    def test_query_performance(self):
        """Temel sorguların performans testi"""
        def test_query():
            self.db.execute("SELECT * FROM tezgah LIMIT 100")
        
        time = timeit.timeit(test_query, number=100)
        print(f"\n100 sorgu süresi: {time:.4f} saniye")
        self.assertLess(time, 0.5)  # 100 sorgu 0.5 saniyeden az sürmeli
    
    @profile
    def test_memory_usage(self):
        """Bellek kullanımı testi"""
        @self.monitor.measure_memory
        def run_operations():
            for _ in range(100):
                self.db.execute("SELECT * FROM bakimlar")
        
        run_operations()
    
    def test_concurrent_access(self):
        """Eşzamanlı erişim testi"""
        import threading
        
        def worker():
            self.db.execute("SELECT * FROM tezgah WHERE id = 1")
        
        threads = [threading.Thread(target=worker) for _ in range(20)]
        start_time = timeit.default_timer()
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        elapsed = timeit.default_timer() - start_time
        print(f"\n20 thread süresi: {elapsed:.4f} saniye")
        self.assertLess(elapsed, 1.0)

if __name__ == "__main__":
    unittest.main()
