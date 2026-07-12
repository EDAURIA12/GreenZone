from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import pandas as pd
import math
import json
import folium
import geopandas as gpd
from fastapi.responses import FileResponse
import os

# Crea la cartella per salvare le mappe dinamicamente se non esiste
os.makedirs("maps", exist_ok=True)

# --- CONFIGURAZIONE DATABASE POSTGIS ---
DB_URL = "postgresql://admin:segreta@localhost:5432/greenzone"
engine = create_engine(DB_URL)
CONFIG_FILE = "config_modello.json"

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    AREA_MIN = config.get("AREA_MIN", 1000.0)
    AREA_MAX = config.get("AREA_MAX", 10000.0)
except FileNotFoundError:
    AREA_MIN = 1000.0
    AREA_MAX = 10000.0

# --- INIZIALIZZAZIONE FASTAPI ---
app = FastAPI(
    title="GreenZone AI - SDSS API",
    description="Motore di Inferenza per il calcolo dell'idoneità dei lotti urbani. Integrato con PostGIS.",
    version="2.0.0" 
)

class LottoInput(BaseModel):
    area_mq: float
    compattezza: float
    peso_area: float = 0.6
    peso_compattezza: float = 0.4

@app.post("/valuta_lotto_simulazione")
def valuta_lotto_simulazione(lotto: LottoInput):
    area_norm = max(0.0, min((lotto.area_mq - AREA_MIN) / (AREA_MAX - AREA_MIN), 1.0))
    score = (area_norm * lotto.peso_area) + (lotto.compattezza * lotto.peso_compattezza)
    score_centesimi = round(score * 100, 2)

    return {
        "suitability_score_calcolato": score_centesimi,
        "dettagli": {
            "area_normalizzata": round(area_norm, 3),
            "compattezza": round(lotto.compattezza, 3)
        } 
    }

@app.get("/genera_mappa_top10")
def genera_mappa_top10(comune: str = "Target"):
    try:
        query = "SELECT id_lotto, geometry, ST_Area(geometry) as area_mq, ST_Perimeter(geometry) as perimetro_m FROM lotti_valutati"
        gdf = gpd.read_postgis(query, con=engine, geom_col='geometry')
        
        if gdf.empty:
            raise HTTPException(status_code=404, detail="Nessun lotto trovato nel database PostGIS.")

        gdf['compattezza'] = gdf.apply(
            lambda row: (4 * math.pi * row['area_mq']) / (row['perimetro_m']**2) if row['perimetro_m'] > 0 else 0, 
            axis=1
        )
        
        gdf['area_norm'] = gdf['area_mq'].apply(lambda x: max(0.0, min((x - AREA_MIN) / (AREA_MAX - AREA_MIN), 1.0)))
        gdf['suitability_score'] = (gdf['area_norm'] * 0.6 + gdf['compattezza'] * 0.4) * 100
        top_10_gdf = gdf.sort_values(by='suitability_score', ascending=False).head(10)
        
        if top_10_gdf.crs and top_10_gdf.crs.to_epsg() != 4326:
            top_10_gdf = top_10_gdf.to_crs(epsg=4326)
            
        centro_y = top_10_gdf.geometry.centroid.y.mean()
        centro_x = top_10_gdf.geometry.centroid.x.mean()
        mappa = folium.Map(location=[centro_y, centro_x], zoom_start=13)
        
        titolo_html = f'''
             <h3 align="center" style="font-size:20px; font-weight:bold; font-family:Arial; margin-top: 20px;">
             Top 10 Aree Riconvertibili - Comune di {comune.capitalize()}
             </h3>
             '''
        mappa.get_root().html.add_child(folium.Element(titolo_html))

        folium.GeoJson(
            top_10_gdf,
            name=f"Top 10 {comune.capitalize()}",
            tooltip=folium.GeoJsonTooltip(
                fields=['id_lotto', 'suitability_score', 'area_mq'],
                aliases=['ID Lotto:', 'Punteggio MCDA:', 'Area (mq):'],
                localize=True
            ),
            style_function=lambda feature: {
                'fillColor': '#28a745',
                'color': '#000000',
                'weight': 2,
                'fillOpacity': 0.7
            }
        ).add_to(mappa)
        
        comune_clean = comune.lower().replace(" ", "_")
        output_file = f"maps/top10_map_{comune_clean}.html"
        mappa.save(output_file)
        
        return {"status": "success", "message": f"Mappa generata per {comune}", "file_url": f"/download_mappa?comune={comune_clean}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")

@app.get("/download_mappa")
def download_mappa(comune: str = "target"):
    comune_clean = comune.lower().replace(" ", "_")
    file_path = f"maps/top10_map_{comune_clean}.html"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='text/html', filename=f"top10_map_{comune_clean}.html")
    raise HTTPException(status_code=404, detail="Mappa non trovata.")

@app.get("/valuta_lotto/{id_lotto}")
def valuta_lotto_db(id_lotto: int):
    # ATTENZIONE: Anche qui usiamo la stessa tabella
    query = text(f"SELECT id_lotto, ST_Area(geometry) as area_mq, ST_Perimeter(geometry) as perimetro_m FROM lotti_industriali WHERE id_lotto = {id_lotto}")
    with engine.connect() as conn:
        df = pd.read_sql(query, con=conn)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="Lotto non trovato in PostGIS.")
        
    lotto = df.iloc[0]
    area = lotto['area_mq']
    perimetro = lotto['perimetro_m']
    
    compattezza = (4 * math.pi * area) / (perimetro ** 2) if perimetro > 0 else 0
    area_norm = max(0.0, min((area - AREA_MIN) / (AREA_MAX - AREA_MIN), 1.0))
    score_centesimi = round(((area_norm * 0.6) + (compattezza * 0.4)) * 100, 2)
    
    return {
        "id_lotto": int(lotto['id_lotto']),
        "estrazione_postgis": {
            "area_mq_reale": round(area, 2),
            "perimetro_m_reale": round(perimetro, 2)
        },
        "suitability_score": score_centesimi
    }