import geopandas as gpd
from sqlalchemy import create_engine, text

# 1. Configurazione
DB_USER = "admin"
DB_PASS = "segreta"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "greenzone"

connection_string = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string)

# 2. Leggi il file GeoJSON
print("Inizio la lettura del file GeoJSON...")
gdf = gpd.read_file("data/raw/dataset_comune_target.geojson")

# 3. Pulizia totale dello schema 'public'
with engine.connect() as conn:
    print("Pulizia totale dello schema 'public'...")
    conn.execute(text("DROP SCHEMA public CASCADE;"))
    conn.execute(text("CREATE SCHEMA public;"))
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
    conn.commit()

# 4. Preparazione dati
# Se 'id_lotto' è nel file, rimuoviamolo dal contenuto per evitare conflitti con l'indice
if 'id_lotto' in gdf.columns:
    gdf = gdf.drop(columns=['id_lotto'])

# Rilevamento CRS
minx, miny, maxx, maxy = gdf.total_bounds
if minx > -180 and maxx < 180 and miny > -90 and maxy < 90:
    print("🗺️ Coordinate WGS84 rilevate. Converto in EPSG:3035...")
    gdf.set_crs(epsg=4326, allow_override=True, inplace=True)
    gdf = gdf.to_crs(epsg=3035)
else:
    print("📏 Coordinate in METRI rilevate.")
    gdf.set_crs(epsg=3035, allow_override=True, inplace=True)

# 5. Trasferimento nel DB
print("Trasferimento 'lotti_valutati' in corso...")
gdf.to_postgis(
    name="lotti_valutati", 
    con=engine, 
    if_exists="replace", 
    index=True, 
    index_label="id_lotto" 
)

print("✅ Trasferimento completato correttamente!")