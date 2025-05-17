import time
import tracemalloc
from functools import wraps
import logging
from utils.logger import AppLogger

class PerformanceMonitor:
    def __init__(self, window=None):
        """Performans izleme sistemini başlatır"""
        self.window = window
        self.logger = AppLogger().get_logger()
        
    def start(self):
        """İzlemeyi başlat"""
        if self.window:
            self.logger.info("Performans izleme başlatıldı")
            # İzleme kodları buraya gelecek

    @staticmethod
    def measure_time(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            logging.info(f"{func.__name__} executed in {end_time-start_time:.4f} seconds")
            return result
        return wrapper

    @staticmethod
    def measure_memory(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            snapshot1 = tracemalloc.take_snapshot()
            result = func(*args, **kwargs)
            snapshot2 = tracemalloc.take_snapshot()
            
            top_stats = snapshot2.compare_to(snapshot1, 'lineno')
            for stat in top_stats[:5]:
                logging.info(f"Memory: {stat}")
            return result
        return wrapper

    @staticmethod
    def log_cpu_usage():
        import psutil
        logging.info(f"CPU Usage: {psutil.cpu_percent()}%")
        logging.info(f"Memory Usage: {psutil.virtual_memory().percent}%")
