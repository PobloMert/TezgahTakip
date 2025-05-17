"""
Font yönetim sistemi
"""

import json
import os
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont

class FontManager:
    font_changed = pyqtSignal(QFont)  # Yeni: Font değişiklik sinyali
    
    def __init__(self):
        self.settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'settings.json')
        
        # Varsayılan font ayarları
        self.default_font = {
            'family': 'Arial',
            'size': 10,
            'bold': False,
            'italic': False,
            'scale': 1.0  # Yeni: Font ölçeklendirme faktörü
        }
        
        # Mevcut font ayarlarını yükle
        self.current_font = self.load_font_setting()
    
    def get_font(self, scale=1.0):
        """Mevcut font ayarlarına göre QFont nesnesi oluştur"""
        font = QFont()
        font.setFamily(self.current_font['family'])
        
        # Ölçeklendirilmiş font boyutu
        base_size = self.current_font['size']
        scaled_size = int(base_size * self.current_font['scale'] * scale)
        font.setPointSize(scaled_size)
        
        font.setBold(self.current_font['bold'])
        font.setItalic(self.current_font['italic'])
        return font
    
    def set_font(self, family, size, bold=False, italic=False):
        """Yeni font ayarlarını kaydet"""
        self.current_font = {
            'family': family,
            'size': size,
            'bold': bold,
            'italic': italic,
            'scale': self.current_font['scale']  # Ölçeklendirme faktörünü koru
        }
        self.save_font_setting()
    
    def set_font_scale(self, scale_factor):
        """Global font ölçeklendirme faktörünü ayarla"""
        self.current_font['scale'] = max(0.5, min(2.0, scale_factor))  # 0.5-2.0 aralığı
        self.save_font_setting()
        self.font_changed.emit(self.get_font())
    
    def get_font_scale(self):
        """Mevcut font ölçeklendirme faktörünü döndür"""
        return self.current_font.get('scale', 1.0)
    
    def save_font_setting(self):
        """Font ayarlarını settings.json dosyasına kaydet"""
        try:
            # Mevcut ayarları oku (varsa)
            settings = {}
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            # Font ayarlarını güncelle
            settings['font'] = self.current_font
            
            # Güncellenmiş ayarları kaydet
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Font ayarı kaydedilemedi: {e}")
    
    def load_font_setting(self):
        """settings.json'dan font ayarlarını yükle"""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    if 'font' in settings:
                        return settings['font']
        except Exception as e:
            print(f"Font ayarı okunamadı: {e}")
        return self.default_font
