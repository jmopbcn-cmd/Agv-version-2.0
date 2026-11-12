
import asyncio
import json
import logging
import os
import threading
import time
import signal
from urllib.parse import urlsplit
from control_motores import ControlMotores

from datetime import datetime
from pathlib import Path

import serial
from serial.tools import list_ports
from websockets.asyncio.server import serve

# =========================================
# AGV CAR INTELIGENT - SERVIDOR PRINCIPAL
# =========================================

TEMPERATURA = Path("/sys/class/thermal/thermal_zone0/temp")
BATERIA = Path("/sys/class/power_supply/fusion-hat")

PUERTO_WS = 8765
LOG = logging.getLogger("agv")
TIMEOUT_PICO = 3.0
PUERTO_UART_PICO = Path("/dev/ttyAMA0")

# Motor del HAT -> etiqueta recibida de la Pico; comprobado por giro individual.
CANALES_ENCODERS = json.loads((Path(__file__).resolve().parents[1] / "config/canales_encoders.json").read_text())
if set(CANALES_ENCODERS) != {"M0", "M1", "M2", "M3"} or set(CANALES_ENCODERS.values()) != {"M0", "M1", "M2", "M3"}:
    raise ValueError("Mapa de encoders no valido")

# Datos compartidos entre el lector serie y el servidor
lock = threading.Lock()
encoders = {}
ultima_lectura = 0.0
puerto_pico = None


def leer_numero(nombre):
    try:
        return int((BATERIA / nombre).read_text().strip())
    except (OSError, ValueError):
        return None


def leer_estado():
    try:
        return (BATERIA / "status").read_text().strip()
    except OSError:
        return "Unknown"


def buscar_pico():
    # En la Pi 5 del AGV, la UART de la Fusion HAT+ sale por /dev/ttyAMA0.
    # Para diagnosticar por USB, se puede forzar la búsqueda del dispositivo MicroPython.
    if os.environ.get("AGV_PICO_PORT") != "usb" and PUERTO_UART_PICO.exists():
        return str(PUERTO_UART_PICO)

    # Raspberry Pi Pico con MicroPython:
    # VID 0x2E8A, PID habitual 0x0005
    for puerto in list_ports.comports():
        if puerto.vid == 0x2E8A and puerto.pid == 0x0005:
            return puerto.device
    return None


def lector_pico():
    global encoders, ultima_lectura, puerto_pico

    while True:
        try:
            puerto = buscar_pico()

            if puerto is None:
                time.sleep(2)
                continue

            print("Pico detectada:", puerto, flush=True)

            with serial.Serial(puerto, 115200, timeout=2) as enlace:
                with lock:
                    puerto_pico = puerto

                while True:
                    linea = enlace.readline()

                    if not linea:
                        continue

                    try:
                        datos = json.loads(
                            linea.decode("utf-8").strip()
                        )
                    except (UnicodeError, ValueError):
                        continue

                    if datos.get("tipo") != "encoders":
                        continue

                    with lock:
                        encoders = {
                            motor: datos[CANALES_ENCODERS[motor]]
                            for motor in ("M0", "M1", "M2", "M3")
                            if isinstance(datos.get(CANALES_ENCODERS[motor]), dict)
                        }
                        ultima_lectura = time.monotonic()

        except (OSError, serial.SerialException) as error:
            print("Error serie Pico:", error, flush=True)

        finally:
            with lock:
                puerto_pico = None

        time.sleep(2)


def obtener_datos():
    try:
        temperatura = round(
            int(TEMPERATURA.read_text().strip()) / 1000, 1
        )
    except (OSError, ValueError):
        temperatura = None

    porcentaje = leer_numero("capacity")
    microvoltios = leer_numero("voltage_now")

    voltaje = (
        round(microvoltios / 1_000_000, 3)
        if microvoltios is not None else None
    )

    with lock:
        recientes = (
            ultima_lectura > 0
            and time.monotonic() - ultima_lectura < TIMEOUT_PICO
        )
        datos_encoders = dict(encoders) if recientes else {}
        puerto = puerto_pico if recientes else None
        muestra = ultima_lectura if recientes else None
        edad = time.monotonic() - ultima_lectura if ultima_lectura else None

    return {
        "dispositivo": "agv-mc100",
        "temperatura_cpu": temperatura,
        "bateria": porcentaje,
        "voltaje": voltaje,
        "estado_bateria": leer_estado(),
        "fusion_hat": porcentaje is not None,
        "pico_conectada": recientes,
        "puerto_pico": puerto,
        "encoders": datos_encoders,
        "muestra_encoders": muestra,
        "edad_encoders_s": round(edad, 3) if edad is not None else None,
        "hora": datetime.now().isoformat(timespec="seconds")
    }


