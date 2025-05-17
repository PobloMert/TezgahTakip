from fpdf import FPDF
import os

class ReportTemplate(FPDF):
    def __init__(self, title, company_name):
        super().__init__()
        self.title = title
        self.company_name = company_name
        self.setup_template()
    
    def setup_template(self):
        """Temel şablon ayarları"""
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(True, margin=15)
        # Sistemde yüklü olan Arial fontunu kullan
        self.add_font('Arial', '', 'Arial.ttf', uni=True)
        self.add_font('Arial', 'B', 'Arial_Bold.ttf', uni=True)
        
    def header(self):
        """Özel header tasarımı"""
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.company_name, 0, 1, 'L')
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, self.title, 0, 1, 'C')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)
    
    def footer(self):
        """Özel footer tasarımı"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Sayfa {self.page_no()}/{{nb}}', 0, 0, 'C')
    
    def add_section(self, title, content):
        """Özelleştirilmiş bölüm ekler"""
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1)
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 8, content)
        self.ln(5)
