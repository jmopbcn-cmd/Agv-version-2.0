
#include <SPI.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <XPT2046_Touchscreen.h>

// =============================================
// AGV MC100 - PANEL TACTIL V1.2
// ESP32E 2.8" - ST7789 + XPT2046
// Raspberry Pi 5 + Fusion HAT+
// Sin control de motores
// =============================================

// Pines LCD confirmados
#define TFT_CS    15
#define TFT_DC     2
#define TFT_MOSI  13
#define TFT_MISO  12
#define TFT_SCLK  14
#define TFT_BL    21

// Pines tactiles confirmados
#define TOUCH_CS    33
#define TOUCH_IRQ   36
#define TOUCH_SCLK  25
#define TOUCH_MOSI  32
#define TOUCH_MISO  39

// Hardware
Adafruit_ST7789 tft(&SPI, TFT_CS, TFT_DC, -1);
SPIClass touchSPI(HSPI);
XPT2046_Touchscreen touch(TOUCH_CS, TOUCH_IRQ);

// Pantalla
const int ANCHO = 320;
const int ALTO = 240;

// Colores
const uint16_t FONDO    = 0x0863;
const uint16_t TARJETA  = 0x2188;
const uint16_t AZUL     = 0x137F;
const uint16_t VERDE    = 0x2F6D;
const uint16_t BLANCO   = 0xFFFF;
const uint16_t GRIS     = 0xB5D6;
const uint16_t AMARILLO = 0xFE40;

// =============================================
// CONFIGURACION DE RED
// =============================================

#include "secrets.h"
const char* RPI_IP = "192.168.1.11";
const uint16_t RPI_PUERTO = 8765;

WebSocketsClient webSocket;

// =============================================
// PAGINAS
// =============================================

enum Pagina {
  INICIO,
  MOTORES,
  SISTEMA
};

Pagina paginaActual = INICIO;

// =============================================
// DATOS DEL AGV
// =============================================

// Datos reales
int bateria = -1;
float voltajeBateria = 0.0;
String estadoBateria = "";
float temperaturaCPU = 0.0;

bool raspberryConectada = false;
bool fusionHatConectada = false;

// Datos simulados: todavia sin encoders integrados
float velocidad = 0.0;
int rpm[4] = {160, 158, 161, 159};

// Control de actualizaciones
unsigned long ultimaRecepcion = 0;
unsigned long ultimaPantalla = 0;

const unsigned long TIMEOUT_DATOS = 5000;

// =============================================
// VALIDAR COMUNICACION
// =============================================

bool datosActuales() {
  return WiFi.status() == WL_CONNECTED &&
         raspberryConectada &&
         ultimaRecepcion != 0 &&
         millis() - ultimaRecepcion < TIMEOUT_DATOS;
}

bool bateriaDisponible() {
  return datosActuales() &&
         fusionHatConectada &&
         bateria >= 0;
}

// =============================================
// FUNCIONES GRAFICAS
// =============================================

void texto(
  int x, int y,
  const char* contenido,
  uint16_t color,
  int tamano = 2
) {
  tft.setTextWrap(false);
  tft.setTextColor(color);
  tft.setTextSize(tamano);
  tft.setCursor(x, y);
  tft.print(contenido);
}

void tarjeta(int x, int y, int w, int h) {
  tft.fillRoundRect(x, y, w, h, 8, TARJETA);
}

// =============================================
// CABECERA
// =============================================

void dibujarCabecera() {
  tft.fillRect(0, 0, ANCHO, 43, AZUL);

  texto(12, 11, "AGV MC100", BLANCO, 3);
  texto(262, 15, "V1.2", VERDE, 1);
}

// =============================================
// MENU TACTIL
// =============================================

void dibujarMenu() {

  const char* nombres[3] = {
    "INICIO", "MOTORES", "SISTEMA"
  };

  for (int i = 0; i < 3; i++) {

    int x = 5 + i * 106;

    uint16_t color =
      ((int)paginaActual == i) ? AZUL : TARJETA;

    tft.fillRoundRect(
      x, 199, 99, 35, 5, color
    );

    texto(x + 10, 211, nombres[i], BLANCO, 1);
  }
}

// =============================================
// PAGINA INICIO
// =============================================

