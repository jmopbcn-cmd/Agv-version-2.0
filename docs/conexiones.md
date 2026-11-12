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

## Pico 2 W y UART de la Fusion HAT+

La Pico lee los cuatro encoders en GP2–GP5 y envía una línea JSON cada 500 ms
por UART0 a 115200 baudios, 8 bits, sin paridad y un bit de parada. El USB
también ofrece la misma telemetría para diagnóstico.

| Pico 2 W | Fusion HAT+ | Uso |
|---|---|---|
| Pin físico 1, GP0 (TX) | RXD del conector UART, GPIO15 de la Pi | Telemetría |
| Pin físico 3, GND | GND del conector UART | Masa común |
| Pin físico 2, GP1 (RX) | TXD del conector UART, GPIO14 de la Pi | Opcional para comunicación de retorno. Dejar libre para solo telemetría. |
| Pin físico 39, VSYS | 5 V regulados, pin físico 2 o 4 del cabezal de 40 pines | Alimentación alternativa al USB |

Hacer el cableado con el equipo apagado. Verificar con un multímetro el
punto de 5 V antes de conectarlo a VSYS. Usar USB o los 5 V regulados para
alimentar la Pico. Para conservar ambas fuentes conectadas, seguir el
esquema con diodo Schottky de la ficha de la Pico. La batería del AGV se
conecta a su entrada en la HAT+.

En la Pi 5 con Ubuntu, la UART del cabezal se comprobó como
`/dev/ttyAMA0`. Para liberarla, hacer una copia de
`/boot/firmware/cmdline.txt`, quitar solo el parámetro
`console=serial0,115200` de su única línea y conservar `enable_uart=1`
en `/boot/firmware/config.txt`. Tras reiniciar, comprobar que
`serial-getty@ttyAMA0` esté inactivo y que solo el lector del AGV abra el
puerto. Para volver a USB, definir `AGV_PICO_PORT=usb` en el entorno del
servicio `agv-websocket` y reiniciarlo. El panel indica el dispositivo
efectivo en `puerto_pico`.

Si se usa `mpremote` por USB, detener primero `agv-websocket` si ocupa
`/dev/ttyACM0`, guardar una copia de los archivos de la Pico y volver a
iniciar el servicio al terminar. El script auxiliar `mesuras.py` de la Pico
usa GP4 y GP5 para I²C y comparte esos pines con dos encoders.

[Conector UART y alimentación de la Fusion HAT+](https://docs.sunfounder.com/projects/fusion-hat/en/latest/hardware/interfaces.html#uart) ·
[Ficha de la Pico 2 W](https://datasheets.raspberrypi.com/picow/pico-2-w-datasheet.pdf)
