# AGB Car Inteligent — AGV MC100

Telemetría de cuatro encoders con Pico 2 W, Raspberry Pi 5 y panel web. Incluye además firmware de pantalla táctil ESP32E V1.2.

## Contenido

- [Encoders y panel web: configuración, uso, protocolo y pruebas](docs/encoders_panel_web.md).

- [Servidor WebSocket: instalación y arranque](docs/servidor_websocket.md).
- [Pantalla V1.2: preparación y bibliotecas](docs/pantalla_v1.2.md).
- [Hardware](docs/hardware.md) y [conexiones](docs/conexiones.md).
- [Registro de comprobaciones y pruebas pendientes](docs/registro_pruebas.md).

El servidor está en src/servidor_ws.py. El programa Arduino está en firmware/PANTALLA_AGV_ESP32E28/PANTALLA_AGV_ESP32E28.ino.

## Credenciales

Antes de compilar la pantalla, copiar secrets.example.h como secrets.h en la misma carpeta y completar las credenciales Wi-Fi localmente. secrets.h está excluido de Git. No publicar contraseñas, archivos .env ni el entorno .venv.

## Estado actual

Versión del 24 de octubre de 2026: lectura de cuatro encoders por USB y telemetría web. Pruebas de giro comunicadas por el usuario; recepción real de los cuatro canales en reposo y respuesta HTTP verificadas remotamente. PID pendiente. La pantalla ESP32 conserva su estado de validación independiente; no confundirla con el panel web. Ver la guía de encoders para límites y comprobaciones pendientes.
