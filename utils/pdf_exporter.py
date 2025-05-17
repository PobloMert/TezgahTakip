from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
import datetime

class PDFExporter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
    def export_report(self, filename, data, report_type):
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elements = []
        
        # Başlık ekle
        title = Paragraph(f"<b>Tezgah Takip Raporu - {report_type}</b>", self.styles['Title'])
        elements.append(title)
        
        # Tarih bilgisi
        date_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        date_text = Paragraph(f"<i>Oluşturulma Tarihi: {date_str}</i>", self.styles['Normal'])
        elements.append(date_text)
        elements.append(Spacer(1, 10*mm))
        
        # Veriyi tablo formatına dönüştür
        table_data = [['Tezgah No', 'Bakım Sayısı', 'Son Bakım', 'Durum']]
        for row in data:
            table_data.append([
                row.get('machine_id', ''),
                row.get('maintenance_count', 0),
                row.get('last_maintenance', '-'),
                row.get('status', '-')
            ])
        
        # Tablo oluştur
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        return filename
