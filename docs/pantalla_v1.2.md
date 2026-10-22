# Pantalla AGV MC100 V1.2

ESP32E 2.8 pulgadas, ST7789 y XPT2046. Original conservado en el PC; esta copia cambia solo las declaraciones Wi-Fi por un include de secrets.h.

## Preparacion

Abrir firmware/PANTALLA_AGV_ESP32E28/PANTALLA_AGV_ESP32E28.ino en Arduino IDE. Copiar secrets.example.h como secrets.h en la misma carpeta y completar la red y clave localmente. secrets.h no se versiona. El ejemplo no conecta hasta completarlo.

Bibliotecas: WebSockets (WebSocketsClient), ArduinoJson 7 (JsonDocument), Adafruit GFX Library, Adafruit ST7735 and ST7789 Library, XPT2046_Touchscreen y sus dependencias. SPI y WiFi pertenecen al core ESP32. No se han fijado versiones de core o bibliotecas: pendientes de identificar en el entorno original. Seleccionar la misma placa y opciones usadas en la pantalla original.

## Conexion

Raspberry configurada: 192.168.1.11, WebSocket puerto 8765, ruta /. Sin control de motores. Pantalla 320 x 240, rotacion 1.

| Interfaz | Pines GPIO |
|---|---|
| LCD | CS 15, DC 2, MOSI 13, MISO 12, SCLK 14, retroiluminacion 21 |
| Tactil | CS 33, IRQ 36, SCLK 25, MOSI 32, MISO 39 |

Calibracion tactil conservada del original; puede necesitar ajuste en otra unidad.

## Comportamiento

Paginas INICIO, MOTORES y SISTEMA. Bateria, voltaje, estado Fusion HAT y temperatura se reciben por JSON del servidor. RPM de los cuatro motores son simuladas; velocidad permanece en 0.0. Caducidad de datos: 5 segundos. Refresco de contenido: 5 segundos. Reconexion WebSocket: 3 segundos.

## Validacion

Revision estatica y separacion de credenciales. No se ha compilado ni flasheado esta copia; falta verificar compilacion con las bibliotecas instaladas, conexion Wi-Fi, recepcion, tactil y recuperacion tras desconectar la Raspberry. La separacion de secretos no cambia pines, calibracion ni protocolo.
