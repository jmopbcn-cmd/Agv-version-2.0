# Servidor WebSocket Raspberry Pi

src/servidor_ws.py escucha en todas las interfaces, puerto 8765, y envia JSON cada segundo.

## Instalacion (fuera del entorno virtual)

Desde /home/olmos/agb-car-inteligent:

    python3 -m venv .venv
    .venv/bin/python -m pip install pyserial==3.5 websockets==17.3

Ejecucion manual, solo con el servicio detenido:

    .venv/bin/python src/servidor_ws.py

No hace falta activar el entorno: se utiliza su Python directamente.

## Arranque automatico (fuera del entorno virtual)

La copia deploy/agb-websocket.service corresponde al servicio instalado. Adaptar usuario y rutas antes de usarla en otra maquina.

    sudo cp deploy/agb-websocket.service /etc/systemd/system/agb-websocket.service
    sudo systemctl daemon-reload
    sudo systemctl enable --now agb-websocket.service
    systemctl is-enabled agb-websocket.service
    systemctl is-active agb-websocket.service
    journalctl -u agb-websocket.service -n 50 --no-pager

Reiniciar el servicio tras cambiar el servidor para cargar la nueva version.

requirements.txt es una captura del entorno con paquetes ROS y no está validado para reinstalación completa. Los comandos anteriores cubren las dependencias directas del servidor; no instalan Fusion HAT+ ni firmware Pico.

Ver [encoders y panel web](encoders_panel_web.md) para el lector USB, los campos pico_conectada, puerto_pico y encoders, y las pruebas del 24 de octubre.

## Protocolo

- dispositivo: agv-mc100.
- temperatura_cpu: grados Celsius desde thermal_zone0/temp.
- bateria: porcentaje o null.
- voltaje: voltios o null.
- estado_bateria: estado de fusion-hat o Unknown.
- fusion_hat: se pudo leer capacity; no prueba todo el hardware.
- hora: fecha y hora local ISO sin zona horaria.

La bateria se lee de /sys/class/power_supply/fusion-hat. Si no puede leerse la temperatura se envía null. El servidor no autentica ni cifra conexiones; utilizar en la red local de confianza.

## Pantalla y secretos

Firmware V1.2 en firmware/PANTALLA_AGV_ESP32E28. Credenciales separadas en secrets.h local ignorado; ejemplo sin claves reales en secrets.example.h. Ver docs/pantalla_v1.2.md. Compilacion y prueba fisica pendientes.

## Verificacion: 22 de octubre de 2026

SSH real a agv-mc100; servicio habilitado y activo; websockets 17.3 instalado. No demuestra funcionamiento de pantalla ni un nuevo reinicio.
