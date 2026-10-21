#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <time.h>
#include "config.h"

#define DHTPIN  4
#define DHTTYPE DHT22

const unsigned long INTERVALO_MS = 30000;  // una lectura cada 30 s
const int BUFFER_MAX = 120;                // 1 hora de respaldo

struct Lectura {
  time_t ts;
  float t;
  float h;
};

Lectura buffer[BUFFER_MAX];
int bufInicio = 0;
int bufCount  = 0;

DHT dht(DHTPIN, DHTTYPE);
unsigned long ultimaLectura = 0;
bool primeraLectura = true;

void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.print("Conectando a WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long inicio = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - inicio < 15000) {
    delay(500);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\nConectado. IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nSin WiFi. Las lecturas quedan en el buffer.");
  }
}

void encolar(const Lectura& l) {
  int idx = (bufInicio + bufCount) % BUFFER_MAX;
  buffer[idx] = l;
  if (bufCount < BUFFER_MAX) bufCount++;
  else bufInicio = (bufInicio + 1) % BUFFER_MAX;  // lleno: se descarta la mas antigua
}

bool enviar(const Lectura& l) {
  if (WiFi.status() != WL_CONNECTED) return false;

  JsonDocument doc;
  doc["device_id"]   = DEVICE_ID;
  doc["lote_id"]     = LOTE_ID;
  doc["etapa"]       = ETAPA;
  doc["temperatura"] = round(l.t * 10) / 10.0;
  doc["humedad"]     = round(l.h * 10) / 10.0;
  if (l.ts > 1700000000) doc["ts_dispositivo"] = (uint32_t)l.ts;  // epoch UTC

  String body;
  serializeJson(doc, body);

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);
  int code = http.POST(body);
  http.end();

  Serial.printf("POST %s -> %d\n", body.c_str(), code);
  return code >= 200 && code < 300;
}

void setup() {
  Serial.begin(115200);
  delay(500);
  dht.begin();
  WiFi.setAutoReconnect(true);
  conectarWiFi();
  configTime(0, 0, "pool.ntp.org", "time.google.com");
}

void loop() {
  if (!primeraLectura && millis() - ultimaLectura < INTERVALO_MS) return;
  primeraLectura = false;
  ultimaLectura = millis();

  conectarWiFi();

  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (isnan(h) || isnan(t) || t < -40 || t > 80 || h < 0 || h > 100) {
    Serial.println("Lectura invalida, se descarta.");
    return;
  }

  Serial.printf("T = %.1f °C   HR = %.1f %%\n", t, h);
  encolar({ time(nullptr), t, h });

  while (bufCount > 0) {
    if (!enviar(buffer[bufInicio])) break;
    bufInicio = (bufInicio + 1) % BUFFER_MAX;
    bufCount--;
  }
  if (bufCount > 0) Serial.printf("Pendientes en buffer: %d\n", bufCount);
}
