import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import qrcode
from PIL import Image
import io
import base64
import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QComboBox, QDateEdit, QCheckBox, QLineEdit, QSplitter
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer, QDate
from database.connection import db_manager
from models.maintenance import Bakim, PilDegisim, Tezgah
from sqlalchemy.orm import Session

class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Filtreleme ve seçim için değişkenler
        self.selected_tezgah = None
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

    def create_maintenance_graph(self):
        # Bakım kayıtları
        session = db_manager.get_session()
        maintenance_records = session.query(Bakim).join(Tezgah).all()
        maintenance_df = pd.DataFrame([
            {
                'tezgah_numarasi': record.tezgah.numarasi,
                'maintenance_date': record.tarih,
                
                'month': record.tarih[:7] if record.tarih and len(record.tarih) >= 7 else 'Bilinmiyor'
            } for record in maintenance_records
        ])
        
        # Eğer hiç veri yoksa uyarı göster
        if maintenance_df.empty:
            from PyQt5.QtWidgets import QLabel
            label = QLabel('Bakım verisi bulunamadı.')
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet('font-size:18px; color:#b71c1c; padding:30px;')
            return label

        # Eksik verileri kontrol et
        maintenance_df = maintenance_df.fillna({'month': 'Bilinmiyor'})

        # Bakım istatistikleri
        # Bakım türü istatistiği kaldırıldı.
        maintenance_by_month = maintenance_df.groupby('month', dropna=False).size()

        # Bakım türü dağılımı
        # Bakım türü grafiği kaldırıldı.

        # Aylık bakım sayıları
        maintenance_monthly_bar = px.bar(
            x=maintenance_by_month.index, 
            y=maintenance_by_month.values, 
            title='Aylık Bakım Sayıları'
        )

        # Grafikleri birleştir
        combined_fig = go.Figure()
        
        combined_fig.add_traces(maintenance_monthly_bar.data)

        combined_fig.update_layout(
            title_text='Tezgah Takip Dashboard',
            height=600,
            showlegend=True,
            template='plotly_white'
        )

        # HTML'e çevir
        dashboard_html = combined_fig.to_html(include_plotlyjs='cdn', full_html=False)
        full_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tezgah Takip Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .dashboard {{ max-width: 1200px; margin: 0 auto; }}
            </style>
        </head>
        <body>
            <div class="dashboard">
                {dashboard_html}
            </div>
        </body>
        </html>
        '''
        web_view = QWebEngineView()
        web_view.setHtml(full_html)
        return web_view

    def create_battery_graph(self):
        # Pil kayıtları
        session = db_manager.get_session()
        battery_records = session.query(PilDegisim).join(Tezgah).all()
        battery_df = pd.DataFrame([
            {
                'tezgah_numarasi': getattr(record.tezgah, 'numarasi', 'Tanımsız'),
                'eksen': getattr(record, 'eksen', 'Tanımsız'),
                'pil_modeli': getattr(record, 'pil_modeli', 'Tanımsız'),
                'tarih': getattr(record, 'tarih', None)
            } for record in battery_records
        ])

        # Eğer hiç veri yoksa veya sütunlar yoksa uyarı göster
        if battery_df.empty or 'tezgah_numarasi' not in battery_df.columns or 'tarih' not in battery_df.columns:
            from PyQt5.QtWidgets import QLabel
            label = QLabel('Pil değişim verisi bulunamadı.')
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet('font-size:18px; color:#b71c1c; padding:30px;')
            return label

        # Tezgah bazında pil değişimleri
        battery_change_scatter = px.scatter(
            battery_df,
            x='tezgah_numarasi',
            y='tarih',
            color='eksen',
            title='Tezgah Bazında Pil Değişimleri'
        )

        # HTML'e çevir
        dashboard_html = battery_change_scatter.to_html(include_plotlyjs='cdn', full_html=False)
        full_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tezgah Takip Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .dashboard {{ max-width: 1200px; margin: 0 auto; }}
            </style>
        </head>
        <body>
            <div class="dashboard">
                {dashboard_html}
            </div>
        </body>
        </html>
        '''
        web_view = QWebEngineView()
        web_view.setHtml(full_html)
        return web_view

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
    
    def update_dashboard(self):
        """Dashboard verilerini günceller"""
        print("Dashboard verilerini güncelleme başlıyor...")
        
        # Veritabanı işlemleri
        session = db_manager.get_session()
        try:
            # SQL sorguları için filtre hazırlama
            maintenance_query = session.query(Bakim).join(Tezgah)
            battery_query = session.query(PilDegisim).join(Tezgah)
            
            # Filtreleri uygula
            if self.filter_active:
                # Tarih aralığı filtreleri
                if self.date_range['start'] and self.date_range['end']:
                    try:
                        start_date = self.date_range['start']
                        end_date = self.date_range['end']
                        # Standart tarih formatına dönüştürme işlemleri (DB'de tarih string olarak tutuluyor olabilir)
                        maintenance_query = maintenance_query.filter(Bakim.tarih.between(start_date, end_date))
                        battery_query = battery_query.filter(PilDegisim.tarih.between(start_date, end_date))
                    except Exception as e:
                        print(f"Tarih filtreleme hatası: {e}")
                
                # Tezgah filtresi
                if self.selected_tezgah:
                    maintenance_query = maintenance_query.filter(Bakim.tezgah_id == self.selected_tezgah)
                    battery_query = battery_query.filter(PilDegisim.tezgah_id == self.selected_tezgah)
                
                # Personel filtresi
                if hasattr(self, 'selected_personel') and self.selected_personel:
                    maintenance_query = maintenance_query.filter(Bakim.bakim_yapan == self.selected_personel)
                    battery_query = battery_query.filter(PilDegisim.bakim_yapan == self.selected_personel)
            
            # Son sorguları çalıştır
            maintenance_records = maintenance_query.all()
            battery_records = battery_query.all()
            
            # Filtre durumunu göster
            filter_status = "Filtrelenmiş Görünüm" if self.filter_active else "Tüm Veriler"
            print(f"Veri durumu: {filter_status} - Bakım: {len(maintenance_records)}, Pil Değişim: {len(battery_records)}")
            
            # Tarih formatlarını standartlaştır ve düzelt
            maintenance_data = []
            for record in maintenance_records:
                try:
                    # Tarih verilerini daha güvenilir bir şekilde işle
                    if isinstance(record.tarih, str) and '-' in record.tarih:
                        parts = record.tarih.split('-')
                        if len(parts) == 3:
                            # DD-MM-YYYY formatını dönüştür
                            day, month, year = parts
                            iso_date = f"{year}-{month}-{day}"
                            month_year = f"{year}-{month}"
                        else:
                            iso_date = record.tarih
                            month_year = record.tarih[:7] if len(record.tarih) >= 7 else 'Bilinmiyor'
                    else:
                        iso_date = str(record.tarih)
                        month_year = 'Bilinmiyor'
                        
                    # Bakım verilerini daha zengin kaydet
                    maintenance_data.append({
                        'tezgah_numarasi': record.tezgah.numarasi,
                        'tezgah_id': record.tezgah_id,
                        'maintenance_date': iso_date,
                        'month_year': month_year,
                        'yapan': record.bakim_yapan,
                        'aciklama': record.aciklama,
                        'id': record.id
                    })
                except Exception as e:
                    print(f"Bakım kaydı işlenirken hata: {e}")
                    
            maintenance_df = pd.DataFrame(maintenance_data)
            
            # Pil değişim kayıtlarını daha detaylı işle
            battery_data = []
            for record in battery_records:
                try:
                    # Tarih formatlarını standartlaştır
                    if isinstance(record.tarih, str) and '-' in record.tarih:
                        parts = record.tarih.split('-')
                        if len(parts) == 3:
                            day, month, year = parts
                            iso_date = f"{year}-{month}-{day}"
                            month_year = f"{year}-{month}"
                        else:
                            iso_date = record.tarih
                            month_year = record.tarih[:7] if len(record.tarih) >= 7 else 'Bilinmiyor'
                    else:
                        iso_date = str(record.tarih)
                        month_year = 'Bilinmiyor'
                    
                    battery_data.append({
                        'tezgah_numarasi': record.tezgah.numarasi,
                        'tezgah_id': record.tezgah_id,
                        'degisim_tarihi': iso_date,
                        'month_year': month_year,
                        'pil_modeli': record.pil_modeli,
                        'yapan': record.bakim_yapan,
                        'id': record.id
                    })
                except Exception as e:
                    print(f"Pil değişim kaydı işlenirken hata: {e}")
                    
            battery_df = pd.DataFrame(battery_data)
            
            # Temel istatistikler hesapla
            toplam_tezgah = session.query(Tezgah).count()
            toplam_bakim = len(maintenance_records)
            toplam_pil_degisim = len(battery_records)
            
            # Tezgah başına ortalama bakım sayısı
            if toplam_tezgah > 0:
                ortalama_bakim = toplam_bakim / toplam_tezgah
            else:
                ortalama_bakim = 0
                
            # Son bakım ve pil değişim tarihlerini bul
            son_bakim_tarihi = "Kayıt yok"
            son_pil_degisim = "Kayıt yok"
            
            if not maintenance_df.empty and 'maintenance_date' in maintenance_df.columns:
                # Son bakım tarihini bul
                try:
                    son_bakim_tarihi = pd.to_datetime(maintenance_df['maintenance_date'], errors='coerce').max()
                    son_bakim_tarihi = son_bakim_tarihi.strftime('%d.%m.%Y') if not pd.isna(son_bakim_tarihi) else "Kayıt yok"
                except Exception as e:
                    print(f"Son bakım tarihi hesaplanırken hata: {e}")
                    son_bakim_tarihi = "Format hatası"
            
            if not battery_df.empty and 'degisim_tarihi' in battery_df.columns:
                # Son pil değişim tarihini bul
                try:
                    son_pil_degisim = pd.to_datetime(battery_df['degisim_tarihi'], errors='coerce').max()
                    son_pil_degisim = son_pil_degisim.strftime('%d.%m.%Y') if not pd.isna(son_pil_degisim) else "Kayıt yok"
                except Exception as e:
                    print(f"Son pil değişim tarihi hesaplanırken hata: {e}")
                    son_pil_degisim = "Format hatası"
            
            # Güncel zaman bilgisi
            import datetime
            now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            
            # İstatistikler topla
            stats = {
                'toplam_tezgah': toplam_tezgah,
                'toplam_bakim': toplam_bakim,
                'toplam_pil_degisim': toplam_pil_degisim,
                'ortalama_bakim': f"{ortalama_bakim:.1f}",
                'son_bakim_tarihi': son_bakim_tarihi,
                'son_pil_degisim': son_pil_degisim,
                'son_guncelleme': now
            }
            
            # İstatistikleri görüntüle
            self.update_stats_display(stats)
            
            # Durum göstergesi
            filter_status_title = "Filtrelenmiş Görünüm" if self.filter_active else "Tüm Veriler"
            
            try:
                # interaktif grafiklerin oluşturulması
                if not maintenance_df.empty or not battery_df.empty:
                    # Bakım kayıtlarının aylara göre dağılımı
                    
                    # Alt grafikler oluşturma
                    fig = make_subplots(
                        rows=2, cols=2,
                        subplot_titles=(
                            "Aylık Bakım Sayıları", 
                            "Tezgah Başına Bakım ve Pil Değişimleri", 
                            "Pil Modeli Dağılımı", 
                            "Bakım Personeli Yoğunluğu"
                        ),
                        specs=[
                            [{"type": "scatter"}, {"type": "bar"}],
                            [{"type": "pie"}, {"type": "pie"}]
                        ]
                    )
                    
                    # Filtre bilgisini başlığa ekle
                    fig.update_layout(
                        title=f"TezgahTakip Dashboard - {filter_status_title}",
                        title_font_size=20,
                        height=800,
                        template="plotly_white"
                    )
                    
                    # 1. Grafik: Aylık bakım sayıları (çizgi grafik)
                    if not maintenance_df.empty and 'month_year' in maintenance_df.columns:
                        # Aylık veriler
                        monthly_maintenance = maintenance_df.groupby('month_year').size().reset_index(name='bakim_sayisi')
                        monthly_maintenance = monthly_maintenance.sort_values('month_year')
                        
                        fig.add_trace(
                            go.Scatter(
                                x=monthly_maintenance['month_year'],
                                y=monthly_maintenance['bakim_sayisi'],
                                mode='lines+markers',
                                name='Bakım Sayısı',
                                line=dict(color='#3498db', width=3),
                                marker=dict(size=8)
                            ),
                            row=1, col=1
                        )
                    
                    # 2. Grafik: Tezgah başına bakım ve pil değişimleri (bar grafik)
                    tezgah_maintenance = pd.DataFrame()
                    tezgah_battery = pd.DataFrame()
                    
                    if not maintenance_df.empty and 'tezgah_numarasi' in maintenance_df.columns:
                        tezgah_maintenance = maintenance_df.groupby('tezgah_numarasi').size().reset_index(name='bakim_sayisi')
                    
                    if not battery_df.empty and 'tezgah_numarasi' in battery_df.columns:
                        tezgah_battery = battery_df.groupby('tezgah_numarasi').size().reset_index(name='pil_degisim_sayisi')
                    
                    if not tezgah_maintenance.empty:
                        fig.add_trace(
                            go.Bar(
                                x=tezgah_maintenance['tezgah_numarasi'],
                                y=tezgah_maintenance['bakim_sayisi'],
                                name='Bakım',
                                marker_color='#3498db'
                            ),
                            row=1, col=2
                        )
                    
                    if not tezgah_battery.empty:
                        fig.add_trace(
                            go.Bar(
                                x=tezgah_battery['tezgah_numarasi'],
                                y=tezgah_battery['pil_degisim_sayisi'],
                                name='Pil Değişim',
                                marker_color='#e74c3c'
                            ),
                            row=1, col=2
                        )
                    
                    # 3. Grafik: Pil modeli dağılımı (pasta grafik)
                    if not battery_df.empty and 'pil_modeli' in battery_df.columns:
                        pil_modeli_distribution = battery_df.groupby('pil_modeli').size().reset_index(name='sayi')
                        
                        fig.add_trace(
                            go.Pie(
                                labels=pil_modeli_distribution['pil_modeli'],
                                values=pil_modeli_distribution['sayi'],
                                hole=.3,
                                marker=dict(colors=['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'])
                            ),
                            row=2, col=1
                        )
                    
                    # 4. Grafik: Bakım yapan kişi dağılımı (pasta grafik)
                    if not maintenance_df.empty and 'yapan' in maintenance_df.columns:
                        personel_distribution = maintenance_df.groupby('yapan').size().reset_index(name='sayi')
                        
                        fig.add_trace(
                            go.Pie(
                                labels=personel_distribution['yapan'],
                                values=personel_distribution['sayi'],
                                hole=.3,
                                marker=dict(colors=['#2ecc71', '#3498db', '#e74c3c', '#f39c12', '#9b59b6'])
                            ),
                            row=2, col=2
                        )
                    
                    # Grafiğin HTML temsilini al
                    dashboard_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
                    
                    # Duyarlı HTML şablonu hazırla
                    html_content = f'''
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
                            .dashboard-container {{ width: 100%; }}
                            .dashboard-title {{ 
                                text-align: center; 
                                color: #2c3e50; 
                                padding: 10px; 
                                background: #ecf0f1; 
                                margin-bottom: 20px; 
                                border-radius: 8px;
                            }}
                            .filters-info {{ 
                                text-align: center; 
                                font-size: 13px; 
                                color: #7f8c8d; 
                                margin-bottom: 10px;
                                font-style: italic;
                            }}
                            .last-update {{ 
                                text-align: right; 
                                font-size: 11px; 
                                color: #95a5a6; 
                                padding: 5px; 
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="dashboard-container">
                            <div class="filters-info">
                                {filter_status_title} - Toplam Bakım: {toplam_bakim}, Pil Değişim: {toplam_pil_degisim}
                            </div>
                            {dashboard_html}
                            <div class="last-update">Son güncelleme: {stats['son_guncelleme']}</div>
                        </div>
                    </body>
                    </html>
                    '''
                    
                    # Web sayfasını yükle
                    self.web_view.setHtml(html_content)
                    print("Grafikler başarıyla oluşturuldu.")
                else:
                    def create_charts(self, maintenance_data, battery_data):
        """Bakım ve pil değişim verilerini görüntülemek için grafikleri oluşturur"""
        try:
            print("Grafikler oluşturuluyor...")
            
            # Web view var mı kontrol et
            if not hasattr(self, 'web_view') or self.web_view is None:
                print("Web view bulunamadı, oluşturuluyor...")
                self.web_view = QWebEngineView()
                self.web_view.setObjectName("dashboard_web_view")
                self.web_view.setMinimumHeight(600)
                left_layout = self.findChild(QVBoxLayout, "left_layout")
                if left_layout:
                    left_layout.addWidget(self.web_view)
                else:
                    print("Left layout bulunamadı!")
                    return
            
            # Her iki veri seti için de boş olma durumunu kontrol et
            if not maintenance_data and not battery_data:
                # Boş grafik yerine basit bir bilgi mesajı göster
                html_content = '''
                <div style="display: flex; justify-content: center; align-items: center; height: 100%; flex-direction: column;">
                    <div style="font-size: 24px; color: #7f8c8d; margin-bottom: 20px;">
                        <span style="font-size: 48px;">📊</span>
                    </div>
                    <div style="font-size: 18px; color: #7f8c8d; text-align: center;">
                        Seçili filtreler için veri bulunamadı.<br>Lütfen filtreleri değiştirin veya tüm verileri görüntüleyin.
                    </div>
                </div>
                '''
                self.web_view.setHtml(html_content)
                print("Boş veri mesajı görüntülendi")
                return
            else:
                # Veri varsa grafikleri oluştur
                # ... (grafik oluşturma kodları buraya gelecek)
                pass
        except Exception as e:
            print(f"Grafik oluşturma hatası: {e}")
                    
                    # Grafiğin HTML temsilini al
                    dashboard_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
                    
                    # Duyarlı HTML şablonu hazırla
                    html_content = f'''
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
                            .dashboard-container {{ width: 100%; }}
                            .dashboard-title {{ 
                                text-align: center; 
                                color: #2c3e50; 
                                padding: 10px; 
                                background: #ecf0f1; 
                                margin-bottom: 20px; 
                                border-radius: 8px;
                            }}
                            .filters-info {{ 
                                text-align: center; 
                                font-size: 13px; 
                                color: #7f8c8d; 
                                margin-bottom: 10px;
                                font-style: italic;
                            }}
                            .last-update {{ 
                                text-align: right; 
                                font-size: 11px; 
                                color: #95a5a6; 
                                padding: 5px; 
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="dashboard-container">
                            <div class="filters-info">
                                {filter_status_title} - Toplam Bakım: {toplam_bakim}, Pil Değişim: {toplam_pil_degisim}
                            </div>
                            {dashboard_html}
                            <div class="last-update">Son güncelleme: {stats['son_guncelleme']}</div>
                        </div>
                    </body>
                    </html>
                    '''
                    
                    # Web sayfasını yükle
                    self.web_view.setHtml(html_content)
                    print("Grafikler başarıyla oluşturuldu.")
                else:
                    # Veri yoksa boş dashboard göster
                    empty_html = f'''
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <style>
                            body {{ font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f5f5f5; }}
                            .empty-message {{ text-align: center; padding: 40px; background: white; border-radius: 10px; border: 1px solid #e0e0e0; }}
                            h2 {{ color: #3498db; }}
                            p {{ color: #7f8c8d; }}
                        </style>
                    </head>
                    <body>
                        <div class="empty-message">
                            <h2>Veri Bulunamadı</h2>
                            <p>Seçtiğiniz filtrelere uygun bakım veya pil değişim kaydı bulunamadı.</p>
                            <p>Lütfen filtreleri değiştirin veya tüm verileri görüntülemek için filtreleri temizleyin.</p>
                        </div>
                    </body>
                    </html>
                    '''
                    self.web_view.setHtml(empty_html)
                    print("Seçilen filtrelere uygun veri bulunamadı.")
            except Exception as e:
                print(f"Grafikleri oluştururken hata: {e}")
                
                # Hata durumunda bilgi göster
                error_html = f'''
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f5f5f5; }}
                        .error-message {{ text-align: center; padding: 40px; background: white; border-radius: 10px; border: 2px solid #e74c3c; }}
                        h2 {{ color: #e74c3c; }}
                        p {{ color: #7f8c8d; }}
                        code {{ background: #f8f9fa; padding: 4px 8px; border-radius: 4px; font-family: monospace; color: #e74c3c; }}
                    </style>
                </head>
                <body>
                    <div class="error-message">
                        <h2>Grafik Oluşturma Hatası</h2>
                        <p>Dashboard grafikleri oluşturulurken bir hata meydana geldi:</p>
                        <code>{str(e)}</code>
                        <p>Lütfen tekrar deneyin veya filtreleri değiştirin.</p>
                    </div>
                </body>
                </html>
                '''
                self.web_view.setHtml(error_html)
        except Exception as e:
            print(f"Dashboard güncellenirken hata: {e}")
        finally:
            session.close()