void dibujarInicio() {

  tarjeta(8, 52, 148, 75);
  tarjeta(164, 52, 148, 75);

  texto(18, 61, "BATERIA", GRIS, 1);
  texto(174, 61, "VELOCIDAD", GRIS, 1);

  char buffer[30];

  if (bateriaDisponible()) {
    snprintf(buffer, sizeof(buffer), "%d%%", bateria);
  } else {
    snprintf(buffer, sizeof(buffer), "--%%");
  }

  texto(
    20, 83, buffer,
    bateriaDisponible() ? VERDE : AMARILLO, 3
  );

  snprintf(
    buffer, sizeof(buffer), "%.1f", velocidad
  );

  texto(178, 83, buffer, BLANCO, 3);

  tarjeta(8, 135, 304, 56);

  texto(18, 144, "ESTADO DEL VEHICULO", GRIS, 1);
  texto(18, 163, "EN ESPERA", VERDE, 2);
  texto(203, 169, "ROS: OFF", AMARILLO, 1);
}

// =============================================
// PAGINA MOTORES
// =============================================

void dibujarMotores() {

  char buffer[30];

  for (int i = 0; i < 4; i++) {

    int columna = i % 2;
    int fila = i / 2;

    int x = 8 + columna * 156;
    int y = 51 + fila * 72;

    tarjeta(x, y, 148, 65);

    snprintf(buffer, sizeof(buffer), "M%d", i + 1);
    texto(x + 12, y + 9, buffer, GRIS, 1);

    snprintf(buffer, sizeof(buffer), "%d", rpm[i]);
    texto(x + 12, y + 26, buffer, BLANCO, 3);

    texto(x + 105, y + 43, "RPM", VERDE, 1);
  }

  texto(17, 184, "VALORES SIMULADOS", AMARILLO, 1);
}

// =============================================
// PAGINA SISTEMA
// =============================================

void dibujarSistema() {

  tarjeta(8, 52, 304, 139);

  texto(19, 63, "ESTADO DEL SISTEMA", BLANCO, 2);

  bool wifiOK = WiFi.status() == WL_CONNECTED;
  bool piOK = datosActuales();
  bool hatOK = piOK && fusionHatConectada;

  // Wi-Fi
  texto(19, 94, "WIFI:", GRIS, 1);
  texto(
    140, 94,
    wifiOK ? "CONECTADO" : "SIN WIFI",
    wifiOK ? VERDE : AMARILLO, 1
  );

  // Raspberry Pi
  texto(19, 115, "RASPBERRY PI:", GRIS, 1);
  texto(
    140, 115,
    piOK ? "CONECTADA" : "SIN DATOS",
    piOK ? VERDE : AMARILLO, 1
  );

  // Fusion HAT+
  texto(19, 136, "FUSION HAT:", GRIS, 1);
  texto(
    140, 136,
    hatOK ? "CONECTADA" : "SIN DATOS",
    hatOK ? VERDE : AMARILLO, 1
  );

  // Temperatura
  texto(19, 157, "TEMPERATURA:", GRIS, 1);

  char buffer[24];

  if (piOK) {
    snprintf(
      buffer, sizeof(buffer),
      "%.1f C", temperaturaCPU
    );
  } else {
    snprintf(buffer, sizeof(buffer), "-- C");
  }

  texto(
    140, 157, buffer,
    piOK ? VERDE : AMARILLO, 1
  );
}

// =============================================
// DIBUJAR PAGINA COMPLETA
// =============================================

void dibujarPagina() {

  tft.fillScreen(FONDO);

  dibujarCabecera();

  switch (paginaActual) {

    case INICIO:
      dibujarInicio();
      break;

    case MOTORES:
      dibujarMotores();
      break;

    case SISTEMA:
      dibujarSistema();
      break;
  }

  dibujarMenu();
}

// =============================================
// ACTUALIZAR SOLO CONTENIDO
// =============================================

void actualizarPantalla() {

  // Evitamos borrar toda la pantalla y el menu
  if (paginaActual == INICIO) {
    tft.fillRect(8, 52, 304, 139, FONDO);
    dibujarInicio();
  }

  if (paginaActual == SISTEMA) {
    tft.fillRect(8, 52, 304, 139, FONDO);
    dibujarSistema();
  }
}

// =============================================
// TACTIL CALIBRADO
// =============================================

