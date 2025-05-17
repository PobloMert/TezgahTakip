"""
Sistem font entegrasyonu
"""

import platform
from PyQt5.QtGui import QFont

def get_system_font():
    """İşletim sistemine göre varsayılan fontu döndür"""
    system = platform.system()
    
    if system == "Windows":
        return QFont("Segoe UI", 9)
    elif system == "Darwin":  # macOS
        return QFont(".AppleSystemUIFont", 13)
    else:  # Linux ve diğerleri
        return QFont("DejaVu Sans", 10)