control_motores = ControlMotores()

def origen_permitido(websocket):
    origen = websocket.request.headers.get('Origin')
    host = websocket.request.headers.get('Host', '')
    return not origen or (urlsplit(origen).scheme in ('http', 'https') and
                          urlsplit(origen).hostname == urlsplit('//' + host).hostname)

async def atender_cliente(websocket):
    async def publicar():
        while True:
            datos = obtener_datos()
            datos['control_motores'] = control_motores.estado(websocket)
            await websocket.send(json.dumps(datos))
            await asyncio.sleep(1)
    publicador = asyncio.create_task(publicar())
    try:
        async for mensaje in websocket:
            try:
                if not origen_permitido(websocket):
                    raise ValueError('El control solo se acepta desde el panel del mismo equipo')
                orden = json.loads(mensaje)
                if not isinstance(orden, dict):
                    raise ValueError('Orden no valida')
                tipo = orden.get('tipo')
                if tipo == 'motor':
                    if orden.get('activo') and not obtener_datos()['fusion_hat']:
                        raise ValueError('Fusion HAT no disponible')
                    await control_motores.ordenar(websocket, orden.get('motor'), orden.get('activo'), orden.get('potencia'))
                elif tipo == 'renovar_motores':
                    control_motores.renovar(websocket)
                    continue
                elif tipo == 'parar_motores':
                    await control_motores.parar()
                else:
                    raise ValueError('Orden desconocida')
                await websocket.send(json.dumps({'tipo': 'control_motores', 'estado': control_motores.estado(websocket)}))
            except (ValueError, TypeError, KeyError) as error:
                await websocket.send(json.dumps({'tipo': 'error_control', 'error': str(error), 'estado': control_motores.estado(websocket)}))
    finally:
        publicador.cancel()
        await asyncio.gather(publicador, return_exceptions=True)
        await control_motores.parar(websocket)


async def registrar_estado_agv():
    # El journal de systemd conserva estos eventos aunque nadie abra el panel.
    bateria_anterior = None
    pico_anterior = None
    error_anterior = None
    proximo_registro = 0
    while True:
        datos = obtener_datos()
        porcentaje = datos['bateria']
        voltaje = datos['voltaje']
        estado = datos['estado_bateria']
        if porcentaje is None:
            nivel = 'sin lectura'
        elif porcentaje <= 10:
            nivel = 'critica'
        elif porcentaje <= 20:
            nivel = 'baja'
        else:
            nivel = 'normal'

        ahora = time.monotonic()
        bateria_actual = (nivel, estado)
        if bateria_actual != bateria_anterior or ahora >= proximo_registro:
            # Los avisos se emiten al cambiar de estado. Las muestras periódicas
            # dejan constancia de la última tensión antes de un corte de energía.
            gravedad = logging.INFO
            if bateria_actual != bateria_anterior and nivel != 'normal':
                gravedad = logging.ERROR if nivel == 'critica' else logging.WARNING
            LOG.log(gravedad, 'BATERIA nivel=%s carga=%s%% voltaje=%s V estado=%s',
                    nivel, porcentaje, voltaje, estado)
            bateria_anterior = bateria_actual
            proximo_registro = ahora + 60

        pico = datos['pico_conectada']
        if pico != pico_anterior:
            if pico:
                LOG.info('PICO telemetría activa puerto=%s', datos['puerto_pico'])
            else:
                LOG.warning('PICO sin muestras recientes de encoders')
            pico_anterior = pico

        error = control_motores.error
        if error != error_anterior:
            if error:
                LOG.error('MOTORES fallo de control: %s', error)
            else:
                LOG.info('MOTORES fallo de control despejado')
            error_anterior = error
        await asyncio.sleep(1)


async def main():
    threading.Thread(target=lector_pico, daemon=True).start()
    vigilancia = asyncio.create_task(control_motores.vigilar())
    registro = asyncio.create_task(registrar_estado_agv())
    apagado = asyncio.Event()
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, apagado.set)
    try:
        async with serve(atender_cliente, '0.0.0.0', PUERTO_WS, max_size=4096):
            print('Servidor AGV iniciado en puerto', PUERTO_WS, flush=True)
            await apagado.wait()
    finally:
        vigilancia.cancel()
        registro.cancel()
        await asyncio.gather(vigilancia, registro, return_exceptions=True)
        await control_motores.parar()


if __name__ == '__main__':
    LOG.setLevel(logging.INFO)
    salida = logging.StreamHandler()
    salida.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    LOG.addHandler(salida)
    asyncio.run(main())