void leerTactil(int &x, int &y) {

  TS_Point p = touch.getPoint();

  x = map(p.x, 3551, 346, 16, 303);
  y = map(p.y, 3646, 440, 12, 227);

  x = constrain(x, 0, 319);
  y = constrain(y, 0, 239);
}

// =============================================
// RECEPCION WEBSOCKET
// =============================================

void eventoWebSocket(
  WStype_t tipo,
  uint8_t* payload,
  size_t longitud
) {

  switch (tipo) {

    case WStype_CONNECTED:

      raspberryConectada = true;
      ultimaRecepcion = 0;

      Serial.println("WebSocket conectado");
      break;

    case WStype_DISCONNECTED:

      raspberryConectada = false;
      fusionHatConectada = false;
      bateria = -1;
      ultimaRecepcion = 0;

      Serial.println("WebSocket desconectado");
      break;

    case WStype_TEXT: {

      JsonDocument doc;

      DeserializationError error =
        deserializeJson(doc, payload, longitud);

      if (error) {
        Serial.println("Error leyendo JSON");
        break;
      }

      // Temperatura de Raspberry Pi
      if (!doc["temperatura_cpu"].isNull()) {
        temperaturaCPU =
          doc["temperatura_cpu"].as<float>();
      }

      // Porcentaje de bateria
      if (!doc["bateria"].isNull()) {
        bateria = doc["bateria"].as<int>();
      } else {
        bateria = -1;
      }

      // Voltaje de bateria
      if (!doc["voltaje"].isNull()) {
        voltajeBateria = doc["voltaje"].as<float>();
      } else {
        voltajeBateria = 0.0;
      }

      // Estado de bateria
      estadoBateria =
        doc["estado_bateria"].as<String>();

      // Estado de Fusion HAT+
      fusionHatConectada =
        doc["fusion_hat"].as<bool>();

      ultimaRecepcion = millis();

      // Diagnostico por monitor serie
      Serial.printf(
        "CPU: %.1f C | Bateria: %d%% | Voltaje: %.3f V | Fusion: %s\n",
        temperaturaCPU,
        bateria,
        voltajeBateria,
        fusionHatConectada ? "OK" : "SIN DATOS"
      );

      break;
    }

    default:
      break;
  }
}

// =============================================
// CONFIGURACION INICIAL
// =============================================

void setup() {

  Serial.begin(115200);

  // Retroiluminacion
  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, HIGH);

  // LCD
  SPI.begin(
    TFT_SCLK,
    TFT_MISO,
    TFT_MOSI,
    TFT_CS
  );

  tft.init(240, 320);
  tft.setRotation(1);
  tft.invertDisplay(false);

  // SPI del tactil
  touchSPI.begin(
    TOUCH_SCLK,
    TOUCH_MISO,
    TOUCH_MOSI,
    TOUCH_CS
  );

  touch.begin(touchSPI);
  touch.setRotation(1);

  // Pantalla inicial
  dibujarPagina();

  Serial.println("AGV MC100 - PANEL V1.2");
  Serial.println("Pantalla y tactil iniciados");

  // Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  // WebSocket Raspberry Pi
  webSocket.begin(RPI_IP, RPI_PUERTO, "/");
  webSocket.onEvent(eventoWebSocket);
  webSocket.setReconnectInterval(3000);
}

// =============================================
// BUCLE PRINCIPAL
// =============================================

void loop() {

  // Mantener comunicacion con la Raspberry
  if (WiFi.status() == WL_CONNECTED) {
    webSocket.loop();
  }

// Actualizar la pantalla cada 5 segundos
if (millis() - ultimaPantalla >= 5000) {

  ultimaPantalla = millis();
  actualizarPantalla();
}

  // Leer pulsaciones tactiles
  if (touch.touched()) {

    int x, y;
    leerTactil(x, y);

    Serial.printf("TOUCH X:%d Y:%d\n", x, y);

    if (y >= 199 && y <= 239) {

      Pagina nuevaPagina;

      if (x < 107) {
        nuevaPagina = INICIO;
      }
      else if (x < 213) {
        nuevaPagina = MOTORES;
      }
      else {
        nuevaPagina = SISTEMA;
      }

      if (nuevaPagina != paginaActual) {
        paginaActual = nuevaPagina;
        dibujarPagina();
      }
    }

    // Esperar a soltar la pantalla
    while (touch.touched()) {
      webSocket.loop();
      delay(10);
    }
  }

  delay(20);
}
