"""
Etkileşimli yardım sistemi
"""
from PyQt5.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

class HelpSystem(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yardım Sistemi")
        self.resize(600, 400)
        
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        self.setLayout(layout)
        
        self.load_help_content()

    def load_help_content(self):
        content = """
        <h1>Tezgah Takip Yardım</h1>
        <h2>Tema Yönetimi</h2>
        <p>Menü > Tema seçeneklerinden istediğiniz temayı seçebilirsiniz.</p>
        <h2>Font Ayarları</h2>
        <p>Menü > Yazı Tipi ile font boyutlarını ayarlayabilirsiniz.</p>
        """
        self.browser.setHtml(content)
