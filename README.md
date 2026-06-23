# GreenZone Finder : AI-Driven Spatial Decision Support System

Questo repository contiene l'implementazione di un Sistema di Supporto alle Decisioni Spaziali (SDSS) per l'individuazione di aree industriali dismesse idonee alla riconversione in parchi pubblici nella città di Salerno.

Il progetto unisce l'analisi geospaziale (GIS) con tecniche di Intelligenza Artificiale, seguendo le *best practice* di Software Engineering.

## Obiettivi e Requisiti di Dominio
Il sistema valuta l'idoneità delle aree basandosi su una serie di vincoli normativi, morfologici e urbani.

**1. Requisiti Escludenti (Hard Constraints) - Implementati via GeoProcessing:**
* Pendenza del terreno: Esclusione delle aree non pianeggianti (basato su DTM).
* Vincolo Idrogeologico (Legge Galasso): Buffer di esclusione di 150 meri dal reticolo idrografico.
* Vincolo di Sicurezza: Buffer di esclusione di 30 metri della rete ferroviaria.
* Dimensione del lotto: Esclusione di aree con superficie minore di 1000 metri quadri (scartati i *pocket parks* non rilevanti per grandi riqualificiazioni).

**2. Requisiti Premianti (Features del Modello AI):**
* **Indice di Compattezza (Polsby-Popper):** Per penalizzare aree lunghe e strette (es. vecchi corridoi stradali) a favore di geometri circolari/quadrate ottimali per un parco. 
* Vicinanza ad aree ad alta densità abitativa (Dati ISTAT).
* Distanza dai parchi già esistenti (per massimizzare la copertura del verde urbano).

**Metodologia e Workflow GeoSpaziale (QGIS)**
La prima fase del progetto ha riguardato l'estrazione e la pulizia dei dati vettoriali tramite il **MOdellatore Grafico di QGIS**.

1. **Intersezione Morfologica:** Il layer Copernicus Urban Atlas è stato ritgliato sulle sole aree pianeggianti di Salerno.
2. **Sottrazine a Cascata (Difference):** Sono stati sottratti geometricamente i buffer fluviali, ferroviari e i parchi esistenti.
3. **Selezione Tematica e Feature Engineering Spaziale:** Sono stati isolati i codici Copernicus *12100* (Aree Industriali) e *13400* (Aree Dismesse). Successivamente, tramite calcolatore di campi, sono state estratte le coordinate del baricanetro (Centroid X/Y) e calcolati Area reale e Perimetro per la successiva analisi in Python.

Il risultato di questa pipeline è il dataset validato e consolidato: 'dataset_parchi_salerno.geojson'.

## Architettura del Sistema MLOps & Analisi Dati (In progress)
L'infrastruttura segue il paradigma MLOps per garantire riproducibilità, tracciamento e deployment continuo:

1. **Data Engineering GeoPandas:** Ingestione del GeoJSON esportato da QGIS.
2. **Machine Learning:** Algoritmi (Clustering/Scoring) per classificare l'idoneità delle 317 aree candidate individuate.
3. **Explainable AI (XAI):** Interpretazione dei risultati spaziali per giustificare l'esclusione o l'alta classificazione di specifiche aree urbane.
4. **Visualizzazione:** Creazione di mappe interattive (Folium) per la fruizione dei risultati da parte dei decisori.
5. **Deployment (FastAPI):** Modello esposto come microservizio RESTful, progettato per essere interrogabile direttamente da un client GIS desktop (QGIS).

## Tecnologie Utilizzate
* **GIS:** QGIS (Modellatore Grafico, Geoprocessing)
* **Data Processing:** Python, GeoPandas, Shapely
* **Machine Learning:** Scikit-Learn / XGBoost, SHAP (per XAI)
* **MLOps:** MLflow, DVC
* **Backend:** FastAPI, Uvicorn

## Setup dell'ambiente Locale
