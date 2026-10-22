# AGB Car Inteligent — AGV MC100

Servidor de telemetría para Raspberry Pi y panel táctil ESP32E V1.2 con ST7789/XPT2046.

## Contenido

- [Servidor WebSocket: instalación y arranque](docs/servidor_websocket.md).
- [Pantalla V1.2: preparación y bibliotecas](docs/pantalla_v1.2.md).
- [Hardware](docs/hardware.md) y [conexiones](docs/conexiones.md).
- [Registro de comprobaciones y pruebas pendientes](docs/registro_pruebas.md).

El servidor está en src/servidor_ws.py. El programa Arduino está en firmware/PANTALLA_AGV_ESP32E28/PANTALLA_AGV_ESP32E28.ino.

## Credenciales

Antes de compilar la pantalla, copiar secrets.example.h como secrets.h en la misma carpeta y completar las credenciales Wi-Fi localmente. secrets.h está excluido de Git. No publicar contraseñas, archivos .env ni el entorno .venv.

## Estado actual

Servidor con telemetría real de temperatura y lecturas disponibles de Fusion HAT+. Pantalla con páginas INICIO, MOTORES y SISTEMA; RPM simuladas y velocidad fija en 0.0. No hay control de motores. La copia del firmware con secretos separados está pendiente de compilación y validación física.
