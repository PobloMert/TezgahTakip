import os
from openpyxl import load_workbook

class ExcelTemplateLoader:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', 'excel_templates')
        
    def get_template(self, template_name):
        """Excel şablonunu yükler ve Workbook objesi döndürür"""
        template_path = os.path.join(self.template_dir, f"{template_name}.xlsx")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"{template_name} şablonu bulunamadı")
            
        return load_workbook(template_path)
    
    def get_available_templates(self):
        """Kullanılabilir şablon listesini döndürür"""
        templates = []
        for file in os.listdir(self.template_dir):
            if file.endswith('.xlsx'):
                templates.append(file.replace('.xlsx', ''))
        return templates
