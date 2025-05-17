"""
Tema yönetim sistemi
"""

import json
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QStyleFactory
from utils.system_theme import SystemThemeDetector

class ThemeManager:
    def __init__(self):
        self.themes = {
            'light': {
                'primary': '#2196F3',
                'secondary': '#2196F3',
                'background': '#FFFFFF',
                'surface': '#F5F5F5',
                'error': '#FF5252',
                'warning': '#FFC107',
                'info': '#2196F3',
                'success': '#4CAF50',
                'text_primary': '#000000',
                'text_secondary': '#616161',
                'border': '#BDBDBD',
                'shadow': '#000000',
                'highlight': '#E3F2FD'
            },
            'dark': {
                'primary': '#2196F3',
                'secondary': '#2196F3',
                'background': '#121212',
                'surface': '#1E1E1E',
                'error': '#FF5252',
                'warning': '#FFC107',
                'info': '#2196F3',
                'success': '#4CAF50',
                'text_primary': '#FFFFFF',
                'text_secondary': '#BDBDBD',
                'border': '#424242',
                'shadow': '#000000',
                'highlight': '#1976D2'
            },
            'blue': {
                'primary': '#1565C0',
                'secondary': '#1976D2',
                'background': '#E3F2FD',
                'surface': '#BBDEFB',
                'error': '#D32F2F',
                'warning': '#FFA000',
                'info': '#1976D2',
                'success': '#388E3C',
                'text_primary': '#0D47A1',
                'text_secondary': '#1976D2',
                'border': '#90CAF9',
                'shadow': '#000000',
                'highlight': '#64B5F6'
            },
            'green': {
                'primary': '#388E3C',
                'secondary': '#43A047',
                'background': '#E8F5E9',
                'surface': '#C8E6C9',
                'error': '#D32F2F',
                'warning': '#FFA000',
                'info': '#388E3C',
                'success': '#43A047',
                'text_primary': '#1B5E20',
                'text_secondary': '#388E3C',
                'border': '#A5D6A7',
                'shadow': '#000000',
                'highlight': '#81C784'
            },
            'darkblue': {
                'primary': '#0D47A1',
                'secondary': '#1976D2',
                'background': '#102027',
                'surface': '#37474F',
                'error': '#FF5252',
                'warning': '#FFC107',
                'info': '#1976D2',
                'success': '#4CAF50',
                'text_primary': '#BBDEFB',
                'text_secondary': '#90CAF9',
                'border': '#263238',
                'shadow': '#000000',
                'highlight': '#1976D2'
            }
        }
        self.settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'settings.json')
        self.current_theme = self.load_theme_setting()
        self.app = None
        
        # Sistem teması izleyici
        self.system_detector = SystemThemeDetector()
        self.system_detector.theme_changed.connect(self.handle_system_theme_change)
        self.follow_system = False

    def load_theme(self, app):
        """Uygulamaya tema uygula"""
        self.app = app
        self.apply_theme(self.current_theme)

    def apply_theme(self, theme_name):
        """Belirtilen temayı uygula"""
        if theme_name not in self.themes:
            return

        theme = self.themes[theme_name]
        self.current_theme = theme_name
        self.save_theme_setting(theme_name)

        # Palet oluşturma
        palette = QPalette()
        
        # Renkler
        primary = QColor(theme['primary'])
        secondary = QColor(theme['secondary'])
        background = QColor(theme['background'])
        surface = QColor(theme['surface'])
        text_primary = QColor(theme['text_primary'])
        text_secondary = QColor(theme['text_secondary'])
        border = QColor(theme['border'])
        shadow = QColor(theme['shadow'])

        # Palet ayarları
        palette.setColor(QPalette.Window, surface)
        palette.setColor(QPalette.WindowText, text_primary)
        palette.setColor(QPalette.Base, background)
        palette.setColor(QPalette.AlternateBase, surface)
        palette.setColor(QPalette.ToolTipBase, text_primary)
        palette.setColor(QPalette.ToolTipText, text_primary)
        palette.setColor(QPalette.Text, text_primary)
        palette.setColor(QPalette.Button, surface)
        palette.setColor(QPalette.ButtonText, text_primary)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, primary)
        palette.setColor(QPalette.Highlight, primary)
        palette.setColor(QPalette.HighlightedText, Qt.white)

        # Uygulamaya paleti uygula
        if self.app:
            self.app.setPalette(palette)
            self.app.setStyle(QStyleFactory.create('Fusion'))

    def toggle_theme(self):
        """Temayı değiştir"""
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.apply_theme(self.current_theme)

    def save_theme_setting(self, theme_name):
        """Seçilen temayı settings.json dosyasına kaydet"""
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump({'theme': theme_name}, f)
        except Exception as e:
            print(f"Tema ayarı kaydedilemedi: {e}")

    def load_theme_setting(self):
        """settings.json'dan temayı yükle, yoksa 'light' dön"""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('theme', 'light')
        except Exception as e:
            print(f"Tema ayarı okunamadı: {e}")
        return 'light'

    def get_theme_list(self):
        """Tüm tema isimlerini döndür"""
        return list(self.themes.keys())

    def get_current_theme(self):
        """Mevcut temayı döndür"""
        return self.current_theme

    def get_theme_colors(self, theme_name=None):
        """Belirtilen tema renklerini döndür"""
        if theme_name is None:
            theme_name = self.current_theme
        return self.themes.get(theme_name, self.themes['light'])

    def handle_system_theme_change(self, new_theme):
        """Sistem teması değiştiğinde otomatik uygula"""
        if self.follow_system:
            self.apply_theme(new_theme)
    
    def set_follow_system(self, follow):
        """Sistem temasını takip etme ayarı"""
        self.follow_system = follow
        if follow:
            self.apply_theme(self.system_detector.get_system_theme())

    def save_custom_theme(self, theme_name, colors):
        """Yeni özel tema kaydet"""
        self.themes[theme_name] = colors
        self.save_theme_setting(theme_name)

    def delete_theme(self, theme_name):
        """Tema sil"""
        if theme_name in self.themes and theme_name not in ['light', 'dark']:
            del self.themes[theme_name]
