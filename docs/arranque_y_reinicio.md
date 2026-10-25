# Arranque y recuperación — 24 de octubre de 2026

Actualización 25/10/2026: ambos servicios están instalados, habilitados y activos; el comprobador confirma HTTP, batería y cuatro canales en reposo. La instalación pendiente descrita abajo corresponde a la preparación inicial. Para una Pi nueva, el instalador conserva la unidad WebSocket existente y no la instala si falta: ver el [manual](../raspberry/tests/README.md). La pantalla guardada ahora recibe RPM reales; su versión instalada sigue pendiente de comprobación visual.

## Estado comprobado antes de la instalación

- agv-websocket.service está habilitado, activo y con Restart=always y RestartSec=3. Ejecuta .venv/bin/python src/servidor_ws.py como olmos. El lector USB reintenta si la Pico no está disponible al arrancar.
- El panel HTTP que funcionaba en la revisión anterior dejó de escuchar en 8080. No existía servicio de arranque HTTP. Se añade deploy/agv-web.service, que sirve únicamente web/ y reinicia el proceso si falla.
- Wi-Fi wlan0 está configurado mediante netplan/systemd-networkd y conectado. La dirección 192.168.1.11 se obtiene por DHCP. La pantalla ESP32 tiene esa IP escrita en el firmware de referencia.
- El usuario olmos necesita contraseña para sudo. La instalación y el reinicio no se pueden completar por SSH no interactivo con los permisos actuales.

## Instalación preparada

Desde la terminal de VS Code conectada a la Pi:

    cd /home/olmos/Agv-version-2.0
    sudo sh deploy/instalar_arranque.sh
    .venv/bin/python deploy/comprobar_arranque.py

El instalador valida las unidades, respalda las anteriores en /var/backups/agv-arranque-FECHA, instala el servicio HTTP y habilita ambos servicios. Conserva la unidad existente del WebSocket; no reinstala dependencias ni cambia el firmware. No reinicia ni mueve motores. No ejecutar otra copia manual del HTTP en 8080.

## Dirección de red y pantalla física

Reservar en el DHCP del router la IP 192.168.1.11 para la MAC de wlan0 de esta Pi (consultable con ip link show wlan0). Mantener la misma red de la pantalla. Sin esa reserva no queda garantizado que la pantalla encuentre el servidor tras renovar la dirección. No se ha modificado el router ni fijado IP en netplan.

El firmware ESP32 de referencia inicializa Wi-Fi y configura reintento WebSocket cada 3 segundos. Eso describe el archivo guardado; no confirma el firmware instalado. La pantalla debe tener alimentación independiente o recuperarla tras el encendido. Hay que observar su vuelta a conexión y actualización tras reiniciar la Pi; recibir JSON en la Pi no demuestra el funcionamiento de la pantalla. La copia de referencia conserva RPM simuladas: no tratarlas como prueba de lectura real de encoders en la pantalla física.

Pico: el archivo guardado firmware/PICO_2W/main.py emite JSON y está pensado para arrancar como main.py en MicroPython. No se ha interrumpido el USB ni leído el sistema de archivos de la Pico para confirmar el archivo desplegado. Un reinicio de la Pi no equivale necesariamente a cortar alimentación a la Pico.

## Prueba de reinicio

Primero completar la instalación y comprobar ambos servicios. Preparar el vehículo inmovilizado y sin pruebas de motores en ejecución. Después:

    sudo reboot

Esperar la reconexión de red, volver a conectar VS Code y ejecutar:

    cd /home/olmos/Agv-version-2.0
    .venv/bin/python deploy/comprobar_arranque.py

Abrir http://192.168.1.11:8080/ desde otro equipo. Confirmar que actualiza datos, que la Pico aparece conectada y que los cuatro motores en reposo dan 0 RPM. Confirmar visualmente la pantalla ESP32 conectada y con temperatura/batería actualizadas. Ningún servicio de esta instalación ordena movimiento de motores. Para validar arranque de todos los dispositivos desde apagado hace falta además una prueba de alimentación completa.

## Diagnóstico y recuperación

    systemctl status agv-websocket.service agv-web.service --no-pager
    journalctl -b -u agv-websocket.service -u agv-web.service -n 80 --no-pager
    ip -brief address
    ls -l /dev/ttyACM*

Sin Pico: comprobar alimentación/cable USB y que no haya monitor serie ocupando el puerto. Sin panel pero WebSocket activo: revisar agv-web.service y puerto 8080. Pantalla sin datos con panel correcto: comprobar IP, red, alimentación y firmware de la pantalla.

Para desactivar solo el servicio HTTP añadido:

    sudo systemctl disable --now agv-web.service

Para revertir su unidad, usar el respaldo indicado por el instalador si existía una unidad anterior. No restaurar archivos de otra fecha sin revisarlos. Los respaldos permanecen fuera de Git.

## Límite de la validación

Preparar y validar estos archivos no acredita que ya estén instalados ni que se haya superado el reinicio. Registrar por separado la instalación, el nuevo arranque y la observación de la pantalla física. No iniciar PID hasta conservar una referencia de arranque comprobada.
