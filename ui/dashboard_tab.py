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
from models.maintenance import Bakim, PilDegisim, Tezgah
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

# Kendi modüllerimiz
from utils.chart_data_provider import ChartDataProvider

class DashboardTab(QWidget):
    """Dashboard sekme sınıfı - PyQtChart kullanarak grafikler gösterir"""
    
    def __init__(self):
        super().__init__()
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
        print("Dashboard yenileniyor...")
        
        # filter_active değişkenini kontrol et ve yoksa oluştur
        if not hasattr(self, 'filter_active'):
            self.filter_active = False
        
        # Veri durumunu yazdır (eğer filtre aktifse)
        try:
            # Toplam veri sayılarını al
            with db_manager.session_scope() as count_session:
                bakim_count = count_session.query(Bakim).count()
                pil_count = count_session.query(PilDegisim).count()
                print(f"Veri durumu: Tüm Veriler - Bakım: {bakim_count}, Pil Değişim: {pil_count}")
        except Exception as e:
            print(f"Veri sayım hatası: {e}")
        
        try:
            # Veritabanı bağlantısı her zaman taze başlat - session sorunlarını önler
            # Önemli: Mevcut session'u kapat
            if hasattr(self, 'session') and self.session is not None:
                try:
                    self.session.close()
                except Exception:
                    pass
                    
            # Yeni bir session aç
            self.session = db_manager.session_factory()
            
            if self.session is None:
                raise ValueError("Veritabanı bağlantısı kurulamadı")
                
            # Tezgah combobox'ı doldur
            self._populate_tezgah_combo()
            
            # İstatistikleri al
            self.stats = self.data_provider.get_basic_stats(self.session)
            
            # Stat kartlarını güncelle
            print("Dashboard istatistikleri güncelleniyor...")
            self._update_stat_cards()
            
            # Grafikleri oluştur/güncelle
            self._update_charts()
            
            print("Dashboard başarıyla güncellendi.")
        
        except Exception as e:
            print(f"Dashboard güncelleme hatası: {e}")
            print(traceback.format_exc())
            
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
                with db_manager.session_scope() as temp_session:
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
            
            # Chart oluştur ve serileri ekle
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
                with db_manager.session_scope() as temp_session:
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
                with db_manager.session_scope() as temp_session:
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
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Başlık
        title_label = QLabel("TezgahTakip Kontrol Paneli")
        title_label.setStyleSheet('''
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 20px;
            text-align: center;
        ''')
        layout.addWidget(title_label)
        
        # Ana içerik
        content_layout = QHBoxLayout()
        
        # Sol taraf grafik ve istatistikler
        left_frame = QFrame()
        left_layout = QVBoxLayout()
        left_layout.setObjectName("left_layout")  # ObjectName ataması
        
        # Grafik gösterimi için web view
        self.web_view = QWebEngineView()
        self.web_view.setObjectName("dashboard_web_view")  # ObjectName ataması
        self.web_view.setMinimumHeight(600)
        left_layout.addWidget(self.web_view)
        
        left_frame.setLayout(left_layout)
        
        # Sağ taraf bilgilendirme ve istatistikler
        right_frame = QFrame()
        right_frame.setMaximumWidth(400)  # Sağ panel genişlik sınırlama
        right_layout = QVBoxLayout()
        
        # Özet İstatistikler
        stats_label = QLabel("Özet İstatistikler")
        stats_label.setStyleSheet('''
            font-size: 18px;
            font-weight: bold;
            color: #2980b9;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        ''')
        right_layout.addWidget(stats_label)
        
        # İstatistik etiketleri - Dinamik olarak güncellenecek
        self.stats_container = QVBoxLayout()
        self.stats_container.setObjectName("stats_container")  # ObjectName ataması
        self.stats_container.setSpacing(8)
        
        # İstatistik widgetları oluştur ve kaydet
        self.stat_widgets = {}
        
        # Stat widget'larına objectName'ler ekleyerek kolay erişim sağlama
        
        # Toplam tezgah sayısı
        total_tezgah_layout = QHBoxLayout()
        total_tezgah_layout.setObjectName("tezgah_layout")
        total_tezgah_icon = QLabel("🔧")
        total_tezgah_icon.setStyleSheet("font-size: 18px;")
        self.stat_widgets['toplam_tezgah'] = QLabel("0")
        self.stat_widgets['toplam_tezgah'].setObjectName("label_toplam_tezgah")
        total_tezgah_layout.addWidget(total_tezgah_icon)
        total_tezgah_layout.addWidget(QLabel("Toplam Tezgah:"))
        total_tezgah_layout.addWidget(self.stat_widgets['toplam_tezgah'])
        total_tezgah_layout.addStretch()
        
        # Toplam bakım sayısı
        total_bakim_layout = QHBoxLayout()
        total_bakim_icon = QLabel("🔨")
        total_bakim_icon.setStyleSheet("font-size: 18px;")
        self.stat_widgets['toplam_bakim'] = QLabel("0")
        total_bakim_layout.addWidget(total_bakim_icon)
        total_bakim_layout.addWidget(QLabel("Toplam Bakım:"))
        total_bakim_layout.addWidget(self.stat_widgets['toplam_bakim'])
        total_bakim_layout.addStretch()
        
        # Toplam pil değişim sayısı
        total_pil_layout = QHBoxLayout()
        total_pil_icon = QLabel("🔋")
        total_pil_icon.setStyleSheet("font-size: 18px;")
        self.stat_widgets['toplam_pil_degisim'] = QLabel("0")
        total_pil_layout.addWidget(total_pil_icon)
        total_pil_layout.addWidget(QLabel("Toplam Pil Değişim:"))
        total_pil_layout.addWidget(self.stat_widgets['toplam_pil_degisim'])
        total_pil_layout.addStretch()
        
        # Son bakım tarihi
        son_bakim_layout = QHBoxLayout()
        son_bakim_icon = QLabel("📅")
        son_bakim_icon.setStyleSheet("font-size: 18px;")
        self.stat_widgets['son_bakim_tarihi'] = QLabel("-")
        son_bakim_layout.addWidget(son_bakim_icon)
        son_bakim_layout.addWidget(QLabel("Son Bakım:"))
        son_bakim_layout.addWidget(self.stat_widgets['son_bakim_tarihi'])
        son_bakim_layout.addStretch()
        
        # Son pil değişim tarihi
        son_pil_layout = QHBoxLayout()
        son_pil_icon = QLabel("📅")
        son_pil_icon.setStyleSheet("font-size: 18px;")
        self.stat_widgets['son_pil_degisim'] = QLabel("-")
        son_pil_layout.addWidget(son_pil_icon)
        son_pil_layout.addWidget(QLabel("Son Pil Değişim:"))
        son_pil_layout.addWidget(self.stat_widgets['son_pil_degisim'])
        son_pil_layout.addStretch()
        
        # Tezgah başına ortalama bakım
        avg_bakim_layout = QHBoxLayout()
        avg_bakim_icon = QLabel("📊")
        avg_bakim_icon.setStyleSheet("font-size: 18px;")
        self.stat_widgets['ortalama_bakim'] = QLabel("0")
        avg_bakim_layout.addWidget(avg_bakim_icon)
        avg_bakim_layout.addWidget(QLabel("Tezgah Başına Bakım:"))
        avg_bakim_layout.addWidget(self.stat_widgets['ortalama_bakim'])
        avg_bakim_layout.addStretch()
        
        # Stat container'a ekle
        stat_card = QFrame()
        stat_card.setObjectName("stat_card")  # ObjectName ataması
        stat_card.setStyleSheet('''
            QFrame {
                background-color: rgba(52, 152, 219, 0.1);
                border-radius: 10px;
                padding: 15px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
            QLabel {
                font-size: 14px;
            }
        ''')
        stat_layout = QVBoxLayout(stat_card)
        stat_layout.setObjectName("stat_inner_layout")  # ObjectName ataması
        stat_layout.addLayout(total_tezgah_layout)
        stat_layout.addLayout(total_bakim_layout)
        stat_layout.addLayout(total_pil_layout)
        stat_layout.addLayout(son_bakim_layout)
        stat_layout.addLayout(son_pil_layout)
        stat_layout.addLayout(avg_bakim_layout)
        self.stats_container.addWidget(stat_card)
        
        right_layout.addLayout(self.stats_container)
        
        # Hızlı erişim bölümü
        quick_access_label = QLabel("Hızlı Erişim")
        quick_access_label.setStyleSheet('''
            font-size: 18px;
            font-weight: bold;
            color: #2980b9;
            margin-top: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        ''')
        right_layout.addWidget(quick_access_label)
        
        # Hızlı erişim butonları
        quick_access_layout = QVBoxLayout()
        
        # Rapor oluştur butonu
        create_report_btn = QPushButton("Rapor Oluştur")
        create_report_btn.setStyleSheet('''
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        ''')
        quick_access_layout.addWidget(create_report_btn)
        
        # Bakım ekle butonu
        add_maintenance_btn = QPushButton("Bakım Ekle")
        add_maintenance_btn.setStyleSheet('''
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        ''')
        quick_access_layout.addWidget(add_maintenance_btn)
        
        # Pil değişim ekle butonu
        add_battery_btn = QPushButton("Pil Değişim Ekle")
        add_battery_btn.setStyleSheet('''
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        ''')
        quick_access_layout.addWidget(add_battery_btn)
        
        right_layout.addLayout(quick_access_layout)
        
        # QR Kod
        qr_code_frame = QFrame()
        qr_code_frame.setStyleSheet('''
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
                margin-top: 20px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        ''')
        qr_layout = QVBoxLayout(qr_code_frame)
        
        qr_title = QLabel("TezgahTakip Mobil Erişim")
        qr_title.setAlignment(Qt.AlignCenter)
        qr_title.setStyleSheet('''
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        ''')
        qr_layout.addWidget(qr_title)
        
        qr_code_label = QLabel()
        qr_code_label.setAlignment(Qt.AlignCenter)
        qr_code = self.generate_qr_code("https://tezgahtakip.com")
        qr_code_label.setPixmap(qr_code)
        qr_layout.addWidget(qr_code_label)
        
        qr_info = QLabel("Mobil cihazınızdan erişim için QR kodu tarayın")
        qr_info.setAlignment(Qt.AlignCenter)
        qr_info.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        qr_layout.addWidget(qr_info)
        
        right_layout.addWidget(qr_code_frame)
        
        # Sağ layout'a boşluk ekle
        right_layout.addStretch()
        right_frame.setLayout(right_layout)
        
        # Filtreleme ve etkileşim paneli
        filter_frame = QFrame()
        filter_frame.setStyleSheet('''
            QFrame {
                background-color: #ecf0f1;
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 15px;
            }
            QLabel {
                font-weight: bold;
            }
            QDateEdit, QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 4px;
                background: white;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
        ''')
        filter_layout = QHBoxLayout(filter_frame)
        
        # Filtreleme paneli:
        # Başlangıç tarihi seçici
        date_layout = QVBoxLayout()
        start_date_label = QLabel("Başlangıç Tarihi:")
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-30))  # Son 30 gün
        date_layout.addWidget(start_date_label)
        date_layout.addWidget(self.start_date)
        
        # Bitiş tarihi seçici
        end_date_label = QLabel("Bitiş Tarihi:")
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(end_date_label)
        date_layout.addWidget(self.end_date)
        
        # Tezgah seçici
        tezgah_layout = QVBoxLayout()
        tezgah_label = QLabel("Tezgah Seçimi:")
        self.tezgah_combo = QComboBox()
        self.tezgah_combo.addItem("Tüm Tezgahlar", None)
        self.populate_tezgah_combo()  # Tezgahları yükle
        tezgah_layout.addWidget(tezgah_label)
        tezgah_layout.addWidget(self.tezgah_combo)
        
        # Bakım personeli filtresi
        personel_layout = QVBoxLayout()
        personel_label = QLabel("Bakım Personeli:")
        self.personel_combo = QComboBox()
        self.personel_combo.addItem("Tüm Personel", None)
        self.populate_personel_combo()  # Personelleri yükle
        personel_layout.addWidget(personel_label)
        personel_layout.addWidget(self.personel_combo)
        
        # Filtreleme ve yenileme butonları
        buttons_layout = QVBoxLayout()
        self.filter_btn = QPushButton("Filtrele")
        self.filter_btn.clicked.connect(self.apply_filters)
        self.refresh_btn = QPushButton("Yenile")
        self.refresh_btn.clicked.connect(self.refresh_dashboard)
        buttons_layout.addWidget(self.filter_btn)
        buttons_layout.addWidget(self.refresh_btn)
        
        # Otomatik yenileme seçeneği
        auto_refresh_layout = QVBoxLayout()
        self.auto_refresh = QCheckBox("Otomatik Yenile")
        self.auto_refresh.setChecked(True)
        self.auto_refresh.stateChanged.connect(self.toggle_auto_refresh)
        auto_refresh_layout.addWidget(self.auto_refresh)
        
        # Tüm filtreleri temizle butonu
        self.clear_filters_btn = QPushButton("Filtreleri Temizle")
        self.clear_filters_btn.clicked.connect(self.clear_filters)
        auto_refresh_layout.addWidget(self.clear_filters_btn)
        
        # Filtreleme panelini düzenle
        filter_layout.addLayout(date_layout)
        filter_layout.addLayout(tezgah_layout)
        filter_layout.addLayout(personel_layout)
        filter_layout.addLayout(buttons_layout)
        filter_layout.addLayout(auto_refresh_layout)
        
        # Ana içeriği düzenle
        content_splitter = QSplitter(Qt.Vertical)
        content_splitter.addWidget(filter_frame)
        
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        content_splitter.addWidget(content_widget)
        
        layout.addWidget(content_splitter)
        self.setLayout(layout)
        
        # Dashboard'u yükle
        self.update_dashboard()
        
    def generate_qr_code(self, url):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="#2980b9", back_color="white")
        
        # Görüntüyü QPixmap'e çevir
        byte_array = io.BytesIO()
        img.save(byte_array, format='PNG')
        qr_pixmap = QPixmap()
        qr_pixmap.loadFromData(byte_array.getvalue())
        
        return qr_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _display_no_data_label(self):
        """Veri olmadığında bir etiket gösterir."""
        from PyQt5.QtWidgets import QLabel, QVBoxLayout
        from PyQt5.QtCore import Qt
        
        label = QLabel('Bakım verisi bulunamadı.')
        label.setAlignment(Qt.AlignCenter)
        
        # Web view'a ekle
        if hasattr(self, 'web_view') and self.web_view:
            try:
                layout = self.web_view.layout()
                if layout is None:
                    layout = QVBoxLayout(self.web_view)
                layout.addWidget(label)
            except RuntimeError as e:
                print(f"Etiket ekleme hatası: {e}")
                print("Web view nesnesi silinmiş olabilir.")
        else:
            print("Web view bulunamadı.")




    def showEvent(self, event):
        """
        Sekme görünür olduğunda çağrılır
        """
        super().showEvent(event)
        self.is_tab_visible = True
        print("Dashboard sekmesi aktif oldu")
        
        # Zamanlama başlat (her dakikada bir güncelleme)
        if hasattr(self, 'update_timer') and not self.update_timer.isActive():
            self.update_timer.start()
            print("Dashboard güncelleme zamanlaması başlatıldı")
        
        # Görünür olduğunda verileri yenile
        self.refresh_dashboard()
    
    def hideEvent(self, event):
        """
        Sekme gizlendiğinde çağrılır
        """
        super().hideEvent(event)
        self.is_tab_visible = False
        
        # Gizlendiğinde zamanlama durdur (performans için)
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
    
    def set_active_status(self, is_active):
        """
        Tab widgettan çağrılan metot, sekmenin aktif/pasif durumunu belirler
        
        Args:
            is_active (bool): Tab'in aktif olup olmadığını belirtir
        """
        self.is_tab_visible = is_active
        
        if is_active:
            # Aktif olduğunda zamanlama başlat ve verileri güncelle
            if hasattr(self, 'update_timer') and not self.update_timer.isActive():
                self.update_timer.start()
                print("Dashboard güncelleme zamanlaması başlatıldı")
            
            # Aktif olduğunda verileri yenile
            self.refresh_dashboard()
        else:
            # Pasif olduğunda zamanlama durdur
            if hasattr(self, 'update_timer') and self.update_timer.isActive():
                self.update_timer.stop()
    
    def populate_tezgah_combo(self):
        """Tezgah seçim menüsünü doldurur"""
        try:
            session = db_manager.get_session()
            tezgahlar = session.query(Tezgah).all()
            for tezgah in tezgahlar:
                self.tezgah_combo.addItem(f"Tezgah {tezgah.numarasi}", tezgah.id)
            session.close()
        except Exception as e:
            print(f"Tezgah listesi yüklenirken hata: {e}")
    
    def populate_personel_combo(self):
        """Bakım personeli seçim menüsünü doldurur"""
        try:
            session = db_manager.get_session()
            # Benzersiz bakım personeli listesi
            personel_list = session.query(Bakim.bakim_yapan).distinct().all()
            for personel in personel_list:
                if personel[0]:  # Boş olmayan personel adları
                    self.personel_combo.addItem(personel[0], personel[0])
            session.close()
        except Exception as e:
            print(f"Personel listesi yüklenirken hata: {e}")
    
    def apply_filters(self):
        """Filtre seçeneklerini uygular ve dashboard'u günceller"""
        # Tarih aralığını al
        self.date_range = {
            'start': self.start_date.date().toString("yyyy-MM-dd"),
            'end': self.end_date.date().toString("yyyy-MM-dd")
        }
        
        # Seçili tezgah ID'sini al
        selected_index = self.tezgah_combo.currentIndex()
        self.selected_tezgah = self.tezgah_combo.itemData(selected_index) if selected_index > 0 else None
        
        # Seçili personeli al
        selected_personel_index = self.personel_combo.currentIndex()
        self.selected_personel = self.personel_combo.itemData(selected_personel_index) if selected_personel_index > 0 else None
        
        # Filtreleme aktif flag'ini güncelle
        self.filter_active = True
        
        # Dashboard'u güncelle
        self.update_dashboard()
        
        # Kullanıcıya bildirim göster
        print(f"Filtreler uygulandı: Tarih Aralığı={self.date_range}, Tezgah={self.selected_tezgah}, Personel={self.selected_personel}")
    
    def clear_filters(self):
        """Tüm filtreleri temizler ve tam veri gösterir"""
        # Filtreleri sıfırla
        self.date_range = {'start': None, 'end': None}
        self.selected_tezgah = None
        self.selected_personel = None
        self.filter_active = False
        
        # UI kontrol panelini sıfırla
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.end_date.setDate(QDate.currentDate())
        self.tezgah_combo.setCurrentIndex(0)
        self.personel_combo.setCurrentIndex(0)
        
        # Dashboard'u güncelle
        self.update_dashboard()
        
        print("Tüm filtreler temizlendi.")
    
    def refresh_dashboard(self):
        """Dashboard'ı manuel olarak yeniler"""
        print("Dashboard yenileniyor...")
        self.update_dashboard()
    
    def toggle_auto_refresh(self, state):
        """Otomatik yenilemeyi açıp kapatır"""
        if state == Qt.Checked:
            # Sadece sekme görünürse ve aktifse başlat
            if self.is_tab_visible and self.is_active:
                self.update_timer.start(30000)  # 30 saniyede bir
            print("Otomatik yenileme açıldı")
        else:
            self.update_timer.stop()
            print("Otomatik yenileme kapatıldı")
            
    def showEvent(self, event):
        """Sekme görünür olduğunda çağrılır"""
        self.is_tab_visible = True
        # Eğer auto_refresh aktifse timer'ı başlat
        if hasattr(self, 'auto_refresh') and self.auto_refresh.isChecked():
            self.update_timer.start(30000)
        # Sekme görünür olduğunda verileri güncelle
        self.update_dashboard()
        super().showEvent(event)
    
    def hideEvent(self, event):
        """Sekme gizlendiğinde çağrılır"""
        self.is_tab_visible = False
        # Timer'ı durdur - başka bir sekmeye geçildiğinde
        # dashboard güncellemesi yapma
        if self.update_timer.isActive():
            self.update_timer.stop()
        super().hideEvent(event)
    
    def set_active_status(self, is_active):
        """Ana uygulama tarafından çağrılır, sekmenin aktif olup olmadığını belirler"""
        self.is_active = is_active
        
        if is_active:
            # Sekme aktif olduğunda
            print("Dashboard sekmesi aktif oldu")
            # Dashboard'u güncelle
            self.refresh_dashboard()
            # Eğer otomatik yenileme aktifse, timer'ı başlat
            if hasattr(self, 'auto_refresh') and self.auto_refresh.isChecked():
                self.update_timer.start(30000)
        else:
            # Sekme pasif olduğunda timer'ı durdur
            if self.update_timer.isActive():
                self.update_timer.stop()
    
    def recreate_stat_widgets(self):
        """Stat widget'larını yeniden oluşturur"""
        print("Stat widget'ları yeniden oluşturuluyor...")
    
    def add_stat_row(self, layout, icon, label_text, value_widget):
        """Tek bir stat satırı ekler"""
        row_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px;")
        text_label = QLabel(label_text)
        
        row_layout.addWidget(icon_label)
        row_layout.addWidget(text_label)
        row_layout.addWidget(value_widget)
        row_layout.addStretch()
        
        layout.addLayout(row_layout)
    
    def update_stats_display(self, stats):
        """Dashboard'daki istatistik widgetlarını günceller"""
        try:
            print("Dashboard istatistikleri güncelleniyor...")
            
            # İstatistik widgetlarını güncelle
            for stat_key, stat_value in stats.items():
                if stat_key in self.stat_widgets:
                    widget = self.stat_widgets[stat_key]
                    if widget is not None:
                        widget.setText(str(stat_value))
                        
                        # Görsel geribildirim - Değerin durumuna göre renk değişimi
                        if stat_key in ['toplam_bakim', 'toplam_pil_degisim']:
                            # Sayısal değerleri karşılaştır
                            try:
                                value = int(stat_value)
                                if value > 100:
                                    color = self.status_colors['normal']  # Yeşil - yüksek aktivite
                                elif value > 50:
                                    color = self.status_colors['warning']  # Turuncu - orta aktivite
                                else:
                                    color = self.status_colors['inactive']  # Gri - düşük aktivite
                                
                                widget.setStyleSheet(f"color: {color}; font-weight: bold;")
                            except (ValueError, RuntimeError, Exception) as e:
                                print(f"Widget renklendirme hatası: {e}")
                            
        except Exception as e:
            print(f"İstatistik gösterimi güncellenirken hata: {e}")
    
    # Eski update_dashboard fonksiyonunun yerine geçen adapter metodu
    # Geriye dönük uyumluluk için
    def update_dashboard(self) -> None:
        """Dashboard verilerini günceller (eski metot)
        Bu metot geriye dönük uyumluluk için korunmuştur. Yeni refresh_dashboard kullanılır.
        """
        # Yeni metoda yönlendir
        self.refresh_dashboard()
        
    # Eski create_charts fonksiyonunun yerine adapter metodu
    def create_charts(self, stats: dict) -> None:
        """Grafikleri oluşturur (eski metot)
        Bu metot geriye dönük uyumluluk için korunmuştur. Yeni _update_charts kullanılır.
        """
        try:
            # Grafikleri güncelleyen yeni metoda yönlendir
            self._update_charts()
        except Exception as e:
            print(f"Grafik oluşturma hatası: {e}")
            print(traceback.format_exc())
    
    def _apply_filters(self, maintenance_query, battery_query):
        """Filtreleri bakım ve pil değişim sorgularına uygular.
        
        Args:
            maintenance_query: Bakım kayıtları sorgusu
            battery_query: Pil değişim kayıtları sorgusu
        
        Returns:
            Tuple[Query, Query]: Filtrelenmiş sorgular
        """
        if self.filter_active:
            # Tarih aralığı filtreleri
            if self.date_range.get('start') and self.date_range.get('end'):
                start_date = self.date_range['start']
                end_date = self.date_range['end']
                maintenance_query = maintenance_query.filter(Bakim.tarih.between(start_date, end_date))
                battery_query = battery_query.filter(PilDegisim.tarih.between(start_date, end_date))
            
            # Tezgah filtresi
            if self.selected_tezgah:
                maintenance_query = maintenance_query.filter(Bakim.tezgah_id == self.selected_tezgah)
                battery_query = battery_query.filter(PilDegisim.tezgah_id == self.selected_tezgah)
            
            # Personel filtresi
            if hasattr(self, 'selected_personel') and self.selected_personel:
                maintenance_query = maintenance_query.filter(Bakim.bakim_yapan == self.selected_personel)
                battery_query = battery_query.filter(PilDegisim.bakim_yapan == self.selected_personel)
        
        return maintenance_query, battery_query
    
    def _calculate_dashboard_stats(self, maintenance_records, battery_records) -> Dict[str, Any]:
        """Dashboard için istatistikleri hesaplar.
        
        Args:
            maintenance_records: Bakım kayıtları
            battery_records: Pil değişim kayıtları
        
        Returns:
            Dict[str, Any]: Hesaplanan dashboard istatistikleri
        """
        # Filtreleme durumunu kontrol et
        filter_status = "Filtreli" if self.filter_active else "Tüm Veriler"
        
        stats = {
            'toplam_tezgah': len(set(record.tezgah_id for record in maintenance_records)),
            'toplam_bakim': len(maintenance_records),
            'toplam_pil_degisim': len(battery_records),
            'son_bakim_tarihi': max((record.tarih for record in maintenance_records), default='-'),
            'son_pil_degisim': max((record.tarih for record in battery_records), default='-'),
            'ortalama_bakim': round(len(maintenance_records) / max(len(set(record.tezgah_id for record in maintenance_records)), 1), 1),
            'son_guncelleme': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Veri durumu hakkında bilgi yaz
        print(f"Veri durumu: {filter_status} - Bakım: {len(maintenance_records)}, Pil Değişim: {len(battery_records)}")
        
        return stats

    def update_dashboard(self):
        """Dashboard verilerini günceller.
        """
        # Session'ı try bloğundan önce tanımla
        session = None
        
        try:
            # Doğru import yollarını kullan
            import sys
            sys.path.append('c:\\Users\\ahmet\\OneDrive\\Masaüstü\\TezgahTakipQt')
            
            # Models klasöründen maintenance.py içindeki sınıfları içe aktar
            from models.maintenance import Bakim, PilDegisim, Tezgah
            from sqlalchemy.orm import joinedload
            from database.connection import db_manager

            session = db_manager.get_session()
            
            # Veritabanı sorgularını hazırla
            maintenance_query = session.query(Bakim).options(joinedload(Bakim.tezgah))
            battery_query = session.query(PilDegisim).options(joinedload(PilDegisim.tezgah))
            
            # Filtreleri uygula
            maintenance_query, battery_query = self._apply_filters(maintenance_query, battery_query)
            
            # Sorguları çalıştır
            maintenance_records = maintenance_query.all()
            battery_records = battery_query.all()
            
            # İstatistikleri hesapla
            stats = self._calculate_dashboard_stats(maintenance_records, battery_records)
            
            # Görsel bileşenleri güncelle
            self.update_stats_display(stats)
            self.create_charts(stats)
            
        except Exception as e:
            print(f"Dashboard güncellenirken hata: {e}")
        finally:
            # Session varsa kapat
            if session:
                session.close()
