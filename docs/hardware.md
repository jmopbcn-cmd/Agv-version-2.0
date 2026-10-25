# Hardware documentado por el código actual

- Raspberry Pi: servidor agv-mc100; servicio agb-websocket.service.
- Fusion HAT+: el servidor intenta leer batería en /sys/class/power_supply/fusion-hat.
- Panel ESP32E de 2.8 pulgadas, controlador LCD ST7789 y táctil XPT2046.
- Resolución lógica 320 × 240; rotación 1.

Los pines y la calibración se conservan del firmware V1.2 original. Ver [conexiones](conexiones.md) y [pantalla](pantalla_v1.2.md).

Esta documentación describe lo configurado en el software. No certifica el cableado físico ni la identificación eléctrica de otra unidad. Actualización 25/10/2026: el firmware ESP32 guardado integra lectura de RPM del servidor; no se confirma aquí la versión instalada. El panel recibe telemetría y no ordena movimiento de motores. Ver el [manual de pruebas](../raspberry/tests/README.md).
