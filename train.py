import geopandas as gpd
import pandas as pd
import numpy as np
import math
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import json
import os
import glob
import matplotlib.pyplot as plt

# 1. Trova dinamicamente l'ultimo file GeoJSON
print("Ricerca del dataset vettoriale in corso...")
lista_file = glob.glob("data/raw/*.geojson")

if not lista_file:
    raise FileNotFoundError("🚨 Errore: Nessun file GeoJSON trovato nella cartella data/raw/")

file_target = max(lista_file, key=os.path.getmtime)
print(f"📂 File rilevato per l'addestramento: {file_target}")

# 2. Caricamento Dati
gdf = gpd.read_file(file_target)

# Pulizia e calcolo deterministico (Rebranding K-Means: Spatial Clustering basato su MCDA)
def calcola_compattezza(area, perimetro):
    if perimetro <= 0 or pd.isna(perimetro):
        return 0
    return (4 * math.pi * area) / (perimetro ** 2)

# Ricerca dinamica nomi colonne (per robustezza)
col_area = next((c for c in gdf.columns if c.lower() in ['area_mq', 'area']), None)
col_perim = next((c for c in gdf.columns if c.lower() in ['perim_m', 'perimeter']), None)

if col_area is None or col_perim is None:
    raise ValueError("Le colonne Area o Perimetro non sono state trovate nel file!")

gdf['compattezza'] = gdf.apply(lambda row: calcola_compattezza(row[col_area], row[col_perim]), axis=1)

# Estrazione limiti per normalizzazione e configurazione modello
area_min = float(gdf[col_area].min())
area_max = float(gdf[col_area].max())

# Filtro sliver polygons (bonifica topologica automatizzata)
gdf_valido = gdf[gdf['compattezza'] > 0.05].copy() 

# Prepariamo le due feature per lo spatial clustering
X = gdf_valido[[col_area, 'compattezza']].copy()

# Standardizzazione (indispensabile per il K-Means)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Addestramento K-Means (3 centroidi: Alta, Media, Bassa priorità)
print("Addestramento Spatial Clustering (K-Means) in corso...")
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
kmeans.fit(X_scaled)

# Assegnazione etichette
gdf_valido['cluster'] = kmeans.labels_

# Salvataggio Modello e Scaler
os.makedirs("models", exist_ok=True)
joblib.dump(kmeans, "models/kmeans_model.pkl")
joblib.dump(scaler, "models/scaler.pkl")

# Salvataggio file di configurazione con i limiti areali della città corrente
config = {
    "AREA_MIN": area_min,
    "AREA_MAX": area_max,
    "COMUNE_TARGET": os.path.basename(file_target)
}
with open("config_modello.json", "w") as f:
    json.dump(config, f)

print(f"✅ Addestramento completato. Limiti Areali salvati: {area_min} - {area_max}")

# Generazione Scatter Plot ESDA per il README
plt.figure(figsize=(10, 6))
scatter = plt.scatter(gdf_valido[col_area], gdf_valido['compattezza'], c=gdf_valido['cluster'], cmap='viridis', s=50, alpha=0.7)
plt.title("Analisi Esplorativa Spaziale (ESDA): Distribuzione Lotti per Cluster", fontsize=14)
plt.xlabel("Estensione (Area mq)", fontsize=12)
plt.ylabel("Indice di Compattezza", fontsize=12)
plt.colorbar(scatter, label='Cluster K-Means')
plt.grid(True, linestyle='--', alpha=0.6)

# Salva il plot
plt.tight_layout()
plt.savefig("scatter_plot_esda.png")
print("✅ Grafico ESDA salvato (scatter_plot_esda.png) per il README.")