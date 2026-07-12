from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QTextEdit, QLineEdit
from qgis.utils import iface
import requests
import math
import webbrowser
import os

class GreenZoneDialog(QDialog):
    def __init__(self, parent=iface.mainWindow()):
        super().__init__(parent)
        self.setWindowTitle("🌱 GreenZone AI - DSS Interattivo")
        self.resize(350, 500)
        self.setModal(False)
        
        layout = QVBoxLayout()

        self.lbl_comune = QLabel("📍 Città Target (Es. Salerno, Battipaglia):")
        self.txt_comune = QLineEdit("Target")
        self.txt_comune.setStyleSheet("padding: 5px; font-size: 14px;")

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

        self.btn_calc = QPushButton("🧠 Valuta Lotti Selezionati")
        self.btn_calc.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_calc.clicked.connect(self.esegui_chiamata_api)

        self.btn_map = QPushButton("🗺️ Genera Mappa Top 10 Globale")
        self.btn_map.setStyleSheet("background-color: #008CBA; color: white; font-weight: bold; padding: 10px;")
        self.btn_map.clicked.connect(self.genera_mappa)

        self.lbl_log = QLabel("Risultati dell'Analisi:")
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #f4f4f4; color: #333; font-family: monospace;")

        layout.addWidget(self.lbl_comune)
        layout.addWidget(self.txt_comune)
        layout.addWidget(self.lbl_area)
        layout.addWidget(self.spin_area)
        layout.addWidget(self.lbl_comp)
        layout.addWidget(self.spin_comp)
        layout.addWidget(self.btn_calc)
        layout.addWidget(self.btn_map)
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
            try:
                # Estrazione DINAMICA dell'Area (Cerca varianti del nome)
                area = None
                for col_name in ['Area_mq', 'area_mq', 'Area', 'area']:
                    try:
                        area = feat[col_name]
                        break
                    except KeyError: pass
                
                # Estrazione DINAMICA del Perimetro (Cerca varianti del nome)
                perimetro = None
                for col_name in ['Perim_m', 'perim_m', 'perimeter', 'Perimeter']:
                    try:
                        perimetro = feat[col_name]
                        break
                    except KeyError: pass

                if area is None or perimetro is None:
                    self.txt_log.append(f"🚨 Errore: Colonne Area o Perimetro mancanti nel lotto {feat.id()}!")
                    break
                
                fid = feat.id()
                
                if perimetro > 0:
                    compattezza = (4 * math.pi * area) / (perimetro ** 2)
                    
                    payload = {
                        "area_mq": area,
                        "compattezza": compattezza,
                        "peso_area": self.spin_area.value(),
                        "peso_compattezza": self.spin_comp.value()
                    }
                    
                    risposta = requests.post("http://127.0.0.1:8000/valuta_lotto_simulazione", json=payload)
                    risposta.raise_for_status() 
                    
                    score = risposta.json().get("suitability_score_calcolato", 0)
                    self.txt_log.append(f"✅ Lotto ID {fid}: Score ⭐ {score}/100")
            
            except requests.exceptions.RequestException:
                self.txt_log.append("🚨 Errore: Il server FastAPI è spento!")
                break 
            except Exception as e:
                self.txt_log.append(f"🚨 Errore: {str(e)}")
                break

        self.txt_log.append("----------------------------")

    def genera_mappa(self):
        comune_input = self.txt_comune.text().strip()
        if not comune_input:
            comune_input = "Target"
            
        self.txt_log.append(f"🗺️ Richiesta mappa per: {comune_input.capitalize()}...")
        
        try:
            url_chiamata = f"http://127.0.0.1:8000/genera_mappa_top10?comune={comune_input}"
            risposta = requests.get(url_chiamata)
            
            if risposta.status_code == 200:
                comune_formattato = comune_input.lower().replace(" ", "_")
                self.txt_log.append(f"✅ Mappa salvata in maps/top10_map_{comune_formattato}.html")
                webbrowser.open(f"http://127.0.0.1:8000/download_mappa?comune={comune_formattato}")
            else:
                self.txt_log.append(f"⚠️ Errore dal server: {risposta.text}")
                
        except requests.exceptions.RequestException:
            self.txt_log.append("🚨 Errore di connessione: Il server FastAPI è spento.")

if not hasattr(iface, 'greenzone_ui'):
    iface.greenzone_ui = None

if iface.greenzone_ui is not None:
    iface.greenzone_ui.close()

iface.greenzone_ui = GreenZoneDialog()
iface.greenzone_ui.show()