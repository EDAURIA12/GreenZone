# GreenZone Finder : AI-Driven Spatial Decision Support System

Questo repository contiene l'implementazione di un Sistema di Supporto alle Decisioni Spaziali (SDSS) per l'individuazione di aree industriali dismesse idonee alla riconversione in parchi pubblici nella città di Salerno.

Il progetto unisce l'analisi geospaziale (GIS) con le best practice di Software Engineering for AI (MLOps).

## Obiettivi e Requisiti di Dominio
Il sistema valuta l'idoneità delle aree basandosi su rigidi vincoli spaziali e normativi (Requirements Engineering):
* **Requisiti Escludenti (Hard Constraints):**
* Pendenza del terreno (Slope) > 15% (Barriere architettoniche).
* Aree a rischio idrogeologico o distanti meno di 150 m da fiumi (Vincolo Galasso).
* Aree con superficie < 2000 mq.
* ** Requisiti Premianti (Features del Modello ML):**
* Vicinanza ad aree ad alta densità abitativa (Dati ISTAT).
* Distanza dai parchi già esistenti (Copertura Attuale).
* Esposizione solare favorevole.

## Architettura del Sistema e MLOps
L'infrastruttura segue il paradigma MLOps per garantire riproducibilità, tracciamento e deployment continuo:

1. **Data Engineering (GeoPandas:** Pipeline per l'ingerstione e il processamento di dati geografici vettoriali aperti (ISTAT, Copernicus Urban Atlas, OpenStreetMap).
2. **Data & Model Versioning (DVC):** Controllo di versione per i dataset spaziali e per i modelli binari, mantenendo il repository Github Leggero.
3. **Experiment Tracking (MLflow):** Tracciamento degli iperparametri, metriche di valutazione e salvataggio dei modelli di Machine Learning durante l'addestramento.
4. **Rxplainable AI (XAI):** Interpretazione globale e locale per mitigare bias spaziali e giustificare l'esclusione/inclusione di specifiche aree urbane.
5. **Deployment (FastAPI):** Modello esposto come microservizio RESTful, progettato per essere interrogabile direttamente da un client GIS desktop (QGIS).

## Tecnologie Utilizzate
* **GIS:** QGIS (Modellatore Grafico, Geoprocessing)
* **Data Processing:** Python, GeoPandas, Shapely
* **Machine Learning:** Scikit-Learn / XGBoost, SHAP (per XAI)
* **MLOps:** MLflow, DVC
* **Backend:** FastAPI, Uvicorn

## Setup dell'ambiente Locale
