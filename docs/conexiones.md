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

## Pico 2 W por UART o USB

La Pico lee los cuatro encoders y publica las muestras por su puerto serie USB.

Con el coche apagado, conecta la Pico 2 W a un puerto USB de la Raspberry Pi con un cable de datos. El cable alimenta la Pico y lleva la telemetría de los encoders. El servidor localiza la Pico por su identificador USB de MicroPython (`2e8a:0005`). En el panel, `puerto_pico` muestra el puerto activo, por ejemplo `/dev/ttyACM0`. La Fusion HAT+ controla los motores y proporciona el estado de la batería.

En este coche la Pico está conectada por la UART de la Fusion HAT+. Con ambos equipos apagados, conecta GP0 / TX de la Pico a RXD de la HAT+ y une GND con GND. La comunicación usa 115200 baudios. La Pico necesita alimentación. Para reproducir esta configuración, instala deploy/20-pico-uart.conf en /etc/systemd/system/agv-websocket.service.d/, luego ejecuta sudo systemctl daemon-reload y reinicia agv-websocket. El panel debe indicar /dev/ttyAMA0. Al retirar ese ajuste, el servidor vuelve a detectar la Pico por USB.

Si se usa `mpremote` por USB, detener primero `agv-websocket` si ocupa
`/dev/ttyACM0`, guardar una copia de los archivos de la Pico y volver a
iniciar el servicio al terminar. El script auxiliar `mesuras.py` de la Pico
usa GP4 y GP5 para I²C y comparte esos pines con dos encoders.

[Ficha de la Pico 2 W](https://datasheets.raspberrypi.com/picow/pico-2-w-datasheet.pdf)
[Ficha de la Pico 2 W](https://datasheets.raspberrypi.com/picow/pico-2-w-datasheet.pdf)

## Wi-Fi directo del coche

La Raspberry emite AGV-Coche en 2,4 GHz. Su IP es 192.168.50.1, el panel usa el puerto 8080 y el WebSocket usa el 8765. Conecta a esa red el mando y la pantalla de 2,8 pulgadas. En el portal de la pantalla, configura la Raspberry en 192.168.50.1 y el puerto AGV en 8765. En Windows, el alias SSH agv apunta a esa IP.

Para restaurar el punto de acceso en Ubuntu, instala hostapd, copia deploy/hostapd-agv.conf.example a /etc/hostapd/hostapd.conf con permisos 600 y añade la clave WPA2 local. Copia deploy/05-agv-directo.network a /etc/systemd/network/. Desde la consola de la Raspberry, enmascara netplan-wpa-wlan0.service y desenmascara y habilita hostapd.service. Reinicia para aplicar ambos cambios. La sesión por la red anterior se interrumpe.

Para compilar el mando como ESP32 Wrover Module, instala la librería Arduino WebSockets y copia firmware/Mando_Joystick_AGV/secrets.example.h a secrets.h en esa carpeta. Edita la clave local. Al arrancar o reconectarse, deja el joystick centrado. Después puedes moverlo sin pulsar el botón SW. El mando pide la parada al volver al centro. Los valores de reposo medidos de este mando son X=1789 e Y=1888.

En la pantalla, entra en AGV y abre Conducir. El deslizador selecciona una potencia máxima común entre el 25 % y el 75 %. Al soltar el deslizador, el ajuste se aplica al joystick táctil y al mando físico. Tras reiniciar el servidor se recupera el 25 %. Al iniciar la marcha, la potencia sube gradualmente desde el 25 %. Al soltar el joystick, la pantalla pide la parada. El ajuste limita el PWM de las órdenes de joystick. La protección por pérdida de telemetría y el reparto en curva siguen activos.

La imagen de aplicación de la pantalla de 2,8 pulgadas se grabó y verificó por COM9. La copia está en firmware/Pantalla_AGV_Minrray/verificado/Pantalla_AGV_Minrray.ino.bin (1 182 336 bytes, SHA-256 5cf6642bebb7054aee9ab94ca28ac4e663883c1fa5986c0a3dfaca543c80d5b5). Es la aplicación de la partición a partir de 0x10000. La configuración Wi-Fi del dispositivo se guarda en su memoria de preferencias.
