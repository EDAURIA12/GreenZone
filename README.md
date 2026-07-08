# 🌿 GreenZone Finder: AI-Driven Spatial Decision Support System

Questo repository contiene l'implementazione di un **Sistema di Supporto alle Decisioni Spaziali (SDSS)** per l'individuazione di aree industriali dismesse idonee alla riconversione in parchi pubblici. Nato sul caso studio della città di Salerno, il sistema è progettato per essere scalabile e applicabile dinamicamente a qualsiasi altro contesto urbano.

Il progetto unisce l'analisi geospaziale (**GIS**) con tecniche di **Intelligenza Artificiale**, seguendo le migliori pratiche di *Software Engineering* e *MLOps*.

---
## 🎯 Obiettivi e Requisiti di Dominio

Il sistema valuta l'idoneità delle aree basandosi su una serie di vincoli normativi, morfologici e urbani suddivisi in due macro-categorie:

### 1. Requisiti Escludenti (Hard Constraints) — *GeoProcessing*
Vengono applicati filtri geometrici rigidi per escludere a priori le aree non idonee tramite QGIS:
* **Pendenza del terreno:** Esclusione delle aree non pianeggianti (basato su Modello Digitale del Terreno - DTM).
* **Vincolo Idrogeologico (Legge Galasso):** Buffer di esclusione di 150 metri dal reticolo idrografico.
* **Vincolo di Sicurezza:** Buffer di esclusione di 30 metri dalla rete ferroviaria.
* **Dimensione del lotto:** Esclusione di aree con superficie inferiore a 1000 metri quadri (vengono scartati i *pocket parks*, non rilevanti per grandi interventi di riqualificazione).

### 2. Requisiti Premianti (Features del Modello AI)
Fattori competitivi ed elementi di merito estratti per addestrare il modello predittivo:
* **Indice di Compattezza (Polsby-Popper):** Penalizza le aree lunghe e strette (es. vecchi corridoi stradali o ferroviari) a favore di geometrie circolari o quadrate, morfologicamente ottimali per un parco.
* **Densità Abitativa:** Vicinanza ad aree ad alta densità di popolazione (basato su dati censuari ISTAT).
* **Distanza dai parchi esistenti:** Massimizzazione della copertura del verde urbano, premiando aree distanti da infrastrutture verdi già presenti per colmare i gap di servizio.

---
## 🗺️ Metodologia e Workflow GeoSpaziale (QGIS)

La prima fase del progetto ha riguardato l'estrazione, la pulizia e la strutturazione dei dati vettoriali tramite il **Modellatore Grafico di QGIS**:

1.  **Intersezione Morfologica:** Il layer *Copernicus Urban Atlas* è stato ritagliato sulle sole aree pianeggianti target idonee.
2.  **Sottrazione a Cascata (*Difference*):** Sono stati sottratti geometricamente i buffer fluviali, ferroviari e le aree dei parchi esistenti.
3.  **Selezione Tematica e Feature Engineering Spaziale:** Sono stati isolati i lotti con codici Copernicus `12100` (Aree Industriali) e `13400` (Aree Dismesse). Successivamente, tramite il calcolatore di campi, sono state estratte le coordinate del baricentro (`Centroid X/Y`) e calcolati l'area reale e il perimetro per la successiva pipeline in Python.

> 📦 **Output di Fase:** Il risultato di questa pipeline geospaziale è un dataset validato, ripulito e consolidato (es. `dataset_comune_target.geojson`).

---
## 🧠 Architettura del Sistema MLOps & Analisi Dati

L'intera infrastruttura segue rigorosamente il paradigma MLOps per garantire riproducibilità, tracciamento degli esperimenti e deployment continuo.

### 1. Data Engineering (GeoPandas) & Sanity Check
Ingestione del GeoJSON esportato da QGIS. Viene calcolato l'Indice di Compattezza per eliminare automaticamente i falsi positivi (artefatti geometrici residui da geoprocessing), garantendo che la macchina valuti solo lotti urbanisticamente validi.

| ID Lotto | Tipo Geometria | Score Compattezza | Stato |
| :--- | :--- | :---: | :--- |
| **5841** | Forma Compatta / Quadrata | `0.67` | **Mantenuta (Idonea)** |
| **5821** | Forma Allungata / Corridoio Irregolare | `0.25` | **Scartata (Artefatto)** |

