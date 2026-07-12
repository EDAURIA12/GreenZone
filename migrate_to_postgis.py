import geopandas as gpd
from sqlalchemy import create_engine

# 1. Configurazione Database
DB_USER = "admin"
DB_PASS = "segreta"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "greenzone"

connection_string = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string)

print("Inizio la lettura del file GeoJSON...")
gdf = gpd.read_file("data/raw/dataset_comune_target.geojson")

# 2. RILEVAMENTO INTELLIGENTE DEL CRS (A prova di esportazione QGIS)
minx, miny, maxx, maxy = gdf.total_bounds

# Se le coordinate sono piccole (es. 14, 40) sono GRADI.
if minx > -180 and maxx < 180 and miny > -90 and maxy < 90:
    print("🗺️ Coordinate in GRADI rilevate. Imposto WGS84 e converto in Metri (EPSG:3035)...")
    gdf.set_crs(epsg=4326, allow_override=True, inplace=True)
    gdf = gdf.to_crs(epsg=3035)
else:
    # Se le coordinate sono grandi (es. 4744189) sono GIÀ IN METRI.
    print("📏 Coordinate in METRI rilevate. Assegno direttamente EPSG:3035 senza riconvertire.")
    gdf.set_crs(epsg=3035, allow_override=True, inplace=True)

# 3. Pulizia id_lotto residui
if 'id_lotto' in gdf.columns:
    gdf = gdf.drop(columns=['id_lotto'])

print("Trasferimento in PostGIS in corso...")
# 4. Spinta nel DB
gdf.to_postgis(
    name="lotti_industriali", 
    con=engine, 
    if_exists="replace", 
    index=True, 
    index_label="id_lotto"
)

print("✅ Trasferimento completato con successo! I dati sono pronti e metricamente perfetti.")