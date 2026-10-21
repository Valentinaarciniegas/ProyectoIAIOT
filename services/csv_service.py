import csv

from config import CSV_FILE

# Encabezados del archivo csv
COLUMNAS = [
    "id_sensor",
    "lote_id",
    "etapa",
    "temperatura",
    "humedad",
    "fecha_medicion",
    "fecha_recepcion",
]


def guardar_registro(registro):
    """
    Guardar una medicion en el archivo csv.
    Las fechas se escriben en formato ISO 8601 (UTC).
    """
    # Crear la carpeta si no existe
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Determinar si es necesario escribir los encabezados
    encabezado = not CSV_FILE.exists() or CSV_FILE.stat().st_size == 0

    fila = {
        "id_sensor": registro["id_sensor"],
        "lote_id": registro["lote_id"],
        "etapa": registro["etapa"],
        "temperatura": registro["temperatura"],
        "humedad": registro["humedad"],
        "fecha_medicion": registro["fecha_medicion"].isoformat(timespec="seconds"),
        "fecha_recepcion": registro["fecha_recepcion"].isoformat(timespec="seconds"),
    }

    # Abrir el csv de modo que apile cada nuevo registro
    with CSV_FILE.open(mode="a", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        if encabezado:
            escritor.writeheader()
        escritor.writerow(fila)

    return fila


def obtener_ultima_medicion():
    """
    Obtener la ultima medicion del csv.
    Se usa como respaldo si MongoDB no esta disponible.
    """
    if not CSV_FILE.exists() or CSV_FILE.stat().st_size == 0:
        return None

    try:
        with CSV_FILE.open(mode="r", newline="", encoding="utf-8-sig") as archivo:
            ultima = None
            for registro in csv.DictReader(archivo):
                ultima = registro
            return ultima
    except (OSError, csv.Error):
        return None
