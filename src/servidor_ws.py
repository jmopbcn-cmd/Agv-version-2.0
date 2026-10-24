
import asyncio
import json
import threading
import time

from datetime import datetime
from pathlib import Path

import serial
from serial.tools import list_ports
from websockets.asyncio.server import serve

# =========================================
# AGB CAR INTELIGENT - SERVIDOR PRINCIPAL
# =========================================

TEMPERATURA = Path("/sys/class/thermal/thermal_zone0/temp")
BATERIA = Path("/sys/class/power_supply/fusion-hat")

PUERTO_WS = 8765
TIMEOUT_PICO = 3.0

# Motor del HAT -> etiqueta recibida de la Pico; comprobado por giro individual.
CANALES_ENCODERS = json.loads((Path(__file__).resolve().parents[1] / "config/canales_encoders.json").read_text())
if set(CANALES_ENCODERS) != {"M0", "M1", "M2", "M3"} or set(CANALES_ENCODERS.values()) != {"M0", "M1", "M2", "M3"}:
    raise ValueError("Mapa de encoders no valido")

# Datos compartidos entre lectura USB y servidor
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

            with serial.Serial(puerto, 115200, timeout=2) as usb:
                with lock:
                    puerto_pico = puerto

                while True:
                    linea = usb.readline()

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
            print("Error USB Pico:", error, flush=True)

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


async def atender_cliente(websocket):
    print("Cliente conectado:", websocket.remote_address)

    try:
        while True:
            datos = obtener_datos()
            await websocket.send(json.dumps(datos))
            await asyncio.sleep(1)
    except Exception as error:
        print("Cliente desconectado:", error)


async def main():
    # Leer los encoders en un hilo independiente
    threading.Thread(
        target=lector_pico,
        daemon=True
    ).start()

    async with serve(
        atender_cliente,
        "0.0.0.0",
        PUERTO_WS
    ):
        print(
            "Servidor AGV iniciado en puerto",
            PUERTO_WS,
            flush=True
        )
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