### 2. Machine Learning: Motore Ibrido (MCDA + K-Means)
Per classificare l'idoneità delle aree rimanenti, viene applicato un approccio che unisce logica di dominio e Machine Learning non supervisionato:
* **Scoring MCDA (Multi-Criteria Decision Analysis):** Calcolo di un *Suitability Score* normalizzato tramite un sistema di pesi personalizzabile (es. bilanciamento tra l'estensione dell'Area e la Compattezza).
* **Clustering K-Means (Scikit-Learn):** Raggruppamento algoritmico dei lotti in 3 cluster naturali di priorità (**Alta**, **Media**, **Bassa**). Questo approccio rimuove i bias decisionali umani e permette l'estrazione oggettiva della *Top 10* assoluta.

### 3. MLOps (Tracciabilità con MLflow)
Per garantire il rigore scientifico del modello e la totale riproducibilità di ogni esecuzione:
* **MLflow Tracking:** Implementato nella fase di training per la storicizzazione degli esperimenti, la registrazione degli iperparametri (es. `K=3`, soglie di scarto calcolate sui percentili) e il monitoraggio delle metriche di performance (inerzia).

### 4. Continuous Training (CT) e Pipeline CI/CD (GitHub Actions)
Il progetto implementa una pipeline automatizzata per garantire la scalabilità immediata ad altri comuni. Applicando il principio **KISS** (*Keep It Simple, Stupid*), per i dataset vettoriali di output (< 100 MB) si è optato per il tracciamento nativo tramite Git.

Al caricamento (*push*) di un nuovo file `dataset_comune_target.geojson`, **GitHub Actions** innesca automaticamente:
1.  L'esecuzione di `train.py` per l'armonizzazione spaziale (conversione unificata nel sistema di riferimento `EPSG:3035`).
2.  Il ricalcolo dei centroidi K-Means e l'aggiornamento dinamico delle soglie (es. l'area massima ideale `AREA_MAX` viene calcolata sul 95° percentile dei nuovi lotti).
3.  L'esportazione del nuovo "cervello" del modello aggiornato nel file `config_modello.json`.

### 5. Database Spaziale (PostGIS su Docker)
Il sistema supera l'utilizzo di file statici implementando un database georeferenziato. Lo script `migrate_to_postgis.py` inserisce i dati elaborati in un container **PostGIS**, abilitando:
* Lettura e interrogazione nativa e spaziale dei dati direttamente da QGIS (architettura Client-Server).
* Storicizzazione e logging delle predizioni effettuate dall'API nella tabella `prediction_logs`, essenziale per futuri riaddestramenti del modello o audit di performance.

### 6. Visualizzazione WEBGIS (Folium)
Riproiezione dei dati spaziali e creazione di una mappa interattiva HTML per consentire la fruizione dei risultati statici da parte dei decisori territoriali:
* **Panoramica globale:** Visualizzazione di tutti i lotti classificati per colore in base al cluster di appartenenza.
* **Dettaglio Top 10:** Evidenziazione dei lotti migliori arricchiti da pop-up informativi interattivi con metriche in tempo reale.

### 7. Explainable AI (XAI)
Per rispettare i principi di tracciabilità e trasparenza, il modello fornisce un output visivo che spiega la logica di classificazione dei cluster, evitando l'effetto *Black Box*. Uno *Scatter Plot* evidenzia come la distribuzione asimmetrica positiva (*Right-Skewed*) dei dati permetta all'algoritmo di premiare i rarissimi lotti che presentano sia estensione che compattezza ottimali.

### 8. Deployment Dinamico e Backend (FastAPI)
L'intero motore logico è pacchettizzato ed esposto come microservizio RESTful (`main.py`) collegato direttamente a PostGIS tramite SQLAlchemy. L'API è agnostica rispetto alla geografia e legge dinamicamente le configurazioni generate dalla pipeline CI/CD.
* **What-If Analysis:** L'endpoint accetta in ingresso parametri metrici e pesi decisionali dinamici inviati dall'utente (es. importanza relativa tra Area e Compattezza), permettendo di valutare l'impatto dei criteri di pianificazione in tempo reale.

### 9. Client QGIS (Interfaccia Utente PyQt)
Sviluppo del modulo client `GreenZone_UI.py` eseguibile nativamente all'interno di QGIS. Genera una GUI fluttuante e non bloccante che consente al pianificatore di:
* Selezionare lotti multipli direttamente sulla mappa vettoriale collegata al database.
* Modificare in tempo reale i pesi multicriterio eseguendo simulazioni istantanee.
* Interrogare l'API locale e ricevere istantaneamente lo *Suitability Score* calcolato dall'IA per ciascun lotto.

