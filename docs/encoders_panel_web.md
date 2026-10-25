# Encoders y panel web — versión del 24 de octubre de 2026

## Referencia vigente del 25 de octubre de 2026

El [manual de pruebas](../raspberry/tests/README.md) reúne el procedimiento actual. Las secciones fechadas anteriores de este documento son historial: ya existen servicio HTTP instalado y pruebas PI conjuntas de 30/40 segundos registradas. El firmware ESP32 guardado ya recibe RPM reales; su despliegue físico no se ha confirmado en esta revisión. Se conserva el mapa del servidor M2→etiqueta Pico M3/GP5 y M3→M2/GP4. Consultar el manual antes de usar las tablas antiguas como correspondencia física.


## Alcance y estado

Versión de código base: edc5caa. Esta guía documenta la lectura de cuatro encoders, su transporte por USB y su visualización web. El control PID no está implementado. La pantalla Arduino ESP32 es un componente distinto: las pruebas del panel web no validan su firmware ni sus RPM.

## Recorrido de los datos

Encoders → Pico 2 W con MicroPython → USB serie → Raspberry Pi 5 → servidor WebSocket en 8765 → navegador con web/index.html. El programa de prueba de motores utiliza Fusion HAT+; el servidor de telemetría no manda potencia a los motores.

| Motor | Posición indicada por el código | GPIO Pico | Inversión en prueba Fusion HAT+ |
|---|---|---|---|
| M0 | Trasera izquierda | GP2 | Sí |
| M1 | Trasera derecha | GP3 | No |
| M2 | Delantera derecha | GP4 | Sí |
| M3 | Delantera izquierda | GP5 | No |

La tabla refleja la configuración del software revisado; no es una inspección eléctrica del cableado. No confundir GPIO Pico con pines de Raspberry Pi ni con números físicos del conector. Esta revisión no determina alimentación, modelo del encoder ni tensión de su salida. Confirmarlos antes de modificar conexiones; las entradas de la Pico son de lógica de 3,3 V.

## Archivos

- firmware/PICO_2W/main.py: aplicación de telemetría JSON para MicroPython; se ejecuta en la Pico.
- firmware/PICO_2W/encoders.py: diagnóstico de cuatro encoders con salida de texto para consola.
- firmware/PICO_2W/test_encoder_m0.py y test_encoder_m1.py: diagnósticos individuales, también para la Pico.
- src/servidor_ws.py: lector USB y servidor de telemetría de la Pi.
- web/index.html: panel del navegador con RPM, pulsos/s, total, CPU y batería.
- raspberry/tests/test_4_motores.py: prueba física; ordena potencia 50 a los cuatro motores durante 10 segundos y solicita detenerlos en finally. No es una prueba automática inocua; no ejecutarla sin preparar el vehículo. El finally no protege frente a un corte eléctrico o una terminación forzada.
- deploy/agb-websocket.service: definición de arranque del servidor de telemetría.

Los diagnósticos de texto y main.py son alternativas. Para el panel, la Pico debe ejecutar la versión que emite JSON. No abrir simultáneamente un monitor serie y el lector del servidor sobre el mismo dispositivo USB.

## Cálculo y protocolo

El firmware configura entrada con pull-up e interrupción por flanco descendente, con 20 pulsos por vuelta y muestreo nominal de 500 ms. Usa el intervalo real transcurrido:

    pulsos_s = pulsos_nuevos * 1000 / intervalo_ms
    RPM = pulsos_s * 60 / 20

Los 20 pulsos por vuelta son un parámetro del código: falta una calibración con vueltas contadas o instrumento de referencia. La lectura de un canal no identifica el sentido de giro. El total es acumulado y se reinicia con el programa de la Pico.

Cada línea USB es un objeto JSON con tipo igual a encoders y los objetos M0, M1, M2 y M3. Cada motor incluye rpm, pulsos_s, total y estado (GIRANDO o PARADO).

El servidor busca VID 0x2E8A y PID 0x0005, abre serie a 115200 y publica una instantánea cada segundo. Declara pico_conectada si ha recibido datos válidos hace menos de 3 segundos; no es solo detección del cable. Sin datos recientes envía encoders vacío y puerto_pico nulo. Los datos de batería y temperatura pueden ser nulos si no se pueden leer.

