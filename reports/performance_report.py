import logging
from datetime import datetime, timedelta
from database.connection import db_manager
from models.maintenance import Bakim, PilDegisim
import matplotlib.pyplot as plt
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fpdf import FPDF
import pandas as pd
import sqlalchemy as sa
import seaborn as sns
import plotly.express as px
from .templates import ReportTemplate

class PerformanceReport:
    def __init__(self):
        self.session = db_manager.Session()
        os.makedirs('reports', exist_ok=True)
        self.template = ReportTemplate(
            title='Tezgah Performans Raporu',
            company_name='PobloMert Makina'
        )
    
    def generate_mttr(self, days=30):
        """Ortalama Tamir Süresi (Mean Time To Repair)"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        results = self.session.query(
            Bakim.tezgah_id,
            (sa.func.julianday(Bakim.tamamlanma_tarihi) - sa.func.julianday(Bakim.tarih)).label('mttr')
        ).filter(
            Bakim.durum == 'Tamamlandı',
            Bakim.tarih.between(start_date, end_date)
        ).all()
        
        return [{'tezgah_id': r[0], 'mttr': r[1]} for r in results]

    def generate_battery_reports(self):
        """Pil ömrü analiz raporu"""
        return self.session.query(
            PilDegisim.eksen,
            sa.func.avg(sa.func.julianday(PilDegisim.tarih)).label('ortalama_ömür')
        ).group_by(PilDegisim.eksen).all()

    def generate_maintenance_frequency(self, days=90):
        """Tezgah bazında bakım sıklığını hesaplar"""
        query = """
        SELECT 
            tezgah_id,
            COUNT(*) as bakim_sayisi
        FROM bakimlar
        WHERE tarih >= date('now', '-{} days')
        GROUP BY tezgah_id
        ORDER BY bakim_sayisi DESC
        """.format(days)
        return self.session.execute(query).fetchall()

    def generate_axis_failure_rate(self):
        """Eksenlerin arıza oranlarını hesaplar"""
        return self.session.query(
            Bakim.eksen,
            sa.func.count().label('arıza_sayisi')
        ).group_by(Bakim.eksen).all()

    def save_report(self, filename, data):
        """Raporu HTML olarak kaydeder"""
        with open(f'reports/{filename}', 'w') as f:
            f.write(self._generate_html(data))
        return f'reports/{filename}'

    def _generate_html(self, data):
        """Rapor HTML şablonu"""
        return f"""
        <html>
        <head><title>Bakım Raporu</title></head>
        <body>
            <h1>Tezgah Bakım Analizleri</h1>
            <pre>{data}</pre>
        </body>
        </html>
        """

    def _embed_plot_to_pdf(self, plot_func, title):
        """Matplotlib grafiğini PDF'e göm"""
        temp_img = 'reports/temp_plot.png'
        plot_func()  # Grafiği oluştur
        
        self.template.set_font('Arial', 'B', 14)
        self.template.cell(0, 10, title, 0, 1)
        self.template.image(temp_img, x=10, y=None, w=180)
        self.template.ln(10)  # Boşluk ekle
        
        if os.path.exists(temp_img):
            os.remove(temp_img)

    def plot_mttr_trend(self):
        # MTTR trend grafiği oluştur
        mttr_data = self.generate_mttr()
        tezgah_ids = [item['tezgah_id'] for item in mttr_data]
        mttr_values = [item['mttr'] for item in mttr_data]
        
        plt.bar(tezgah_ids, mttr_values)
        plt.xlabel('Tezgah ID')
        plt.ylabel('MTTR (gün)')
        plt.title('MTTR Trend Grafiği')
        plt.savefig('reports/temp_plot.png')

    def plot_maintenance_freq(self):
        # Bakım sıklığı grafiği oluştur
        freq_data = self.generate_maintenance_frequency()
        tezgah_ids = [item[0] for item in freq_data]
        freq_values = [item[1] for item in freq_data]
        
        plt.bar(tezgah_ids, freq_values)
        plt.xlabel('Tezgah ID')
        plt.ylabel('Bakım Sıklığı')
        plt.title('Bakım Sıklığı Grafiği')
        plt.savefig('reports/temp_plot.png')

    def generate_heatmap(self):
        """Bakım sıklığı heatmap oluşturur"""
        data = self.session.query(
            sa.func.strftime('%W', Bakim.tarih).label('hafta'),
            Bakim.tezgah_id,
            sa.func.count().label('sayi')
        ).group_by('hafta', 'tezgah_id').all()
        
        df = pd.DataFrame(data, columns=['hafta', 'tezgah_id', 'sayi'])
        pivot = df.pivot(index='hafta', columns='tezgah_id', values='sayi')
        
        plt.figure(figsize=(12, 6))
        sns.heatmap(pivot, annot=True, fmt='d', cmap='YlOrRd')
        plt.title('Haftalık Bakım Sıklığı')
        plt.savefig('reports/heatmap.png')
        return 'reports/heatmap.png'
    
    def generate_interactive_graph(self):
        """Etkileşimli Plotly grafiği oluşturur"""
        mttr = self.generate_mttr()
        freq = self.generate_maintenance_frequency()
        
        df = pd.DataFrame({
            'tezgah_id': [x['tezgah_id'] for x in mttr],
            'mttr': [x['mttr'] for x in mttr],
            'freq': [next((y[1] for y in freq if y[0] == x['tezgah_id']), 0) for x in mttr]
        })
        
        fig = px.scatter(
            df, x='mttr', y='freq', 
            color='tezgah_id', size='freq',
            hover_data=['tezgah_id'],
            title='MTTR vs Bakım Sıklığı'
        )
        
        fig.write_html('reports/interactive_graph.html')
        return 'reports/interactive_graph.html'

    def _prepare_report_data(self):
        # Detaylı metrikler için veri hazırla
        mttr_data = self.generate_mttr()
        freq_data = self.generate_maintenance_frequency()
        axis_failure_data = self.generate_axis_failure_rate()
        
        data = []
        for tezgah_id in set([item['tezgah_id'] for item in mttr_data]):
            mttr = next((item['mttr'] for item in mttr_data if item['tezgah_id'] == tezgah_id), None)
            freq = next((item[1] for item in freq_data if item[0] == tezgah_id), None)
            axis_failure = next((item[1] for item in axis_failure_data if item[0] == tezgah_id), None)
            
            data.append([tezgah_id, mttr, freq, axis_failure])
        
        return data

    def generate_pdf_report(self, filename='tezgah_raporu.pdf'):
        """Şablon tabanlı PDF raporu"""
        self.template.add_page()
        
        # Başlık ve bilgiler
        self.template.add_section(
            'Genel Performans Özeti',
            'Bu rapor tezgahların son 30 günlük performansını göstermektedir.'
        )
        
        # Grafikleri ekle
        self._embed_plot_to_pdf(self.plot_mttr_trend, 'MTTR Trend Grafiği')
        self._embed_plot_to_pdf(self.plot_maintenance_freq, 'Bakım Sıklığı')
        
        # Detaylı analiz
        self.template.add_page()
        self.template.add_section(
            'Detaylı Metrikler',
            'Aşağıda tezgah bazında detaylı performans metrikleri bulunmaktadır.'
        )
        
        # Tabloları oluştur
        self._add_metrics_table()
        
        self.template.output(f'reports/{filename}')
        return f'reports/{filename}'
    
    def _add_metrics_table(self):
        """Özelleştirilmiş metrik tablosu"""
        data = self._prepare_report_data()
        
        with self.template.table(
            col_widths=[40, 30, 40, 40],
            headings_style={'fill_color': (66, 129, 164), 'text_color': (255, 255, 255)},
            row_fill_color=(224, 235, 241)
        ) as table:
            # Başlıklar
            table.row(['Tezgah', 'MTTR', 'Bakım Sıklığı', 'Arıza Oranı'])
            
            # Veriler
            for row in data:
                table.row([
                    str(row[0]),
                    f"{row[1]:.2f} gün",
                    str(row[2]),
                    str(row[3])
                ])

    def __del__(self):
        self.session.close()
