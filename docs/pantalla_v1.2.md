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

Paginas INICIO, MOTORES y SISTEMA. Bateria, voltaje, estado Fusion HAT y temperatura se reciben por JSON del servidor. Actualización actual: RPM de los cuatro motores recibidas por JSON; velocidad lineal permanece en 0.0, sin calibrar. Caducidad de datos: 5 segundos. Refresco de contenido: 1 segundo. Reconexion WebSocket: 3 segundos.

## Validacion

Revision estatica y separacion de credenciales. No se ha compilado ni flasheado esta copia; falta verificar compilacion con las bibliotecas instaladas, conexion Wi-Fi, recepcion, tactil y recuperacion tras desconectar la Raspberry. La separacion de secretos no cambia pines, calibracion ni protocolo.

## Actualización RPM reales (24 de octubre de 2026)

Se sustituye el arreglo de RPM simuladas por lectura de encoders.M0/M1/M2/M3 del JSON, validada con pico_conectada y caducidad de datos. La página MOTORES se refresca cada segundo, muestra etiquetas M0–M3 y -- sin datos válidos. Conserva pines y calibración táctil. La velocidad lineal permanece sin calibrar.

Programa original de Windows conservado; copia de trabajo en D:/Documentos/Arduino/AGB_RPM_REALES/PANTALLA_AGV_ESP32E28. Credenciales locales excluidas de Git. Copia completa previa de flash de 4 MB guardada localmente en carpeta respaldo, fuera de Git. Identificada ESP32-D0WD-V3, flash 4 MB, puerto COM7. Compilación y carga se registran por separado cuando concluyan.

Prueba de motores: cuatro puertos a potencia fija 40 % durante 60 segundos (05:28:02–05:29:02 según reloj Pi), parada automática registrada y comprobación posterior de cuatro canales a 0 RPM. Durante giro se recibieron RPM reales aproximadas 406–497; esta prueba es de potencia fija y no de regulación PID.

### Compilación y carga completadas

Compilación correcta con esp32:esp32:esp32, core ESP32 3.3.12: 1125019 bytes de programa (85 %). Carga en COM7 completada con verificación de datos y reinicio automático. Lectura serie posterior confirma mensajes de batería/CPU cada segundo y Fusion OK, sin errores JSON observados. No se ha observado visualmente el LCD desde el ordenador: confirmar página MOTORES, etiquetas M0–M3 y RPM REALES. Con ruedas paradas debe mostrar 0.0; falta comprobación visual durante giro con esta versión. Copia de memoria previa de 4194304 bytes verificada localmente; no se publica por contener configuración del dispositivo.
