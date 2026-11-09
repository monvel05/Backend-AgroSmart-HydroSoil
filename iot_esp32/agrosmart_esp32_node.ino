/*
 * ============================================================================
 * AGROSMART HYDRO-SOIL — FIRMWARE NODO IoT ESP32 (MULTI-CIRCUITO)
 * ============================================================================
 * Descripción:
 *   Código base para cada circuito de riego con ESP32.
 *   1. Lee sensores de Humedad de Suelo, pH y Electroconductividad (EC).
 *   2. Envía lecturas periódicas a FastAPI (POST /api/iot/telemetria)
 *      autenticándose con su header de seguridad X-Device-Token.
 *   3. Consulta comandos de riego manual o rutinas optimizadas por IA
 *      (GET /api/iot/comando/{dispositivo_id}) para activar/desactivar
 *      el relevador de la electroválvula de ese circuito.
 * ============================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h> // Instalar librería "ArduinoJson" de Benoit Blanchon

// 1. CONFIGURACIÓN DE RED WIFI
const char* WIFI_SSID     = "TU_RED_WIFI";
const char* WIFI_PASSWORD = "TU_PASSWORD_WIFI";

// 2. CONFIGURACIÓN DEL SERVIDOR BACKEND (FASTAPI)
const char* BACKEND_BASE_URL = "http://192.168.1.100:8000"; // IP de tu PC corriendo FastAPI

// 3. IDENTIDAD Y SEGURIDAD DEL CIRCUITO (Copiar desde la pestaña "Circuitos ESP32" de la Web)
const char* DISPOSITIVO_ID      = "ESP32-CIRCUITO-01";
const char* TOKEN_AUTENTICACION = "ags_tok_9f8e7d6c5b4a3f2e1d0c";
const char* TIPO_CULTIVO        = "rodado";        // "rodado" o "hidroponico"
const char* SECTOR_RIEGO        = "Sector Norte - Parcela A1";
const float COORD_LAT           = 21.8469;
const float COORD_LNG           = -102.7188;

// 4. PINES DE HARDWARE DEL CIRCUITO EN EL ESP32
const int PIN_SENSOR_HUMEDAD = 34; // ADC1_CH6
const int PIN_SENSOR_PH      = 35; // ADC1_CH7
const int PIN_SENSOR_EC      = 32; // ADC1_CH4
const int PIN_RELE_VALVULA   = 26; // Salida digital a módulo relevador (Electroválvula)
const int PIN_LED_ESTADO     = 2;  // LED integrado en placa ESP32

unsigned long ultimoEnvioTelemetria = 0;
const unsigned long INTERVALO_TELEMETRIA_MS = 15000; // Cada 15 segundos

unsigned long ultimaConsultaComando = 0;
const unsigned long INTERVALO_COMANDO_MS = 5000;     // Cada 5 segundos

bool valvulaAbierta = false;

void setup() {
  Serial.begin(115200);
  pinMode(PIN_RELE_VALVULA, OUTPUT);
  pinMode(PIN_LED_ESTADO, OUTPUT);
  digitalWrite(PIN_RELE_VALVULA, LOW); // Válvula cerrada por defecto

  Serial.println("\n[AgroSmart Hydro-Soil] Iniciando Nodo ESP32...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[WiFi] Conectado! IP asignada: " + WiFi.localIP().toString());
}

float leerHumedadSuelo() {
  int raw = analogRead(PIN_SENSOR_HUMEDAD);
  // Mapeo calibrable de ADC (4095 = seco, 1200 = saturado)
  float porcentaje = map(raw, 4095, 1200, 0, 100);
  return constrain(porcentaje, 0.0, 100.0);
}

float leerPH() {
  int raw = analogRead(PIN_SENSOR_PH);
  float voltaje = raw * (3.3 / 4095.0);
  return constrain(7.0 + ((2.5 - voltaje) / 0.18), 3.5, 9.5);
}

float leerElectroconductividad() {
  int raw = analogRead(PIN_SENSOR_EC);
  float voltaje = raw * (3.3 / 4095.0);
  return constrain(voltaje * 1.45, 0.2, 4.5); // mS/cm
}

void enviarTelemetria() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = String(BACKEND_BASE_URL) + "/api/iot/telemetria";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", TOKEN_AUTENTICACION);

  StaticJsonDocument<512> doc;
  doc["dispositivo_id"] = DISPOSITIVO_ID;
  doc["tipo_cultivo"]   = TIPO_CULTIVO;
  doc["ip_asignada"]    = WiFi.localIP().toString();

  JsonObject lecturas = doc.createNestedObject("lecturas");
  lecturas["humedad_suelo"]        = leerHumedadSuelo();
  lecturas["ph"]                   = leerPH();
  lecturas["electroconductividad"] = leerElectroconductividad();

  JsonObject ubicacion = doc.createNestedObject("ubicacion");
  ubicacion["sector"] = SECTOR_RIEGO;
  JsonArray coords = ubicacion.createNestedArray("coordenadas");
  coords.add(COORD_LAT);
  coords.add(COORD_LNG);

  String payload;
  serializeJson(doc, payload);

  int httpResponseCode = http.POST(payload);
  Serial.printf("[Telemetría] POST %s -> HTTP %d\n", url.c_str(), httpResponseCode);
  http.end();
}

void consultarComandoValvula() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = String(BACKEND_BASE_URL) + "/api/iot/comando/" + String(DISPOSITIVO_ID);
  http.begin(url);
  http.addHeader("X-Device-Token", TOKEN_AUTENTICACION);

  int httpResponseCode = http.GET();
  if (httpResponseCode == 200) {
    String response = http.getString();
    StaticJsonDocument<384> doc;
    if (deserializeJson(doc, response) == DeserializationError::Ok) {
      bool activarValvula = doc["abrir_valvula"] | false;
      int duracionMin     = doc["duracion_minutos"] | 0;

      if (activarValvula != valvulaAbierta) {
        valvulaAbierta = activarValvula;
        digitalWrite(PIN_RELE_VALVULA, valvulaAbierta ? HIGH : LOW);
        digitalWrite(PIN_LED_ESTADO, valvulaAbierta ? HIGH : LOW);
        Serial.printf("[Válvula] Cambio de estado -> %s (%d min)\n",
                      valvulaAbierta ? "ABIERTA (REGANDO)" : "CERRADA", duracionMin);
      }
    }
  }
  http.end();
}

void loop() {
  unsigned long ahora = millis();

  if (ahora - ultimoEnvioTelemetria >= INTERVALO_TELEMETRIA_MS) {
    ultimoEnvioTelemetria = ahora;
    enviarTelemetria();
  }

  if (ahora - ultimaConsultaComando >= INTERVALO_COMANDO_MS) {
    ultimaConsultaComando = ahora;
    consultarComandoValvula();
  }
}
