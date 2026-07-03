from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QTextEdit
import requests
import math

class GreenZoneDialog(QDialog):
    # Passando iface.mainWindow() come parent, la finestra capisce che è "figlia" di QGIS
    # e resterà sempre in primo piano senza bloccare il programma!
    def __init__(self, parent=iface.mainWindow()):
        super().__init__(parent)
        self.setWindowTitle("🌱 GreenZone AI - DSS Interattivo")
        self.resize(350, 400)
        self.setModal(False) # FONDAMENTALE: Rende la finestra non bloccante!
        
        layout = QVBoxLayout()

        # --- SEZIONE PESI ---
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

        # --- BOTTONE ---
        self.btn_calc = QPushButton("🧠 Interroga Modello AI")
        self.btn_calc.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_calc.clicked.connect(self.esegui_chiamata_api)

        # --- CONSOLE DEI RISULTATI ---
        self.lbl_log = QLabel("Risultati dell'Analisi:")
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True) # L'utente non può scriverci dentro
        self.txt_log.setStyleSheet("background-color: #f4f4f4; color: #333; font-family: monospace;")

        # Assembliamo la finestra
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
        
        # Puliamo lo schermo e diciamo quanti lotti stiamo analizzando
        self.txt_log.clear()
        self.txt_log.append(f"🔍 Avvio analisi per {len(selezionati)} lotti...")
        
        # CICLO FOR: Iteriamo su TUTTI i lotti selezionati
        for feat in selezionati:
            geom = feat.geometry()
            area = geom.area()
            perimetro = geom.length()
            fid = feat.id() # Prendiamo l'ID univoco del lotto in QGIS
            
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
                    
                    # Stampiamo il risultato nel nostro mini-schermo
                    self.txt_log.append(f"✅ Lotto ID {fid}: Score ⭐ {score}/100")
                
                except Exception as e:
                    self.txt_log.append("🚨 Errore: Il server FastAPI è spento!")
                    break # Se il server è giù, fermiamo il ciclo per non intaserlo di errori

        self.txt_log.append("----------------------------")

# --- TRUCCO PER NON FARLA CHIUDERE ---
# Salviamo l'interfaccia in una variabile globale di QGIS così non scompare
if not hasattr(iface, 'greenzone_ui'):
    iface.greenzone_ui = None

# Se c'è già una finestra aperta, chiudila prima di aprirne una nuova
if iface.greenzone_ui is not None:
    iface.greenzone_ui.close()

iface.greenzone_ui = GreenZoneDialog()
iface.greenzone_ui.show() # Usiamo .show() invece di .exec_() per renderla fluttuante!