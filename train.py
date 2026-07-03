import geopandas as gpd
import pandas as pd
import numpy as np
import math
import json
import mlflow
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler

# Configurazione iniziale
# Simuliamo che la pipeline di CI/CD scarichi il nuovo
# dataset in questa posizione

INPUT_FILE = "data/raw/dataset_comune_target.geojson"
CONGIF_OUTPUT_FILE = "config_modello.json"

print("Avvio MlOps Continuous Training Pipeline")
print(f"Lettuare del dataset spaziale: {INPUT_FILE}")

try:
    # Andiamo a caricare i dati
    gdf = gpd.read_file(INPUT_FILE)
except Exception as e:
    print(f"Errore: File non trovato, verifica che la CI/CD abbia scaricato il dato. Dettaglio di seguito: {e}")
    exit(1)


# GIS Engineering: Armonizzazione Spaziale

# Vi sono più fusi UTM per l'Italia
# per generalizzare, riproiettiamo tutto nel sistema
# ETRS89 / LAEA Europe (EPSG:3035)
# Standard europeo per preservare le proporzioni delle aree senza distorsioni.

print(f"CRS originale rilevato: {gdf.crs}")


if gdf.crs is None or gdf.crs.to_epsg() != 3035:
    print("Riproiezione forzata in EPSG:3035 in corso per garantire che i calcoli metrici siano unificati")
    gdf = gdf.to_crs(epsg=3035)

print("Armonizzazione spaziale completata")

# Ingegneria delle features e calcolo dinamico

print("Calcolo delle metriche spaziali")

# Siccome abbiamo ora tutto in EPSG:3035 possiamo calcolare
# l'area in metri quadri esatti

gdf['area_mq'] = gdf.geometry.area
gdf['perimetro_m'] = gdf.geometry.length

# Ora possiamo calcolare la compattezza di Polsby-Popper
# questo per ogni lotto gestendo la divisione per zero in caso di 
# geometrie anomale

gdf['compattezza'] = gdf.apply(
    lambda row: (4 * math.pi * row['area_mq']) / (row['perimetro_m']**2) if row['perimetro_m'] > 0 else 0,
    axis=1
)

# come area massimo andiamo a scartare il 5% della top dei lotti
# per definire "l'area ideale"
AREA_MIN = 1000.0
AREA_MAX = float(gdf['area_mq'].quantile(0.95))
print(f"Dinamica del comune: Area minima: {AREA_MIN} mq | Area Massima(95° Percentile): {round(AREA_MAX,2)} mq")

# Ora passiamo all'addestramento del modello K-Means
print("Addestramento del K-Means")
# Questo filtrando i lotti validi come da requisiti di dominio
lotti_validi = gdf[gdf['area_mq'] >= AREA_MIN].copy()
scaler = MinMaxScaler()
features = scaler.fit_transform(lotti_validi[['area_mq','compattezza']])

mlflow.set_experiment("GreenZone_CT")

with mlflow.start_run(run_name="Addestramento_Dinamico_Comune"):
    
    # Ricalcoliamo i 3 cluster
    k = 3
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(features)

    # Registrazione dei parametri
    mlflow.log_param("n_clusters",k)
    mlflow.log_param("area_min_impostata",AREA_MIN)
    mlflow.log_param("area_max_calcolata_95_perc", AREA_MAX)

    # Registriamo le Metriche (es. l'inerzia del k-means, quanto sono compatti i cluster)
    mlflow.log_metric("kmeans_inertia", kmeans.inertia_)

    # Registriamo il modello stesso e il file di configurazione come artefatto
    mlflow.sklearn.log_model(kmeans, "modello_kmeans")

    # Salvataggio file di configurazione
    print(f"Salvataggio configurazione in {CONGIF_OUTPUT_FILE}")
    config = {
        "AREA_MIN" : AREA_MIN,
        "AREA_MAX" : AREA_MAX,
        "KMEANS_CENTROIDS" : kmeans.cluster_centers_.tolist()
    }
    with open(CONGIF_OUTPUT_FILE, "w") as f:
        json.dump(config, f, indent = 4)

    mlflow.log_artifact(CONGIF_OUTPUT_FILE)

print("Addestramento completato con successo! Il modello è pronto per la fase di Deployment")

