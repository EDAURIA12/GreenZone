from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import pandas as pd
import math
import json

# --- CONFIGURAZIONE DATABASE POSTGIS ---
DB_URL = "postgresql://admin:segreta@localhost:5432/greenzone"
engine = create_engine(DB_URL)
CONFIG_FILE = "config_modello.json"

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    AREA_MIN = config["AREA_MIN"]
    AREA_MAX = config["AREA_MAX"]

    print(f"Configurazione caricata. AREA_MAX calibrata a: {AREA_MAX} mq")
except FileNotFoundError:
    print("Arrenzione, File di configurazione non trovato. Ritorno ai valori di default (Salerno).")
    AREA_MIN = 1000.0
    AREA_MAX = 10000.0

# --- INIZIALIZZAZIONE FASTAPI ---
app = FastAPI(
    title="GreenZone AI - SDSS API",
    description="Motore di Inferenza per il calcolo dell'idoneità dei lotti urbani a Salerno. Integrato con PostGIS.",
    version="2.0.0" 
)

# --- SCHEMI PYDANTIC E COSTANTI ---
class LottoInput(BaseModel):
    area_mq: float
    compattezza: float

# --- 1. ENDPOINT: Health Check ---
@app.get("/")
def home():
    return {
        "status": "online",
        "database": "PostGIS connesso",
        "message": "Benvenuto nell'API del SDSS GreenZone. Il motore IA è pronto."
    }

# --- 2. ENDPOINT: Simulazione What-If ---
@app.post("/valuta_lotto_simulazione")
def valuta_lotto_simulazione(dati: LottoInput):
    # Normalizzazione
    area_norm = max(0.0, min((dati.area_mq - AREA_MIN) / (AREA_MAX - AREA_MIN), 1.0))
    score_stimato_0_1 = (area_norm * 0.6) + (dati.compattezza * 0.4)
    score_centesimi = round(score_stimato_0_1 * 100, 2)

    # Logging Monitoraggio
    try:
        log_query = text(f"""
            INSERT INTO prediction_logs (input_area_mq, input_compattezza, output_score, tipo_richiesta)
            VALUES ({dati.area_mq}, {dati.compattezza}, {score_centesimi}, 'Simulazione UI')
        """)
        with engine.begin() as conn:
            conn.execute(log_query)
    except Exception as e:
        print(f"Errore log simulazione: {e}")

    return {
        "dati_ricevuti": {"area_inserita": dati.area_mq, "compattezza_inserita": dati.compattezza},
        "suitability_score_calcolato": score_centesimi,
        "status": "Simulazione completata con successo"
    }

# --- 3. ENDPOINT: Interrogazione nativa spaziale ---
@app.get("/valuta_lotto_db/{id_lotto}")
def valuta_lotto_db(id_lotto: int):
    query = f"""
        SELECT id_lotto, ST_Area(geometry) as area_mq, ST_Perimeter(geometry) as perimetro_m
        FROM lotti_industriali WHERE id_lotto = {id_lotto}
    """
    
    try:
        df = pd.read_sql(query, con=engine)
        if df.empty:
            raise HTTPException(status_code=404, detail="Lotto non trovato.")
        
        lotto = df.iloc[0]
        area = lotto['area_mq']
        perimetro = lotto['perimetro_m']
        
        compattezza = (4 * math.pi * area) / (perimetro ** 2) if perimetro > 0 else 0
        area_norm = max(0.0, min((area - AREA_MIN) / (AREA_MAX - AREA_MIN), 1.0))
        score_centesimi = round(((area_norm * 0.6) + (compattezza * 0.4)) * 100, 2)
        
        # Logging Monitoraggio
        try:
            log_query = text(f"""
                INSERT INTO prediction_logs (input_area_mq, input_compattezza, output_score, tipo_richiesta)
                VALUES ({area}, {compattezza}, {score_centesimi}, 'Estrazione DB')
            """)
            with engine.begin() as conn:
                conn.execute(log_query)
        except Exception as e:
            print(f"Errore log DB: {e}")

        return {
            "id_lotto": int(lotto['id_lotto']),
            "estrazione_postgis": {
                "area_mq_reale": round(area, 2),
                "perimetro_m_reale": round(perimetro, 2),
                "compattezza_calcolata": round(compattezza, 4)
            },
            "suitability_score_calcolato": score_centesimi,
            "status": "Dati geometrici estratti e valutati da PostGIS"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")