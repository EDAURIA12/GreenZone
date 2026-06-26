from fastapi import FastAPI
from pydantic import BaseModel

# Inizializziamo l'applicazione FastAPI

app= FastAPI(
    title="GreenZone AI - DSS API",
    description="Motore di Inferenza per il calcolo dell'idoneità dei lotti urbani a Salerno",
    version="1.0.0"
)

# Definiamo lo schema dei dati in ingresso (Data Validation con Pydantic)
# Diciamo all'API che ci aspettiamo un JSON con un'area e una compattezza in numeri decimali

class LottoInput(BaseModel):
    area_mq : float
    compattezza : float

# Primo EndPoint, rotta di base per verificare che il server sia 
# effettivamente acceso (Health Check)

@app.get("/")
def home():
    return{
        "status":"online",
        "message":"Benvenuto nell'API del SDSS GreenZone. Il motore IA è pronto."
    }

# Secondo EndPoint, l'effettiva rotta predittiva e cuore del software
# Riceve i dati del lotto in POST e calcola un punteggio grezzo

@app.post("/valuta_lotto")
def valuta_lotto(dati: LottoInput):

    # Calcoliamo un punteggio indicativo basato sui pesi del progetto (60% Area, 40% Compattezza)
    # N.B. L'area viene divisa poi per 1000 per simulare vagamente una normalizzazione in questa parte
    # di prototipo
    score_stimato = ((dati.area_mq/1000)*0.6) + (dati.compattezza * 0.4)

    # Infine restituiamo il risultato al client in formato JSON

    return{
        "dati ricevuti" :{
            "area_inserita": dati.area_mq,
            "compattezza_inserita":dati.compattezza
        },
    "suitability_score_calcolato":round(score_stimato,2),
    "status" : "Elaborazione completata con successo"
    }
