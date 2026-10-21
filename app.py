from datetime import datetime, timezone
from threading import Lock
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, render_template, request
from pymongo.errors import PyMongoError
from werkzeug.exceptions import HTTPException

import config
from services import csv_service, mongo_service

# Inicializar la aplicacion en Flask
app = Flask(__name__)

# Evita que dos peticiones escriban el csv al mismo tiempo
bloqueo = Lock()

ZONA = ZoneInfo(config.ZONA_HORARIA)

# Epoch minimo valido: si el ESP32 aun no sincronizo NTP envia valores pequenos
EPOCH_MINIMO = 1_700_000_000


def a_hora_local(fecha):
    """Convierte un datetime (o texto ISO) a la zona horaria del proyecto."""
    if fecha is None:
        return "Sin mediciones"
    if isinstance(fecha, str):
        fecha = datetime.fromisoformat(fecha)
    return fecha.astimezone(ZONA).strftime("%Y-%m-%d %H:%M:%S")


def validar_medicion(datos):
    """
    Valida el JSON recibido y construye el registro a guardar.
    Acepta 'id_sensor' o 'device_id' (el nombre que usa el firmware del ESP32).
    Retorna (registro, None) o (None, mensaje_error).
    """
    if not isinstance(datos, dict):
        return None, "Se requiere un objeto JSON"

    id_sensor = datos.get("id_sensor") or datos.get("device_id")
    if not id_sensor:
        return None, "Falta el campo id_sensor (o device_id)"

    try:
        temperatura = float(datos["temperatura"])
        humedad = float(datos["humedad"])
    except (KeyError, TypeError, ValueError):
        return None, "Envie temperatura y humedad numericas"

    if not config.TEMP_MIN <= temperatura <= config.TEMP_MAX:
        return None, "Temperatura fuera del rango del sensor"
    if not config.HUM_MIN <= humedad <= config.HUM_MAX:
        return None, "Humedad fuera del rango del sensor"

    ahora = datetime.now(timezone.utc)

    # Hora real de la medicion: la del ESP32 si viene sincronizada,
    # si no, la hora en que llego al servidor
    ts = datos.get("ts_dispositivo")
    if isinstance(ts, (int, float)) and EPOCH_MINIMO < ts <= ahora.timestamp() + 300:
        fecha_medicion = datetime.fromtimestamp(ts, timezone.utc)
        ts = int(ts)
    else:
        fecha_medicion = ahora
        ts = None

    registro = {
        "id_sensor": str(id_sensor),
        "lote_id": str(datos.get("lote_id") or "SIN-LOTE"),
        "etapa": str(datos.get("etapa") or "sin-etapa"),
        "temperatura": round(temperatura, 1),
        "humedad": round(humedad, 1),
        "fecha_medicion": fecha_medicion,
        "fecha_recepcion": ahora,
    }
    if ts is not None:
        registro["ts_dispositivo"] = ts
    return registro, None


@app.route("/", methods=["GET"])
def inicio():
    """Dashboard: ultima medicion y tabla con las ultimas 20."""
    historial = []
    origen = "MongoDB"
    try:
        historial = mongo_service.obtener_mediciones(limite=20)
        ultima = historial[0] if historial else None
    except PyMongoError:
        # Respaldo: leer la ultima medicion del csv
        origen = "CSV (MongoDB no disponible)"
        with bloqueo:
            ultima = csv_service.obtener_ultima_medicion()

    for fila in historial:
        fila["fecha_local"] = a_hora_local(fila["fecha_medicion"])

    return render_template(
        "index.html",
        temperatura=ultima["temperatura"] if ultima else "--",
        humedad=ultima["humedad"] if ultima else "--",
        id_sensor=ultima["id_sensor"] if ultima else "--",
        lote_id=ultima["lote_id"] if ultima else "--",
        etapa=ultima["etapa"] if ultima else "--",
        fecha=a_hora_local(ultima["fecha_medicion"]) if ultima else "Sin mediciones",
        historial=historial,
        origen=origen,
    )


# /api/lecturas se deja como alias para el firmware original
@app.route("/api/mediciones", methods=["POST"])
@app.route("/api/lecturas", methods=["POST"])
def recibir_medicion():
    """
    Recibe la medicion del ESP32 y la guarda en MongoDB y en el csv.
    Primero MongoDB: si falla se responde 503 y el ESP32 la reintenta
    desde su buffer, sin dejar el csv con datos que no estan en la base.
    """
    registro, error = validar_medicion(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400

    try:
        nuevo = mongo_service.guardar_registro(registro)
    except PyMongoError:
        app.logger.exception("No se pudo guardar en MongoDB")
        return jsonify({"error": "Base de datos no disponible, reintente"}), 503

    if not nuevo:
        # El ESP32 reenvio una lectura que ya estaba guardada
        return jsonify({"mensaje": "Registro ya existente, se ignora"}), 200

    with bloqueo:
        fila = csv_service.guardar_registro(registro)

    return jsonify({"mensaje": "Registro guardado correctamente", "registro": fila}), 201


@app.route("/api/mediciones", methods=["GET"])
def listar_mediciones():
    """
    Consulta las mediciones guardadas en MongoDB.
    Parametros opcionales: ?limite=50&lote_id=LOTE-2026-001
    """
    limite = min(request.args.get("limite", 50, type=int), 1000)
    lote_id = request.args.get("lote_id")
    try:
        datos = mongo_service.obtener_mediciones(limite=limite, lote_id=lote_id)
    except PyMongoError:
        return jsonify({"error": "Base de datos no disponible"}), 503

    for fila in datos:
        for campo in ("fecha_medicion", "fecha_recepcion"):
            fila[campo] = fila[campo].isoformat(timespec="seconds")
    return jsonify(datos)


@app.route("/health", methods=["GET"])
def health():
    """Estado del servidor y de la base de datos."""
    ok = mongo_service.esta_disponible()
    return jsonify({"api": "ok", "mongodb": "ok" if ok else "caida"}), 200 if ok else 503


@app.errorhandler(HTTPException)
def manejar_http(e):
    """Errores HTTP normales (404, 405...) con su codigo real."""
    return jsonify({"error": e.name}), e.code


@app.errorhandler(Exception)
def manejar_excepcion(e):
    """Errores no controlados: se registran en el log sin exponer detalles."""
    app.logger.exception("Error no controlado")
    return jsonify({"error": "Internal Server Error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
