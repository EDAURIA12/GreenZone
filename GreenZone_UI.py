from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QTextEdit
from qgis.utils import iface
import requests
import math

class GreenZoneDialog(QDialog):
    def __init__(self, parent=iface.mainWindow()):
        super().__init__(parent)
        self.setWindowTitle("🌱 GreenZone AI - DSS Interattivo")
        self.resize(350, 400)
        self.setModal(False)
        
        layout = QVBoxLayout()

        self.lbl_area = QLabel("Importanza Area (0.0 - 1.0):")
        self.spin_area = QDoubleSpinBox()
        self.spin_area.setRange(0.0, 1.0)
        self.spin_area.setSingleStep(0.1)
        self.spin_area.setValue(0.6)

        self.lbl_comp = QLabel("Importanza Compattezza (0.0 - 1.0):")
        self.spin_comp = QDoubleSpinBox()
        self.spin_comp.setRange(0.0, 1.0)
        self.spin_comp.setSingleStep(0.1)
        self.spin_comp.setValue(0.4)

        self.btn_calc = QPushButton("🧠 Interroga Modello AI")
        self.btn_calc.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_calc.clicked.connect(self.esegui_chiamata_api)

        self.lbl_log = QLabel("Risultati dell'Analisi:")
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #f4f4f4; color: #333; font-family: monospace;")

        layout.addWidget(self.lbl_area)
        layout.addWidget(self.spin_area)
        layout.addWidget(self.lbl_comp)
        layout.addWidget(self.spin_comp)
        layout.addWidget(self.btn_calc)
        layout.addWidget(self.lbl_log)
        layout.addWidget(self.txt_log)
        self.setLayout(layout)

    def esegui_chiamata_api(self):
        layer = iface.activeLayer()
        selezionati = layer.selectedFeatures()
        
        if not selezionati:
            self.txt_log.append("⚠️ Attenzione: Seleziona almeno un lotto sulla mappa!")
            return
        
        self.txt_log.clear()
        self.txt_log.append(f"🔍 Avvio analisi per {len(selezionati)} lotti...")
        
        for feat in selezionati:
            area = feat['Area_mq']
            perimetro = feat['perimeter']
            fid = feat.id()
            
            if perimetro > 0:
                compattezza = (4 * math.pi * area) / (perimetro ** 2)
                
                payload = {
                    "area_mq": area,
                    "compattezza": compattezza,
                    "peso_area": self.spin_area.value(),
                    "peso_compattezza": self.spin_comp.value()
                }
                
                try:
                    risposta = requests.post("http://127.0.0.1:8000/valuta_lotto_simulazione", json=payload)
                    score = risposta.json().get("suitability_score_calcolato", 0)
                    
                    self.txt_log.append(f"✅ Lotto ID {fid}: Score ⭐ {score}/100")
                
                except Exception:
                    self.txt_log.append("🚨 Errore: Il server FastAPI è spento!")
                    break 

        self.txt_log.append("----------------------------")

if not hasattr(iface, 'greenzone_ui'):
    iface.greenzone_ui = None

if iface.greenzone_ui is not None:
    iface.greenzone_ui.close()

iface.greenzone_ui = GreenZoneDialog()
iface.greenzone_ui.show()