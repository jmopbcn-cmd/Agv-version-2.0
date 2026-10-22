# Conexiones configuradas

## Red

El panel se conecta a la red definida en su secrets.h local y usa ws://192.168.1.11:8765/ para recibir telemetría de la Raspberry. Actualizar RPI_IP en el firmware si cambia esa dirección.

## GPIO del panel

| Interfaz | Señal | GPIO |
|---|---|---:|
| LCD | CS | 15 |
| LCD | DC | 2 |
| LCD | MOSI | 13 |
| LCD | MISO | 12 |
| LCD | SCLK | 14 |
| LCD | Retroiluminación | 21 |
| Táctil | CS | 33 |
| Táctil | IRQ | 36 |
| Táctil | SCLK | 25 |
| Táctil | MOSI | 32 |
| Táctil | MISO | 39 |

Asignaciones tomadas del firmware V1.2, no medidas de nuevo sobre la placa. No representan un esquema de alimentación o de cableado de motores.
