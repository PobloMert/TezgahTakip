import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # GUI olmadan matplotlib kullanımı için
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import KeepTogether
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from database.connection import db_manager
from models.maintenance import Bakim, PilDegisim, Tezgah
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta, date
import io
import sys
import calendar
import locale
import json
import re
import tempfile
import shutil

class ReportGenerator:
    def __init__(self):
        # Raporların kaydedileceği klasörü oluştur
        self.reports_dir = os.path.join(os.path.dirname(__file__), '..', 'raporlar')
        self.templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        self.images_dir = os.path.join(os.path.dirname(__file__), '..', 'images')
        
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Tarih formatları
        self.date_format = '%d-%m-%Y'
        self.display_date_format = '%d.%m.%Y'
        
        # Rapor şablonları 
        self.templates = {
            'default': {
                'name': 'Varsayılan Şablon',
                'colors': {
                    'header': colors.darkblue,
                    'subheader': colors.blue,
                    'text': colors.black,
                    'table_header': colors.lightblue,
                    'table_odd': colors.whitesmoke,
                    'table_even': colors.lightgrey,
                }
            },
            'professional': {
                'name': 'Profesyonel Şablon',
                'colors': {
                    'header': colors.black,
                    'subheader': colors.darkgrey,
                    'text': colors.black,
                    'table_header': colors.darkgrey,
                    'table_odd': colors.whitesmoke,
                    'table_even': colors.lightgrey,
                }
            },
            'colorful': {
                'name': 'Renkli Şablon',
                'colors': {
                    'header': colors.darkgreen,
                    'subheader': colors.green,
                    'text': colors.black,
                    'table_header': colors.lightgreen,
                    'table_odd': colors.whitesmoke,
                    'table_even': colors.lightgrey,
                }
            }
        }
        
        # Fontları kaydet
        self._register_fonts()

    def generate_maintenance_report(self, start_date=None, end_date=None, tezgah_ids=None, include_charts=True, include_stats=True, template='default'):
        """Gelişmiş bakım raporunu oluşturur"""
        print(f"Bakım raporu oluşturuluyor: {start_date} - {end_date}")
        print(f"Seçilen tezgahlar: {tezgah_ids}")
        print(f"Grafikler: {include_charts}, İstatistikler: {include_stats}, Şablon: {template}")
        
        session = db_manager.get_session()
        try:
            # Tarih aralığı kontrolü
            if not start_date:
                start_date = datetime.now() - timedelta(days=90)
            if not end_date:
                end_date = datetime.now()

            # Bakım kayıtlarını sorgula
            query = session.query(Bakim).join(Tezgah).options(joinedload(Bakim.tezgah))
            
            # Tezgah ID'lerine göre filtreleme
            if tezgah_ids and len(tezgah_ids) > 0:
                query = query.filter(Bakim.tezgah_id.in_(tezgah_ids))
            
            # Tarih filtrelemesi
            if isinstance(start_date, str):
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                except ValueError:
                    start_date = datetime.now() - timedelta(days=90)
                    
            if isinstance(end_date, str):
                try:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
                except ValueError:
                    end_date = datetime.now()
                
            # Tüm kayıtları al
            all_records = query.all()
            
            # Tarih filtreleme için kayıtları işle
            maintenance_records = []
            for record in all_records:
                record_date = None
                if isinstance(record.tarih, str):
                    try:
                        # DD-MM-YYYY formatından datetime'a çevir
                        parts = record.tarih.split('-')
                        if len(parts) == 3:
                            day, month, year = map(int, parts)
                            record_date = datetime(year, month, day)
                    except (ValueError, TypeError):
                        continue
                else:
                    record_date = record.tarih
                    
                # datetime ve date karşılaştırma sorununu çözmek için
                if record_date:
                    # Her iki tarafı da aynı tipte karşılaştırmak için date objesine dönüştür
                    if isinstance(record_date, datetime):
                        record_date = record_date.date()
                    if isinstance(start_date, datetime):
                        start_date_date = start_date.date()
                    else:
                        start_date_date = start_date
                    if isinstance(end_date, datetime):
                        end_date_date = end_date.date()
                    else:
                        end_date_date = end_date
                        
                    if start_date_date <= record_date <= end_date_date:
                        maintenance_records.append(record)
                    
            print(f"Filtrelenmiş kayıt sayısı: {len(maintenance_records)}")

            # İstatistikleri oluştur
            stats = None
            chart_paths = []
            
            if include_stats or include_charts:
                # Geçici klasör oluştur
                temp_dir = os.path.join(self.reports_dir, 'temp_charts')
                os.makedirs(temp_dir, exist_ok=True)
                
                # İstatistikleri hesapla
                stats = self._generate_maintenance_stats(maintenance_records)
                
                # Grafikler
                if include_charts:
                    chart_paths = self._create_maintenance_charts(stats, temp_dir)

            # Pandas DataFrame'e dönüştür - temiz veri
            maintenance_data = []
            for record in maintenance_records:
                try:
                    # Tüm verileri temizleyerek ekle
                    maintenance_data.append({
                        'Tezgah No': str(record.tezgah.numarasi),
                        'Bakım Tarihi': str(record.tarih) if record.tarih else '',
                        'Açıklama': self._simplify_text(record.aciklama),
                        'Yapan': self._simplify_text(record.bakim_yapan)
                    })
                except Exception as e:
                    print(f"Veri dönüştürme hatası: {e}")
            
            maintenance_df = pd.DataFrame(maintenance_data)

            # Rapor dosyalarını oluşturmak için timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Klasörü oluştur
            os.makedirs(self.reports_dir, exist_ok=True)
            
            # Rapor başlığı oluştur
            date_range = self._format_date_range(start_date, end_date)
            tezgah_names = self._get_tezgah_names(tezgah_ids)
            report_title = f"Bakım Raporu: {date_range} ({tezgah_names})"
            
            # Excel raporu
            excel_path = os.path.join(self.reports_dir, f'bakim_raporu_{timestamp}.xlsx')
            
            try:
                # Excel ayarları
                writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
                workbook = writer.book
                
                # Ana sayfa - Encoding belirterek Excel'e yaz
                maintenance_df.to_excel(writer, sheet_name='Bakım Kayıtları', index=False)
                
                # Ana sayfadaki sütun genişliklerini ayarla
                worksheet = writer.sheets['Bakım Kayıtları']
                for idx, col in enumerate(maintenance_df.columns):
                    # Maksimum sütun genişliğini hesapla
                    max_len = max(maintenance_df[col].astype(str).map(len).max(), len(str(col))) + 3
                    worksheet.set_column(idx, idx, max_len)
                
                # İstatistikler sayfası (varsa)
                if include_stats and stats and len(stats) > 0:
                    stats_sheet = workbook.add_worksheet('İstatistikler')
                    row = 0
                    
                    # Başlık - Kalın ve büyük yazı tipi
                    header_format = workbook.add_format({'bold': True, 'font_size': 14})
                    stats_sheet.write(row, 0, 'Bakım İstatistikleri', header_format)
                    row += 2
                    
                    # Alt başlık formatı
                    subheader_format = workbook.add_format({'bold': True, 'font_size': 12})
                    # Veri formatı
                    data_format = workbook.add_format({'align': 'center'})
                    
                    # Toplam sayı
                    if 'toplam_bakim' in stats:
                        stats_sheet.write(row, 0, 'Toplam Bakım Sayısı', subheader_format)
                        stats_sheet.write(row, 1, stats['toplam_bakim'], data_format)
                        row += 2
                    
                    # Tezgah bazlı istatistikler
                    if 'tezgah_bakim_sayilari' in stats and stats['tezgah_bakim_sayilari']:
                        stats_sheet.write(row, 0, 'Tezgah Bazında Bakım Sayıları', subheader_format)
                        row += 1
                        
                        # Tablo başlıkları
                        col_header_format = workbook.add_format({'bold': True, 'align': 'center', 'border': 1, 'bg_color': '#D9E1F2'})
                        stats_sheet.write(row, 0, 'Tezgah No', col_header_format)
                        stats_sheet.write(row, 1, 'Bakım Sayısı', col_header_format)
                        row += 1
                        
                        # Tezgah verileri
                        cell_format = workbook.add_format({'border': 1})
                        row_num = row
                        for tezgah_no, count in stats['tezgah_bakim_sayilari'].items():
                            stats_sheet.write(row_num, 0, tezgah_no, cell_format)
                            stats_sheet.write(row_num, 1, count, cell_format)
                            row_num += 1
                        
                        # Grafik ekle
                        if include_charts:
                            # Veri aralığını hazırla
                            num_items = len(stats['tezgah_bakim_sayilari'])
                            chart = workbook.add_chart({'type': 'column'})
                            
                            # Seri ekle
                            chart.add_series({
                                'name': 'Bakım Sayısı',
                                'categories': ['İstatistikler', row, 0, row + num_items - 1, 0],
                                'values': ['İstatistikler', row, 1, row + num_items - 1, 1],
                                'fill': {'color': '#5B9BD5'}
                            })
                            
                            # Grafik ayarları
                            chart.set_title({'name': 'Tezgah Bazında Bakım Sayıları'})
                            chart.set_x_axis({'name': 'Tezgah No'})
                            chart.set_y_axis({'name': 'Bakım Sayısı'})
                            chart.set_legend({'position': 'top'})
                            
                            # Grafiği yerleştir (G sütunu)
                            stats_sheet.insert_chart('D' + str(row), chart, {'x_scale': 1.5, 'y_scale': 1.5})
                        
                        row = row_num + 15  # Grafik için boşluk bırak
                    
                    # Bakım yapan istatistikleri
                    if 'bakim_yapanlar' in stats and stats['bakim_yapanlar']:
                        stats_sheet.write(row, 0, 'Bakım Yapanlar Dağılımı', subheader_format)
                        row += 1
                        
                        # Tablo başlıkları
                        stats_sheet.write(row, 0, 'Yapan', col_header_format)
                        stats_sheet.write(row, 1, 'Bakım Sayısı', col_header_format)
                        row += 1
                        
                        # Bakım yapan verileri
                        row_num = row
                        for yapan, count in stats['bakim_yapanlar'].items():
                            stats_sheet.write(row_num, 0, yapan, cell_format)
                            stats_sheet.write(row_num, 1, count, cell_format)
                            row_num += 1
                            
                        # Grafik ekle - Pasta grafiği
                        if include_charts and len(stats['bakim_yapanlar']) > 0:
                            num_items = len(stats['bakim_yapanlar'])
                            pie_chart = workbook.add_chart({'type': 'pie'})
                            
                            # Seri ekle
                            pie_chart.add_series({
                                'name': 'Bakım Yapanlar',
                                'categories': ['İstatistikler', row, 0, row + num_items - 1, 0],
                                'values': ['İstatistikler', row, 1, row + num_items - 1, 1],
                                'data_labels': {'percentage': True, 'category': True}
                            })
                            
                            # Grafik ayarları
                            pie_chart.set_title({'name': 'Bakım Yapan Kişi Dağılımı'})
                            pie_chart.set_legend({'position': 'bottom'})
                            
                            # Grafiği yerleştir
                            stats_sheet.insert_chart('D' + str(row), pie_chart, {'x_scale': 1.5, 'y_scale': 1.5})
                            
                        row = row_num + 15  # Grafik için boşluk bırak
                    
                    # Ay bazında bakım trendi
                    if 'aylik_bakim' in stats and stats['aylik_bakim']:
                        stats_sheet.write(row, 0, 'Aylık Bakım Trendi', subheader_format)
                        row += 1
                        
                        # Tablo başlıkları
                        stats_sheet.write(row, 0, 'Ay', col_header_format)
                        stats_sheet.write(row, 1, 'Bakım Sayısı', col_header_format)
                        row += 1
                        
                        # Aylık bakım verileri
                        row_num = row
                        for ay, count in stats['aylik_bakim'].items():
                            stats_sheet.write(row_num, 0, ay, cell_format)
                            stats_sheet.write(row_num, 1, count, cell_format)
                            row_num += 1
                            
                        # Grafik ekle - Çizgi grafiği
                        if include_charts and len(stats['aylik_bakim']) > 1:
                            num_items = len(stats['aylik_bakim'])
                            line_chart = workbook.add_chart({'type': 'line'})
                            
                            # Seri ekle
                            line_chart.add_series({
                                'name': 'Bakım Sayısı',
                                'categories': ['İstatistikler', row, 0, row + num_items - 1, 0],
                                'values': ['İstatistikler', row, 1, row + num_items - 1, 1],
                                'marker': {'type': 'circle', 'size': 8},
                                'line': {'width': 2.5, 'color': '#4472C4'}
                            })
                            
                            # Grafik ayarları
                            line_chart.set_title({'name': 'Aylık Bakım Trendi'})
                            line_chart.set_x_axis({'name': 'Ay'})
                            line_chart.set_y_axis({'name': 'Bakım Sayısı'})
                            
                            # Grafiği yerleştir
                            stats_sheet.insert_chart('D' + str(row), line_chart, {'x_scale': 1.5, 'y_scale': 1.5})
                        
                        row = row_num + 15  # Grafik için boşluk bırak
                
                writer.close()
                print("Excel raporu başarıyla oluşturuldu")
            except Exception as e:
                print(f"Excel oluşturulurken hata: {e}")
                return None

            # PDF raporu
            pdf_path = os.path.join(self.reports_dir, f'bakim_raporu_{timestamp}.pdf')
            try:
                self._generate_pdf_report(maintenance_df, pdf_path, report_title, stats, chart_paths, template)
                print("PDF raporu başarıyla oluşturuldu")
            except Exception as e:
                print(f"PDF raporu oluşturulurken hata: {e}")

            return {
                'excel_path': excel_path,
                'pdf_path': pdf_path
            }
        except Exception as e:
            print(f"Rapor oluşturulurken hata: {e}")
            return None
        finally:
            session.close()
            
    def generate_battery_report(self, start_date=None, end_date=None, tezgah_ids=None, include_charts=True, include_stats=True, group_by_model=False, template='default'):
        """Gelişmiş pil değişim raporunu oluşturur"""
        print(f"Pil değişim raporu oluşturuluyor: {start_date} - {end_date}")
        print(f"Seçilen tezgahlar: {tezgah_ids}")
        print(f"Grafikler: {include_charts}, İstatistikler: {include_stats}, Modele göre: {group_by_model}, Şablon: {template}")
        
        session = db_manager.get_session()
        try:
            # Tarih aralığı kontrolü
            if not start_date:
                start_date = datetime.now() - timedelta(days=90)
            if not end_date:
                end_date = datetime.now()

            # Pil değişim kayıtlarını sorgula
            query = session.query(PilDegisim).join(Tezgah).options(joinedload(PilDegisim.tezgah))
            
            # Tezgah ID'lerine göre filtreleme
            if tezgah_ids and len(tezgah_ids) > 0:
                query = query.filter(PilDegisim.tezgah_id.in_(tezgah_ids))
            
            # Tarih filtrelemesi
            if isinstance(start_date, str):
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                except ValueError:
                    start_date = datetime.now() - timedelta(days=90)
                    
            if isinstance(end_date, str):
                try:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
                except ValueError:
                    end_date = datetime.now()
                
            # Tüm kayıtları al
            all_records = query.all()
            
            # Tarih filtreleme için kayıtları işle
            battery_records = []
            for record in all_records:
                record_date = None
                if isinstance(record.tarih, str):
                    try:
                        # DD-MM-YYYY formatından datetime'a çevir
                        parts = record.tarih.split('-')
                        if len(parts) == 3:
                            day, month, year = map(int, parts)
                            record_date = datetime(year, month, day)
                    except (ValueError, TypeError):
                        continue
                else:
                    record_date = record.tarih
                    
                # datetime ve date karşılaştırma sorununu çözmek için
                if record_date:
                    # Her iki tarafı da aynı tipte karşılaştırmak için date objesine dönüştür
                    if isinstance(record_date, datetime):
                        record_date = record_date.date()
                    if isinstance(start_date, datetime):
                        start_date_date = start_date.date()
                    else:
                        start_date_date = start_date
                    if isinstance(end_date, datetime):
                        end_date_date = end_date.date()
                    else:
                        end_date_date = end_date
                        
                    if start_date_date <= record_date <= end_date_date:
                        battery_records.append(record)
                    
            print(f"Filtrelenmiş kayıt sayısı: {len(battery_records)}")

            # İstatistikleri oluştur
            stats = None
            chart_paths = []
            
            if include_stats or include_charts:
                # Geçici klasör oluştur
                temp_dir = os.path.join(self.reports_dir, 'temp_charts')
                os.makedirs(temp_dir, exist_ok=True)
                
                # İstatistikleri hesapla
                stats = self._generate_battery_stats(battery_records)
                
                # Grafikler
                if include_charts:
                    chart_paths = self._create_battery_charts(stats, temp_dir)

            # Pandas DataFrame'e dönüştür - temiz veri
            battery_data = []
            for record in battery_records:
                try:
                    # Tüm verileri temizleyerek ekle
                    battery_data.append({
                        'Tezgah No': str(record.tezgah.numarasi),
                        'Değişim Tarihi': str(record.tarih) if record.tarih else '',
                        'Pil Modeli': self._simplify_text(record.pil_modeli),
                        'Yapan': self._simplify_text(record.degisim_yapan)
                    })
                except Exception as e:
                    print(f"Veri dönüştürme hatası: {e}")
            
            battery_df = pd.DataFrame(battery_data)

            # Rapor dosyalarını oluşturmak için timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Klasörü oluştur
            os.makedirs(self.reports_dir, exist_ok=True)
            
            # Rapor başlığı oluştur
            date_range = self._format_date_range(start_date, end_date)
            tezgah_names = self._get_tezgah_names(tezgah_ids)
            report_title = f"Pil Değişim Raporu: {date_range} ({tezgah_names})"
            
            # Excel raporu
            excel_path = os.path.join(self.reports_dir, f'pil_degisim_raporu_{timestamp}.xlsx')
            
            try:
                # Excel ayarları
                writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
                workbook = writer.book
                
                # Ana sayfa - Encoding belirterek Excel'e yaz
                battery_df.to_excel(writer, sheet_name='Pil Değişim Kayıtları', index=False)
                
                # Ana sayfadaki sütun genişliklerini ayarla
                worksheet = writer.sheets['Pil Değişim Kayıtları']
                for idx, col in enumerate(battery_df.columns):
                    # Maksimum sütun genişliğini hesapla
                    max_len = max(battery_df[col].astype(str).map(len).max(), len(str(col))) + 3
                    worksheet.set_column(idx, idx, max_len)
                
                # Format tanımlamaları
                header_format = workbook.add_format({'bold': True, 'font_size': 14})
                subheader_format = workbook.add_format({'bold': True, 'font_size': 12})
                data_format = workbook.add_format({'align': 'center'})
                col_header_format = workbook.add_format({'bold': True, 'align': 'center', 'border': 1, 'bg_color': '#FFCC99'})  # Turuncu renk tonu
                cell_format = workbook.add_format({'border': 1})
                
                # Pil modeline göre gruplandırma isteği varsa, ek sayfa ekle
                if group_by_model and not battery_df.empty:
                    # Model bazında gruplandır
                    grouped_df = battery_df.groupby('Pil Modeli')
                    model_sheet = workbook.add_worksheet('Modele Göre')
                    row = 0
                    
                    # Başlık - Kalın format
                    model_sheet.write(row, 0, 'Modele Göre Pil Değişim Sayıları', header_format)
                    row += 2
                    
                    # Tablo başlıkları
                    model_sheet.write(row, 0, 'Pil Modeli', col_header_format)
                    model_sheet.write(row, 1, 'Değişim Sayısı', col_header_format)
                    row += 1
                    
                    # Pil modeli verileri
                    row_num = row
                    for model, group in grouped_df:
                        model_sheet.write(row_num, 0, model, cell_format)
                        model_sheet.write(row_num, 1, len(group), cell_format)
                        row_num += 1
                    
                    # Grafik ekle - Pasta grafiği
                    if include_charts:
                        num_items = len(grouped_df)
                        pie_chart = workbook.add_chart({'type': 'pie'})
                        
                        # Seri ekle
                        pie_chart.add_series({
                            'name': 'Pil Modeli Dağılımı',
                            'categories': ['Modele Göre', row, 0, row + num_items - 1, 0],
                            'values': ['Modele Göre', row, 1, row + num_items - 1, 1],
                            'data_labels': {'percentage': True, 'category': True}
                        })
                        
                        # Grafik ayarları
                        pie_chart.set_title({'name': 'Pil Modeli Dağılımı'})
                        pie_chart.set_legend({'position': 'bottom'})
                        
                        # Grafiği yerleştir
                        model_sheet.insert_chart('D' + str(row), pie_chart, {'x_scale': 1.5, 'y_scale': 1.5})
                
                # İstatistikler sayfası (varsa)
                if include_stats and stats and len(stats) > 0:
                    stats_sheet = workbook.add_worksheet('İstatistikler')
                    row = 0
                    
                    # Başlık
                    stats_sheet.write(row, 0, 'Pil Değişim İstatistikleri', header_format)
                    row += 2
                    
                    # Toplam sayı
                    if 'toplam_pil_degisim' in stats:
                        stats_sheet.write(row, 0, 'Toplam Pil Değişim Sayısı', subheader_format)
                        stats_sheet.write(row, 1, stats['toplam_pil_degisim'], data_format)
                        row += 2
                    
                    # Tezgah bazlı istatistikler
                    if 'tezgah_pil_sayilari' in stats and stats['tezgah_pil_sayilari']:
                        stats_sheet.write(row, 0, 'Tezgah Bazında Pil Değişim Sayıları', subheader_format)
                        row += 1
                        
                        # Tablo başlıkları
                        stats_sheet.write(row, 0, 'Tezgah No', col_header_format)
                        stats_sheet.write(row, 1, 'Değişim Sayısı', col_header_format)
                        row += 1
                        
                        # Tezgah verileri
                        row_num = row
                        for tezgah_no, count in stats['tezgah_pil_sayilari'].items():
                            stats_sheet.write(row_num, 0, tezgah_no, cell_format)
                            stats_sheet.write(row_num, 1, count, cell_format)
                            row_num += 1
                            
                        # Grafik ekle - Çubuk grafik
                        if include_charts:
                            num_items = len(stats['tezgah_pil_sayilari'])
                            chart = workbook.add_chart({'type': 'column'})
                            
                            # Seri ekle
                            chart.add_series({
                                'name': 'Pil Değişim',
                                'categories': ['İstatistikler', row, 0, row + num_items - 1, 0],
                                'values': ['İstatistikler', row, 1, row + num_items - 1, 1],
                                'fill': {'color': '#FF9966'}  # Turuncu renk tonu
                            })
                            
                            # Grafik ayarları
                            chart.set_title({'name': 'Tezgah Bazında Pil Değişimleri'})
                            chart.set_x_axis({'name': 'Tezgah No'})
                            chart.set_y_axis({'name': 'Değişim Sayısı'})
                            
                            # Grafiği yerleştir
                            stats_sheet.insert_chart('D' + str(row), chart, {'x_scale': 1.5, 'y_scale': 1.5})
                            
                        row = row_num + 15  # Grafik için boşluk bırak
                    
                    # Pil modeli istatistikleri
                    if 'pil_modelleri' in stats and stats['pil_modelleri']:
                        stats_sheet.write(row, 0, 'Pil Modeli Dağılımı', subheader_format)
                        row += 1
                        
                        # Tablo başlıkları
                        stats_sheet.write(row, 0, 'Model', col_header_format)
                        stats_sheet.write(row, 1, 'Kullanım Sayısı', col_header_format)
                        row += 1
                        
                        # Model verileri
                        row_num = row
                        for model, count in stats['pil_modelleri'].items():
                            stats_sheet.write(row_num, 0, model, cell_format)
                            stats_sheet.write(row_num, 1, count, cell_format)
                            row_num += 1
                            
                        # Grafik ekle - Pasta grafik
                        if include_charts and len(stats['pil_modelleri']) > 0:
                            num_items = len(stats['pil_modelleri'])
                            pie_chart = workbook.add_chart({'type': 'pie'})
                            
                            # Seri ekle
                            pie_chart.add_series({
                                'name': 'Pil Modelleri',
                                'categories': ['İstatistikler', row, 0, row + num_items - 1, 0],
                                'values': ['İstatistikler', row, 1, row + num_items - 1, 1],
                                'data_labels': {'percentage': True, 'category': True}
                            })
                            
                            # Grafik ayarları
                            pie_chart.set_title({'name': 'Pil Modeli Dağılımı'})
                            pie_chart.set_legend({'position': 'bottom'})
                            
                            # Grafiği yerleştir
                            stats_sheet.insert_chart('D' + str(row), pie_chart, {'x_scale': 1.5, 'y_scale': 1.5})
                            
                        row = row_num + 15  # Grafik için boşluk bırak
                        
                    # Ay bazında pil değişim trendi
                    if 'aylik_pil_degisim' in stats and stats['aylik_pil_degisim']:
                        stats_sheet.write(row, 0, 'Aylık Pil Değişim Trendi', subheader_format)
                        row += 1
                        
                        # Tablo başlıkları
                        stats_sheet.write(row, 0, 'Ay', col_header_format)
                        stats_sheet.write(row, 1, 'Değişim Sayısı', col_header_format)
                        row += 1
                        
                        # Aylık değişim verileri
                        row_num = row
                        for ay, count in stats['aylik_pil_degisim'].items():
                            stats_sheet.write(row_num, 0, ay, cell_format)
                            stats_sheet.write(row_num, 1, count, cell_format)
                            row_num += 1
                            
                        # Grafik ekle - Çizgi grafiği
                        if include_charts and len(stats['aylik_pil_degisim']) > 1:
                            num_items = len(stats['aylik_pil_degisim'])
                            line_chart = workbook.add_chart({'type': 'line'})
                            
                            # Seri ekle
                            line_chart.add_series({
                                'name': 'Pil Değişim',
                                'categories': ['İstatistikler', row, 0, row + num_items - 1, 0],
                                'values': ['İstatistikler', row, 1, row + num_items - 1, 1],
                                'marker': {'type': 'circle', 'size': 8},
                                'line': {'width': 2.5, 'color': '#FF8C00'}  # Turuncu renk tonu
                            })
                            
                            # Grafik ayarları
                            line_chart.set_title({'name': 'Aylık Pil Değişim Trendi'})
                            line_chart.set_x_axis({'name': 'Ay'})
                            line_chart.set_y_axis({'name': 'Değişim Sayısı'})
                            
                            # Grafiği yerleştir
                            stats_sheet.insert_chart('D' + str(row), line_chart, {'x_scale': 1.5, 'y_scale': 1.5})
                
                writer.close()
                print("Excel raporu başarıyla oluşturuldu")
            except Exception as e:
                print(f"Excel oluşturulurken hata: {e}")
                return None

            # PDF raporu
            pdf_path = os.path.join(self.reports_dir, f'pil_degisim_raporu_{timestamp}.pdf')
            try:
                self._generate_pdf_report(battery_df, pdf_path, report_title, stats, chart_paths, template)
                print("PDF raporu başarıyla oluşturuldu")
            except Exception as e:
                print(f"PDF raporu oluşturulurken hata: {e}")

            return {
                'excel_path': excel_path,
                'pdf_path': pdf_path
            }
        except Exception as e:
            print(f"Rapor oluşturulurken hata: {e}")
            return None
        finally:
            session.close()

    def _generate_maintenance_stats(self, maintenance_records):
        """Bakım kayıtları için istatistikleri hesaplar"""
        stats = {}
        
        try:
            if not maintenance_records or len(maintenance_records) == 0:
                return stats
                
            # Tezgah bazlı bakım sayıları
            tezgah_stats = {}
            for record in maintenance_records:
                tezgah_no = record.tezgah.numarasi
                if tezgah_no not in tezgah_stats:
                    tezgah_stats[tezgah_no] = 0
                tezgah_stats[tezgah_no] += 1
            
            # Tezgah bazında bakım sıklığı
            stats['tezgah_bakim_sayilari'] = tezgah_stats
            
            # Bakım yapanların istatistikleri
            yapan_stats = {}
            for record in maintenance_records:
                yapan = self._simplify_text(record.bakim_yapan)
                if yapan not in yapan_stats:
                    yapan_stats[yapan] = 0
                yapan_stats[yapan] += 1
            
            stats['bakim_yapanlar'] = yapan_stats
            
            # Ay bazında bakım sayıları
            ay_stats = {}
            for record in maintenance_records:
                # Tarih formatını kontrol et ve ay bilgisini çıkar
                tarih = record.tarih
                ay = None
                
                if isinstance(tarih, str):
                    try:
                        # DD-MM-YYYY formatını analiz et
                        parts = tarih.split('-')
                        if len(parts) == 3:
                            ay = int(parts[1])  # Ay kısmı
                    except:
                        pass
                elif isinstance(tarih, datetime) or isinstance(tarih, date):
                    ay = tarih.month
                    
                if ay:
                    ay_adi = calendar.month_name[ay]
                    if ay_adi not in ay_stats:
                        ay_stats[ay_adi] = 0
                    ay_stats[ay_adi] += 1
            
            stats['aylik_bakim'] = ay_stats
            
            # Toplam bakım sayısı
            stats['toplam_bakim'] = len(maintenance_records)
            
            return stats
            
        except Exception as e:
            print(f"Bakım istatistikleri hesaplanırken hata: {e}")
            return {}
    
    def _generate_battery_stats(self, battery_records):
        """Pil değişim kayıtları için istatistikleri hesaplar"""
        stats = {}
        
        try:
            if not battery_records or len(battery_records) == 0:
                return stats
                
            # Tezgah bazlı pil değişim sayıları
            tezgah_stats = {}
            for record in battery_records:
                tezgah_no = record.tezgah.numarasi
                if tezgah_no not in tezgah_stats:
                    tezgah_stats[tezgah_no] = 0
                tezgah_stats[tezgah_no] += 1
            
            # Tezgah bazında pil değişim sıklığı
            stats['tezgah_pil_sayilari'] = tezgah_stats
            
            # Pil modeli istatistikleri
            model_stats = {}
            for record in battery_records:
                model = self._simplify_text(record.pil_modeli)
                if model not in model_stats:
                    model_stats[model] = 0
                model_stats[model] += 1
            
            stats['pil_modelleri'] = model_stats
            
            # Ay bazında pil değişim sayıları
            ay_stats = {}
            for record in battery_records:
                # Tarih formatını kontrol et ve ay bilgisini çıkar
                tarih = record.tarih
                ay = None
                
                if isinstance(tarih, str):
                    try:
                        # DD-MM-YYYY formatını analiz et
                        parts = tarih.split('-')
                        if len(parts) == 3:
                            ay = int(parts[1])  # Ay kısmı
                    except:
                        pass
                elif isinstance(tarih, datetime) or isinstance(tarih, date):
                    ay = tarih.month
                    
                if ay:
                    ay_adi = calendar.month_name[ay]
                    if ay_adi not in ay_stats:
                        ay_stats[ay_adi] = 0
                    ay_stats[ay_adi] += 1
            
            stats['aylik_pil_degisim'] = ay_stats
            
            # Toplam pil değişim sayısı
            stats['toplam_pil_degisim'] = len(battery_records)
            
            return stats
            
        except Exception as e:
            print(f"Pil değişim istatistikleri hesaplanırken hata: {e}")
            return {}
    
    def _create_maintenance_charts(self, stats, output_dir):
        """Bakım istatistikleri için grafikler oluşturur"""
        chart_paths = []
        
        try:
            if not stats or not os.path.exists(output_dir):
                return chart_paths
            
            # 1. Tezgah bazında bakım sayıları grafiği
            if 'tezgah_bakim_sayilari' in stats and stats['tezgah_bakim_sayilari']:
                tezgah_stats = stats['tezgah_bakim_sayilari']
                
                plt.figure(figsize=(10, 6))
                plt.bar(tezgah_stats.keys(), tezgah_stats.values(), color='skyblue')
                plt.title('Tezgah Baz\u0131nda Bak\u0131m Say\u0131lar\u0131')
                plt.xlabel('Tezgah No')
                plt.ylabel('Bak\u0131m Say\u0131s\u0131')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Grafik dosyasını kaydet
                tezgah_chart_path = os.path.join(output_dir, 'tezgah_bakim_chart.png')
                plt.savefig(tezgah_chart_path)
                plt.close()
                chart_paths.append(tezgah_chart_path)
            
            # 2. Aylık bakım trendi grafiği
            if 'aylik_bakim' in stats and stats['aylik_bakim']:
                aylik_stats = stats['aylik_bakim']
                
                plt.figure(figsize=(10, 6))
                plt.plot(list(aylik_stats.keys()), list(aylik_stats.values()), marker='o', linestyle='-', color='green')
                plt.title('Ayl\u0131k Bak\u0131m Trendi')
                plt.xlabel('Ay')
                plt.ylabel('Bak\u0131m Say\u0131s\u0131')
                plt.xticks(rotation=45)
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                
                # Grafik dosyasını kaydet
                aylik_chart_path = os.path.join(output_dir, 'aylik_bakim_chart.png')
                plt.savefig(aylik_chart_path)
                plt.close()
                chart_paths.append(aylik_chart_path)
            
            # 3. Bakım yapanlar pasta grafiği
            if 'bakim_yapanlar' in stats and stats['bakim_yapanlar']:
                yapan_stats = stats['bakim_yapanlar']
                
                plt.figure(figsize=(8, 8))
                plt.pie(yapan_stats.values(), labels=yapan_stats.keys(), autopct='%1.1f%%', startangle=90, shadow=True)
                plt.title('Bak\u0131m Yapanlar Da\u011f\u0131l\u0131m\u0131')
                plt.axis('equal')  # Eşit oranlarda görüntülemek için
                
                # Grafik dosyasını kaydet
                yapan_chart_path = os.path.join(output_dir, 'bakim_yapan_chart.png')
                plt.savefig(yapan_chart_path)
                plt.close()
                chart_paths.append(yapan_chart_path)
                
            return chart_paths
            
        except Exception as e:
            print(f"Bakım grafikleri oluşturulurken hata: {e}")
            return []
    
    def _create_battery_charts(self, stats, output_dir):
        """Pil değişim istatistikleri için grafikler oluşturur"""
        chart_paths = []
        
        try:
            if not stats or not os.path.exists(output_dir):
                return chart_paths
            
            # 1. Tezgah bazında pil değişim sayıları grafiği
            if 'tezgah_pil_sayilari' in stats and stats['tezgah_pil_sayilari']:
                tezgah_stats = stats['tezgah_pil_sayilari']
                
                plt.figure(figsize=(10, 6))
                plt.bar(tezgah_stats.keys(), tezgah_stats.values(), color='orange')
                plt.title('Tezgah Baz\u0131nda Pil De\u011fi\u015fim Say\u0131lar\u0131')
                plt.xlabel('Tezgah No')
                plt.ylabel('De\u011fi\u015fim Say\u0131s\u0131')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Grafik dosyasını kaydet
                tezgah_chart_path = os.path.join(output_dir, 'tezgah_pil_chart.png')
                plt.savefig(tezgah_chart_path)
                plt.close()
                chart_paths.append(tezgah_chart_path)
            
            # 2. Aylık pil değişim trendi grafiği
            if 'aylik_pil_degisim' in stats and stats['aylik_pil_degisim']:
                aylik_stats = stats['aylik_pil_degisim']
                
                plt.figure(figsize=(10, 6))
                plt.plot(list(aylik_stats.keys()), list(aylik_stats.values()), marker='o', linestyle='-', color='blue')
                plt.title('Ayl\u0131k Pil De\u011fi\u015fim Trendi')
                plt.xlabel('Ay')
                plt.ylabel('De\u011fi\u015fim Say\u0131s\u0131')
                plt.xticks(rotation=45)
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                
                # Grafik dosyasını kaydet
                aylik_chart_path = os.path.join(output_dir, 'aylik_pil_chart.png')
                plt.savefig(aylik_chart_path)
                plt.close()
                chart_paths.append(aylik_chart_path)
            
            # 3. Pil modeli pasta grafiği
            if 'pil_modelleri' in stats and stats['pil_modelleri']:
                model_stats = stats['pil_modelleri']
                
                plt.figure(figsize=(8, 8))
                plt.pie(model_stats.values(), labels=model_stats.keys(), autopct='%1.1f%%', startangle=90, shadow=True)
                plt.title('Pil Modeli Da\u011f\u0131l\u0131m\u0131')
                plt.axis('equal')  # Eşit oranlarda görüntülemek için
                
                # Grafik dosyasını kaydet
                model_chart_path = os.path.join(output_dir, 'pil_model_chart.png')
                plt.savefig(model_chart_path)
                plt.close()
                chart_paths.append(model_chart_path)
                
            return chart_paths
            
        except Exception as e:
            print(f"Pil değişim grafikleri oluşturulurken hata: {e}")
            return []
    
    def _generate_pdf_report(self, dataframe, output_path, title, stats=None, chart_paths=None, template='default'):
        """
        Gelişmiş PDF raporu oluşturur
        
        Args:
            dataframe (pd.DataFrame): Rapor verisi
            output_path (str): Çıktı PDF dosyası yolu
            title (str): Rapor başlığı
            stats (dict): İstatistikler
            chart_paths (list): Grafik dosya yolları
            template (str): Kullanılacak şablon adı
        """
        try:
            # Stil ve tema
            styles, colors_dict = self._create_styles(template)
            
            # PDF belgesi oluştur
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            elements = []
            
            # Başlık ekle
            elements.append(Paragraph(title, styles['Title_Turkish']))
            elements.append(Spacer(1, 0.5*cm))
            
            # Tarih bilgisi
            date_info = f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}" 
            elements.append(Paragraph(date_info, styles['Normal_Turkish']))
            elements.append(Spacer(1, 0.5*cm))
            
            # Boş DataFrame kontrolü
            if dataframe.empty:
                elements.append(Paragraph("Bu tarih aralığında kayıt bulunamadı.", styles['Normal_Turkish']))
            else:
                # İstatistik özeti (varsa)
                if stats and len(stats) > 0:
                    elements.append(Paragraph("İstatistik Özeti", styles['Heading1_Turkish']))
                    elements.append(Spacer(1, 0.3*cm))
                    
                    # Toplam kayıt sayısı
                    if 'toplam_bakim' in stats:
                        elements.append(Paragraph(f"Toplam Bakım Sayısı: {stats['toplam_bakim']}", styles['Normal_Turkish']))
                    if 'toplam_pil_degisim' in stats:
                        elements.append(Paragraph(f"Toplam Pil Değişim Sayısı: {stats['toplam_pil_degisim']}", styles['Normal_Turkish']))
                    
                    elements.append(Spacer(1, 0.5*cm))
                
                # Grafikleri ekle (varsa)
                if chart_paths and len(chart_paths) > 0:
                    elements.append(Paragraph("Grafikler", styles['Heading1_Turkish']))
                    elements.append(Spacer(1, 0.3*cm))
                    
                    for chart_path in chart_paths:
                        try:
                            # Her grafik için açıklama ve grafik ekle
                            chart_name = os.path.basename(chart_path).replace('.png', '').replace('_', ' ').title()
                            elements.append(Paragraph(chart_name, styles['Normal_Turkish']))
                            elements.append(Spacer(1, 0.2*cm))
                            
                            # Grafik boyutu ayarla (eni 15 cm olacak şekilde)
                            img = Image(chart_path, width=15*cm, height=10*cm)
                            elements.append(img)
                            elements.append(Spacer(1, 0.5*cm))
                        except Exception as e:
                            print(f"Grafik eklenirken hata: {e}")
                    
                    elements.append(Spacer(1, 0.5*cm))
                
                # Veri tablosunu ekle
                elements.append(Paragraph("Kayıt Listesi", styles['Heading1_Turkish']))
                elements.append(Spacer(1, 0.3*cm))
                
                # Tablo verilerini hazırla
                table_data = [dataframe.columns.tolist()] + dataframe.values.tolist()
                
                # Tablo stili
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors_dict['table_header']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold-Turkish'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                # Tablonun satır renklerini zebra stili olarak ayarla
                for i in range(1, len(table_data)):
                    if i % 2 == 0:
                        bg_color = colors_dict['table_even']
                    else:
                        bg_color = colors_dict['table_odd']
                    table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), bg_color)]))
                
                elements.append(table)
            
            # PDF oluştur
            doc.build(elements)
            print(f"PDF raporu oluşturuldu: {output_path}")
            return True
        except Exception as e:
            print(f"PDF oluşturma hatası: {e}")
            return False

    def _register_fonts(self):
        """Türkçe karakterleri destekleyen fontları kaydeder"""
        try:
            # Windows sisteme özel font yüklemeleri
            font_paths = {
                'Arial-Turkish': "C:\\Windows\\Fonts\\arial.ttf",
                'Arial-Bold-Turkish': "C:\\Windows\\Fonts\\arialbd.ttf",
                'Times-Turkish': "C:\\Windows\\Fonts\\times.ttf",
                'Verdana-Turkish': "C:\\Windows\\Fonts\\verdana.ttf"
            }
            
            # Fontları kaydet
            for name, path in font_paths.items():
                if os.path.exists(path):
                    pdfmetrics.registerFont(TTFont(name, path))
                    print(f"Font yüklendi: {name}")
            
        except Exception as e:
            print(f"Font yükleme hatası: {e}")
            print("Varsayılan fontlar kullanılacak")
    
    def _create_styles(self, template='default'):
        """Rapor için stil ayarları oluşturur"""
        # Şablon renklerini al
        if template not in self.templates:
            template = 'default'
            
        colors_dict = self.templates[template]['colors']
        
        # Temel stiller
        styles = getSampleStyleSheet()
        
        # Özel stiller
        styles.add(ParagraphStyle(
            name='Title_Turkish',
            parent=styles['Title'],
            fontName='Arial-Bold-Turkish',
            textColor=colors_dict['header']
        ))
        
        styles.add(ParagraphStyle(
            name='Heading1_Turkish',
            parent=styles['Heading1'],
            fontName='Arial-Bold-Turkish',
            textColor=colors_dict['subheader']
        ))
        
        styles.add(ParagraphStyle(
            name='Normal_Turkish',
            parent=styles['Normal'],
            fontName='Arial-Turkish',
            textColor=colors_dict['text']
        ))
        
        return styles, colors_dict
        
    def _simplify_text(self, text):
        """Metni basitleştirir, Türkçe karakter sorunlarını giderir"""
        if text is None:
            return ""
            
        try:
            # Önce uygun string'e çevir
            if not isinstance(text, str):
                text = str(text)
                
            # Tüm sorunlu karakterleri temizle
            cleaned_text = ""
            for char in text:
                # ASCII aralığındaki güvenli karakterleri kullan
                if 32 <= ord(char) <= 126:
                    cleaned_text += char
                # Türkçe karakterleri inglizce karşılıklarıyla değiştir
                elif char == 'ç': cleaned_text += 'c'  # ç -> c
                elif char == 'Ç': cleaned_text += 'C'  # Ç -> C
                elif char == 'ğ': cleaned_text += 'g'  # ğ -> g
                elif char == 'Ğ': cleaned_text += 'G'  # Ğ -> G
                elif char == 'ı': cleaned_text += 'i'  # ı -> i
                elif char == 'İ': cleaned_text += 'I'  # İ -> I
                elif char == 'ö': cleaned_text += 'o'  # ö -> o
                elif char == 'Ö': cleaned_text += 'O'  # Ö -> O
                elif char == 'ş': cleaned_text += 's'  # ş -> s
                elif char == 'Ş': cleaned_text += 'S'  # Ş -> S
                elif char == 'ü': cleaned_text += 'u'  # ü -> u
                elif char == 'Ü': cleaned_text += 'U'  # Ü -> U
                # Diğer karakterleri boşlukla değiştir
                else:
                    cleaned_text += ' '
            return cleaned_text
        except Exception as e:
            print(f"Metin basitleştirme hatası: {e}")
            return ""
    
    def _format_date_range(self, start_date, end_date):
        """Tarih aralığını formatlayarak döndürür"""
        try:
            # Tarih nesnelerini oluştur
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                
            # Görüntülenecek formatla döndür
            start_str = start_date.strftime(self.display_date_format)
            end_str = end_date.strftime(self.display_date_format)
            
            return f"{start_str} - {end_str}"
        except Exception:
            return "Tarih aralığı belirtilmemiş"
            
    def _get_tezgah_names(self, tezgah_ids):
        """Tezgah ID'lerine göre tezgah isimlerini döndürür"""
        if not tezgah_ids or len(tezgah_ids) == 0:
            return "Tüm Tezgahlar"
            
        try:
            session = db_manager.get_session()
            tezgahlar = session.query(Tezgah).filter(Tezgah.id.in_(tezgah_ids)).all()
            session.close()
            
            if not tezgahlar:
                return "Tüm Tezgahlar"
                
            # Tezgah numaralarını birleştir
            tezgah_names = [tezgah.numarasi for tezgah in tezgahlar]
            if len(tezgah_names) <= 3:
                return ", ".join(tezgah_names)
            else:
                return f"{len(tezgah_names)} Tezgah Seçildi"
        except Exception as e:
            print(f"Tezgah isimleri alınırken hata: {e}")
            return "Tüm Tezgahlar"

report_generator = ReportGenerator()