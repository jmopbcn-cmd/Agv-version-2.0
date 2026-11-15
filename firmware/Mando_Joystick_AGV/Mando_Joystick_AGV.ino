#include <WiFi.h>
#include <WebSocketsClient.h>

constexpr int PIN_X = 34;
constexpr int PIN_Y = 35;
constexpr int CENTRO_X = 1789;
constexpr int CENTRO_Y = 1888;
constexpr char SSID[] = "AGV-Coche";
#include "secrets.h"
constexpr unsigned long INTERVALO_MS = 80;

WebSocketsClient socket;
bool conectado = false;
bool habilitado = false;
bool marcha = false;
unsigned long ultimoEnvio;

float eje(int valor, int centro) {
  return constrain((valor - centro) / float(valor >= centro ? 4095 - centro : centro), -1.0f, 1.0f);
}

void parar() {
  if (marcha && conectado) {
    if (!socket.sendTXT("{\"tipo\":\"soltar_marcha\"}")) {
      socket.disconnect();
    }
  }
  marcha = false;
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(SSID, PASSWORD);
  socket.begin("192.168.50.1", 8765, "/");
  socket.setExtraHeaders("Origin: http://192.168.50.1");
  socket.setReconnectInterval(1000);
  socket.onEvent([](WStype_t evento, uint8_t* datos, size_t longitud) {
    if (evento == WStype_CONNECTED || evento == WStype_DISCONNECTED) {
      conectado = evento == WStype_CONNECTED;
      habilitado = false;
      marcha = false;
      Serial.println(conectado ? "AGV conectado" : "AGV desconectado");
    }
  });
}

void loop() {
  socket.loop();
  if (!conectado) return;

  const float x = -eje(analogRead(PIN_X), CENTRO_X);
  const float y = -eje(analogRead(PIN_Y), CENTRO_Y);
  const bool centrado = hypotf(x, y) <= 0.22f;

  if (!habilitado) {
    habilitado = centrado;
    return;
  }
  if (centrado) {
    parar();
    return;
  }

  const unsigned long ahora = millis();
  if (ahora - ultimoEnvio < INTERVALO_MS) return;
  ultimoEnvio = ahora;

  char mensaje[96];
  snprintf(mensaje, sizeof(mensaje),
           "{\"tipo\":\"marcha\",\"sentido\":\"joystick\",\"x\":%.3f,\"y\":%.3f}", x, y);
  if (socket.sendTXT(mensaje)) {
    marcha = true;
  } else {
    socket.disconnect();
  }
}
