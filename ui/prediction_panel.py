from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QPushButton, QLineEdit
from PyQt5.QtCore import Qt
from ml.predictive_maintenance import PredictiveMaintenance

class PredictionPanel(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.pm = PredictiveMaintenance()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Form alanları
        form = QFormLayout()
        
        self.age_input = QLineEdit()
        self.usage_input = QLineEdit()
        self.maintenance_count_input = QLineEdit()
        
        form.addRow("Ekipman Yaşı (gün):", self.age_input)
        form.addRow("Kullanım Saati:", self.usage_input)
        form.addRow("Bakım Sayısı:", self.maintenance_count_input)
        
        # Sonuç etiketi
        self.result_label = QLabel("Sonuç bekleniyor...")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size: 16px;")
        
        # Tahmin butonu
        predict_btn = QPushButton("Tahmin Yap")
        predict_btn.clicked.connect(self.predict)
        
        layout.addLayout(form)
        layout.addWidget(predict_btn)
        layout.addWidget(self.result_label)
        self.setLayout(layout)
    
    def predict(self):
        try:
            equipment_data = {
                'equipment_age': float(self.age_input.text()),
                'kullanım_saati': float(self.usage_input.text()),
                'bakim_sayisi': int(self.maintenance_count_input.text())
            }
            
            result = self.pm.predict(equipment_data)
            
            # Sonucu renk kodlu göster
            if result['oneri'] == 'ACIL_BAKIM':
                color = "red"
            else:
                color = "green"
                
            self.result_label.setText(
                f"<span style='color:{color};'>"
                f"Arıza Olasılığı: %{result['ariza_olasiligi']*100:.2f}<br>"
                f"Öneri: {result['oneri']}"
                f"</span>"
            )
        except Exception as e:
            self.result_label.setText(f"<span style='color:red;'>Hata: {str(e)}</span>")
            logging.error(f"Tahmin hatası: {e}")