---
## 🚀 Scalabilità Dimostrata: Il caso "Battipaglia"

Per validare l'architettura dinamica del progetto, il sistema è stato testato con successo sul comune di **Battipaglia** (Piana del Sele).
A differenza di Salerno, caratterizzata da vincoli orografici stringenti e lotti di dimensioni ridotte, Battipaglia presenta una morfologia totalmente pianeggiante e aree industriali estremamente vaste.

Senza scrivere una singola riga di codice aggiuntiva, l'immissione del nuovo dataset grezzo nel repository ha innescato la pipeline CI/CD che ha:
* **Adattato dinamicamente la soglia** `AREA_MAX` ai nuovi standard della città (passando da ~73.000 m² di Salerno a ~244.000 m² di Battipaglia).
* **Ricalibrato i centroidi** dei cluster K-Means in base alle nuove proporzioni dei dati.
* Permesso a QGIS di interrogare il database restituendo *Suitability Score* perfetti, coerenti e calibrati sul nuovo contesto geografico.

---

## 💻 Tecnologie Utilizzate

| Ambito | Strumenti / Librerie |
| :--- | :--- |
| **GIS & UI** | QGIS, PyQGIS, PyQt5, Folium |
| **Data Processing** | Python, GeoPandas, Shapely |
| **Machine Learning & MLOps** | Scikit-Learn, MLflow, GitHub Actions |
| **Backend & Database** | FastAPI, Uvicorn, Pydantic, PostgreSQL + PostGIS, SQLAlchemy, Docker |

---
## ⚙️ Setup e Utilizzo dell'Ambiente

Per riprodurre il progetto in locale e interrogarlo tramite QGIS, seguire questi passaggi:

### 1. Prerequisiti
* Python 3.10 o superiore
* Docker Desktop in esecuzione
* QGIS 3.x installato

### 2. Setup dell'Ambiente Locale
Clonare il repository e configurare l'ambiente virtuale:

```bash
git clone [https://github.com/EDAURIA12/GreenZone.git](https://github.com/EDAURIA12/GreenZone.git)
cd GreenZone
python -m venv .venv
```
# Attivazione dell'ambiente virtuale:
```bash
# Windows:
.venv\Scripts\activate
# MacOS/Linux:
source .venv/bin/activate
```

# Installazione delle dipendenze
```bash
pip install -r requirements.txt
```

### 3. Inizializzazione del Database e Migrazione Dati
Avviare un container PostGIS locale e popolare le tabelle spaziali con i dati del comune target:

```bash
#Avvio rapido di PostGIS via Docker
docker run --name greenzone_postgis -e POSTGRES_PASSWORD=segreta -e POSTGRES_USER=admin -e POSTGRES_DB=greenzone -p 5432:5432 -d postgis/postgis
```

```bash
#Migrazione del GeoJson processato nel database
python migrate_to_postgis.py
```
### 4. Avvio del Microservizio (Backend AI)
Avviare il server FastAPI per metter in ascolto il motore di inferenza:

```bash
uvicorn main:app --reload
```

### 5. Utilizzo dell'interfaccia in QGIS (Frontend)

Aprire QGIS.
Connettersi al database PostGIS locale (Host:localhost, porta: 5432, DB: greenzone, User: admin, Pass: segreta).
Dal pannello Browser, trascinare il layer lotti_industriali (situato nello schema public) nel pannello Layer.
Aprire la Console di Python in QGIS (Plugin->Console Python).
Incollare il contenuto dello script GreenZone_UI.py e premere Play.

Simulazione: Selezionare uno o più lotti sulla mappa di QGIS, regolare i pesi di inferenza sulla UI fluttuante e cliccare su Interroga Modello AI.

## Come Testare un nuovo Comune (Continuous Training)
Per applicare l'IA ad un nuovo comune:

Esportare da QGIS i lotti candidati (dopo il GeoProcessing) rinominando il file in dataset_comune_target.geojson.
Sostituire il file nella cartella data/raw/ e fare git add, git commit e git push.
Attendere il completamento della GitHub Action, che eseguirà il retraining dell'IA sui nuovi dati.
Eseguire il git pull in locale per ottenere il nuovo config_modello.json.
Rieseguire
```bash
python migrate_to_postgis.py
```
Così da aggiornare il database locale con i nuovi lotti