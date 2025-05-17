from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTextEdit, 
                            QPushButton, QHBoxLayout, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QTextCursor
import traceback

class ErrorDialog(QDialog):
    def __init__(self, title, user_message, technical_details="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(":/icons/error.png"))
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        
        # Kullanıcı dostu mesaj
        user_msg = QLabel(user_message)
        user_msg.setWordWrap(True)
        user_msg.setStyleSheet("font-size: 14px; color: #d32f2f;")
        
        # Teknik detaylar
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlainText(technical_details)
        self.details_text.setVisible(False)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        self.details_btn = QPushButton("Teknik Detaylar")
        self.details_btn.setCheckable(True)
        self.details_btn.clicked.connect(self.toggle_details)
        
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.details_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addWidget(user_msg)
        layout.addWidget(self.details_text)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def toggle_details(self):
        self.details_text.setVisible(not self.details_text.isVisible())
        self.adjustSize()