El navegador usa el mismo nombre de host que la página, puerto 8765. Reintenta 3 segundos después del cierre del WebSocket. La barra de 0–500 RPM es una escala visual provisional, no un límite del motor. No hay temporizador propio del navegador para detectar una conexión abierta que deja de enviar mensajes.

## Uso y diagnóstico en la Pi

Directorio: /home/olmos/agb-car-inteligent.

Comprobar sin mover motores:

    cd /home/olmos/agb-car-inteligent
    systemctl is-active agb-websocket.service
    journalctl -u agb-websocket.service -n 50 --no-pager
    ls -l /dev/ttyACM*

Abrir el panel en la red local: http://192.168.1.11:8080/ (dirección de la conexión comprobada en esta revisión; puede cambiar por DHCP).

Si el servidor HTTP no está activo, se puede servir solo la carpeta web con:

    cd /home/olmos/agb-car-inteligent
    python3 -m http.server 8080 --directory web

Este comando es una alternativa manual; no ejecutarlo si 8080 ya está ocupado. No se ha creado ni verificado un servicio de arranque automático para HTTP.

El servidor de telemetría utiliza .venv/bin/python. Para arranque manual, solo con el servicio detenido:

    .venv/bin/python src/servidor_ws.py

Dependencias directas del servidor: pyserial y websockets. requirements.txt conserva la captura del entorno actual, con numerosos paquetes ROS; no se ha validado como instalador portable de una Pi nueva. No reinstalarlo indiscriminadamente sobre el sistema funcional. Para reproducir el hardware también se necesitan MicroPython en Pico y el entorno Fusion HAT+ para las pruebas de motores; no se ha registrado su versión exacta en esta revisión.

La copia de main.py en Git no prueba que su contenido sea idéntico al archivo desplegado en la Pico. Antes de reflashear, conservar la copia que haya en la placa y comprobar la versión de MicroPython. No se ha reflasheado aquí.

## Pruebas y límites

Comunicado por el usuario: M0 y M1 comprobados individualmente; M2 y M3 juntos; los cuatro encoders muestran RPM al girar y 0 al detenerse; panel web con telemetría. No se conservan series numéricas de esas pruebas.

Verificado por acceso remoto el 24 de octubre de 2026: servicio WebSocket activo; recepción de JSON real con Pico conectada por /dev/ttyACM0, cuatro motores PARADO, RPM 0 y contadores acumulados distintos de cero; respuesta HTTP 200 con el panel AGB. Sintaxis de los seis archivos Python guardados comprobada sin ejecutarlos; revisión automática sin coincidencias de credenciales. No se han accionado motores, reiniciado servicios, reiniciado la Pi ni inspeccionado visualmente el panel en navegador durante esta revisión.

Pendientes: calibración de pulsos por vuelta y referencia del eje; cuatro motores simultáneos con registro de RPM; respuesta bajo carga; desconexión/reconexión USB observada; reinicio completo; arranque automático del HTTP; correspondencia entre firmware guardado y desplegado; sentido y cableado físicos. Las RPM no equivalen a velocidad lineal sin diámetro efectivo de rueda y validación mecánica.

## Siguiente etapa: PID

Conservar esta versión como referencia. Desarrollar un regulador por motor con consigna común, límites de potencia, protección frente a acumulación integral y parada ante pérdida de telemetría. Ajustar primero un motor y después comprobar el conjunto. No hay PID operativo en esta versión.

## Guardado y recuperación

    git status --short --branch
    git log -3 --oneline

El commit edc5caa conserva el código antes de la documentación y del PID. Para examinarlo sin cambiar los archivos del proyecto en uso, crear una copia separada con git worktree add --detach ../agb-car-referencia edc5caa. Ese comando prepara archivos; no cambia automáticamente el programa que esté ejecutando un servicio ni el firmware de la Pico.

## Actualización de correspondencia de canales durante pruebas PID
La tabla inicial refleja etiquetas del firmware. Se confirmó cruce de etiquetas M2/M3 respecto a puertos HAT. El servidor utiliza config/canales_encoders.json: M2 lee etiqueta Pico M3 (GP5), M3 lee M2 (GP4). M0/M1 conservan GP2/GP3. Ver docs/pid_velocidad.md para registros antes y después. No se modifica cableado ni firmware.
