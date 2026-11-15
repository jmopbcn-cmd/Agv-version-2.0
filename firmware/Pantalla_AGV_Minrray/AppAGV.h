#pragma once
namespace AppAGV {
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





WebSocketsClient webSocket;

// =============================================
// PAGINAS
// =============================================

enum Pagina {
  INICIO,
  MOTORES,
  SISTEMA,
  CONDUCIR
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

// RPM recibidas del servidor; -1 significa sin lectura valida.
float velocidad = 0.0; // Sin conversion a velocidad lineal calibrada.
float rpm[4] = {-1, -1, -1, -1};
bool picoConectada = false;

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

  texto(12, 11, "AGV MC100", BLANCO, 2);

}

// =============================================
// MENU TACTIL
// =============================================

void dibujarMenu() {

  const char* nombres[4] = {
    "INICIO", "MOTORES", "SISTEMA", "CONDUCIR"
  };

  for (int i = 0; i < 4; i++) {

    int x = 4 + i * 79;

    uint16_t color =
      ((int)paginaActual == i) ? AZUL : TARJETA;

    tft.fillRoundRect(
      x, 199, 75, 35, 5, color
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

    snprintf(buffer, sizeof(buffer), "M%d", i);
    texto(x + 12, y + 9, buffer, GRIS, 1);

    if (datosActuales() && picoConectada && rpm[i] >= 0) {
      snprintf(buffer, sizeof(buffer), "%.1f", rpm[i]);
    } else {
      snprintf(buffer, sizeof(buffer), "--");
    }
    texto(x + 12, y + 26, buffer, BLANCO, 3);

    texto(x + 105, y + 43, "RPM", VERDE, 1);
  }

  texto(17, 184, datosActuales() && picoConectada ? "RPM REALES" : "SIN DATOS ENCODERS",
        datosActuales() && picoConectada ? VERDE : AMARILLO, 1);
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

  bool picoOK = piOK && picoConectada;
  texto(19, 178, "PICO 2 W:", GRIS, 1);
  texto(
    140, 178,
    picoOK ? "CONECTADA" : "SIN DATOS",
    picoOK ? VERDE : AMARILLO, 1
  );
}

// =============================================
// DIBUJAR PAGINA COMPLETA
// =============================================


int marcha = -1;
bool dedoJoystick = false;
int joyX = 130, joyY = 122;
unsigned long renovacion = 0;
bool mandoOcupado = false;
bool rechazo = false;

void soltarMarcha() {
  if (marcha < 0) return;
  marcha = -1;
  webSocket.sendTXT("{\"tipo\":\"soltar_marcha\"}");
}

void dibujarConducir() {
  tft.fillRect(8, 48, 304, 26, FONDO);
  const char* estado = rechazo ? "Orden rechazada o marcha detenida" :
    !datosActuales() || !picoConectada || !fusionHatConectada ? "Esperando conexion y encoders" :
    mandoOcupado ? "Control ocupado" : "Manten pulsado para mover";
  texto(12, 55, estado, BLANCO, 1);
  tft.fillCircle(130, 122, 66, TARJETA);
  tft.drawCircle(130, 122, 66, GRIS);
  tft.drawCircle(130, 122, 11, GRIS);
  tft.fillCircle(joyX, joyY, 13, marcha >= 0 ? VERDE : AZUL);
  tft.fillRoundRect(214, 104, 100, 35, 6, 0xA800);
  texto(245, 117, "PARAR", BLANCO, 1);
}

bool dentro(int x, int y, int left, int top) {
  return x >= left && x < left + 100 && y >= top && y < top + 35;
}

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

    case CONDUCIR:
      dibujarConducir();
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

  if (paginaActual == CONDUCIR) dibujarConducir();

  // Evitamos borrar toda la pantalla y el menu
  if (paginaActual == INICIO) {
    tft.fillRect(8, 52, 304, 139, FONDO);
    dibujarInicio();
  }

  if (paginaActual == MOTORES) {
    tft.fillRect(8, 52, 304, 139, FONDO);
    dibujarMotores();
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
      marcha = -1;
      dedoJoystick = false;
      mandoOcupado = false;

      raspberryConectada = false;
      picoConectada = false;
      for (int i = 0; i < 4; i++) rpm[i] = -1;
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

      const char* tipoMensaje = doc["tipo"] | "";
      if (strcmp(tipoMensaje, "error_control") == 0) {
        soltarMarcha();
        dedoJoystick = false;
        rechazo = true;
        break;
      }
      if (strcmp(tipoMensaje, "control_motores") == 0) break;
      mandoOcupado = doc["control_motores"]["ocupado"] | false;
      if (marcha >= 0 && !doc["control_motores"]["error"].isNull()) {
        soltarMarcha();
        rechazo = true;
      }
      picoConectada = doc["pico_conectada"] | false;
      for (int i = 0; i < 4; i++) {
        char nombre[3];
        snprintf(nombre, sizeof(nombre), "M%d", i);
        JsonVariant valor = doc["encoders"][nombre]["rpm"];
        float lectura = valor.is<float>() ? valor.as<float>() : -1;
        rpm[i] = picoConectada && isfinite(lectura) && lectura >= 0 && lectura <= 2000 ? lectura : -1;
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

void enter() {
 paginaActual=INICIO; raspberryConectada=false; ultimaRecepcion=0;
 dibujarPagina();
 String origen = "Origin: http://" + rpiHost;
 webSocket.setExtraHeaders(origen.c_str());
 webSocket.begin(rpiHost.c_str(),rpiPort,"/");
 webSocket.onEvent(eventoWebSocket); webSocket.setReconnectInterval(3000);
}
void leave(){soltarMarcha();webSocket.disconnect();raspberryConectada=false;ultimaRecepcion=0;}


void loop(bool down, bool edge, int x, int y) {
  if (WiFi.status() == WL_CONNECTED) webSocket.loop();
  const bool listo = datosActuales() && millis() - ultimaRecepcion < 2500 &&
                     picoConectada && fusionHatConectada && !mandoOcupado;
  if (!down || !listo) {
    dedoJoystick = false;
    soltarMarcha();
  }
  if (edge && y >= 199 && x >= 4 && x < 320) {
    dedoJoystick = false;
    soltarMarcha();
    paginaActual = static_cast<Pagina>((x - 4) / 79);
    dibujarPagina();
  } else if (paginaActual == CONDUCIR && edge) {
    rechazo = false;
    if (dentro(x, y, 214, 104)) {
      dedoJoystick = false;
      soltarMarcha();
      webSocket.sendTXT("{\"tipo\":\"parar_motores\"}");
    } else if (listo && hypotf(x - 130, y - 122) <= 66) {
      dedoJoystick = true;
    }
  }
  if (paginaActual == CONDUCIR) {
    float dx = dedoJoystick ? (x - 130) / 55.0f : 0;
    float dy = dedoJoystick ? (y - 122) / 55.0f : 0;
    float distancia = hypotf(dx, dy);
    float escala = max(1.0f, distancia);
    int nuevoX = 130 + roundf(51 * dx / escala);
    int nuevoY = 122 - roundf(51 * dy / escala);
    if (distancia <= .18f) {
      soltarMarcha();
    } else if (marcha < 0 || millis() - renovacion >= 150) {
      char orden[90];
      snprintf(orden, sizeof(orden),
               "{\"tipo\":\"marcha\",\"sentido\":\"joystick\",\"x\":%.4f,\"y\":%.4f}",
               dx / escala, dy / escala);
      renovacion = millis();
      if (webSocket.sendTXT(orden)) marcha = 0;
      else {
        dedoJoystick = false;
        soltarMarcha();
      }
    }
    if (nuevoX != joyX || nuevoY != joyY) {
      joyX = nuevoX;
      joyY = nuevoY;
      dibujarConducir();
    }
  }
  if (millis() - ultimaPantalla >= 1000) {
    ultimaPantalla = millis();
    actualizarPantalla();
  }
}
}
