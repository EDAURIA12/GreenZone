import geopandas as gpd
from sqlalchemy import create_engine

# 1. Configura la stringa di connessione a PostGIS
DB_USER = "admin"
DB_PASS = "segreta"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "greenzone"

connection_string = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string)

print("Inizio la lettura del file GeoJSON...")
# 2. Carica il dataset validato
gdf = gpd.read_file("data/processed/dataset_parchi_salerno.geojson")
# 3. Assicurati che il sistema di riferimento (CRS) sia corretto (es. WGS84 = 4326 o Monte Mario = 3004)
# Sostituisci 4326 con l'EPSG corretto del tuo progetto se diverso
if gdf.crs is None:
    gdf.set_crs(epsg=4326, inplace=True)

print("Trasferimento dei dati in PostGIS in corso...")
# 4. Spingi i dati nel database (crea automaticamente la tabella spaziale)
gdf.to_postgis(
    name="lotti_industriali", 
    con=engine, 
    if_exists="replace", 
    index=True, 
    index_label="id_lotto"
)

print("Migrazione completata con successo! I tuoi lotti sono ora nel database.")