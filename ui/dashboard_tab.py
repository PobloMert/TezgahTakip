import sys
import datetime
import traceback
from typing import Dict, Any, Optional, List, Tuple

# PyQt5 importları
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
                            QComboBox, QDateEdit, QCheckBox, QLineEdit, QSplitter, QGridLayout,
                            QScrollArea, QSizePolicy, QTabWidget)
from PyQt5.QtGui import QPixmap, QColor, QFont, QIcon, QPainter
from PyQt5.QtCore import Qt, QTimer, QDate, QSize, QRectF, QMargins

# PyQtChart importları
from PyQt5.QtChart import (QChart, QChartView, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis,
                          QPieSeries, QPieSlice, QLineSeries, QDateTimeAxis, QSplineSeries, QScatterSeries)

# Veritabanı importları
from database.connection import db_manager
from models.bakim import Bakim, PilDegisim, Tezgah  # Doğru import yolu
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

# Kendi modüllerimiz
from utils.chart_data_provider import ChartDataProvider

class DashboardTab(QWidget):
    """Dashboard sekme sınıfı - PyQtChart kullanarak grafikler gösterir"""
    
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.setObjectName("dashboardTab")
        
        # Versiyon bilgisi
        self.version = "2.0.0"
        
        # Ana layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Filtre durumunu başlat
        self.filter_active = False
        
        # İstatistik ve widget değişkenlerini başlat
        self.stats = {
            'toplam_tezgah': 0,
            'toplam_bakim': 0,
            'toplam_pil_degisim': 0,
            'ortalama_bakim': 0,
            'son_guncelleme': '-',
            'son_bakim_tarihi': '-',
            'son_pil_degisim': '-'
        }
        self.stat_widgets = {}
        
        # Veri sağlayıcı
        self.data_provider = ChartDataProvider
        
        # Filtre çubuğu
        self.create_filter_bar()
        
        # İstatistik kartları
        self.create_stat_cards()
        
        # Grafikler bölümü oluştur
        self.charts_layout = QGridLayout()
        self.charts_layout.setSpacing(15)
        
        # Grafik tutucuları
        self.maintenance_chart_view = None
        self.battery_chart_view = None 
        self.monthly_maintenance_chart_view = None
        self.top_tezgahlar_chart_view = None
        self.maintenance_distribution_chart_view = None
        
        # Ana layout içine yerleştir
        chart_frame = QFrame()
        chart_frame.setFrameShape(QFrame.StyledPanel)
        chart_frame.setLayout(self.charts_layout)
        
        # Scroll area oluştur (grafiklerin kayması için)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(chart_frame)
        
        self.main_layout.addWidget(scroll_area)
        
        # Güncelleme butonu
        self.create_refresh_button()
        
        # İlk veri güncellemesi
        self.refresh_dashboard()
        
        # Filtreleme ve seçim için değişkenler
        self.selected_tezgah = None
        self.stats = {}
        self.session = None
        self.filter_active = False
        
        # Otomatik güncelleme için zamanlama
        self.update_timer = QTimer()
        self.update_timer.setInterval(60000)  # 60 saniyede bir güncelle
        self.update_timer.timeout.connect(self.refresh_dashboard)
        
        # Görünürlük takibi
        self.is_tab_visible = False
        self.is_active = False
        
        # İstatistik widget'ları için sözlük
        self.stat_widgets = {}
    
    def create_filter_bar(self):
        """
        Filtreleme çubuğunu oluştur
        """
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.StyledPanel)
        filter_layout = QHBoxLayout(filter_frame)
        
        # Başlık etiketi
        title_label = QLabel("İstatistik Gösterge Paneli")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        
        # Tezgah filtresi
        tezgah_label = QLabel("Tezgah:")
        self.tezgah_combo = QComboBox()
        self.tezgah_combo.addItem("Tümü", None)
        self.tezgah_combo.currentIndexChanged.connect(self.on_filter_changed)
        
        # Tarih filtresi
        date_label = QLabel("Tarih Aralığı:")
        self.date_range_combo = QComboBox()
        self.date_range_combo.addItem("Son 30 Gün", 30)
        self.date_range_combo.addItem("Son 90 Gün", 90)
        self.date_range_combo.addItem("Son 180 Gün", 180)
        self.date_range_combo.addItem("Son 1 Yıl", 365)
        self.date_range_combo.addItem("Tüm Zamanlar", 0)
        self.date_range_combo.currentIndexChanged.connect(self.on_filter_changed)
        
        # Layouta ekle
        filter_layout.addWidget(title_label)
        filter_layout.addStretch()
        filter_layout.addWidget(tezgah_label)
        filter_layout.addWidget(self.tezgah_combo)
        filter_layout.addWidget(date_label)
        filter_layout.addWidget(self.date_range_combo)
        
        self.main_layout.addWidget(filter_frame)
    
    def create_stat_cards(self):
        """
        İstatistik kartlarını oluştur
        """
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.StyledPanel)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(15)
        
        # Tezgah kartı
        self.tezgah_card = self._create_stat_card("Toplam Tezgah", "0", "#3498db")
        
        # Bakım kartı
        self.bakim_card = self._create_stat_card("Toplam Bakım", "0", "#2ecc71")
        
        # Pil değişim kartı
        self.pil_card = self._create_stat_card("Toplam Pil Değişimi", "0", "#e74c3c")
        
        # Son güncelleme
        self.update_card = self._create_stat_card("Son Güncelleme", "-", "#95a5a6")
        
        # Ortalama bakım
        self.avg_card = self._create_stat_card("Ortalama Bakım/Tezgah", "0", "#9b59b6")
        
        # Layouta ekle
        stats_layout.addWidget(self.tezgah_card)
        stats_layout.addWidget(self.bakim_card)
        stats_layout.addWidget(self.pil_card)
        stats_layout.addWidget(self.avg_card)
        stats_layout.addWidget(self.update_card)
        
        self.main_layout.addWidget(stats_frame)
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """
        İstatistik kartı oluştur
        
        Args:
            title (str): Kart başlığı
            value (str): Kart değeri
            color (str): Kart rengi (hex kodu)
            
        Returns:
            QFrame: Oluşturulan kart widget'ı
        """
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"background-color: {color}; color: white; border-radius: 5px;")
        card.setMinimumHeight(100)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(card)
        
        # Başlık
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Değer
        value_label = QLabel(value)
        key_name = title.lower().replace(' ', '_')
        value_label.setObjectName(f"{key_name}_value")
        value_label.setStyleSheet("font-size: 24pt; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        
        # Widget'i kayıt altına al (güncellemeler için)
        self.stat_widgets[key_name] = value_label
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        return card
    
    def create_refresh_button(self):
        """
        Güncelleme butonu oluştur
        """
        refresh_btn = QPushButton("Gösterge Panelini Güncelle")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_dashboard)
        
        # Ana layouta ekle (en alt)
        self.main_layout.addWidget(refresh_btn)
    
    def refresh_dashboard(self):
        """
        Dashboard verilerini güncelle
        """
        try:
            self.session = self.db_manager.get_session()
            
            # Temel istatistikler
            stats = {
                'toplam_tezgah': self.session.query(Tezgah).count(),
                'toplam_bakim': self.session.query(Bakim).count(),
                'toplam_pil_degisim': self.session.query(PilDegisim).count()
            }
            
            # Combobox'ı güncelle
            self.tezgah_combo.clear()
            tezgahlar = self.session.query(Tezgah).order_by(Tezgah.numarasi).all()
            for tezgah in tezgahlar:
                self.tezgah_combo.addItem(tezgah.numarasi, tezgah.id)
                
            # Dashboard'ı güncelle
            self.update_stats(stats)
            
        except Exception as e:
            print(f"Dashboard güncelleme hatası: {e}")
        finally:
            if hasattr(self, 'session') and self.session:
                self.session.close()
    
    def _populate_tezgah_combo(self):
        """
        Tezgah combobox'ını veritabanından gelen verilerle doldur
        """
        try:
            # Mevcut seçimi kaydet
            current_index = self.tezgah_combo.currentIndex()
            
            # Combobox'ı temizle (ilk öğe hariç)
            while self.tezgah_combo.count() > 1:
                self.tezgah_combo.removeItem(1)
            
            # Tezgahları sorgula
            tezgahlar = self.session.query(Tezgah).order_by(Tezgah.numarasi).all()
            
            # Tezgahları combobox'a ekle
            for tezgah in tezgahlar:
                self.tezgah_combo.addItem(f"Tezgah {tezgah.numarasi}", tezgah.id)
            
            # Önceki seçimi geri yükle veya ilk öğeyi seç
            if current_index >= 0 and current_index < self.tezgah_combo.count():
                self.tezgah_combo.setCurrentIndex(current_index)
            else:
                self.tezgah_combo.setCurrentIndex(0)
        
        except Exception as e:
            print(f"Tezgah combobox doldurma hatası: {e}")
            
    def _update_stat_cards(self):
        """
        İstatistik kartlarını güncelle
        """
        try:
            # Sonuçların boş olma durumunu kontrol et
            if not hasattr(self, 'stats') or self.stats is None:
                self.stats = {
                    'toplam_tezgah': 0,
                    'toplam_bakim': 0,
                    'toplam_pil_degisim': 0,
                    'ortalama_bakim': 0,
                    'son_guncelleme': '-',
                    'son_bakim_tarihi': '-',
                    'son_pil_degisim': '-'
                }
            
            # stat_widgets'in tanımlı olduğundan emin ol
            if not hasattr(self, 'stat_widgets') or self.stat_widgets is None:
                self.stat_widgets = {}
                
            # Tezgah sayısı
            if 'toplam_tezgah' in self.stat_widgets:
                self.stat_widgets['toplam_tezgah'].setText(str(self.stats.get('toplam_tezgah', 0)))
            
            # Bakım sayısı
            if 'toplam_bakım' in self.stat_widgets:
                self.stat_widgets['toplam_bakım'].setText(str(self.stats.get('toplam_bakim', 0)))
            
            # Pil değişim sayısı
            if 'toplam_pil_değişimi' in self.stat_widgets:
                self.stat_widgets['toplam_pil_değişimi'].setText(str(self.stats.get('toplam_pil_degisim', 0)))
            
            # Ortalama bakım
            if 'ortalama_bakım/tezgah' in self.stat_widgets:
                self.stat_widgets['ortalama_bakım/tezgah'].setText(str(self.stats.get('ortalama_bakim', 0)))
            
            # Son güncelleme
            if 'son_güncelleme' in self.stat_widgets:
                self.stat_widgets['son_güncelleme'].setText(str(self.stats.get('son_guncelleme', '-')))
        
        except Exception as e:
            print(f"İstatistik gösterimi güncelleme hatası: {e}")
            import traceback
            print(traceback.format_exc())
    
    def on_filter_changed(self):
        """
        Filtre değiştiğinde tetiklenir
        """
        # Seçili tezgahı güncelle
        if self.tezgah_combo.currentIndex() > 0:
            self.selected_tezgah = self.tezgah_combo.currentData()
        else:
            self.selected_tezgah = None
        
        # Dashboard'u güncelle
        self.refresh_dashboard()
        
    def _update_charts(self):
        """
        Tüm grafikleri güncelle/oluştur
        """
        try:
            # Grid'i temizle
            self._clear_charts_layout()
            
            # Bakım istatistiği grafikleri
            self.maintenance_chart_view = self._create_maintenance_chart()
            self.charts_layout.addWidget(self.maintenance_chart_view, 0, 0)
            
            # Pil değişim grafikleri
            self.battery_chart_view = self._create_battery_chart()
            self.charts_layout.addWidget(self.battery_chart_view, 0, 1)
            
            # Aylık bakım grafiği
            self.monthly_maintenance_chart_view = self._create_monthly_maintenance_chart()
            self.charts_layout.addWidget(self.monthly_maintenance_chart_view, 1, 0, 1, 2)
            
            # En çok bakım yapılan tezgahlar
            self.top_tezgahlar_chart_view = self._create_top_tezgahlar_chart()
            self.charts_layout.addWidget(self.top_tezgahlar_chart_view, 2, 0)
            
            # Bakım dağılımı (pasta grafik)
            self.maintenance_distribution_chart_view = self._create_maintenance_distribution_chart()
            self.charts_layout.addWidget(self.maintenance_distribution_chart_view, 2, 1)
            
        except Exception as e:
            print(f"Grafik güncelleme hatası: {e}")
            print(traceback.format_exc())
    
    def _clear_charts_layout(self):
        """
        Önceki grafikleri temizle
        """
        # Tüm grafik görünümlerini temizle
        for i in reversed(range(self.charts_layout.count())): 
            item = self.charts_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
    
    def _create_maintenance_chart(self) -> QChartView:
        """
        Toplam bakım sayısını gösteren bar grafik oluştur
        
        Returns:
            QChartView: Oluşturulan grafik görünümü
        """
        try:
            # Bakım sayısını al
            maintenance_count = self.stats.get('toplam_bakim', 0)
            
            # Bar seti oluştur
            bar_set = QBarSet("Bakım Sayısı")
            bar_set.append(maintenance_count)
            bar_set.setColor(QColor("#2ecc71"))
            
            # Seriyi oluştur ve bar setini ekle
            series = QBarSeries()
            series.append(bar_set)
            
            # Chart oluştur ve seriyi ekle
            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("Toplam Bakım Sayısı")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            chart.setBackgroundVisible(False)
            chart.legend().setVisible(False)
            
            # Eksen ayarlarını yap
            categories = ["Bakım Sayısı"]
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)
            
            axis_y = QValueAxis()
            axis_y.setRange(0, max(maintenance_count * 1.2, 10))  # Biraz boşluk bırak
            axis_y.setLabelFormat("%d")
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)
            
            # QChartView oluştur
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            chart_view.setMinimumHeight(250)
            chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            return chart_view
            
        except Exception as e:
            print(f"Bakım grafiği oluşturma hatası: {e}")
            # Boş grafik döndür
            chart = QChart()
            chart.setTitle("Bakım Grafiği Oluşturulamadı")
            chart_view = QChartView(chart)
            return chart_view
    
    def _create_battery_chart(self) -> QChartView:
        """
        Toplam pil değişim sayısını gösteren bar grafik oluştur
        
        Returns:
            QChartView: Oluşturulan grafik görünümü
        """
        try:
            # Pil değişim sayısını al
            battery_count = self.stats.get('toplam_pil_degisim', 0)
            
            # Bar seti oluştur
            bar_set = QBarSet("Pil Değişim Sayısı")
            bar_set.append(battery_count)
            bar_set.setColor(QColor("#e74c3c"))
            
            # Seriyi oluştur ve bar setini ekle
            series = QBarSeries()
            series.append(bar_set)
            
            # Chart oluştur ve seriyi ekle
            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("Toplam Pil Değişim Sayısı")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            chart.setBackgroundVisible(False)
            chart.legend().setVisible(False)
            
            # Eksen ayarlarını yap
            categories = ["Pil Değişim"]
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)
            
            axis_y = QValueAxis()
            axis_y.setRange(0, max(battery_count * 1.2, 10))  # Biraz boşluk bırak
            axis_y.setLabelFormat("%d")
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)
            
            # QChartView oluştur
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            chart_view.setMinimumHeight(250)
            chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            return chart_view
            
        except Exception as e:
            print(f"Pil değişim grafiği oluşturma hatası: {e}")
            # Boş grafik döndür
            chart = QChart()
            chart.setTitle("Pil Değişim Grafiği Oluşturulamadı")
            chart_view = QChartView(chart)
            return chart_view
            
    def _create_monthly_maintenance_chart(self) -> QChartView:
        """
        Aylık bakım istatistiklerini gösteren çizgi grafik oluştur
        
        Returns:
            QChartView: Oluşturulan grafik görünümü
        """
        try:
            # Seçili tarih aralığından gösterilecek ay sayısını belirle
            selected_range = self.date_range_combo.currentData()
            months_to_show = 12
            if selected_range == 30:
                months_to_show = 6
            elif selected_range == 90:
                months_to_show = 9
            elif selected_range == 180:
                months_to_show = 12
            elif selected_range == 365:
                months_to_show = 24
            
            # Session null kontrolü
            if not hasattr(self, 'session') or self.session is None:
                # Yeni bir session aç
                with self.db_manager.session_scope() as temp_session:
                    # Verileri al
                    months, maintenance_counts = self.data_provider.get_maintenance_by_month(temp_session, months_to_show)
            else:
                # Verileri al
                months, maintenance_counts = self.data_provider.get_maintenance_by_month(self.session, months_to_show)
            
            # Çizgi serisi oluştur
            series = QLineSeries()
            series.setName("Aylık Bakım Sayısı")
            
            # Veri noktası serisi oluştur (görsel efekt için)
            scatter_series = QScatterSeries()
            scatter_series.setName("Bakım Sayısı")
            scatter_series.setMarkerSize(10)
            
            # Veri noktalarını ekle
            for i, (month, count) in enumerate(zip(months, maintenance_counts)):
                series.append(i, count)
                scatter_series.append(i, count)
            
            # Chart oluştur
            chart = QChart()
            chart.addSeries(series)
            chart.addSeries(scatter_series)
            chart.setTitle("Aylık Bakım İstatistikleri")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # X ekseni ayarları
            axis_x = QBarCategoryAxis()
            axis_x.append(months)
            chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)
            scatter_series.attachAxis(axis_x)
            
            # Y ekseni ayarları
            axis_y = QValueAxis()
            max_value = max(maintenance_counts) if maintenance_counts else 10
            axis_y.setRange(0, max_value * 1.2 or 10)
            axis_y.setLabelFormat("%d")
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)
            scatter_series.attachAxis(axis_y)
            
            # Görsel ayarlar
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)
            
            # QChartView oluştur
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            chart_view.setMinimumHeight(300)
            
            return chart_view
            
        except Exception as e:
            print(f"Aylık bakım grafiği oluşturma hatası: {e}")
            print(traceback.format_exc())
            # Boş grafik döndür
            chart = QChart()
            chart.setTitle("Aylık Bakım Grafiği Oluşturulamadı")
            chart_view = QChartView(chart)
            return chart_view
    
    def _create_top_tezgahlar_chart(self) -> QChartView:
        """
        En çok bakım yapılan tezgahları gösteren bar grafik oluştur
        
        Returns:
            QChartView: Oluşturulan grafik görünümü
        """
        try:
            # Session null kontrolü
            if not hasattr(self, 'session') or self.session is None:
                # Yeni bir session aç
                with self.db_manager.session_scope() as temp_session:
                    # En çok bakım yapılan tezgahların verilerini al
                    tezgah_numaralari, bakim_sayilari = self.data_provider.get_top_tezgahlar_by_maintenance(temp_session, 5)
            else:
                # En çok bakım yapılan tezgahların verilerini al
                tezgah_numaralari, bakim_sayilari = self.data_provider.get_top_tezgahlar_by_maintenance(self.session, 5)
            
            if not tezgah_numaralari or not bakim_sayilari:
                raise ValueError("Tezgah bakım verisi bulunamadı.")
            
            # Bar seti oluştur
            bar_set = QBarSet("Bakım Sayısı")
            bar_set.append(bakim_sayilari)
            bar_set.setColor(QColor("#3498db"))
            
            # Bar serisi oluştur
            series = QBarSeries()
            series.append(bar_set)
            
            # Chart oluştur
            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("En Çok Bakım Yapılan Tezgahlar")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # X ekseni ayarları
            axis_x = QBarCategoryAxis()
            axis_x.append(tezgah_numaralari)
            chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)
            
            # Y ekseni ayarları
            axis_y = QValueAxis()
            max_value = max(bakim_sayilari) if bakim_sayilari else 10
            axis_y.setRange(0, max_value * 1.2 or 10)
            axis_y.setLabelFormat("%d")
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)
            
            # Görsel ayarlar
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)
            
            # QChartView oluştur
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            chart_view.setMinimumHeight(250)
            
            return chart_view
            
        except Exception as e:
            print(f"Top tezgahlar grafiği oluşturma hatası: {e}")
            # Boş grafik döndür
            chart = QChart()
            chart.setTitle("Tezgah Bakım Grafiği Oluşturulamadı")
            chart_view = QChartView(chart)
            return chart_view
            
    def _create_maintenance_distribution_chart(self) -> QChartView:
        """
        Bakım dağılımını gösteren pasta grafik oluştur
        
        Returns:
            QChartView: Oluşturulan grafik görünümü
        """
        try:
            # Session null kontrolü
            if not hasattr(self, 'session') or self.session is None:
                # Yeni bir session aç
                with self.db_manager.session_scope() as temp_session:
                    # Tür bazlı bakım dağılımını al
                    categories, percentages = self.data_provider.get_maintenance_distribution_by_tezgah(temp_session)
            else:
                # Tür bazlı bakım dağılımını al
                categories, percentages = self.data_provider.get_maintenance_distribution_by_tezgah(self.session)
            
            if not categories or not percentages:
                raise ValueError("Bakım dağılımı verisi bulunamadı.")
            
            # Pasta serisi oluştur
            series = QPieSeries()
            series.setName("Bakım Dağılımı")
            
            # Renkler - kategorilere göre sabit renk atama
            colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c", "#34495e"]
            
            # Veri dilimlerini ekle
            for i, (category, percentage) in enumerate(zip(categories, percentages)):
                slice = series.append(f"{category} ({percentage}%)", percentage)
                color_index = i % len(colors)
                slice.setColor(QColor(colors[color_index]))
                if percentage > 10:  # Belirli bir yüzdenin üzerindeki dilimleri vurgula
                    slice.setExploded(True)
                    slice.setLabelVisible(True)
            
            # Chart oluştur
            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("Bakım Dağılımı (Tür Bazlı)")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Görsel ayarlar
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignRight)
            
            # QChartView oluştur
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            chart_view.setMinimumHeight(250)
            
            return chart_view
            
        except Exception as e:
            print(f"Bakım dağılımı grafiği oluşturma hatası: {e}")
            # Boş grafik döndür
            chart = QChart()
            chart.setTitle("Bakım Dağılımı Grafiği Oluşturulamadı")
            chart_view = QChartView(chart)
            return chart_view
        self.date_range = {'start': None, 'end': None}
        self.filter_active = False
        self.is_tab_visible = False  # Sekme görünürlük durumu
        self.is_active = False  # Ana uygulama tarafından kontrol edilen aktiflik durumu
        
        # Canlı güncelleme için zamanlayıcı
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.refresh_dashboard)
        
        # Veriye dayalı renk kodları ve stil ayarları
        self.status_colors = {
            'normal': '#2ecc71',  # Yeşil
            'warning': '#f39c12', # Turuncu
            'critical': '#e74c3c', # Kırmızı
            'inactive': '#95a5a6'  # Gri
        }
        
        # Set yerine string key'ler kullan
        self.color_mapping = {
            'normal': '#2ecc71',
            'warning': '#f39c12',
            'critical': '#e74c3c'
        }
        
        self.init_ui()
        
        # Zamanlayıcı başlatılması showEvent'te yapılacak
        self.setStyleSheet('''
            QLabel {
                font-weight: bold;
                color: #2c3e50;
            }
            QFrame {
                background-color: rgba(255, 255, 255, 230);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                padding: 15px;
            }
        ''')

    def init_ui(self):
        """Arayüzü yeni istatistik metoduna göre güncelle"""
        stats = self.db_manager.get_system_stats()
        
        top_row = QHBoxLayout()
        top_row.addWidget(self.create_stat_widget("Toplam Tezgah", stats.get('tezgah_count', 0)))
        top_row.addWidget(self.create_stat_widget("Bakım Bekleyen", stats.get('pending_maintenance', 0)))
        top_row.addWidget(self.create_stat_widget("Tamamlanan Bakım", stats.get('completed_maintenance', 0)))
        
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.create_stat_widget("Son Bakım", stats.get('last_maintenance', 'Kayıt Yok')))
