import os
from pathlib import Path

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Conexión a MongoDB.
# Local:  mongodb://localhost:27017
# AWS:    mongodb://usuario:clave@IP_PRIVADA:27017/?authSource=cocatrace
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.environ.get("MONGO_DB", "cocatrace")
MONGO_COLECCION = os.environ.get("MONGO_COLECCION", "mediciones")

# Archivo CSV de respaldo
CSV_FILE = Path(os.environ.get("CSV_FILE", BASE_DIR / "data" / "mediciones.csv"))

# Zona horaria para mostrar las fechas en el dashboard
ZONA_HORARIA = os.environ.get("ZONA_HORARIA", "America/Bogota")

# Rangos físicos válidos del DHT22
TEMP_MIN, TEMP_MAX = -40.0, 80.0
HUM_MIN, HUM_MAX = 0.0, 100.0
