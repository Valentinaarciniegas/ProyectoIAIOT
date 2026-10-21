#pragma once
// Copia este archivo como config.h y pon tus datos (config.h no se sube a GitHub)

const char* WIFI_SSID  = "TU_RED_WIFI";      // solo redes de 2.4 GHz
const char* WIFI_PASS  = "TU_CLAVE";
// Local: IP de Windows en el WiFi (la VM está en NAT con reenvío del puerto 5000).
// AWS: IP elástica del EC2.
const char* SERVER_URL = "http://192.168.40.13:5000/api/mediciones";

const char* DEVICE_ID = "esp32-secadero-01";
const char* LOTE_ID   = "LOTE-2026-001";
const char* ETAPA     = "secado";   // "secado" o "almacenamiento"
