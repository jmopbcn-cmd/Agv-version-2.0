#include <WiFi.h>
#include <WebSocketsClient.h>

constexpr int PIN_X = 34;
constexpr int PIN_Y = 35;
constexpr int PIN_SW = 32;
constexpr char SSID[] = "AGV-Coche";
#include "secrets.h"
constexpr unsigned long INTERVALO_MS = 80;

WebSocketsClient socket;
bool conectado = false;
bool requiereSoltar = true;
bool habilitado = false;
bool marcha = false;
int centroX;
int centroY;
unsigned long ultimoEnvio;

int medirCentro(int pin) {
  long suma = 0;
  for (int i = 0; i < 32; ++i) {
    suma += analogRead(pin);
    delay(4);
  }
  return suma / 32;
}

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
  pinMode(PIN_SW, INPUT_PULLUP);
  analogReadResolution(12);
  centroX = medirCentro(PIN_X);
  centroY = medirCentro(PIN_Y);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(SSID, PASSWORD);
  socket.begin("192.168.50.1", 8765, "/");
  socket.setExtraHeaders("Origin: http://192.168.50.1");
  socket.setReconnectInterval(1000);
  socket.onEvent([](WStype_t evento, uint8_t* datos, size_t longitud) {
    if (evento == WStype_CONNECTED || evento == WStype_DISCONNECTED) {
      conectado = evento == WStype_CONNECTED;
      requiereSoltar = true;
      habilitado = false;
      marcha = false;
      Serial.println(conectado ? "AGV conectado" : "AGV desconectado");
    }
  });
}

void loop() {
  socket.loop();
  if (!conectado) return;

  const float x = eje(analogRead(PIN_X), centroX);
  const float y = -eje(analogRead(PIN_Y), centroY);
  const bool centrado = hypotf(x, y) <= 0.22f;
  const bool pulsado = digitalRead(PIN_SW) == LOW;

  if (!pulsado) {
    parar();
    habilitado = false;
    requiereSoltar = false;
    return;
  }
  if (requiereSoltar) return;
  if (!habilitado) {
    requiereSoltar = !centrado || centroX < 500 || centroX > 3595 || centroY < 500 || centroY > 3595;
    habilitado = !requiereSoltar;
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
