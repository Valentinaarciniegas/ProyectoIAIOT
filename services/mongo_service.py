from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError

from config import MONGO_COLECCION, MONGO_DB, MONGO_URI

# Timeout corto: el ESP32 espera la respuesta maximo 5 s
_cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000, tz_aware=True)
_coleccion = _cliente[MONGO_DB][MONGO_COLECCION]

_indices_creados = False


def _crear_indices():
    """
    Crea los indices una sola vez:
    - Consultas rapidas por fecha y por lote.
    - Indice unico (sensor + hora de medicion) para no duplicar lecturas
      que el ESP32 reenvia desde su buffer si no recibio la respuesta.
    """
    global _indices_creados
    if _indices_creados:
        return
    _coleccion.create_index([("fecha_medicion", DESCENDING)])
    _coleccion.create_index([("lote_id", ASCENDING), ("fecha_medicion", DESCENDING)])
    _coleccion.create_index(
        [("id_sensor", ASCENDING), ("ts_dispositivo", ASCENDING)],
        unique=True,
        partialFilterExpression={"ts_dispositivo": {"$type": "number"}},
    )
    _indices_creados = True


def guardar_registro(registro):
    """
    Inserta una medicion.
    Retorna True si se guardo y False si ya existia (duplicado).
    Lanza PyMongoError si MongoDB no esta disponible.
    """
    _crear_indices()
    try:
        _coleccion.insert_one(dict(registro))
        return True
    except DuplicateKeyError:
        return False


def obtener_mediciones(limite=50, lote_id=None):
    """Ultimas mediciones, de la mas reciente a la mas antigua."""
    filtro = {"lote_id": lote_id} if lote_id else {}
    cursor = (
        _coleccion.find(filtro, {"_id": 0})
        .sort("fecha_medicion", DESCENDING)
        .limit(limite)
    )
    return list(cursor)


def esta_disponible():
    try:
        _cliente.admin.command("ping")
        return True
    except PyMongoError:
        return False
