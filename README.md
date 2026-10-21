# Monitor IoT: temperatura y humedad con ESP32

Servidor Flask que recibe las mediciones de un ESP32 con sensor DHT22 y las guarda en **MongoDB** y en un **CSV**. Es parte del proyecto de trazabilidad de bioproductos de hoja de coca: cada lectura queda asociada a un lote y a una etapa, que puede ser secado o almacenamiento.

## Estructura

```
proyecto_iot/
├── app.py                  # API y dashboard (Flask)
├── config.py               # Configuración por variables de entorno
├── services/
│   ├── csv_service.py      # Escritura y lectura del CSV
│   └── mongo_service.py    # Conexión e índices de MongoDB
├── templates/index.html    # Dashboard (se actualiza cada 5 s)
├── static/css/styles.css
├── data/mediciones.csv     # Se crea automáticamente
├── firmware/cocatrace_th/  # Código del ESP32 (Arduino)
└── requirements.txt
```

## Hardware y firmware

- ESP32 DevKit + DHT22 (`+` → 3V3, `out` → GPIO4, `−` → GND).
- El firmware lee el sensor cada 30 s y envía un POST con JSON. Guarda hasta 120 lecturas en un buffer circular si no hay WiFi o el servidor no responde, y usa hora NTP.
- Para configurarlo, copia `firmware/cocatrace_th/config.example.h` como `config.h` y pon la red WiFi (2,4 GHz) y la URL del servidor. `config.h` no se sube al repositorio.
- Librerías de Arduino: `DHT sensor library` (Adafruit) y `ArduinoJson` (v7).

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/mediciones` (alias `/api/lecturas`) | Recibe una medición del ESP32 |
| GET | `/api/mediciones?limite=50&lote_id=...` | Consulta mediciones guardadas en MongoDB |
| GET | `/` | Dashboard web |
| GET | `/health` | Estado de la API y de MongoDB |

JSON que envía el ESP32:

```json
{"device_id": "esp32-secadero-01", "lote_id": "LOTE-2026-001", "etapa": "secado",
 "temperatura": 26.8, "humedad": 67.3, "ts_dispositivo": 1792544704}
```

- Se acepta tanto `device_id` como `id_sensor`.
- `ts_dispositivo` (epoch UTC) es opcional. Si viene, se usa como hora real de la medición.

## Comportamiento

- **Orden de guardado:** primero en MongoDB y después en el CSV.
- **Si MongoDB no está disponible:** responde `503`, y el ESP32 reintenta desde su buffer.
- **Lecturas duplicadas:** las identifica por sensor + `ts_dispositivo` y responde `200` sin guardarlas de nuevo.
- **Validación:** rechaza datos fuera del rango del DHT22 (−40 a 80 °C, 0 a 100 %HR) con `400`.

## Ejecutar

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py                      # desarrollo, puerto 5000
gunicorn -w 2 -b 0.0.0.0:5000 app:app   # producción
```

Variables de entorno opcionales: `MONGO_URI`, `MONGO_DB`, `MONGO_COLECCION`, `CSV_FILE`, `ZONA_HORARIA`.

## Despliegue local (Ubuntu Server en VirtualBox)

- Ubuntu Server 26.04 LTS con MongoDB 8.0.20 (repositorio `noble` de MongoDB, versión fijada con `apt-mark hold`).
- La VM usa red NAT con reenvío de puertos de VirtualBox: host `5000` → VM `5000` (Flask) y host `127.0.0.1:2222` → VM `22` (SSH). El firewall de Windows permite el puerto 5000 solo desde la red local.
- El ESP32 envía a `http://<IP-del-PC-en-el-WiFi>:5000/api/mediciones`.
- MongoDB solo escucha en `127.0.0.1` dentro de la VM. Para consultarlo: `mongosh cocatrace` en la VM, o MongoDB Compass con túnel SSH.

## Despliegue en AWS

Pendiente: EC2 con la app en una subred pública con IP elástica, y MongoDB en una subred privada. Para la app solo cambia la variable `MONGO_URI`.
