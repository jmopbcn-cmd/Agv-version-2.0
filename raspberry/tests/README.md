# Manual de montaje y pruebas del AGV MC100

Revisión: 25 de octubre de 2026. Repositorio comprobado en la Raspberry: /home/olmos/agb-car-inteligent, equipo agv-mc100. Referencia de código al revisar: c2fb463ac9eb8f61852616d4f1a01e1b47b222a2.

Esta guía reúne procedimientos basados en archivos existentes. Los comandos de movimiento y de acceso directo a la Pico se documentan para ejecución manual posterior: no se ejecutaron al preparar este manual. Las instrucciones generales de instalación son preparación propuesta para una máquina nueva; no equivalen a una instalación desde cero ensayada.

## Índice y orden recomendado

1. [Preparación de Ubuntu y Python](#1-preparación-de-ubuntu-y-python).
2. [Red](#2-red).
3. [Conexiones y correspondencia de canales](#3-conexiones-y-correspondencia-de-canales).
4. [Servicios y WebSocket](#4-servicios-y-websocket).
5. [USB de la Pico](#5-usb-de-la-pico).
6. [Encoders individuales](#6-encoders-individuales).
7. [Cuatro encoders simultáneos](#7-cuatro-encoders-simultáneos).
8. [Motores individuales M0–M3](#8-motores-individuales-m0m3).
9. [Cuatro motores simultáneos](#9-cuatro-motores-simultáneos).
10. [Motores y encoders juntos](#10-motores-y-encoders-juntos).
11. [Web y pantalla ESP32E](#11-web-y-pantalla-esp32e).
12. [Errores, recuperación y registro](#12-errores-recuperación-y-registro).

Primero comprobar servicios y sensores en reposo, después girar discos a mano y por último realizar pruebas motorizadas. Para todas las pruebas físicas: chasis estable, sin ruedas por ahora o ejes completamente libres, cables apartados del giro y acceso al corte de alimentación de motores. No ejecutar dos programas que controlen motores a la vez. Detener el servicio de telemetría NO detiene un programa independiente de motores.

## 1. Preparación de Ubuntu y Python

### Equipo y archivos existentes

Se ha consultado Ubuntu 24.04.5 LTS, kernel 6.8.0-1065-raspi, en la Pi de este proyecto. No se ha reinstalado Ubuntu ni validado otra imagen. Para una unidad nueva hacen falta Ubuntu operativo, red, acceso de usuario y Fusion HAT+ con biblioteca y controlador compatibles. La versión y el procedimiento exacto de instalación del controlador HAT no están registrados de forma reproducible; no sustituirlos por un comando supuesto. Conservar el sistema funcional como referencia.

Comandos generales de Ubuntu, sin necesidad de activar .venv:

~~~bash
# Identificar la máquina y el sistema antes de instalar nada.
hostname
cat /etc/os-release
uname -r

# Solo en una máquina nueva: instalar utilidades básicas, no el controlador HAT.
sudo apt update
sudo apt install python3 python3-venv python3-pip git curl usbutils

# Solo si aún no existe la copia; usar el acceso GitHub autorizado de esa persona.
cd /home/olmos
git clone https://github.com/jmopbcn-cmd/Agv-version-2.0.git agb-car-inteligent

# En el equipo existente entrar directamente, sin volver a clonar encima.
cd /home/olmos/agb-car-inteligent
git status --short --branch
git log -3 --oneline
~~~

En otra instalación adaptar /home/olmos y User=olmos en las unidades systemd. Los archivos bajo sources/ del proyecto ChatGPT son referencias de solo lectura; el repositorio operativo es el de la Raspberry.

### Tres maneras de ejecutar Python

| Contexto | Ejemplo | Uso en este proyecto |
|---|---|---|
| Ubuntu, fuera de .venv | python3 ... | Pruebas de motores: aquí está disponible fusion_hat |
| .venv activado | source .venv/bin/activate; python ... | Servidor, bibliotecas USB y WebSocket |
| Ruta directa, sin activar | .venv/bin/python ... | Servicios y diagnósticos de telemetría; equivale al Python anterior |

Activar el entorno no instala fusion_hat. La revisión actual confirma que el Python del sistema encuentra esa biblioteca y .venv no la encuentra. No usar sudo python como solución genérica ni cambiar el entorno que funciona.

~~~bash
# Solo si NO existe .venv: crearlo desde la raíz del repositorio.
python3 -m venv .venv

# Solo para preparar un entorno nuevo: dependencias directas con versiones observadas.
.venv/bin/python -m pip install pyserial==3.5 websockets==17.3 mpremote==1.29.0

# Comprobar versiones sin abrir el USB ni inicializar motores.
.venv/bin/python -m pip show pyserial websockets mpremote
python3 -c 'import importlib.util; print(importlib.util.find_spec("fusion_hat"))'
.venv/bin/python -c 'import importlib.util; print(importlib.util.find_spec("fusion_hat"))'

# Alternativa con entorno activado: comprobar qué intérprete se usa.
source .venv/bin/activate
python -c 'import sys; print(sys.executable)'
python -m pip show pyserial websockets
# Volver al Python del sistema antes de pruebas de motores.
deactivate
~~~

Resultado esperado: biblioteca HAT localizable en el sistema y pyserial/websockets en .venv. requirements.txt contiene una captura amplia con ROS; no usar pip install -r requirements.txt indiscriminadamente para reconstruir una Pi nueva. Si falta fusion_hat o el controlador del HAT, detener la preparación de motores y completar esa instalación con la documentación correspondiente al hardware real. El servidor por sí solo no instala ni valida el HAT.

Prueba puramente de software, sin conexión ni movimiento de motores:

~~~bash
# Desde la raíz; solo prueba la clase matemática PID.
python3 raspberry/tests/test_pid.py
~~~

Esperado: cinco pruebas unitarias según el archivo actual. No ejecutar descubrimiento general de todos los archivos test_*.py: test_4_motores.py mueve hardware al ejecutarse/importarse.

## 2. Red

**Objetivo:** identificar IP, interfaces y ruta de salida. **Conexiones:** Pi conectada a la LAN; navegador y ESP32 en una red con acceso a la Pi.

~~~bash
# Ubuntu: IP de cada interfaz y direcciones del equipo.
ip -brief address
hostname -I
# Ver interfaces y dirección MAC (útil para reserva DHCP).
ip -brief link
ip link show wlan0
# Ver la puerta de enlace/rutas.
ip route
# Comprobar nombre local; su resolución depende de la red.
hostname
~~~

**Esperado:** en la revisión wlan0 está UP con 192.168.1.11/24; eth0 aparece DOWN. La IP puede cambiar por DHCP. Web: http://192.168.1.11:8080/; WebSocket: ws://192.168.1.11:8765/. Reservar la IP en el router facilita que la pantalla encuentre el servidor: el firmware guardado contiene esa dirección en RPI_IP.

**Problemas:** si no hay dirección, resolver red antes de Python. Si localhost funciona y otro equipo no, comprobar IP vigente, misma LAN, aislamiento Wi-Fi y reglas de acceso. No cambiar netplan ni abrir puertos a Internet como primer intento. Los puertos 8080 y 8765 ofrecen servicios diferentes.

## 3. Conexiones y correspondencia de canales

Cadena actual: Raspberry Pi 5 → Fusion HAT+ → motores; cuatro sensores → Pico → USB → Raspberry → WebSocket → web/ESP32.

| Puerto motor HAT | Posición usada por la prueba de motores | Invertido por software | Etiqueta USB Pico que publica ese motor | GPIO Pico correspondiente |
|---|---|---|---|---|
| M0 | Trasera izquierda | Sí | M0 | GP2 |
| M1 | Trasera derecha | No | M1 | GP3 |
| M2 | Delantera derecha | Sí | M3 | GP5 |
| M3 | Delantera izquierda | No | M2 | GP4 |

Fuentes: raspberry/tests/test_4_motores.py, firmware/PICO_2W/main.py y config/canales_encoders.json. El mapa M2/M3 fue corregido en el servidor tras pruebas individuales registradas; no cambiarlo para hacerlo coincidir con una tabla antigua. El JSON bruto USB y los diagnósticos Pico conservan sus etiquetas originales. Web, WebSocket y cliente PID ya usan los nombres corregidos de los puertos HAT.

GP2–GP5 son GPIO de Pico, no números físicos del conector ni GPIO de Raspberry. Los archivos usan el nombre Pico 2 W; el usuario identifica su placa como Pico 2WH. Verificar la identificación y MicroPython instalados antes de preparar otra placa; el nombre de carpeta no certifica la variante física.

Antes de cablear, identificar VCC, GND y salida digital de cada módulo LM393 por su serigrafía/esquema real. LM393 no define un pinout universal. Confirmar alimentación, masa común de señales y salida compatible con lógica de 3,3 V de Pico; una salida de 5 V requiere adaptación. No alimentar motores desde GPIO/USB. Verificar polaridad, alimentación del HAT y corriente de bloqueo de los motores. Este repositorio no aporta un esquema eléctrico completo ni un presupuesto de corriente verificado: no basta para certificar un montaje eléctrico desde cero.

Los programas Pico usan pull-up, flanco descendente, 20 pulsos/vuelta y cálculo cada 500 ms. Los 20 pulsos son configuración pendiente de calibración física; comprobar ranuras/flancos y eje de referencia. Un canal no mide el sentido de giro. Los totales se reinician al reiniciar el programa Pico.

## 4. Servicios y WebSocket

**Objetivo:** comprobar telemetría y arranque automático. **Conexiones:** Pi y HAT operativos, Pico USB con el main.py JSON funcional y sensores conectados para validar los cuatro canales.

| Servicio | Archivo del repositorio | Función |
|---|---|---|
| agb-websocket.service | deploy/agb-websocket.service | .venv/bin/python src/servidor_ws.py; puerto 8765 |
| agb-web.service | deploy/agb-web.service | .venv/bin/python -m http.server; carpeta web/; puerto 8080 |

~~~bash
cd /home/olmos/agb-car-inteligent
# Ubuntu: consultar estado y configuración efectiva, sin cambiarlos.
systemctl is-enabled agb-websocket.service agb-web.service
systemctl is-active agb-websocket.service agb-web.service
systemctl status agb-websocket.service agb-web.service --no-pager
systemctl cat agb-websocket.service agb-web.service
journalctl -b -u agb-websocket.service -u agb-web.service -n 80 --no-pager
ss -ltnp | grep -E ':8765|:8080'

# Directo con .venv: prueba existente de HTTP, batería y dos mensajes WebSocket.
.venv/bin/python deploy/comprobar_arranque.py
~~~

**Esperado:** ambos servicios enabled/active; HTTP idéntico a web/index.html; batería y voltaje numéricos; fusion_hat=true; Pico con datos recientes y cuatro RPM numéricas. En reposo esperar cuatro 0 RPM y comprobarlos en la salida: el comprobador exige valores numéricos, no exige que sean cero. No valida visualmente la pantalla ni demuestra giro físico.

El servidor escucha en todas las interfaces, transmite cada segundo, lee USB a 115200 y reconoce VID 2E8A/PID 0005. Además de batería/CPU/hora publica pico_conectada, puerto_pico, encoders, muestra_encoders y edad_encoders_s. Sin datos recientes de Pico (3 s) no debe interpretarse la última lectura como actual. fusion_hat=true acredita lectura de batería, no una prueba completa del HAT.

### Iniciar, detener y comprobar

Estos comandos son de Ubuntu; no necesitan activar .venv. Ejecutarlos manualmente solo cuando proceda; reiniciar telemetría durante PID puede provocar su parada por pérdida de datos.

~~~bash
# Iniciar o detener los servicios actuales.
sudo systemctl start agb-websocket.service agb-web.service
sudo systemctl stop agb-websocket.service agb-web.service
# Recargar los procesos tras un cambio aprobado de configuración/código.
sudo systemctl restart agb-websocket.service agb-web.service
# Activar arranque automático; desactivarlo no equivale a cortar motores.
sudo systemctl enable agb-websocket.service agb-web.service
sudo systemctl disable agb-websocket.service agb-web.service
# Consultar de nuevo después de la acción elegida.
systemctl status agb-websocket.service agb-web.service --no-pager
~~~

Son acciones alternativas; no pegar todo el bloque en secuencia. Para parar y deshabilitar un servicio en una sola orden existe systemctl disable --now NOMBRE.

### Instalación en otra Pi y ejecución manual

El instalador existente respalda unidades en /var/backups/agb-arranque-FECHA, instala HTTP y conserva la unidad WebSocket existente. Por eso NO instala por sí solo WebSocket en una Pi completamente nueva. Tras adaptar rutas/usuario y revisar las unidades:

~~~bash
# Solo máquina nueva sin unidad WebSocket: instalar su copia revisada.
sudo install -m 644 deploy/agb-websocket.service /etc/systemd/system/agb-websocket.service
# Instalar HTTP y habilitar/iniciar ambos con el instalador existente.
sudo sh deploy/instalar_arranque.sh
# Comprobar el resultado sin mover motores.
.venv/bin/python deploy/comprobar_arranque.py
~~~

En una Pi funcional conservar y comparar las unidades existentes antes de cualquier sustitución; no ejecutar el primer comando para sobrescribirlas. El instalador lleva rutas absolutas del equipo olmos.

Para diagnóstico manual, parar solo el servicio correspondiente y comprobar que el puerto queda libre:

~~~bash
# Terminal 1: alternativa manual del WebSocket, sin activar entorno.
sudo systemctl stop agb-websocket.service
.venv/bin/python src/servidor_ws.py
# Ctrl+C termina el proceso manual; después recuperar el servicio.
sudo systemctl start agb-websocket.service
~~~

~~~bash
# Alternativa HTTP manual desde la raíz; no ejecutar si ya está ocupado 8080.
sudo systemctl stop agb-web.service
.venv/bin/python -m http.server 8080 --bind 0.0.0.0 --directory web
# Ctrl+C; después restaurar el servicio.
sudo systemctl start agb-web.service
~~~

**Problemas:** Address already in use indica otra copia ocupando el puerto. No lanzar más copias. Si una unidad no existe, revisar instalación; si falla, consultar journalctl. No activar motores para diagnosticar el servidor.

## 5. USB de la Pico

**Objetivo:** identificar el dispositivo y distinguir detección USB de recepción válida. **Conexiones:** cable USB de datos entre Pi y Pico; firmware MicroPython/main.py funcional en Pico. La copia Git no demuestra identidad con lo instalado.

~~~bash
# Ubuntu: listar dispositivos; no interrumpe el programa Pico.
lsusb
ls -l /dev/ttyACM*
# Con .venv directo: listar puertos con identificadores USB.
.venv/bin/python -m serial.tools.list_ports -v
# Consultar usuario/grupos y permisos, sin modificarlos.
id
# Ver mensajes del lector del servicio.
journalctl -u agb-websocket.service -n 50 --no-pager
~~~

**Esperado:** puerto tipo /dev/ttyACM0 (puede cambiar) y telemetría reciente en el comprobador. El programa firmware/PICO_2W/main.py envía una línea JSON con tipo=encoders y objetos M0–M3 con rpm, pulsos_s, total y estado. firmware/PICO_2W/encoders.py imprime texto y NO es el programa para alimentar el servidor.

**Problemas:** cable solo de carga, permiso denegado, otro monitor serie abierto, aplicación incorrecta o VID/PID diferente. Un dispositivo USB enumerado no acredita datos JSON válidos. Si falta permiso, verificar el grupo propietario del dispositivo; si es dialout y el usuario no pertenece, un administrador puede añadirlo con sudo usermod -aG dialout olmos y renovar sesión/reiniciar el servicio cuando no haya pruebas. No aplicar chmod 777.

## 6. Encoders individuales

**Objetivo:** comprobar pulsos de un sensor girando el disco a mano, con alimentación de motores desconectada. **Conexiones:** Pico por USB, sensor y disco alineados, señal y alimentación verificadas según sección 3. No hace falta activar el HAT para girar a mano.

Los scripts existentes se ejecutan EN la Pico mediante mpremote, nunca con python3 de Ubuntu: importan machine. mpremote run ejecuta un archivo local temporalmente; no copia ni sustituye main.py. Sí interrumpe/reinicia la aplicación de MicroPython para ejecutar el diagnóstico. Reservar una sesión de mantenimiento y detener antes el lector USB.

~~~bash
cd /home/olmos/agb-car-inteligent
# Ubuntu: liberar USB; no tener ningún cliente PID en ejecución.
sudo systemctl stop agb-websocket.service
# Identificar el puerto real antes de usar el ejemplo /dev/ttyACM0.
.venv/bin/python -m serial.tools.list_ports -v

# Directo con .venv: ejecutar SOLO el diagnóstico elegido en la Pico.
.venv/bin/mpremote connect /dev/ttyACM0 run firmware/PICO_2W/test_encoder_m0.py
# Alternativas individuales; no pegarlas todas para ejecutarlas a la vez.
.venv/bin/mpremote connect /dev/ttyACM0 run firmware/PICO_2W/test_encoder_m1.py
.venv/bin/mpremote connect /dev/ttyACM0 run firmware/PICO_2W/test_encoder_m2.py
.venv/bin/mpremote connect /dev/ttyACM0 run firmware/PICO_2W/test_encoder_m3.py
~~~

| Archivo | GPIO realmente leído | Interpretación actual respecto al HAT |
|---|---|---|
| test_encoder_m0.py | GP2 | M0 |
| test_encoder_m1.py | GP3 | M1 |
| test_encoder_m2.py | GP4 | M3 tras el mapa del servidor |
| test_encoder_m3.py | GP5 | M2 tras el mapa del servidor |

Los diagnósticos M2/M3 se incorporan al repositorio tras revisión. Sus textos identifican la etiqueta Pico, el GPIO y el canal HAT correspondiente, sin modificar GPIO ni comportamiento. Esta revisión no los ejecutó en la Pico. La copia pico_main_backup.py coincide con firmware/PICO_2W/main.py al incorporarse; no acredita el contenido instalado en la placa.

**Esperado:** al girar el disco correspondiente aumentan total y pulsos/s y aparecen RPM positivas; al parar, RPM y pulsos/s vuelven a cero mientras total se conserva. Sin movimiento no debe crecer total. Registrar vueltas contadas para contrastar los 20 pulsos/vuelta.

Para terminar: Ctrl+C, cerrar mpremote y recuperar la aplicación JSON existente. Con el USB ya libre, reconectar físicamente la Pico reinicia su main.py instalado; esto reinicia contadores. No copiar firmware para recuperar una simple sesión de diagnóstico. Después:

~~~bash
# Ubuntu: recuperar lector y confirmar que vuelve JSON válido.
sudo systemctl start agb-websocket.service
.venv/bin/python deploy/comprobar_arranque.py
~~~

**Problemas:** sin pulsos, revisar disco, alineación, nivel digital y masa. Pulsos en reposo sugieren ruido/señal inestable; no aumentar potencia para compensar. Si cambia el canal mostrado respecto al HAT, recordar el mapa M2/M3. Si aparece ModuleNotFoundError: machine, el archivo se ha ejecutado en Ubuntu en vez de Pico.

## 7. Cuatro encoders simultáneos

**Objetivo:** comprobar independencia de los cuatro canales y su retorno a reposo. **Conexiones:** cuatro sensores/Pico/USB, discos libres y motores sin alimentación para giro manual.

Opción integrada recomendada: mantener el main.py JSON y los servicios activos, abrir la web y mover un disco cada vez, después varios a mano. Confirmar que solo aumenta el canal HAT correspondiente en cada prueba individual.

~~~bash
# Sin acceder directamente al USB: validar primero los cuatro canales publicados.
.venv/bin/python deploy/comprobar_arranque.py
~~~

Opción de consola Pico, en sesión de mantenimiento como la sección anterior:

~~~bash
# Liberar USB y ejecutar el diagnóstico existente de los cuatro GPIO.
sudo systemctl stop agb-websocket.service
.venv/bin/mpremote connect /dev/ttyACM0 run firmware/PICO_2W/encoders.py
# Tras Ctrl+C, cerrar mpremote, reiniciar Pico con su main.py y recuperar servicio.
sudo systemctl start agb-websocket.service
~~~

**Esperado:** cuatro líneas de estado; canales manipulados con pulsos y otros a cero, todos a cero después de detenerse. En consola Pico los nombres M2/M3 son anteriores al mapa; en web ya están corregidos. Los totales no tienen que coincidir entre canales.

**Problemas:** si hay salida de texto pero el servidor no reconoce encoders, sigue ejecutándose encoders.py; recuperar el main.py instalado. Si todos muestran datos antiguos, comprobar pico_conectada y antigüedad; no tratar una imagen congelada de la web como lectura viva.

## 8. Motores individuales M0–M3

**Objetivo:** comprobar un puerto cada vez y su encoder asociado con la herramienta existente. No hay cuatro archivos test_motor_m0.py…m3.py: se usa raspberry/probar_pid.py con --motores. Esta prueba depende de telemetría; no es una prueba de potencia abierta sin sensores.

**Conexiones:** alimentación HAT/motores correcta, chasis estable sin ruedas/ejes libres, Pico y cuatro sensores comprobados, servicios activos. Verificar mapa antes del movimiento. Ejecutar desde raíz, fuera de .venv: python3 del sistema dispone de fusion_hat y dependencias del cliente en este equipo.

~~~bash
cd /home/olmos/agb-car-inteligent
# Primero comprobar servicios y datos sin movimiento.
.venv/bin/python deploy/comprobar_arranque.py
# Comprobar la ayuda no inicia motores.
python3 raspberry/probar_pid.py --help
# Cada prueba necesita un nombre de registro que todavía no exista.
# SIN --mover: calcula órdenes y registra; no inicializa motores.
python3 raspberry/probar_pid.py --motores M0 --rpm 60 --segundos 5 --registro "registros/manual_sin_movimiento_$(date +%Y%m%d_%H%M%S).csv"
~~~

Los siguientes son comandos de MOVIMIENTO, para ejecutar uno por vez y comprobar parada entre pruebas. Ejemplos conservadores nuevos construidos con opciones existentes, no resultados físicos ya obtenidos:

~~~bash
# M0, trasera izquierda: prueba breve, consigna 60 RPM, límite de orden 25 %.
python3 raspberry/probar_pid.py --mover --motores M0 --rpm 60 --segundos 5 --potencia-max 25 --registro "registros/manual_M0_$(date +%Y%m%d_%H%M%S).csv"
# M1, trasera derecha; ejecutar después de verificar M0 detenido.
python3 raspberry/probar_pid.py --mover --motores M1 --rpm 60 --segundos 5 --potencia-max 25 --registro "registros/manual_M1_$(date +%Y%m%d_%H%M%S).csv"
# M2, delantera derecha; publicado desde GP5 por el mapa actual.
python3 raspberry/probar_pid.py --mover --motores M2 --rpm 60 --segundos 5 --potencia-max 25 --registro "registros/manual_M2_$(date +%Y%m%d_%H%M%S).csv"
# M3, delantera izquierda; publicado desde GP4 por el mapa actual.
python3 raspberry/probar_pid.py --mover --motores M3 --rpm 60 --segundos 5 --potencia-max 25 --registro "registros/manual_M3_$(date +%Y%m%d_%H%M%S).csv"
~~~

**Esperado:** gira solo el motor seleccionado, aumenta su contador publicado y registra RPM/potencia. El cliente solicita parada en finally; Ctrl+C/SIGTERM también pasan por esa salida. Confirmar físicamente la parada y varias muestras a 0 RPM antes de continuar. Una prueba de 5 s no valida estabilidad de regulación ni comportamiento bajo carga. Una consigna baja no garantiza giro ni ausencia de sobreimpulso.

**Problemas:** si no gira, revisar alimentación y HAT; si gira pero marca cero, detener y revisar encoder/mapa. El cliente corta tras 3 s sin pulsos con orden ≥10 %, o por datos caducados/ausentes/inválidos. No quitar esa protección ni subir potencia para ocultar el fallo. Ganancias y base provienen de config/pid_motores.json y son provisionales. Un error FileExistsError pide un nombre nuevo, no sobrescribir registros anteriores.

## 9. Cuatro motores simultáneos

**Objetivo:** conocer la prueba abierta existente y distinguirla de la regulación conjunta. **Conexiones:** cuatro motores en sus puertos HAT, alimentación dimensionada, chasis seguro y giro libre. Esta prueba no necesita Pico y NO verifica encoders ni corta por falta de pulsos.

~~~bash
# MOVIMIENTO: Ubuntu/Python del sistema, fuera de .venv, desde la raíz.
# El archivo aplica potencia 50 a los cuatro motores durante 10 segundos.
python3 raspberry/tests/test_4_motores.py
~~~

**Esperado:** cuatro motores giran a la vez y se solicita su parada al terminar. El archivo invierte M0/M2. No tiene argumentos de potencia ni duración: no inventar --potencia o --segundos para este script. Por su orden del 50 %, no es la primera prueba recomendada al montar el vehículo; completar antes las individuales limitadas.

**Problemas:** caída de tensión, reset o pérdida de USB al arrancar apuntan a revisar alimentación/corriente y cableado antes de repetir. Ctrl+C entra en finally, pero SIGKILL, bloqueo o fallo de hardware pueden impedir la parada. No ejecutar pytest sobre este archivo; no es una prueba unitaria.

## 10. Motores y encoders juntos

**Objetivo:** verificar correspondencia, lectura simultánea, registro y retorno a reposo con control PI provisional. **Conexiones:** las de las pruebas individuales; ambos servicios y main.py Pico activos. No abrir mpremote ni monitor USB durante la prueba.

~~~bash
# Sin movimiento: verifica prerequisitos y genera un CSV nuevo.
.venv/bin/python deploy/comprobar_arranque.py
python3 raspberry/probar_pid.py --motores M0,M1,M2,M3 --rpm 120 --segundos 5 --registro "registros/manual_cuatro_sin_mover_$(date +%Y%m%d_%H%M%S).csv"

# MOVIMIENTO, solo tras superar las individuales: procedimiento de 30 s.
# Usa la configuración guardada y limita la orden aplicada a 25 %.
python3 raspberry/probar_pid.py --mover --motores M0,M1,M2,M3 --rpm 120 --segundos 30 --potencia-max 25 --registro "registros/manual_cuatro_30s_$(date +%Y%m%d_%H%M%S).csv"

# Tras terminar, volver a consultar y confirmar físicamente parada/0 RPM.
.venv/bin/python deploy/comprobar_arranque.py
~~~

**Esperado:** cuatro RPM y órdenes registradas en CSV (segundos, motor, consigna_rpm, rpm, potencia, mover); final sin error y cuatro motores parados. El cliente usa muestras WebSocket cada segundo, no un lazo rápido. Actualmente kp=0.03, ki=0.02, kd=0, base=18 por motor. kd=0 significa PI con base, no derivada ajustada. Admite 1–60 s, consigna 0–120 RPM y límite máximo de orden 35 %. No cambiar esos límites para forzar un ensayo fallido.

**Evidencia histórica:** registros/pid_cuatro_30s_mapa_corregido_01.csv y su resumen documentan 30 s completados. Excluyendo 10 s de arranque: medias 121.16, 123.24, 119.96 y 121.74 RPM (M0–M3); hubo sobreimpulso inicial hasta 305.4 RPM. registros/pid_cuatro_40s_pantallas_01.csv documenta 40 s completados. No prueba trayectoria recta, carga en suelo ni calibración absoluta de RPM. Detalles y fallos previos en [PID](../../docs/pid_velocidad.md).

**Problemas:** datos repetidos, edad >1.25 s, falta de Pico/HAT o RPM inválidas causan corte. El bloqueo /tmp/agb-pid.lock impide dos copias de este cliente, no otros programas de motores. Detener desde la terminal de prueba con Ctrl+C y comprobar físicamente; no asumir que parar WebSocket es una parada de emergencia. El PID no está instalado como servicio de arranque.

## 11. Web y pantalla ESP32E

### Panel web

**Objetivo:** comprobar servicio HTTP, conexión WebSocket y actualización real. **Conexiones:** Pi, Pico y navegador accesible desde la misma LAN.

~~~bash
# Ubuntu: comprobar HTTP local y las unidades; no mueve motores.
curl -I http://127.0.0.1:8080/
systemctl is-active agb-web.service agb-websocket.service
# Diagnóstico existente: compara el HTML recibido con web/index.html.
.venv/bin/python deploy/comprobar_arranque.py
~~~

Abrir http://192.168.1.11:8080/ con la IP vigente. **Esperado:** panel de AGB, conexión activa, Pico conectada, CPU/batería/voltaje y cuatro canales. Con motores sin alimentación girar a mano un disco y confirmar su canal, después cero al parar. Comprobar que siguen llegando mensajes, no solo que cargó la página. No exigir que los totales sean iguales.

**Problemas:** HTML visible sin datos: revisar 8765; conexión rechazada a 8080: revisar HTTP. La web usa el host de la página para WebSocket. Si hay valores congelados, revisar conexión y caducidad en el servidor; el comprobador remoto no acredita el renderizado visual del navegador.

### Pantalla ESP32E

**Objetivo:** contrastar la pantalla física con la misma telemetría. **Conexiones:** pantalla alimentada, Wi-Fi correcto, Pi accesible en 192.168.1.11:8765. Referencia: firmware/PANTALLA_AGV_ESP32E28/PANTALLA_AGV_ESP32E28.ino, LCD ST7789 y táctil XPT2046. Ver [pantalla](../../docs/pantalla_v1.2.md) y [pines](../../docs/conexiones.md).

No hay un comando Ubuntu que demuestre por sí solo que la pantalla funciona. Ejecutar el comprobador anterior para validar el origen y luego observar conexión, temperatura/batería, navegación táctil y cuatro RPM. El firmware actual guardado lee encoders del JSON, descarta RPM inválidas y muestra RPM REALES o SIN DATOS ENCODERS; las referencias anteriores a RPM simuladas describen una versión antigua. Falta confirmar qué binario está instalado físicamente.

**Esperado:** valores coherentes con web, cambios de RPM del mismo canal al girar manualmente y retorno a cero; sin señal válida debe indicar ausencia de datos. Una pantalla a 0 RPM sin prueba de actualización no demuestra conexión.

**Problemas:** web correcta/pantalla incorrecta: revisar IP fija del firmware, red, alimentación, credenciales locales y versión instalada. secrets.h es local e ignorado; secrets.example.h es la plantilla. No publicar secretos ni reflashear como primer diagnóstico. Esta tarea no compiló ni cargó firmware.

## 12. Errores, recuperación y registro

| Error o síntoma observado/documentado | Interpretación y solución |
|---|---|
| fusion_hat no disponible en .venv | Usar Python del sistema fuera de .venv para los motores; no modificar el entorno funcional. |
| requirements.txt con paquetes ROS | Captura de entorno, no instalador portable validado; preparar solo dependencias directas indicadas y resolver HAT aparte. |
| Puerto 8080 no volvía tras arranque | Se añadió agb-web.service; hoy está habilitado y activo. Revisar unidad/registro si se repite. |
| USB sin datos o ocupado | Un solo lector; cerrar monitor/mpremote y recuperar main.py JSON. |
| Encoder gira físicamente pero muestra 0 | Parar; revisar señal y alineación. M1 tuvo fallos intermitentes sin causa identificada; una repetición correcta no explica el fallo anterior. |
| M2/M3 no corresponden a su motor | Cruce confirmado por giro individual y corregido en config/canales_encoders.json; no duplicar intercambio en firmware/cableado. |
| Diagnósticos antiguos M2/M3 dicen M1 | Textos copiados corregidos en esta revisión; identificar siempre GPIO y mapa Pico/HAT. |
| Cortes Sin pulsos durante 3 segundos | Protección del cliente. Corregir sensor/mapa; no eliminarla ni elevar potencia sin diagnóstico. |
| Overshoot/oscilación en PID | Ajuste provisional; analizar CSV, primero individual y con giro libre. No presentar media cercana a consigna como estabilidad demostrada. |
| Tras reinicio falta batería; I2C -110, fallo de probe 1-0017 | Fallo registrado el 24/10. Reasociar driver/reinicializar bus no recuperó batería; apagado completo posterior sí. No se demuestra resuelto el reinicio normal. |
| fusion_hat=true pero otra parte falla | El indicador procede de batería; no certifica motor, encoder ni pantalla. |
| CSV ya existe | El cliente abre en modo exclusivo; elegir nombre nuevo y conservar las medidas anteriores. |

Diagnóstico de batería/controlador, comandos de Ubuntu sin órdenes de movimiento:

~~~bash
# Consultar datos del controlador y errores del arranque actual.
ls -l /sys/class/power_supply/
cat /sys/class/power_supply/fusion-hat/capacity
cat /sys/class/power_supply/fusion-hat/voltage_now
journalctl -k -b --no-pager | grep -Ei 'fusion|i2c|timeout|1-0017'
~~~

No ejecutar automáticamente deploy/recuperar_fusion_hat.sh: reasocia un controlador y puede inicializar periféricos; su intento anterior no solucionó el fallo. Antes de apagar, terminar toda prueba de motores, confirmar parada, guardar registros y apagar Ubuntu ordenadamente. Un reinicio normal y un corte completo de alimentación son ensayos diferentes. Consultar [arranque](../../docs/arranque_y_reinicio.md) y [registro histórico](../../docs/registro_pruebas.md).

### Evidencia de esta revisión, sin movimiento

25/10/2026: acceso de lectura al repositorio real y unidades instaladas; ambos servicios enabled/active; HTTP coincide con web/index.html; dos mensajes con batería 99 %, voltaje 8.385 V, fusion_hat=true y M0–M3 a 0 RPM. Son valores de esa consulta, no estado permanente ni calibración. No se interrumpió USB, no se reiniciaron servicios y no se accionaron motores. No se inspeccionó visualmente web ni pantalla física. No se modificó firmware, configuración o ganancias.

### Hoja de registro para cada prueba futura

Anotar fecha, operador, commit, alimentación, ruedas/ejes libres, motor/GP/etiqueta probados, comando exacto, nombre CSV, duración prevista/real, observación física, RPM/contadores antes-durante-después, errores y parada confirmada. Separar observación del operador, lectura de telemetría y conclusión. Conservar registros originales.

### Límites para repetir el montaje desde cero

Esta guía permite seguir el software existente y sus pruebas sin inventar archivos. Para un montaje íntegramente reproducible siguen faltando: esquema eléctrico completo validado, revisión/serigrafía y tensiones de módulos reales, versión/instalación exacta del controlador Fusion HAT+, imagen y versión MicroPython desplegadas, copia contrastada del main.py instalado y validación del firmware físico ESP32. Completar esos datos antes de declarar otra unidad equivalente o validar uso en suelo.

## 13. Consultas adicionales de referencia

Estos ejemplos completan el diagnóstico sin crear nuevos archivos de prueba ni sustituir programas que ya funcionan. Trabajar desde /home/olmos/agb-car-inteligent. No pegar órdenes de mantenimiento durante una prueba de motores.

### Recibir dos mensajes WebSocket, sin abrir otro lector USB

Objetivo: ver los campos exactos publicados y distinguir falta de datos de un valor cero real. Conexiones: servidor activo; Pico/HAT operativos para validar también sus medidas. Ejecución directa con el entorno, sin activarlo:

~~~bash
# Solo recibe telemetría: no manda órdenes de motor ni accede directamente al USB.
.venv/bin/python - <<'PY'
import asyncio
import json
from websockets.asyncio.client import connect
async def main():
    async with connect('ws://127.0.0.1:8765/', open_timeout=5) as ws:
        for _ in range(2):
            datos = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            print(json.dumps(datos, ensure_ascii=False, indent=2))
asyncio.run(main())
PY
~~~

Esperado: hora actualizada, pico_conectada verdadero, cuatro objetos en encoders y medidas válidas; en reposo, cuatro RPM cero. Conexión rechazada: revisar servicio/8765. Pico falsa o encoders vacío: revisar sección USB. Los 0 RPM no sustituyen una prueba de giro.

### Leer el JSON USB directamente, sin programar la Pico

Objetivo: comprobar si la placa emite JSON antes de atribuir el fallo al servidor. Conexiones: Pico con su aplicación JSON ya instalada; cable USB de datos. Detener primero toda prueba de motores. Este método es alternativo al servidor y no se ejecuta simultáneamente con mpremote, Thonny ni otro monitor.

~~~bash
# Ubuntu general: liberar el lector, después de confirmar la parada de motores.
sudo systemctl stop agb-websocket.service

# Ejecución directa: leer ocho líneas y cerrar el puerto automáticamente.
# Cambiar /dev/ttyACM0 si la enumeración de puertos indicó otra ruta.
.venv/bin/python - <<'PY'
import serial
with serial.Serial('/dev/ttyACM0', 115200, timeout=2) as usb:
    for _ in range(8):
        print(usb.readline().decode('utf-8', errors='replace').strip())
PY

# Ubuntu general: restaurar la lectura normal una vez cerrado el puerto.
sudo systemctl start agb-websocket.service

# Ejecución directa: confirmar recuperación del conjunto.
.venv/bin/python deploy/comprobar_arranque.py
~~~

Esperado: objetos JSON con tipo encoders y canales M0–M3; las etiquetas aquí son las originales Pico, anteriores a la corrección M2/M3. Líneas vacías: comprobar cable, puerto y programa en ejecución. Texto de diagnóstico en lugar de JSON: recuperar el main.py instalado según la sección 6. Esta lectura no escribe archivos ni envía instrucciones a la placa. Los comandos se documentan para mantenimiento; no se abrió el USB en exclusiva durante esta revisión.

### Comprobar con .venv activado y volver al sistema

~~~bash
# Ubuntu general: entrar y activar el entorno de la terminal actual.
cd /home/olmos/agb-car-inteligent
source .venv/bin/activate

# Con .venv activado: diagnóstico existente de servicios y datos.
python deploy/comprobar_arranque.py

# Salir antes de usar python3 para motores.
deactivate

# Ubuntu general: consultar versión instalada sin inicializar motores.
/usr/bin/python3 -c 'import importlib.metadata as m; print(m.version("fusion_hat"))'
~~~

En la consulta del 25/10 se encontró fusion_hat 1.14.0 en el Python del sistema; .venv no contiene el módulo. Para evitar depender de si quedó un entorno activado, las órdenes de motor que empiezan por python3 en las secciones 8–10 se pueden ejecutar con /usr/bin/python3, el intérprete del sistema comprobado. Las órdenes .venv/bin/python seleccionan siempre el entorno, aunque no esté activado.

### Detalles de web, pantalla y terminal que evitan confusiones

- Abrir el panel por HTTP en la Pi, no index.html como archivo local: el JavaScript utiliza el host de la página para conectarse a 8765. El servicio actual no proporciona HTTPS/WSS.
- La barra 0–500 RPM es una escala visual provisional. La velocidad lineal de INICIO en la ESP32 no está calibrada ni se calcula a partir de las RPM en el firmware revisado.
- La copia ESP32 guardada configura serie a 115200, reintento WebSocket a 3 s y caducidad de datos a 5 s. Verificar físicamente INICIO, MOTORES y SISTEMA: el archivo no demuestra qué versión está grabada.
- No dejar código C++ del Arduino pegado en la terminal Ubuntu. Si aparece [200~cat: command not found, cancelar con Ctrl+C y volver a escribir solo el comando, sin el prompt olmos@agv-mc100 ni marcadores de pegado.
- FileExistsError exige un nombre CSV nuevo. Un bloqueo de /tmp/agb-pid.lock exige localizar y finalizar la prueba anterior normalmente; borrar el archivo para iniciar otro controlador no es una solución.
- El finally de test_4_motores.py solicita parada durante el bloque de prueba; además de los fallos forzados, un error al construir motores antes del try puede quedar fuera de esa protección. Confirmar la parada física.

La conversación disponible contiene confirmación del usuario de 0,0 y después valores cambiantes, pero no identifica con suficiente detalle todos los pasos ni qué pantalla se observaba. Se conserva como indicio comunicado; no se usa para certificar toda la pantalla ESP32 ni una prueba física nueva.

## Resultado posterior a esta guía: revisar antes de mover

La revisión motorizada posterior detectó incidencias: M0/M1 con picos a 60 RPM y M2 sin pulsos con lectura posterior M3. La correspondencia de la tabla representa la configuración guardada, pendiente de revalidación física actual. No ejecutar las pruebas conjuntas hasta resolverlo. Ver [resultados](../../registros/revision_20261025T175053_resultados.md).

## Ajuste posterior con sensores alineados

Las ganancias actuales guardadas son kp=0.005, ki=0.005, kd=0, base=18; sustituyen las citadas como historicas arriba. Dos pruebas conjuntas de 60 s a 120 RPM y limite 25 % completadas. Sigue siendo provisional: sobreimpulso y oscilacion residual pendientes. Ver [informe](../../registros/ajuste_20261025T182255_informe.md).
