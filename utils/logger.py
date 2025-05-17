import logging
import logging.handlers
import os
from datetime import datetime

class AppLogger:
    def __init__(self, app_name="TezgahTakip", log_dir="logs"):
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Log klasörü yoksa oluştur
        os.makedirs(log_dir, exist_ok=True)
        
        # Log dosya adı
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler (10MB'da rotate)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Handlers ekle
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def get_logger(self):
        return self.logger
    
    def sanitize_log(self, message):
        """Hassas verileri loglardan temizle"""
        sensitive_keys = ['password', 'token', 'secret']
        if isinstance(message, dict):
            return {k: '***REDACTED***' if any(sk in k.lower() for sk in sensitive_keys) else v 
                   for k, v in message.items()}
        return message
